"""Tests for the closure guard."""

from __future__ import annotations

import os
from datetime import datetime

import pytest

os.environ.setdefault("CLOCK_MODE", "simulated")
from app.core.clock import _reset_clock
from app.db.models import (
    Case,
    ClosureProposal,
    ClosureProposalStatus,
    Escalation,
    Evidence,
    User,
    UserRole,
)
from app.domain.closure_guard import ClosureGuard, ClosureGuardError


@pytest.fixture(autouse=True)
def reset_clock_fixture():
    _reset_clock()
    os.environ["CLOCK_MODE"] = "simulated"
    yield
    _reset_clock()


@pytest.fixture()
def clinician_user(db_session, sample_provider):
    """A User with clinician role."""
    user = User(name="Test Clinician", role=UserRole.clinician, provider_id=sample_provider.id)
    db_session.add(user)
    db_session.flush()
    return user


@pytest.fixture()
def supervisor_user(db_session, sample_provider):
    """A User with supervisor role."""
    user = User(name="Test Supervisor", role=UserRole.supervisor, provider_id=sample_provider.id)
    db_session.add(user)
    db_session.flush()
    return user


@pytest.fixture()
def ai_user(db_session, sample_provider):
    """A User that simulates an AI agent (navigator role — AI cannot be clinician/supervisor)."""
    user = User(name="AI Agent", role=UserRole.navigator, provider_id=sample_provider.id)
    db_session.add(user)
    db_session.flush()
    return user


def _add_evidence(db_session, case_id, recorded_by_id):
    ev = Evidence(
        case_id=case_id,
        evidence_type="colonoscopy_report",
        recorded_by=recorded_by_id,
        recorded_at=datetime(2026, 1, 20, 10, 0, 0),
    )
    db_session.add(ev)
    db_session.flush()
    return ev


def _add_approved_proposal(db_session, case_id, proposed_by, decided_by_id, decision_reason="Clinician reviewed and approved"):
    proposal = ClosureProposal(
        case_id=case_id,
        proposed_by=proposed_by,
        basis_json='{"type": "completed_treatment"}',
        status=ClosureProposalStatus.approved,
        decided_by=decided_by_id,
        decided_at=datetime(2026, 1, 20, 11, 0, 0),
        decision_reason=decision_reason,
    )
    db_session.add(proposal)
    db_session.flush()
    return proposal


class TestClosureGuardCanClose:
    def test_closure_without_proposal_fails(self, db_session, sample_case):
        """can_close fails when there is no approved closure proposal."""
        guard = ClosureGuard()
        ok, reasons = guard.can_close(sample_case.id, db_session)
        assert ok is False
        assert any("proposal" in r.lower() for r in reasons)

    def test_closure_without_human_approval_fails(self, db_session, sample_case, sample_user):
        """can_close fails when the proposal has no decider (decided_by=None)."""
        proposal = ClosureProposal(
            case_id=sample_case.id,
            proposed_by=sample_user.id,
            basis_json='{"type": "completed_treatment"}',
            status=ClosureProposalStatus.approved,
            decided_by=None,  # No decider
            decision_reason="Some reason",
        )
        db_session.add(proposal)
        db_session.flush()

        guard = ClosureGuard()
        ok, reasons = guard.can_close(sample_case.id, db_session)
        assert ok is False
        assert any("decider" in r.lower() for r in reasons)

    def test_closure_with_ai_approval_fails(self, db_session, sample_case, ai_user, sample_user):
        """
        proposed_by='ai' with the decider being a navigator (not clinician/supervisor) fails.
        AI cannot approve a closure — only clinician or supervisor can.
        """
        # ai_user has navigator role, which is not allowed to approve closure
        proposal = ClosureProposal(
            case_id=sample_case.id,
            proposed_by="ai",
            basis_json='{"type": "completed_treatment"}',
            status=ClosureProposalStatus.approved,
            decided_by=ai_user.id,  # navigator role — not authorized
            decided_at=datetime(2026, 1, 20, 11, 0, 0),
            decision_reason="AI decided this should close",
        )
        db_session.add(proposal)
        db_session.flush()

        guard = ClosureGuard()
        ok, reasons = guard.can_close(sample_case.id, db_session)
        assert ok is False
        assert any("clinician" in r.lower() or "supervisor" in r.lower() or "role" in r.lower() for r in reasons)

    def test_closure_without_evidence_fails(self, db_session, sample_case, clinician_user, sample_user):
        """can_close fails when no evidence is attached."""
        _add_approved_proposal(db_session, sample_case.id, sample_user.id, clinician_user.id)
        # No evidence added

        guard = ClosureGuard()
        ok, reasons = guard.can_close(sample_case.id, db_session)
        assert ok is False
        assert any("evidence" in r.lower() for r in reasons)

    def test_closure_with_open_escalation_fails(
        self, db_session, sample_case, clinician_user, sample_user
    ):
        """can_close fails when there is an unresolved escalation."""
        _add_approved_proposal(db_session, sample_case.id, sample_user.id, clinician_user.id)
        _add_evidence(db_session, sample_case.id, sample_user.id)

        escalation = Escalation(
            case_id=sample_case.id,
            tier=1,
            reason="SLA breach",
            raised_at=datetime(2026, 1, 16, 9, 0, 0),
            resolved_at=None,  # Still open
        )
        db_session.add(escalation)
        db_session.flush()

        guard = ClosureGuard()
        ok, reasons = guard.can_close(sample_case.id, db_session)
        assert ok is False
        assert any("escalation" in r.lower() for r in reasons)

    def test_closure_without_decision_reason_fails(
        self, db_session, sample_case, clinician_user, sample_user
    ):
        """can_close fails when decision_reason is empty or whitespace."""
        proposal = ClosureProposal(
            case_id=sample_case.id,
            proposed_by=sample_user.id,
            basis_json='{"type": "completed_treatment"}',
            status=ClosureProposalStatus.approved,
            decided_by=clinician_user.id,
            decided_at=datetime(2026, 1, 20, 11, 0, 0),
            decision_reason="   ",  # whitespace only — invalid
        )
        db_session.add(proposal)
        db_session.flush()
        _add_evidence(db_session, sample_case.id, sample_user.id)

        guard = ClosureGuard()
        ok, reasons = guard.can_close(sample_case.id, db_session)
        assert ok is False
        assert any("reason" in r.lower() for r in reasons)

    def test_closure_with_all_conditions_succeeds(
        self, db_session, sample_case, clinician_user, sample_user
    ):
        """can_close returns True when all conditions are met."""
        _add_approved_proposal(db_session, sample_case.id, sample_user.id, clinician_user.id)
        _add_evidence(db_session, sample_case.id, sample_user.id)
        # No open escalations

        guard = ClosureGuard()
        ok, reasons = guard.can_close(sample_case.id, db_session)
        assert ok is True, f"Expected success but got reasons: {reasons}"
        assert reasons == []

    def test_adversarial_ai_closure_attempt(self, db_session, sample_case, ai_user, sample_user):
        """
        CRITICAL: Simulate an AI trying to close a case by setting proposed_by='ai'
        AND decided_by to a navigator-role user (the closest an AI user can get).
        This MUST fail — only clinician/supervisor can approve closure.
        """
        # An AI creates the proposal and also tries to approve it via a navigator user
        proposal = ClosureProposal(
            case_id=sample_case.id,
            proposed_by="ai",
            basis_json='{"type": "completed_treatment", "ai_confidence": 0.99}',
            status=ClosureProposalStatus.approved,
            decided_by=ai_user.id,  # Navigator role — not authorized to approve
            decided_at=datetime(2026, 1, 20, 11, 0, 0),
            decision_reason="Automated closure: all pathway steps completed",
        )
        db_session.add(proposal)
        db_session.flush()
        _add_evidence(db_session, sample_case.id, sample_user.id)

        guard = ClosureGuard()
        ok, reasons = guard.can_close(sample_case.id, db_session)

        # Must fail — AI cannot close a case
        assert ok is False, "SAFETY VIOLATION: AI was able to close a case without human approval"
        assert any(
            "clinician" in r.lower() or "supervisor" in r.lower() or "role" in r.lower()
            for r in reasons
        ), f"Expected role-related failure reason, got: {reasons}"


class TestClosureGuardCloseCase:
    def test_close_case_raises_when_conditions_not_met(
        self, db_session, sample_case, sample_user
    ):
        """close_case() raises ClosureGuardError when pre-conditions are unmet."""
        guard = ClosureGuard()
        with pytest.raises(ClosureGuardError) as exc_info:
            guard.close_case(sample_case.id, sample_user.id, db_session)
        assert exc_info.value.reasons

    def test_close_case_succeeds_with_all_conditions(
        self, db_session, sample_case, clinician_user, sample_user
    ):
        """close_case() succeeds when all conditions are met."""
        _add_approved_proposal(db_session, sample_case.id, sample_user.id, clinician_user.id)
        _add_evidence(db_session, sample_case.id, sample_user.id)

        guard = ClosureGuard()
        event = guard.close_case(sample_case.id, clinician_user.id, db_session)
        db_session.commit()

        assert event.to_state == "CLOSED"
        db_session.refresh(sample_case)
        assert sample_case.current_state == "CLOSED"
        assert sample_case.closed_at is not None
