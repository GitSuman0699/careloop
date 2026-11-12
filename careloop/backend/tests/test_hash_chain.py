"""Tests for the tamper-evident hash chain."""

from __future__ import annotations

import copy

from app.core.hashing import compute_event_hash, verify_chain


def _make_event(seq: int, data: dict, prev_hash: str) -> dict:
    """Build a chain event dict with computed hash."""
    event_data = {"seq": seq, **data}
    h = compute_event_hash(event_data, prev_hash)
    return {"seq": seq, **data, "hash": h, "prev_hash": prev_hash}


class TestComputeEventHash:
    def test_compute_hash_deterministic(self):
        """Same inputs always produce the same hash."""
        data = {"case_id": "abc", "event_type": "state_transition"}
        h1 = compute_event_hash(data, "genesis")
        h2 = compute_event_hash(data, "genesis")
        assert h1 == h2

    def test_compute_hash_changes_with_data(self):
        """Different event_data produces a different hash."""
        data_a = {"case_id": "abc", "event_type": "state_transition"}
        data_b = {"case_id": "abc", "event_type": "case_closed"}
        assert compute_event_hash(data_a, "genesis") != compute_event_hash(data_b, "genesis")

    def test_compute_hash_changes_with_prev_hash(self):
        """Same data but different prev_hash produces a different hash."""
        data = {"case_id": "abc"}
        assert compute_event_hash(data, "genesis") != compute_event_hash(data, "other_hash")

    def test_compute_hash_returns_hex_string(self):
        """Hash is a 64-char lowercase hex string (SHA-256)."""
        h = compute_event_hash({"x": 1}, "genesis")
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)


class TestVerifyChain:
    def test_verify_chain_empty(self):
        """An empty list of events is a valid chain."""
        ok, reason = verify_chain([])
        assert ok is True
        assert reason is None

    def test_verify_chain_valid(self):
        """A correctly constructed chain passes verification."""
        e1 = _make_event(1, {"case_id": "c1", "event_type": "init"}, "genesis")
        e2 = _make_event(2, {"case_id": "c1", "event_type": "notify"}, e1["hash"])
        e3 = _make_event(3, {"case_id": "c1", "event_type": "close"}, e2["hash"])
        ok, reason = verify_chain([e1, e2, e3])
        assert ok is True
        assert reason is None

    def test_verify_chain_tampered(self):
        """Modifying an event's data breaks verification."""
        e1 = _make_event(1, {"case_id": "c1", "event_type": "init"}, "genesis")
        e2 = _make_event(2, {"case_id": "c1", "event_type": "notify"}, e1["hash"])

        # Tamper with e1's data without updating hash
        tampered = copy.deepcopy(e1)
        tampered["event_type"] = "TAMPERED"

        ok, reason = verify_chain([tampered, e2])
        assert ok is False
        assert reason is not None

    def test_verify_chain_broken_link(self):
        """A prev_hash that doesn't match the preceding event's hash is caught."""
        e1 = _make_event(1, {"case_id": "c1", "event_type": "init"}, "genesis")
        # e2 references wrong prev_hash
        e2 = _make_event(2, {"case_id": "c1", "event_type": "notify"}, "wrong_prev")

        ok, reason = verify_chain([e1, e2])
        assert ok is False
        assert reason is not None

    def test_verify_chain_single_event(self):
        """A single valid event verifies successfully."""
        e1 = _make_event(1, {"case_id": "c1", "type": "init"}, "genesis")
        ok, reason = verify_chain([e1])
        assert ok is True

    def test_chain_built_by_transitions(self, db_session, sample_case, sample_user, fit_pathway):
        """Events created by StateMachine.transition form a valid chain."""
        import os
        os.environ["CLOCK_MODE"] = "simulated"
        from app.core.clock import _reset_clock
        _reset_clock()

        from app.domain.state_machine import StateMachine
        sm = StateMachine(fit_pathway)

        # Perform a valid transition
        sm.transition(
            case_id=sample_case.id,
            from_state="RESULT_ISSUED",
            to_state="PATIENT_NOTIFIED",
            actor_id=sample_user.id,
            actor_role="navigator",
            db=db_session,
        )
        db_session.commit()

        from app.db.models import CaseEvent
        events = (
            db_session.query(CaseEvent)
            .filter(CaseEvent.case_id == sample_case.id)
            .order_by(CaseEvent.seq)
            .all()
        )

        # Serialize to dicts for verify_chain
        chain = [
            {
                "seq": ev.seq,
                "case_id": ev.case_id,
                "event_type": ev.event_type,
                "from_state": ev.from_state,
                "to_state": ev.to_state,
                "actor_id": ev.actor_id,
                "actor_role": ev.actor_role,
                "occurred_at": ev.occurred_at.isoformat(),
                "hash": ev.hash,
                "prev_hash": ev.prev_hash,
            }
            for ev in events
        ]
        ok, reason = verify_chain(chain)
        assert ok is True, f"Chain invalid: {reason}"
