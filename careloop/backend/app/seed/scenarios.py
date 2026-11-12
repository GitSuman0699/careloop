"""Demo scenarios A to F for the 7-minute judge presentation."""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from typing import Dict, List
from sqlalchemy.orm import Session

from app.core.clock import get_clock
from app.core.hashing import compute_event_hash
from app.core.ids import generate_id
from app.db.models import (
    AIAction,
    AIActionKind,
    Appointment,
    AppointmentStatus,
    Case,
    CaseEvent,
    ClosureProposal,
    ClosureProposalStatus,
    Consent,
    Escalation,
    Evidence,
    Message,
    MessageStatus,
    Patient,
    Provider,
    ProviderType,
    Referral,
    ReferralStatus,
    SLATimer,
    SLAStatus,
    User,
    UserRole,
)


def seed_demo_scenarios(db: Session, providers: Dict[str, Provider], users: Dict[str, User]) -> Dict[str, Case]:
    """Seed the 6 canonical demo cases (A to F)."""
    clock = get_clock()
    base_time = clock.now() - timedelta(days=25)
    cases = {}

    nav_user = users["navigator"]
    clin_user = users["clinician"]
    sup_user = users["supervisor"]
    screening_center = providers["screening"]
    endoscopy_center = providers["specialist"]

    # -------------------------------------------------------------------------
    # Case A: "Amira" — The Happy Path (Arabic notification, acknowledgement,
    # colonoscopy attendance, evidence-backed human-approved closure)
    # -------------------------------------------------------------------------
    pt_a = Patient(
        id="pt-demo-amira",
        synthetic_name="Amira Al-Mansouri",
        dob=date(1972, 4, 18),
        sex="F",
        language="ar",
        preferred_channel="app",
        provider_id=screening_center.id,
    )
    db.add(pt_a)
    db.flush()

    case_a = Case(
        id="case-demo-a-amira",
        patient_id=pt_a.id,
        pathway_id="fit_positive_to_colonoscopy",
        urgency_tier="routine_actionable",
        current_state="CLOSED",
        owner_id=clin_user.id,
        owner_provider_id=endoscopy_center.id,
        opened_at=base_time,
        closed_at=base_time + timedelta(days=22),
        closure_type="procedure_report_received",
    )
    db.add(case_a)
    db.flush()

    # Events chain for Amira
    events_a = [
        ("case_opened", None, "RESULT_ISSUED", nav_user.id, "navigator", base_time, {"note": "FIT Positive result ingested"}),
        ("state_transition", "RESULT_ISSUED", "PATIENT_NOTIFIED", nav_user.id, "navigator", base_time + timedelta(days=1), {"channel": "app", "lang": "ar"}),
        ("state_transition", "PATIENT_NOTIFIED", "PATIENT_ACKNOWLEDGED", pt_a.id, "patient", base_time + timedelta(days=2), {"method": "digital_ack"}),
        ("state_transition", "PATIENT_ACKNOWLEDGED", "CONFIRMATION_DONE", nav_user.id, "navigator", base_time + timedelta(days=4), {"intent": "proceed"}),
        ("state_transition", "CONFIRMATION_DONE", "REFERRAL_SENT", nav_user.id, "navigator", base_time + timedelta(days=6), {"to_provider": endoscopy_center.name}),
        ("state_transition", "REFERRAL_SENT", "REFERRAL_ACCEPTED", clin_user.id, "clinician", base_time + timedelta(days=8), {"slot_available": True}),
        ("state_transition", "REFERRAL_ACCEPTED", "APPOINTMENT_BOOKED", nav_user.id, "navigator", base_time + timedelta(days=10), {"slot_date": "2026-02-02"}),
        ("state_transition", "APPOINTMENT_BOOKED", "APPOINTMENT_ATTENDED", clin_user.id, "clinician", base_time + timedelta(days=18), {"attended": True}),
        ("state_transition", "APPOINTMENT_ATTENDED", "TREATMENT_OR_SURVEILLANCE", clin_user.id, "clinician", base_time + timedelta(days=19), {"findings": "Tubular adenoma removed"}),
        ("state_transition", "TREATMENT_OR_SURVEILLANCE", "CLOSURE_PROPOSED", nav_user.id, "navigator", base_time + timedelta(days=20), {"evidence": "colonoscopy_report_attached"}),
        ("case_closed", "CLOSURE_PROPOSED", "CLOSED", clin_user.id, "clinician", base_time + timedelta(days=22), {"decision_reason": "Colonoscopy performed; polyps resected; 3-year surveillance scheduled."}),
    ]

    prev_hash = "genesis"
    for seq, (etype, fstate, tstate, actor, arole, occ_at, payload) in enumerate(events_a, 1):
        edata = {
            "case_id": case_a.id,
            "seq": seq,
            "event_type": etype,
            "from_state": fstate,
            "to_state": tstate,
            "actor_id": actor,
            "actor_role": arole,
            "occurred_at": occ_at.isoformat(),
            "payload": payload,
        }
        h = compute_event_hash(edata, prev_hash)
        db.add(CaseEvent(
            id=generate_id(),
            case_id=case_a.id,
            seq=seq,
            event_type=etype,
            from_state=fstate,
            to_state=tstate,
            actor_id=actor,
            actor_role=arole,
            occurred_at=occ_at,
            payload_json=json.dumps(payload),
            prev_hash=prev_hash,
            hash=h,
        ))
        prev_hash = h

    # Evidence and approved proposal for Amira
    ev_a = Evidence(
        id=generate_id(),
        case_id=case_a.id,
        evidence_type="colonoscopy_report",
        ref="DOC-ENDO-2026-0941",
        recorded_by=clin_user.id,
        recorded_at=base_time + timedelta(days=20),
        payload_json=json.dumps({"findings": "Complete colonoscopy to caecum. 6mm polyp resected. Histology benign adenoma."}),
    )
    db.add(ev_a)

    prop_a = ClosureProposal(
        id=generate_id(),
        case_id=case_a.id,
        proposed_by=nav_user.id,
        basis_json=json.dumps({"basis": "colonoscopy completed and surveillance plan established"}),
        status=ClosureProposalStatus.approved,
        decided_by=clin_user.id,
        decided_at=base_time + timedelta(days=22),
        decision_reason="Colonoscopy performed; polyps resected; 3-year surveillance scheduled.",
    )
    db.add(prop_a)
    cases["A"] = case_a

    # -------------------------------------------------------------------------
    # Case B: "Rahul" — Escalating retries (never acknowledges; channel retries;
    # navigator call task created)
    # -------------------------------------------------------------------------
    pt_b = Patient(
        id="pt-demo-rahul",
        synthetic_name="Rahul Sharma",
        dob=date(1968, 11, 3),
        sex="M",
        language="en",
        preferred_channel="sms",
        provider_id=screening_center.id,
    )
    db.add(pt_b)
    db.flush()

    case_b = Case(
        id="case-demo-b-rahul",
        patient_id=pt_b.id,
        pathway_id="fit_positive_to_colonoscopy",
        urgency_tier="routine_actionable",
        current_state="PATIENT_NOTIFIED",
        owner_id=nav_user.id,
        owner_provider_id=screening_center.id,
        opened_at=clock.now() - timedelta(days=9),
    )
    db.add(case_b)
    db.flush()

    # Breached SLA timer for Rahul
    timer_b = SLATimer(
        id=generate_id(),
        case_id=case_b.id,
        step="PATIENT_NOTIFIED",
        due_at=clock.now() - timedelta(days=2),
        warn_at=clock.now() - timedelta(days=4),
        status=SLAStatus.breached,
    )
    db.add(timer_b)

    esc_b = Escalation(
        id=generate_id(),
        case_id=case_b.id,
        tier=1,
        reason="Patient unacknowledged after 3 automated attempts (App + SMS). Navigator phone outreach call task generated.",
        raised_at=clock.now() - timedelta(days=2),
        assigned_to=nav_user.id,
    )
    db.add(esc_b)
    cases["B"] = case_b

    # -------------------------------------------------------------------------
    # Case C: "Maria" — Rejected referral (auto-returned ownership & re-routing)
    # -------------------------------------------------------------------------
    pt_c = Patient(
        id="pt-demo-maria",
        synthetic_name="Maria Santos",
        dob=date(1975, 8, 22),
        sex="F",
        language="en",
        preferred_channel="app",
        provider_id=screening_center.id,
    )
    db.add(pt_c)
    db.flush()

    case_c = Case(
        id="case-demo-c-maria",
        patient_id=pt_c.id,
        pathway_id="fit_positive_to_colonoscopy",
        urgency_tier="routine_actionable",
        current_state="REFERRAL_REJECTED",
        owner_id=nav_user.id,
        owner_provider_id=screening_center.id,
        opened_at=clock.now() - timedelta(days=12),
    )
    db.add(case_c)
    db.flush()

    ref_c = Referral(
        id=generate_id(),
        case_id=case_c.id,
        from_provider_id=screening_center.id,
        to_provider_id=endoscopy_center.id,
        status=ReferralStatus.rejected,
        sent_at=clock.now() - timedelta(days=4),
        responded_at=clock.now() - timedelta(days=1),
    )
    db.add(ref_c)

    esc_c = Escalation(
        id=generate_id(),
        case_id=case_c.id,
        tier=1,
        reason="Referral rejected by clinic: Capacity full for outpatient sedation. Returned to navigator for alternative hospital routing.",
        raised_at=clock.now() - timedelta(days=1),
        assigned_to=nav_user.id,
    )
    db.add(esc_c)
    cases["C"] = case_c

    # -------------------------------------------------------------------------
    # Case D: "Omar" — Red Flag at acknowledgement (urgency upgraded to urgent,
    # immediate clinical lead alert)
    # -------------------------------------------------------------------------
    pt_d = Patient(
        id="pt-demo-omar",
        synthetic_name="Omar Tariq",
        dob=date(1962, 1, 30),
        sex="M",
        language="ar",
        preferred_channel="app",
        provider_id=screening_center.id,
    )
    db.add(pt_d)
    db.flush()

    case_d = Case(
        id="case-demo-d-omar",
        patient_id=pt_d.id,
        pathway_id="fit_positive_to_colonoscopy",
        urgency_tier="urgent",
        current_state="CONFIRMATION_PENDING",
        owner_id=clin_user.id,
        owner_provider_id=endoscopy_center.id,
        opened_at=clock.now() - timedelta(days=3),
    )
    db.add(case_d)
    db.flush()

    esc_d = Escalation(
        id=generate_id(),
        case_id=case_d.id,
        tier=2,
        reason="RED FLAG TRIGGERED: Patient reported unexplained rectal bleeding and >5% weight loss. Case escalated to Clinical Lead.",
        raised_at=clock.now() - timedelta(days=1),
        assigned_to=clin_user.id,
    )
    db.add(esc_d)
    cases["D"] = case_d

    # -------------------------------------------------------------------------
    # Case E: "Chen" — Provider transfer with unbroken hash chain
    # -------------------------------------------------------------------------
    pt_e = Patient(
        id="pt-demo-chen",
        synthetic_name="Chen Wei",
        dob=date(1979, 9, 14),
        sex="M",
        language="en",
        preferred_channel="app",
        provider_id=screening_center.id,
    )
    db.add(pt_e)
    db.flush()

    case_e = Case(
        id="case-demo-e-chen",
        patient_id=pt_e.id,
        pathway_id="fit_positive_to_colonoscopy",
        urgency_tier="routine_actionable",
        current_state="TRANSFERRED",
        owner_id=clin_user.id,
        owner_provider_id=endoscopy_center.id,
        opened_at=clock.now() - timedelta(days=14),
    )
    db.add(case_e)
    db.flush()

    # Chain with handoff offer and accept
    e_events = [
        ("case_opened", None, "RESULT_ISSUED", nav_user.id, "navigator", clock.now() - timedelta(days=14), {}),
        ("handoff_offered", None, None, nav_user.id, "navigator", clock.now() - timedelta(days=6), {"to_provider": endoscopy_center.id}),
        ("handoff_accepted", None, None, clin_user.id, "clinician", clock.now() - timedelta(days=5), {"new_owner": clin_user.id}),
        ("state_transition", "RESULT_ISSUED", "TRANSFERRED", clin_user.id, "clinician", clock.now() - timedelta(days=5), {"relocation": "Regional Transfer"}),
    ]
    prev_h = "genesis"
    for seq, (etype, fs, ts, actor, arole, occ, payload) in enumerate(e_events, 1):
        edata = {"case_id": case_e.id, "seq": seq, "event_type": etype, "from_state": fs, "to_state": ts, "actor_id": actor, "occurred_at": occ.isoformat()}
        h = compute_event_hash(edata, prev_h)
        db.add(CaseEvent(
            id=generate_id(),
            case_id=case_e.id,
            seq=seq,
            event_type=etype,
            from_state=fs,
            to_state=ts,
            actor_id=actor,
            actor_role=arole,
            occurred_at=occ,
            payload_json=json.dumps(payload),
            prev_hash=prev_h,
            hash=h,
        ))
        prev_h = h
    cases["E"] = case_e

    # -------------------------------------------------------------------------
    # Case F: AI Blocked — Banned terms / diagnosis disclosure blocked by validator
    # -------------------------------------------------------------------------
    pt_f = Patient(
        id="pt-demo-fatima",
        synthetic_name="Fatima Al-Nuaimi",
        dob=date(1983, 3, 12),
        sex="F",
        language="en",
        preferred_channel="app",
        provider_id=screening_center.id,
    )
    db.add(pt_f)
    db.flush()

    case_f = Case(
        id="case-demo-f-blocked",
        patient_id=pt_f.id,
        pathway_id="fit_positive_to_colonoscopy",
        urgency_tier="routine_actionable",
        current_state="PATIENT_NOTIFIED",
        owner_id=nav_user.id,
        owner_provider_id=screening_center.id,
        opened_at=clock.now() - timedelta(days=2),
    )
    db.add(case_f)
    db.flush()

    # AI Action that was blocked by validator
    ai_act_f = AIAction(
        id=generate_id(),
        kind=AIActionKind.message_rewrite,
        provider="mock_llm",
        model="claude-sonnet-5-5",
        input_hash="hash_raw_template_input",
        output_text="Your screening test was positive. You have cancer and need an emergency operation immediately.",
        validator_passed=False,
        fallback_used=True,
        reviewed_by=None,
        reviewed_at=None,
    )
    db.add(ai_act_f)
    db.flush()

    # The actual message sent used the deterministic safe fallback!
    msg_f = Message(
        id=generate_id(),
        case_id=case_f.id,
        patient_id=pt_f.id,
        channel="app",
        language="en",
        template_id="fit_positive_notification",
        body="Dear Fatima Al-Nuaimi,\n\nYour recent bowel screening test has returned a result that needs routine follow-up. Please log in to your portal to review recommended next steps.",
        status=MessageStatus.delivered,
        sent_at=clock.now() - timedelta(days=2),
        delivered_at=clock.now() - timedelta(days=2),
        validator_result_json=json.dumps({
            "passed": False,
            "violations": ["Diagnosis disclosure violation: contains 'you have cancer'", "Banned term violation: contains 'emergency'"],
            "fallback_used": True,
        }),
        ai_action_id=ai_act_f.id,
    )
    db.add(msg_f)
    cases["F"] = case_f

    db.commit()
    return cases
