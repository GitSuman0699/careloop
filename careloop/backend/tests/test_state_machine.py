"""Tests for the case state machine."""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("CLOCK_MODE", "simulated")
from app.core.clock import SimulatedClock, _reset_clock
from app.db.models import Case, CaseEvent
from app.domain.pathway_loader import PathwayConfig
from app.domain.state_machine import IllegalTransitionError, StateMachine


# ---------------------------------------------------------------------------
# Helper — build a test pathway in-memory
# ---------------------------------------------------------------------------

def _make_test_pathway() -> PathwayConfig:
    """Return a PathwayConfig with a simple linear sequence for testing."""
    return PathwayConfig.model_validate(
        {
            "id": "test_fit",
            "title": "Test FIT Pathway",
            "version": "0.1.0",
            "steps": [
                {
                    "id": "RESULT_ISSUED",
                    "label": "Result issued",
                    "next": ["PATIENT_NOTIFIED"],
                },
                {
                    "id": "PATIENT_NOTIFIED",
                    "label": "Patient notified",
                    "next": ["PATIENT_ACKNOWLEDGED"],
                },
                {
                    "id": "PATIENT_ACKNOWLEDGED",
                    "label": "Patient acknowledged",
                    "next": ["CONFIRMATION_PENDING"],
                },
                {
                    "id": "CONFIRMATION_PENDING",
                    "label": "Confirmation pending",
                    "next": ["CONFIRMATION_DONE"],
                },
                {
                    "id": "CONFIRMATION_DONE",
                    "label": "Confirmation done",
                    "next": ["REFERRAL_SENT"],
                },
                {
                    "id": "REFERRAL_SENT",
                    "label": "Referral sent",
                    "next": ["REFERRAL_ACCEPTED"],
                },
                {
                    "id": "REFERRAL_ACCEPTED",
                    "label": "Referral accepted",
                    "next": ["APPOINTMENT_BOOKED"],
                },
                {
                    "id": "APPOINTMENT_BOOKED",
                    "label": "Appointment booked",
                    "next": ["APPOINTMENT_ATTENDED"],
                },
                {
                    "id": "APPOINTMENT_ATTENDED",
                    "label": "Appointment attended",
                    "next": ["TREATMENT_OR_SURVEILLANCE"],
                },
                {
                    "id": "TREATMENT_OR_SURVEILLANCE",
                    "label": "Treatment or surveillance",
                    "next": ["CLOSURE_PROPOSED"],
                },
                {
                    "id": "CLOSURE_PROPOSED",
                    "label": "Closure proposed",
                    "next": ["CLOSED"],
                },
                {
                    "id": "CLOSED",
                    "label": "Closed",
                    "next": [],
                },
            ],
            "closure": {
                "requires_human_approval": True,
                "allowed_types": ["completed_treatment"],
            },
        }
    )


@pytest.fixture()
def test_pathway() -> PathwayConfig:
    return _make_test_pathway()


@pytest.fixture()
def state_machine(test_pathway) -> StateMachine:
    return StateMachine(test_pathway)


@pytest.fixture(autouse=True)
def reset_clock():
    _reset_clock()
    os.environ["CLOCK_MODE"] = "simulated"
    yield
    _reset_clock()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestCanTransition:
    def test_legal_transition_succeeds(self, state_machine):
        """RESULT_ISSUED → PATIENT_NOTIFIED is a legal move."""
        assert state_machine.can_transition("RESULT_ISSUED", "PATIENT_NOTIFIED") is True

    def test_illegal_transition_raises(self, state_machine):
        """RESULT_ISSUED → CLOSED returns False (direct close blocked)."""
        # can_transition returns False for CLOSED regardless of pathway
        assert state_machine.can_transition("RESULT_ISSUED", "CLOSED") is False

    def test_skip_state_blocked(self, state_machine):
        """Skipping a step (RESULT_ISSUED → PATIENT_ACKNOWLEDGED) returns False."""
        assert state_machine.can_transition("RESULT_ISSUED", "PATIENT_ACKNOWLEDGED") is False

    def test_backwards_transition_blocked(self, state_machine):
        """Reverse transition is blocked."""
        assert state_machine.can_transition("PATIENT_NOTIFIED", "RESULT_ISSUED") is False


class TestGetAllowedNextStates:
    def test_get_allowed_next_states(self, state_machine):
        """RESULT_ISSUED → [PATIENT_NOTIFIED] only."""
        allowed = state_machine.get_allowed_next_states("RESULT_ISSUED")
        assert allowed == ["PATIENT_NOTIFIED"]

    def test_closed_excluded_from_allowed_next(self, state_machine):
        """CLOSED is never listed in get_allowed_next_states even if in pathway."""
        # CLOSURE_PROPOSED has CLOSED as next — but CLOSED is excluded
        allowed = state_machine.get_allowed_next_states("CLOSURE_PROPOSED")
        assert "CLOSED" not in allowed

    def test_unknown_state_returns_empty(self, state_machine):
        """Unknown state returns empty list."""
        allowed = state_machine.get_allowed_next_states("NONEXISTENT_STATE")
        assert allowed == []


class TestTransition:
    def test_legal_transition_in_db(
        self, state_machine, db_session, sample_case, sample_user
    ):
        """A legal transition creates a CaseEvent and updates Case.current_state."""
        event = state_machine.transition(
            case_id=sample_case.id,
            from_state="RESULT_ISSUED",
            to_state="PATIENT_NOTIFIED",
            actor_id=sample_user.id,
            actor_role="navigator",
            db=db_session,
        )
        db_session.commit()

        assert isinstance(event, CaseEvent)
        assert event.from_state == "RESULT_ISSUED"
        assert event.to_state == "PATIENT_NOTIFIED"
        assert event.actor_id == sample_user.id
        assert event.actor_role == "navigator"
        assert event.event_type == "state_transition"

    def test_case_state_updated_on_transition(
        self, state_machine, db_session, sample_case, sample_user
    ):
        """Case.current_state is updated after a transition."""
        state_machine.transition(
            case_id=sample_case.id,
            from_state="RESULT_ISSUED",
            to_state="PATIENT_NOTIFIED",
            actor_id=sample_user.id,
            actor_role="navigator",
            db=db_session,
        )
        db_session.commit()
        db_session.refresh(sample_case)
        assert sample_case.current_state == "PATIENT_NOTIFIED"

    def test_event_created_on_transition(
        self, state_machine, db_session, sample_case, sample_user
    ):
        """transition() writes a CaseEvent row with correct fields."""
        state_machine.transition(
            case_id=sample_case.id,
            from_state="RESULT_ISSUED",
            to_state="PATIENT_NOTIFIED",
            actor_id=sample_user.id,
            actor_role="navigator",
            db=db_session,
        )
        db_session.commit()

        events = (
            db_session.query(CaseEvent)
            .filter(CaseEvent.case_id == sample_case.id)
            .all()
        )
        assert len(events) == 1
        ev = events[0]
        assert ev.seq == 1
        assert ev.prev_hash == "genesis"
        assert ev.hash != ""
        assert ev.occurred_at is not None

    def test_illegal_transition_raises_error(
        self, state_machine, db_session, sample_case, sample_user
    ):
        """RESULT_ISSUED → CLOSED raises IllegalTransitionError."""
        with pytest.raises(IllegalTransitionError):
            state_machine.transition(
                case_id=sample_case.id,
                from_state="RESULT_ISSUED",
                to_state="CLOSED",
                actor_id=sample_user.id,
                actor_role="navigator",
                db=db_session,
            )

    def test_direct_close_blocked(
        self, state_machine, db_session, sample_case, sample_user
    ):
        """Any state → CLOSED via transition() raises IllegalTransitionError (closure guard required)."""
        with pytest.raises(IllegalTransitionError):
            state_machine.transition(
                case_id=sample_case.id,
                from_state="CLOSURE_PROPOSED",
                to_state="CLOSED",
                actor_id=sample_user.id,
                actor_role="navigator",
                db=db_session,
            )

    def test_skip_transition_raises(
        self, state_machine, db_session, sample_case, sample_user
    ):
        """Skipping steps raises IllegalTransitionError."""
        with pytest.raises(IllegalTransitionError):
            state_machine.transition(
                case_id=sample_case.id,
                from_state="RESULT_ISSUED",
                to_state="CONFIRMATION_PENDING",
                actor_id=sample_user.id,
                actor_role="navigator",
                db=db_session,
            )

    def test_all_pathway_transitions_valid(self, test_pathway):
        """Every step's 'next' entries reference steps that exist in the pathway."""
        step_ids = {s.id for s in test_pathway.steps}
        for step in test_pathway.steps:
            for next_state in step.next:
                assert next_state in step_ids, (
                    f"Step '{step.id}' references unknown next state '{next_state}'"
                )

    def test_hash_chain_seq_increments(
        self, state_machine, db_session, sample_case, sample_user
    ):
        """Consecutive transitions produce seq 1, 2, ... with chained hashes."""
        sm = state_machine

        ev1 = sm.transition(
            case_id=sample_case.id,
            from_state="RESULT_ISSUED",
            to_state="PATIENT_NOTIFIED",
            actor_id=sample_user.id,
            actor_role="navigator",
            db=db_session,
        )
        ev2 = sm.transition(
            case_id=sample_case.id,
            from_state="PATIENT_NOTIFIED",
            to_state="PATIENT_ACKNOWLEDGED",
            actor_id=sample_user.id,
            actor_role="navigator",
            db=db_session,
        )
        db_session.commit()

        assert ev1.seq == 1
        assert ev2.seq == 2
        assert ev2.prev_hash == ev1.hash
