"""Patient-facing endpoints — acknowledgement, red-flag reporting, teach-back comprehension."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.clock import get_clock
from app.core.ids import generate_id
from app.db.models import (
    Appointment,
    AppointmentStatus,
    Case,
    CaseEvent,
    Escalation,
    Patient,
    User,
    UserRole,
)
from app.db.session import get_db
from app.domain.pathway_loader import load_pathway
from app.domain.urgency import evaluate_red_flags
from app.domain.state_machine import StateMachine

router = APIRouter(prefix="/patients", tags=["patients"])


class AcknowledgeRequest(BaseModel):
    case_id: str


class RedFlagSubmission(BaseModel):
    case_id: str
    answers: Dict[str, Any]  # e.g., {"rectal_bleeding": True, "weight_loss_pct": 6.0}


class TeachbackSubmission(BaseModel):
    case_id: str
    question_id: str
    selected_option_id: str


class ChooseAppointmentRequest(BaseModel):
    case_id: str
    slot_at: str
    provider_id: str


class NeedHelpRequest(BaseModel):
    case_id: str
    note: Optional[str] = "Patient requested navigator assistance via 'I need help' button"


@router.post("/{patient_id}/acknowledge")
def patient_acknowledge(
    patient_id: str,
    req: AcknowledgeRequest,
    db: Session = Depends(get_db),
):
    """Patient acknowledges notification of screening result."""
    case = db.query(Case).filter(Case.id == req.case_id, Case.patient_id == patient_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found for patient")

    pathway = load_pathway(case.pathway_id)
    sm = StateMachine(pathway)

    # If current state is PATIENT_NOTIFIED, transition to PATIENT_ACKNOWLEDGED
    if case.current_state == "PATIENT_NOTIFIED" and sm.can_transition("PATIENT_NOTIFIED", "PATIENT_ACKNOWLEDGED"):
        # Get patient user or default
        user = db.query(User).filter(User.role == UserRole.patient).first()
        actor_id = user.id if user else "patient-self"
        sm.transition(
            case_id=case.id,
            from_state="PATIENT_NOTIFIED",
            to_state="PATIENT_ACKNOWLEDGED",
            actor_id=actor_id,
            actor_role="patient",
            evidence={"type": "patient_digital_acknowledgement"},
            db=db,
        )
        db.commit()

    return {"status": "acknowledged", "case_id": case.id, "current_state": case.current_state}


@router.post("/{patient_id}/redflags")
def submit_red_flags(
    patient_id: str,
    req: RedFlagSubmission,
    db: Session = Depends(get_db),
):
    """Patient submits red-flag symptom questionnaire."""
    case = db.query(Case).filter(Case.id == req.case_id, Case.patient_id == patient_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    pathway = load_pathway(case.pathway_id)
    new_tier, triggered_rules = evaluate_red_flags(pathway, req.answers)

    now = get_clock().now()
    upgraded = False
    safe_action = "Please continue with your scheduled care pathway steps."

    if new_tier:
        upgraded = True
        case.urgency_tier = new_tier
        safe_action = (
            "IMPORTANT: Red-flag symptoms reported. Please contact your clinician or seek urgent medical "
            "advice immediately. Your care navigator and clinical lead have been alerted with high priority."
        )

        # Raise Tier 2 Escalation immediately
        esc = Escalation(
            id=generate_id(),
            case_id=case.id,
            tier=2,
            reason=f"Patient reported red-flag symptoms: {', '.join(triggered_rules)}. Urgency elevated to {new_tier}.",
            raised_at=now,
        )
        db.add(esc)

        # Record event
        from app.core.hashing import compute_event_hash
        import json
        last_event = db.query(CaseEvent).filter(CaseEvent.case_id == case.id).order_by(CaseEvent.seq.desc()).first()
        prev_h = last_event.hash if last_event else "genesis"
        n_seq = (last_event.seq + 1) if last_event else 1
        ev_data = {
            "case_id": case.id,
            "seq": n_seq,
            "event_type": "red_flags_reported",
            "actor_id": "patient-self",
            "actor_role": "patient",
            "occurred_at": now.isoformat(),
            "payload": {"triggered_rules": triggered_rules, "new_urgency": new_tier},
        }
        h = compute_event_hash(ev_data, prev_h)
        db.add(CaseEvent(
            id=generate_id(),
            case_id=case.id,
            seq=n_seq,
            event_type="red_flags_reported",
            actor_id="patient-self",
            actor_role="patient",
            occurred_at=now,
            payload_json=json.dumps(ev_data["payload"]),
            prev_hash=prev_h,
            hash=h,
        ))

        db.commit()

    return {
        "case_id": case.id,
        "upgraded": upgraded,
        "new_urgency_tier": case.urgency_tier,
        "triggered_rules": triggered_rules,
        "safe_action_guidance": safe_action,
    }


@router.post("/{patient_id}/teachback")
def submit_teachback(
    patient_id: str,
    req: TeachbackSubmission,
    db: Session = Depends(get_db),
):
    """Record teach-back comprehension check response."""
    # Correct answer for screening follow-up is typically option 2 ("Arrange follow-up colonoscopy")
    is_correct = req.selected_option_id in ["opt_colonoscopy", "opt_followup", "opt_correct", "2"]

    now = get_clock().now()
    if not is_correct:
        # Create navigator follow-up task
        esc = Escalation(
            id=generate_id(),
            case_id=req.case_id,
            tier=1,
            reason=f"Teach-back check failed or incomplete (answered {req.selected_option_id}). Navigator outreach needed.",
            raised_at=now,
        )
        db.add(esc)
        db.commit()

    return {
        "status": "recorded",
        "is_correct": is_correct,
        "needs_followup": not is_correct,
    }


@router.post("/{patient_id}/appointments/choose")
def choose_appointment(
    patient_id: str,
    req: ChooseAppointmentRequest,
    db: Session = Depends(get_db),
):
    """Patient selects an offered appointment slot."""
    case = db.query(Case).filter(Case.id == req.case_id, Case.patient_id == patient_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    from datetime import datetime
    slot_dt = datetime.fromisoformat(req.slot_at)

    apt = Appointment(
        id=generate_id(),
        case_id=case.id,
        provider_id=req.provider_id,
        slot_at=slot_dt,
        status=AppointmentStatus.booked,
    )
    db.add(apt)

    pathway = load_pathway(case.pathway_id)
    sm = StateMachine(pathway)
    if sm.can_transition(case.current_state, "APPOINTMENT_BOOKED"):
        sm.transition(
            case_id=case.id,
            from_state=case.current_state,
            to_state="APPOINTMENT_BOOKED",
            actor_id="patient-self",
            actor_role="patient",
            evidence={"appointment_id": apt.id, "slot_at": req.slot_at},
            db=db,
        )

    db.commit()
    return {"status": "booked", "appointment_id": apt.id, "slot_at": req.slot_at}


@router.post("/{patient_id}/help")
def request_help(
    patient_id: str,
    req: NeedHelpRequest,
    db: Session = Depends(get_db),
):
    """Patient triggers 'I need help' button."""
    now = get_clock().now()
    esc = Escalation(
        id=generate_id(),
        case_id=req.case_id,
        tier=1,
        reason=f"Patient clicked 'I need help': {req.note}",
        raised_at=now,
    )
    db.add(esc)
    db.commit()
    return {"status": "help_requested", "message": "Your care navigator has been alerted and will reach out to you."}
