"""State machine — enforces legal case transitions based on a pathway config."""

from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy.orm import Session

from app.core.clock import get_clock
from app.core.hashing import compute_event_hash
from app.core.ids import generate_id
from app.db.models import Case, CaseEvent
from app.domain.pathway_loader import PathwayConfig


# ---------------------------------------------------------------------------
# Custom exception
# ---------------------------------------------------------------------------
class IllegalTransitionError(Exception):
    """Raised when a state transition is not allowed by the pathway."""

    def __init__(self, from_state: str, to_state: str, reason: str = "") -> None:
        self.from_state = from_state
        self.to_state = to_state
        self.reason = reason
        msg = f"Illegal transition: {from_state} → {to_state}"
        if reason:
            msg += f" ({reason})"
        super().__init__(msg)


# ---------------------------------------------------------------------------
# State machine
# ---------------------------------------------------------------------------
class StateMachine:
    """Validates and executes state transitions for a pathway."""

    CLOSED_STATE = "CLOSED"

    def __init__(self, pathway: PathwayConfig) -> None:
        self._pathway = pathway
        # Build transition lookup
        self._transitions: dict[str, list[str]] = {}
        for step in pathway.steps:
            self._transitions[step.id] = list(step.next)

    def can_transition(self, from_state: str, to_state: str) -> bool:
        """Return ``True`` if *from_state* → *to_state* is a legal move."""
        if to_state == self.CLOSED_STATE:
            return False  # must go through closure guard
        allowed = self._transitions.get(from_state, [])
        return to_state in allowed

    def get_allowed_next_states(self, current_state: str) -> list[str]:
        """Return the list of states reachable from *current_state*.

        The CLOSED state is never listed here — use the closure guard.
        """
        nexts = list(self._transitions.get(current_state, []))
        if self.CLOSED_STATE in nexts:
            nexts.remove(self.CLOSED_STATE)
        return nexts

    def transition(
        self,
        case_id: str,
        from_state: str,
        to_state: str,
        actor_id: str,
        actor_role: str,
        evidence: dict | None = None,
        *,
        db: Session,
    ) -> CaseEvent:
        """Execute a transition: validate, create a CaseEvent, update the Case.

        Raises :class:`IllegalTransitionError` if the move is forbidden.
        """
        # Block direct transitions to CLOSED
        if to_state == self.CLOSED_STATE:
            raise IllegalTransitionError(
                from_state,
                to_state,
                "CLOSED can only be reached via the closure guard",
            )

        if not self.can_transition(from_state, to_state):
            raise IllegalTransitionError(from_state, to_state, "not in pathway transitions")

        clock = get_clock()
        now = clock.now()

        # Determine the previous hash in the chain for this case
        last_event: CaseEvent | None = (
            db.query(CaseEvent)
            .filter(CaseEvent.case_id == case_id)
            .order_by(CaseEvent.seq.desc())
            .first()
        )
        prev_hash = last_event.hash if last_event else "genesis"
        next_seq = (last_event.seq + 1) if last_event else 1

        # Build event data for hashing
        event_data = {
            "case_id": case_id,
            "seq": next_seq,
            "event_type": "state_transition",
            "from_state": from_state,
            "to_state": to_state,
            "actor_id": actor_id,
            "actor_role": actor_role,
            "occurred_at": now.isoformat(),
        }
        if evidence:
            event_data["evidence"] = evidence

        event_hash = compute_event_hash(event_data, prev_hash)

        event = CaseEvent(
            id=generate_id(),
            case_id=case_id,
            seq=next_seq,
            event_type="state_transition",
            from_state=from_state,
            to_state=to_state,
            actor_id=actor_id,
            actor_role=actor_role,
            occurred_at=now,
            payload_json=json.dumps(evidence) if evidence else None,
            prev_hash=prev_hash,
            hash=event_hash,
        )
        db.add(event)

        # Update the case record
        case = db.query(Case).filter(Case.id == case_id).one()
        case.current_state = to_state
        db.flush()

        return event
