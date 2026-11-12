"""Ownership and Hand-off engine — guarantees single owner invariant and manages hand-offs."""

from __future__ import annotations

from datetime import datetime
from typing import Optional, Tuple

from sqlalchemy.orm import Session

from app.core.clock import get_clock
from app.core.ids import generate_id
from app.db.models import Case, CaseEvent, Provider, User, UserRole
from app.core.hashing import compute_event_hash


class OwnershipError(Exception):
    """Raised when an ownership or hand-off invariant is violated."""
    pass


class OwnershipEngine:
    """Manages assignment, hand-off offer/accept, and caseload limits."""

    def __init__(self, db: Session):
        self.db = db
        self.clock = get_clock()

    def assign_case(
        self, case_id: str, new_owner_id: str, actor_id: str, actor_role: str
    ) -> Case:
        """Assign or reassign a case to a new owner."""
        case = self.db.query(Case).filter(Case.id == case_id).one()
        user = self.db.query(User).filter(User.id == new_owner_id).one()

        old_owner_id = case.owner_id
        case.owner_id = user.id
        case.owner_provider_id = user.provider_id

        # Record event
        self._record_ownership_event(
            case_id=case.id,
            event_type="case_assigned",
            actor_id=actor_id,
            actor_role=actor_role,
            payload={
                "previous_owner_id": old_owner_id,
                "new_owner_id": user.id,
                "provider_id": user.provider_id,
            },
        )
        self.db.flush()
        return case

    def offer_handoff(
        self,
        case_id: str,
        to_provider_id: str,
        to_user_id: Optional[str],
        actor_id: str,
        actor_role: str,
    ) -> CaseEvent:
        """Offer a hand-off of case ownership to another provider/user."""
        case = self.db.query(Case).filter(Case.id == case_id).one()

        event = self._record_ownership_event(
            case_id=case.id,
            event_type="handoff_offered",
            actor_id=actor_id,
            actor_role=actor_role,
            payload={
                "from_owner_id": case.owner_id,
                "from_provider_id": case.owner_provider_id,
                "to_provider_id": to_provider_id,
                "to_user_id": to_user_id,
                "status": "pending_acceptance",
            },
        )
        self.db.flush()
        return event

    def accept_handoff(
        self, case_id: str, accepting_user_id: str, actor_role: str
    ) -> Tuple[Case, CaseEvent]:
        """Accept an offered hand-off, transferring ownership."""
        case = self.db.query(Case).filter(Case.id == case_id).one()
        user = self.db.query(User).filter(User.id == accepting_user_id).one()

        old_owner = case.owner_id
        case.owner_id = user.id
        case.owner_provider_id = user.provider_id

        event = self._record_ownership_event(
            case_id=case.id,
            event_type="handoff_accepted",
            actor_id=accepting_user_id,
            actor_role=actor_role,
            payload={
                "previous_owner_id": old_owner,
                "new_owner_id": user.id,
                "new_provider_id": user.provider_id,
            },
        )
        self.db.flush()
        return case, event

    def _record_ownership_event(
        self,
        case_id: str,
        event_type: str,
        actor_id: str,
        actor_role: str,
        payload: dict,
    ) -> CaseEvent:
        now = self.clock.now()
        last_event = (
            self.db.query(CaseEvent)
            .filter(CaseEvent.case_id == case_id)
            .order_by(CaseEvent.seq.desc())
            .first()
        )
        prev_hash = last_event.hash if last_event else "genesis"
        next_seq = (last_event.seq + 1) if last_event else 1

        event_data = {
            "case_id": case_id,
            "seq": next_seq,
            "event_type": event_type,
            "actor_id": actor_id,
            "actor_role": actor_role,
            "occurred_at": now.isoformat(),
            "payload": payload,
        }
        event_hash = compute_event_hash(event_data, prev_hash)

        import json
        event = CaseEvent(
            id=generate_id(),
            case_id=case_id,
            seq=next_seq,
            event_type=event_type,
            from_state=None,
            to_state=None,
            actor_id=actor_id,
            actor_role=actor_role,
            occurred_at=now,
            payload_json=json.dumps(payload),
            prev_hash=prev_hash,
            hash=event_hash,
        )
        self.db.add(event)
        return event
