"""Closure guard — enforces human-approval and evidence checks before closing a case."""

from __future__ import annotations

import json

from sqlalchemy.orm import Session

from app.core.clock import get_clock
from app.core.hashing import compute_event_hash
from app.core.ids import generate_id
from app.db.models import (
    Case,
    CaseEvent,
    ClosureProposal,
    ClosureProposalStatus,
    Escalation,
    Evidence,
    User,
    UserRole,
)


class ClosureGuardError(Exception):
    """Raised when a case cannot be closed due to unmet requirements."""

    def __init__(self, reasons: list[str]) -> None:
        self.reasons = reasons
        super().__init__(f"Closure blocked: {'; '.join(reasons)}")


class ClosureGuard:
    """Validates that all closure pre-conditions are met before sealing a case."""

    CLOSED_STATE = "CLOSED"

    def can_close(self, case_id: str, db: Session) -> tuple[bool, list[str]]:
        """Check whether *case_id* meets all closure requirements.

        Returns ``(True, [])`` when the case may be closed, or
        ``(False, [reason, ...])`` listing every failed check.
        """
        reasons: list[str] = []

        # 1. Approved closure proposal must exist
        approved_proposal: ClosureProposal | None = (
            db.query(ClosureProposal)
            .filter(
                ClosureProposal.case_id == case_id,
                ClosureProposal.status == ClosureProposalStatus.approved,
            )
            .first()
        )
        if approved_proposal is None:
            reasons.append("No approved closure proposal exists for this case")
        else:
            # 2. Approver must be a human with clinician or supervisor role
            #    and decision_reason must be non-empty
            if approved_proposal.decided_by is None:
                reasons.append("Closure proposal has no decider")
            else:
                decider: User | None = (
                    db.query(User)
                    .filter(User.id == approved_proposal.decided_by)
                    .first()
                )
                if decider is None:
                    reasons.append("Decider user not found")
                elif decider.role not in (UserRole.clinician, UserRole.supervisor):
                    reasons.append(
                        f"Decider role must be clinician or supervisor, got {decider.role.value}"
                    )
            if not approved_proposal.decision_reason or not approved_proposal.decision_reason.strip():
                reasons.append("Closure proposal decision_reason is empty")

        # 3. Evidence of an allowed type must be attached
        case: Case | None = db.query(Case).filter(Case.id == case_id).first()
        if case is None:
            reasons.append(f"Case {case_id} not found")
            return (False, reasons)

        evidence_count = (
            db.query(Evidence)
            .filter(Evidence.case_id == case_id)
            .count()
        )
        if evidence_count == 0:
            reasons.append("No evidence attached to the case")

        # 4. No open (unresolved) escalation
        open_escalations = (
            db.query(Escalation)
            .filter(
                Escalation.case_id == case_id,
                Escalation.resolved_at.is_(None),
            )
            .count()
        )
        if open_escalations > 0:
            reasons.append(
                f"{open_escalations} unresolved escalation(s) remain on the case"
            )

        return (len(reasons) == 0, reasons)

    def close_case(
        self, case_id: str, actor_id: str, db: Session
    ) -> CaseEvent:
        """Close a case after verifying all guard conditions.

        Raises :class:`ClosureGuardError` if pre-conditions are not met.
        """
        ok, reasons = self.can_close(case_id, db)
        if not ok:
            raise ClosureGuardError(reasons)

        clock = get_clock()
        now = clock.now()

        case = db.query(Case).filter(Case.id == case_id).one()
        actor = db.query(User).filter(User.id == actor_id).one()

        # Build the closing event
        last_event: CaseEvent | None = (
            db.query(CaseEvent)
            .filter(CaseEvent.case_id == case_id)
            .order_by(CaseEvent.seq.desc())
            .first()
        )
        prev_hash = last_event.hash if last_event else "genesis"
        next_seq = (last_event.seq + 1) if last_event else 1

        event_data = {
            "case_id": case_id,
            "seq": next_seq,
            "event_type": "case_closed",
            "from_state": case.current_state,
            "to_state": self.CLOSED_STATE,
            "actor_id": actor_id,
            "actor_role": actor.role.value if hasattr(actor.role, "value") else actor.role,
            "occurred_at": now.isoformat(),
        }
        event_hash = compute_event_hash(event_data, prev_hash)

        event = CaseEvent(
            id=generate_id(),
            case_id=case_id,
            seq=next_seq,
            event_type="case_closed",
            from_state=case.current_state,
            to_state=self.CLOSED_STATE,
            actor_id=actor_id,
            actor_role=actor.role.value if hasattr(actor.role, "value") else actor.role,
            occurred_at=now,
            payload_json=None,
            prev_hash=prev_hash,
            hash=event_hash,
        )
        db.add(event)

        case.current_state = self.CLOSED_STATE
        case.closed_at = now
        db.flush()

        return event
