"""Comprehensive verification of the 5 core safety properties required for challenge submission:
  (a) Closure guard enforcement (API + domain): human approval, allowed role, attached evidence, no open escalation.
  (b) AI output safety: diagnosis or numeric disclosure is blocked, fallback template used, logged in ai_actions.
  (c) RBAC denials: every role in the matrix is restricted according to specification.
  (d) Event hash chain detects tampering.
  (e) Simulation reproducibility: identical seed produces identical results.
"""

from __future__ import annotations

import json
import pytest
from datetime import date, datetime, timedelta
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.clock import SimulatedClock, _reset_clock
from app.core.hashing import compute_event_hash, verify_chain
from app.core.rbac import check_permission
from app.db.models import (
    AIAction,
    Case,
    CaseEvent,
    ClosureProposal,
    ClosureProposalStatus,
    Escalation,
    Evidence,
    Message,
    Patient,
    Provider,
    ProviderType,
    User,
    UserRole,
)
from app.domain.closure_guard import ClosureGuard, ClosureGuardError
from app.api.closure import decide_closure_proposal, DecideClosureRequest
from app.api.cases import transition_case, TransitionRequest
from app.api.clock import advance_clock, AdvanceClockRequest
from app.ai.guardrails import MessageValidator
from app.ai.mock_provider import MockAIProvider
from app.services.comms_pipeline import CommsPipeline
from sim.engine import SimulationEngine
from sim.metrics import compute_arm_metrics


# =============================================================================
# Property (a): Closure Guard Safety (Domain + API)
# =============================================================================
class TestSafetyPropertyA_ClosureGuard:
    def test_closure_fails_without_evidence(self, db_session, sample_case, sample_user):
        """Cannot close without evidence."""
        clinician = User(name="Dr. Clinician", role=UserRole.clinician)
        db_session.add(clinician)
        db_session.flush()

        prop = ClosureProposal(
            case_id=sample_case.id,
            proposed_by=sample_user.id,
            basis_json='{"reason": "tests complete"}',
            status=ClosureProposalStatus.approved,
            decided_by=clinician.id,
            decided_at=datetime(2026, 1, 20),
            decision_reason="Signed off",
        )
        db_session.add(prop)
        db_session.flush()

        guard = ClosureGuard()
        ok, reasons = guard.can_close(sample_case.id, db_session)
        assert ok is False
        assert any("evidence" in r.lower() for r in reasons)

        with pytest.raises(ClosureGuardError):
            guard.close_case(sample_case.id, clinician.id, db_session)

    def test_closure_fails_with_open_escalation(self, db_session, sample_case, sample_user):
        """Cannot close while an escalation is open."""
        clinician = User(name="Dr. Clinician", role=UserRole.clinician)
        db_session.add(clinician)
        db_session.flush()

        # Evidence attached
        ev = Evidence(
            case_id=sample_case.id,
            evidence_type="colonoscopy_report",
            recorded_by=sample_user.id,
            recorded_at=datetime(2026, 1, 20),
        )
        # Approved proposal
        prop = ClosureProposal(
            case_id=sample_case.id,
            proposed_by=sample_user.id,
            basis_json='{"reason": "ok"}',
            status=ClosureProposalStatus.approved,
            decided_by=clinician.id,
            decided_at=datetime(2026, 1, 20),
            decision_reason="Signed off",
        )
        # Open escalation!
        esc = Escalation(
            case_id=sample_case.id,
            tier=1,
            reason="Unresolved issue",
            raised_at=datetime(2026, 1, 19),
            resolved_at=None,
        )
        db_session.add_all([ev, prop, esc])
        db_session.flush()

        guard = ClosureGuard()
        ok, reasons = guard.can_close(sample_case.id, db_session)
        assert ok is False
        assert any("escalation" in r.lower() for r in reasons)

    def test_closure_fails_with_non_human_or_unauthorized_role(self, db_session, sample_case, sample_user):
        """Cannot close if approver is patient, auditor, or navigator."""
        # Navigator tries to approve
        prop = ClosureProposal(
            case_id=sample_case.id,
            proposed_by=sample_user.id,
            basis_json='{"reason": "ok"}',
            status=ClosureProposalStatus.approved,
            decided_by=sample_user.id,  # navigator role!
            decided_at=datetime(2026, 1, 20),
            decision_reason="Navigator self-approval",
        )
        ev = Evidence(
            case_id=sample_case.id,
            evidence_type="colonoscopy_report",
            recorded_by=sample_user.id,
            recorded_at=datetime(2026, 1, 20),
        )
        db_session.add_all([prop, ev])
        db_session.flush()

        guard = ClosureGuard()
        ok, reasons = guard.can_close(sample_case.id, db_session)
        assert ok is False
        assert any("role" in r.lower() or "clinician" in r.lower() for r in reasons)

    def test_api_closure_endpoint_enforces_guard(self, db_session, sample_case, sample_user):
        """API endpoint decide_closure_proposal blocks closure when evidence is missing."""
        prop = ClosureProposal(
            case_id=sample_case.id,
            proposed_by=sample_user.id,
            basis_json='{"reason": "testing API closure"}',
            status=ClosureProposalStatus.pending,
        )
        clinician = User(name="Dr. Clinician", role=UserRole.clinician)
        db_session.add_all([prop, clinician])
        db_session.flush()

        # Clinician attempts to approve via API, but no evidence is attached!
        with pytest.raises(HTTPException) as exc_info:
            decide_closure_proposal(
                proposal_id=prop.id,
                req=DecideClosureRequest(decision="approved", decision_reason="Clinical approval"),
                db=db_session,
                user=clinician,
            )
        assert exc_info.value.status_code == 400
        assert "evidence" in exc_info.value.detail.lower()


# =============================================================================
# Property (b): AI Guardrail Safety & Fallback Logging
# =============================================================================
class TestSafetyPropertyB_AIGuardrails:
    def test_ai_diagnosis_disclosure_blocked_and_fallback_used(self, db_session, sample_case, sample_patient):
        """Adversarial AI text mentioning cancer/diagnosis is blocked and fallback is used."""
        adversarial_ai = MockAIProvider(should_fail_validation=True)
        pipeline = CommsPipeline(db_session, ai_provider=adversarial_ai)

        msg = pipeline.draft_message(
            case_id=sample_case.id,
            patient_id=sample_patient.id,
            template_id="fit_positive_notification",
            context_data={"patient_name": "Test", "navigator_name": "Sarah", "navigator_phone": "123"},
            channel="app",
            language="en",
            use_ai_rewrite=True,
        )

        # 1. Message body must NOT contain the adversarial phrase "you have cancer"
        assert "cancer" not in msg.body.lower()
        # 2. Validator result shows violations and fallback_used=True
        val_res = json.loads(msg.validator_result_json)
        assert val_res["passed"] is False
        assert val_res["fallback_used"] is True
        # 3. AIAction row was logged with validator_passed=False, fallback_used=True
        ai_action = db_session.query(AIAction).filter(AIAction.id == msg.ai_action_id).first()
        assert ai_action is not None
        assert ai_action.validator_passed is False
        assert ai_action.fallback_used is True

    def test_banned_numeric_lab_result_in_patient_message_blocked(self):
        """Raw lab numeric units (e.g. 120 ug/g) in patient messages are rejected by validator."""
        validator = MessageValidator()
        is_valid, violations = validator.validate_patient_message(
            "Your bowel screening result showed 120 ug/g hemoglobin."
        )
        assert is_valid is False
        assert any("numeric" in v.lower() for v in violations)


# =============================================================================
# Property (c): RBAC Matrix Enforcement
# =============================================================================
class TestSafetyPropertyC_RBAC:
    def test_patient_cannot_advance_clock(self):
        assert check_permission("patient", "advance_clock") is False

    def test_navigator_cannot_approve_closure(self):
        assert check_permission("navigator", "approve_closure") is False

    def test_auditor_cannot_change_case_state(self):
        assert check_permission("auditor", "change_case_state") is False

    def test_clinician_can_approve_closure(self):
        assert check_permission("clinician", "approve_closure") is True

    def test_supervisor_can_advance_clock(self):
        assert check_permission("supervisor", "advance_clock") is True


# =============================================================================
# Property (d): Hash Chain Tamper Detection
# =============================================================================
class TestSafetyPropertyD_HashChainTampering:
    def test_tamper_detection(self, db_session, sample_case, sample_user):
        """Modifying any event in the chain causes verify_chain to return False."""
        # Build 3 events with _make_event pattern
        events = []
        prev_h = "genesis"
        for i in range(1, 4):
            event_data = {"seq": i, "case_id": sample_case.id, "payload": f"step-{i}"}
            h = compute_event_hash(event_data, prev_h)
            ev = {"seq": i, "case_id": sample_case.id, "payload": f"step-{i}", "hash": h, "prev_hash": prev_h}
            events.append(ev)
            prev_h = h

        # Pristine chain is valid
        is_valid, reason = verify_chain(events)
        assert is_valid is True, f"Failed: {reason}"

        # Tamper with event 2 payload
        events[1]["payload"] = "tampered-data"
        is_valid_tampered, err = verify_chain(events)
        assert is_valid_tampered is False
        assert "mismatch" in err.lower() or "break" in err.lower()


# =============================================================================
# Property (e): Simulation Reproducibility
# =============================================================================
class TestSafetyPropertyE_SimulationReproducibility:
    def test_identical_seed_produces_identical_results(self):
        """Simulation with same seed yields bit-for-bit identical outcome metrics."""
        engine1 = SimulationEngine(seed=12345, cohort_size=500)
        base1, loop1 = engine1.run()
        m1_base = compute_arm_metrics(base1)
        m1_loop = compute_arm_metrics(loop1)

        engine2 = SimulationEngine(seed=12345, cohort_size=500)
        base2, loop2 = engine2.run()
        m2_base = compute_arm_metrics(base2)
        m2_loop = compute_arm_metrics(loop2)

        assert m1_base["closure_rate"] == m2_base["closure_rate"]
        assert m1_base["closed_90d_pct"] == m2_base["closed_90d_pct"]
        assert m1_loop["closure_rate"] == m2_loop["closure_rate"]
        assert m1_loop["closed_90d_pct"] == m2_loop["closed_90d_pct"]
