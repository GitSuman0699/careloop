"""Exception queues router — prioritized queues for navigators and clinicians."""

from __future__ import annotations

from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.db.models import Case, Escalation, SLATimer, SLAStatus, User
from app.db.session import get_db

router = APIRouter(prefix="/queues", tags=["queues"])


def _format_cases(cases: List[Case]) -> List[dict]:
    return [
        {
            "id": c.id,
            "patient_id": c.patient_id,
            "patient_name": c.patient.synthetic_name if c.patient else "Unknown",
            "pathway_id": c.pathway_id,
            "urgency_tier": c.urgency_tier,
            "current_state": c.current_state,
            "owner_id": c.owner_id,
            "owner_name": c.owner.name if c.owner else "Unassigned",
            "opened_at": c.opened_at.isoformat() if c.opened_at else None,
        }
        for c in cases
    ]


@router.get("/overdue")
def get_overdue_queue(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    cases = (
        db.query(Case)
        .join(SLATimer, Case.id == SLATimer.case_id)
        .filter(SLATimer.status == SLAStatus.breached, Case.closed_at.is_(None))
        .distinct()
        .all()
    )
    return _format_cases(cases)


@router.get("/unassigned")
def get_unassigned_queue(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    cases = db.query(Case).filter(Case.owner_id.is_(None), Case.closed_at.is_(None)).all()
    return _format_cases(cases)


@router.get("/rejected")
def get_rejected_queue(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    cases = db.query(Case).filter(Case.current_state == "REFERRAL_REJECTED", Case.closed_at.is_(None)).all()
    return _format_cases(cases)


@router.get("/urgent")
def get_urgent_queue(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    cases = db.query(Case).filter(Case.urgency_tier == "urgent", Case.closed_at.is_(None)).all()
    return _format_cases(cases)


@router.get("/unreachable")
def get_unreachable_queue(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    cases = db.query(Case).filter(Case.current_state == "PATIENT_UNREACHABLE", Case.closed_at.is_(None)).all()
    return _format_cases(cases)

