"""Closure proposals and human-governed closure API router."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.auth import get_current_user, require_permission
from app.core.clock import get_clock
from app.db.models import ClosureProposal, ClosureProposalStatus, User, UserRole
from app.db.session import get_db
from app.domain.closure_guard import ClosureGuard, ClosureGuardError

router = APIRouter(prefix="/closure-proposals", tags=["closure"])


class DecideClosureRequest(BaseModel):
    decision: str  # "approved" or "rejected"
    decision_reason: str


@router.post("/{proposal_id}/decide")
def decide_closure_proposal(
    proposal_id: str,
    req: DecideClosureRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("approve_closure")),
):
    """Clinician or Supervisor decides on a closure proposal.
    
    If approved, calls ClosureGuard to seal the case.
    """
    proposal = db.query(ClosureProposal).filter(ClosureProposal.id == proposal_id).first()
    if not proposal:
        raise HTTPException(status_code=404, detail="Closure proposal not found")

    if not req.decision_reason or not req.decision_reason.strip():
        raise HTTPException(status_code=400, detail="Decision reason must be non-empty")

    clock = get_clock()
    now = clock.now()

    if req.decision.lower() == "approved":
        proposal.status = ClosureProposalStatus.approved
        proposal.decided_by = user.id
        proposal.decided_at = now
        proposal.decision_reason = req.decision_reason
        db.flush()

        # Execute ClosureGuard
        guard = ClosureGuard()
        try:
            event = guard.close_case(case_id=proposal.case_id, actor_id=user.id, db=db)
            db.commit()
            return {
                "status": "approved_and_closed",
                "proposal_id": proposal.id,
                "case_id": proposal.case_id,
                "closed_at": now.isoformat(),
                "event_seq": event.seq,
                "event_hash": event.hash,
            }
        except ClosureGuardError as e:
            db.rollback()
            raise HTTPException(status_code=400, detail=f"Closure blocked by guard: {str(e)}")

    elif req.decision.lower() == "rejected":
        proposal.status = ClosureProposalStatus.rejected
        proposal.decided_by = user.id
        proposal.decided_at = now
        proposal.decision_reason = req.decision_reason
        db.commit()
        return {
            "status": "rejected",
            "proposal_id": proposal.id,
            "case_id": proposal.case_id,
            "decision_reason": req.decision_reason,
        }
    else:
        raise HTTPException(status_code=400, detail="Decision must be 'approved' or 'rejected'")

