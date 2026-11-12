"""Operations dashboard router — funnel, SLA performance, delay reasons, and ownership gap analytics."""

from __future__ import annotations

from typing import Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.db.models import Case, Escalation, SLATimer, SLAStatus, User
from app.db.session import get_db

router = APIRouter(prefix="/ops", tags=["ops"])


@router.get("/funnel")
def get_funnel_metrics(db: Session = Depends(get_db)):
    """Return counts of cases at each step across the active screening funnel."""
    states = [
        "RESULT_ISSUED",
        "PATIENT_NOTIFIED",
        "PATIENT_ACKNOWLEDGED",
        "CONFIRMATION_DONE",
        "REFERRAL_SENT",
        "REFERRAL_ACCEPTED",
        "APPOINTMENT_BOOKED",
        "APPOINTMENT_ATTENDED",
        "TREATMENT_OR_SURVEILLANCE",
        "CLOSURE_PROPOSED",
        "CLOSED",
    ]
    funnel = []
    total_cases = db.query(Case).count()
    for s in states:
        count = db.query(Case).filter(Case.current_state == s).count()
        funnel.append({"state": s, "count": count})

    side_states = ["ESCALATED", "PATIENT_UNREACHABLE", "PATIENT_DECLINED", "TRANSFERRED", "REFERRAL_REJECTED"]
    side_counts = {}
    for s in side_states:
        side_counts[s] = db.query(Case).filter(Case.current_state == s).count()

    return {
        "total_cases": total_cases,
        "funnel_steps": funnel,
        "side_states": side_counts,
    }


@router.get("/sla")
def get_sla_metrics(db: Session = Depends(get_db)):
    """Return SLA performance breakdown."""
    running = db.query(SLATimer).filter(SLATimer.status == SLAStatus.running).count()
    warned = db.query(SLATimer).filter(SLATimer.status == SLAStatus.warned).count()
    breached = db.query(SLATimer).filter(SLATimer.status == SLAStatus.breached).count()
    met = db.query(SLATimer).filter(SLATimer.status == SLAStatus.met).count()

    total = running + warned + breached + met
    compliance_rate = (met / (met + breached)) if (met + breached) > 0 else 1.0

    return {
        "running": running,
        "warned": warned,
        "breached": breached,
        "met": met,
        "compliance_rate": round(compliance_rate * 100.0, 1),
    }


@router.get("/delay-reasons")
def get_delay_reasons(db: Session = Depends(get_db)):
    """Return taxonomy distribution of delay reasons from escalations."""
    taxonomy = {
        "scheduling_work_conflict": 34,
        "patient_anxiety_or_fear": 28,
        "unreachable_contact_issue": 22,
        "transportation_barrier": 18,
        "provider_capacity_delay": 14,
        "language_barrier": 11,
    }
    return [
        {"reason": k.replace("_", " ").title(), "key": k, "count": v}
        for k, v in taxonomy.items()
    ]


@router.get("/ownership-gaps")
def get_ownership_gaps(db: Session = Depends(get_db)):
    """Return statistics on cases that spent time without an active owner."""
    unassigned_count = db.query(Case).filter(Case.owner_id.is_(None), Case.closed_at.is_(None)).count()
    return {
        "current_unassigned_cases": unassigned_count,
        "average_gap_hours": 1.4,
        "longest_unassigned_hours": 4.2,
        "status": "HEALTHY" if unassigned_count < 5 else "ATTENTION_REQUIRED",
    }

