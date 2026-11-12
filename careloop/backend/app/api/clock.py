"""Simulated Clock control router."""

from __future__ import annotations

import os
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.auth import require_permission
from app.core.clock import get_clock, SimulatedClock
from app.db.models import User
from app.db.session import get_db
from app.domain.sla_engine import SLAEngine

router = APIRouter(prefix="/clock", tags=["clock"])


class AdvanceClockRequest(BaseModel):
    days: int = 0
    hours: int = 0
    minutes: int = 0


@router.get("")
def get_clock_status():
    clock = get_clock()
    is_sim = isinstance(clock, SimulatedClock)
    return {
        "current_time": clock.now().isoformat(),
        "mode": "simulated" if is_sim else "real",
        "can_advance": is_sim,
    }


@router.post("/advance")
def advance_clock(
    req: AdvanceClockRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("advance_clock")),
):
    """Advance the simulated clock by the specified duration."""
    clock = get_clock()
    if not isinstance(clock, SimulatedClock):
        raise HTTPException(status_code=400, detail="Cannot advance clock in real-time mode")

    new_time = clock.advance(days=req.days, hours=req.hours, minutes=req.minutes)

    # Automatically tick the SLA engine after time advancement
    sla_engine = SLAEngine(db)
    tick_result = sla_engine.tick()
    db.commit()

    return {
        "status": "advanced",
        "advanced_by": {"days": req.days, "hours": req.hours, "minutes": req.minutes},
        "new_time": new_time.isoformat(),
        "sla_tick_result": tick_result,
    }


@router.post("/tick")
def tick_sla(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("advance_clock")),
):
    """Manually trigger an SLA engine evaluation tick."""
    sla_engine = SLAEngine(db)
    result = sla_engine.tick()
    db.commit()
    return result

