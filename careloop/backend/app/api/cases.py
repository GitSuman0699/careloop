"""Cases router — case ledger, state transitions, tamper-evident hash chain verification."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.auth import get_current_user, require_permission
from app.core.clock import get_clock
from app.core.hashing import verify_chain
from app.core.ids import generate_id
from app.db.models import (
    AuditAction,
    AuditLog,
    Case,
    CaseEvent,
    ClosureProposal,
    ClosureProposalStatus,
    Escalation,
    Evidence,
    Patient,
    User,
    UserRole,
)
from app.db.session import get_db
from app.domain.ownership import OwnershipEngine
from app.domain.pathway_loader import load_pathway
from app.domain.state_machine import IllegalTransitionError, StateMachine
from app.services.comms_pipeline import CommsPipeline
from app.services.consult_packet import ConsultPacketService

router = APIRouter(prefix="/cases", tags=["cases"])


class IngestResultRequest(BaseModel):
    patient_id: str
    pathway_id: str = "fit_positive_to_colonoscopy"
    urgency_tier: str = "routine_actionable"
    initial_owner_id: Optional[str] = None
    initial_provider_id: Optional[str] = None
    clinical_note: Optional[str] = None


class TransitionRequest(BaseModel):
    to_state: str
    evidence: Optional[Dict[str, Any]] = None


class HandoffOfferRequest(BaseModel):
    to_provider_id: str
    to_user_id: Optional[str] = None


class HandoffAcceptRequest(BaseModel):
    pass


class EscalateRequest(BaseModel):
    tier: int = 1
    reason: str


class ClosureProposalRequest(BaseModel):
    basis: Dict[str, Any]
    evidence_type: str = "colonoscopy_report"
    evidence_ref: Optional[str] = None


@router.post("/ingest-result", status_code=status.HTTP_201_CREATED)
def ingest_result(
    req: IngestResultRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("change_case_state")),
):
    """Ingest a new actionable screening finding and open a tracked case."""
    clock = get_clock()
    now = clock.now()

    patient = db.query(Patient).filter(Patient.id == req.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    pathway = load_pathway(req.pathway_id)
    initial_state = pathway.steps[0].id if pathway.steps else "RESULT_ISSUED"

    case = Case(
        id=generate_id(),
        patient_id=req.patient_id,
        pathway_id=req.pathway_id,
        urgency_tier=req.urgency_tier,
        current_state=initial_state,
        owner_id=req.initial_owner_id or user.id,
        owner_provider_id=req.initial_provider_id or user.provider_id,
        opened_at=now,
    )
    db.add(case)
    db.flush()

    # Genesis event
    from app.core.hashing import compute_event_hash
    event_data = {
        "case_id": case.id,
        "seq": 1,
        "event_type": "case_opened",
        "from_state": None,
        "to_state": initial_state,
        "actor_id": user.id,
        "actor_role": user.role.value if hasattr(user.role, "value") else str(user.role),
        "occurred_at": now.isoformat(),
        "payload": {"note": req.clinical_note or "Actionable screening result ingested"},
    }
    genesis_hash = compute_event_hash(event_data, "genesis")

    event = CaseEvent(
        id=generate_id(),
        case_id=case.id,
        seq=1,
        event_type="case_opened",
        from_state=None,
        to_state=initial_state,
        actor_id=user.id,
        actor_role=user.role.value if hasattr(user.role, "value") else str(user.role),
        occurred_at=now,
        payload_json=json.dumps(event_data["payload"]),
        prev_hash="genesis",
        hash=genesis_hash,
    )
    db.add(event)

    # Automatically notify patient if initial step auto transitions or has template
    comms = CommsPipeline(db)
    comms.draft_message(
        case_id=case.id,
        patient_id=patient.id,
        template_id="fit_positive_notification",
        context_data={
            "patient_name": patient.synthetic_name,
            "navigator_name": user.name,
            "navigator_phone": "+971 2 555 0100",
        },
        channel=patient.preferred_channel or "app",
        language=patient.language or "en",
    )

    db.commit()
    db.refresh(case)
    return {"status": "created", "case_id": case.id, "current_state": case.current_state}


@router.get("")
def list_cases(
    pathway_id: Optional[str] = None,
    current_state: Optional[str] = None,
    urgency_tier: Optional[str] = None,
    owner_id: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List cases with optional filters."""
    query = db.query(Case)
    if pathway_id:
        query = query.filter(Case.pathway_id == pathway_id)
    if current_state:
        query = query.filter(Case.current_state == current_state)
    if urgency_tier:
        query = query.filter(Case.urgency_tier == urgency_tier)
    if owner_id:
        query = query.filter(Case.owner_id == owner_id)

    cases = query.order_by(Case.opened_at.desc()).limit(200).all()

    # Audit log read
    clock = get_clock()
    log = AuditLog(
        id=generate_id(),
        actor_id=user.id,
        role=user.role.value if hasattr(user.role, "value") else str(user.role),
        action=AuditAction.read,
        object_type="case_list",
        object_id="filter_query",
        at=clock.now(),
        purpose="List cases in navigation queue",
    )
    db.add(log)
    db.commit()

    results = []
    for c in cases:
        results.append({
            "id": c.id,
            "patient_id": c.patient_id,
            "patient_name": c.patient.synthetic_name if c.patient else "Unknown",
            "pathway_id": c.pathway_id,
            "urgency_tier": c.urgency_tier,
            "current_state": c.current_state,
            "owner_id": c.owner_id,
            "owner_name": c.owner.name if c.owner else "Unassigned",
            "opened_at": c.opened_at.isoformat() if c.opened_at else None,
            "closed_at": c.closed_at.isoformat() if c.closed_at else None,
        })
    return results


@router.get("/{case_id}")
def get_case(
    case_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get single case detail."""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    # Audit read
    clock = get_clock()
    log = AuditLog(
        id=generate_id(),
        actor_id=user.id,
        role=user.role.value if hasattr(user.role, "value") else str(user.role),
        action=AuditAction.read,
        object_type="case",
        object_id=case_id,
        at=clock.now(),
        purpose=f"View case details: {case_id}",
    )
    db.add(log)
    db.commit()

    return {
        "id": case.id,
        "patient_id": case.patient_id,
        "patient_name": case.patient.synthetic_name if case.patient else None,
        "patient_dob": case.patient.dob.isoformat() if case.patient else None,
        "patient_language": case.patient.language if case.patient else "en",
        "pathway_id": case.pathway_id,
        "urgency_tier": case.urgency_tier,
        "current_state": case.current_state,
        "owner_id": case.owner_id,
        "owner_name": case.owner.name if case.owner else "Unassigned",
        "opened_at": case.opened_at.isoformat() if case.opened_at else None,
        "closed_at": case.closed_at.isoformat() if case.closed_at else None,
        "closure_type": case.closure_type,
    }


@router.get("/{case_id}/timeline")
def get_case_timeline(
    case_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Fetch complete append-only event ledger for a case."""
    events = (
        db.query(CaseEvent)
        .filter(CaseEvent.case_id == case_id)
        .order_by(CaseEvent.seq.asc())
        .all()
    )
    return [
        {
            "seq": e.seq,
            "event_type": e.event_type,
            "from_state": e.from_state,
            "to_state": e.to_state,
            "actor_id": e.actor_id,
            "actor_role": e.actor_role,
            "occurred_at": e.occurred_at.isoformat(),
            "payload": json.loads(e.payload_json) if e.payload_json else None,
            "prev_hash": e.prev_hash,
            "hash": e.hash,
        }
        for e in events
    ]


@router.get("/{case_id}/verify-chain")
def verify_case_chain(
    case_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Verify cryptographic integrity of the case's hash chain."""
    events = (
        db.query(CaseEvent)
        .filter(CaseEvent.case_id == case_id)
        .order_by(CaseEvent.seq.asc())
        .all()
    )
    raw_events = [
        {
            "case_id": e.case_id,
            "seq": e.seq,
            "event_type": e.event_type,
            "from_state": e.from_state,
            "to_state": e.to_state,
            "actor_id": e.actor_id,
            "actor_role": e.actor_role,
            "occurred_at": e.occurred_at.isoformat(),
            "payload_json": e.payload_json,
            "prev_hash": e.prev_hash,
            "hash": e.hash,
        }
        for e in events
    ]
    is_valid, err = verify_chain(raw_events)
    return {
        "case_id": case_id,
        "event_count": len(events),
        "is_valid": is_valid,
        "error": err,
        "verified_at": get_clock().now().isoformat(),
    }


@router.post("/{case_id}/transition")
def transition_case(
    case_id: str,
    req: TransitionRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("change_case_state")),
):
    """Execute a valid state transition in the pathway."""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    pathway = load_pathway(case.pathway_id)
    sm = StateMachine(pathway)

    try:
        user_role_str = user.role.value if hasattr(user.role, "value") else str(user.role)
        event = sm.transition(
            case_id=case.id,
            from_state=case.current_state,
            to_state=req.to_state,
            actor_id=user.id,
            actor_role=user_role_str,
            evidence=req.evidence,
            db=db,
        )
        db.commit()
        return {
            "status": "transitioned",
            "from_state": event.from_state,
            "to_state": event.to_state,
            "event_seq": event.seq,
            "hash": event.hash,
        }
    except IllegalTransitionError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{case_id}/handoff/offer")
def offer_handoff(
    case_id: str,
    req: HandoffOfferRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("change_case_state")),
):
    """Offer case handoff to another provider."""
    engine = OwnershipEngine(db)
    user_role_str = user.role.value if hasattr(user.role, "value") else str(user.role)
    event = engine.offer_handoff(
        case_id=case_id,
        to_provider_id=req.to_provider_id,
        to_user_id=req.to_user_id,
        actor_id=user.id,
        actor_role=user_role_str,
    )
    db.commit()
    return {"status": "offered", "event_seq": event.seq}


@router.post("/{case_id}/handoff/accept")
def accept_handoff(
    case_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("change_case_state")),
):
    """Accept offered case handoff, transferring single ownership."""
    engine = OwnershipEngine(db)
    user_role_str = user.role.value if hasattr(user.role, "value") else str(user.role)
    case, event = engine.accept_handoff(
        case_id=case_id,
        accepting_user_id=user.id,
        actor_role=user_role_str,
    )
    db.commit()
    return {"status": "accepted", "new_owner_id": case.owner_id, "event_seq": event.seq}


@router.post("/{case_id}/escalate")
def escalate_case(
    case_id: str,
    req: EscalateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("change_case_state")),
):
    """Raise an escalation on a case."""
    clock = get_clock()
    esc = Escalation(
        id=generate_id(),
        case_id=case_id,
        tier=req.tier,
        reason=req.reason,
        raised_at=clock.now(),
        assigned_to=user.id,
    )
    db.add(esc)
    db.commit()
    return {"status": "escalated", "escalation_id": esc.id, "tier": esc.tier}


@router.post("/{case_id}/closure-proposals")
def propose_closure(
    case_id: str,
    req: ClosureProposalRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Propose closure for a case and record evidence."""
    clock = get_clock()
    now = clock.now()

    # 1. Attach Evidence
    evidence = Evidence(
        id=generate_id(),
        case_id=case_id,
        evidence_type=req.evidence_type,
        ref=req.evidence_ref,
        recorded_by=user.id,
        recorded_at=now,
        payload_json=json.dumps(req.basis),
    )
    db.add(evidence)

    # 2. Create proposal in pending state
    proposal = ClosureProposal(
        id=generate_id(),
        case_id=case_id,
        proposed_by=user.id,
        basis_json=json.dumps(req.basis),
        status=ClosureProposalStatus.pending,
    )
    db.add(proposal)
    db.commit()
    return {"status": "proposed", "proposal_id": proposal.id, "evidence_id": evidence.id}


@router.get("/{case_id}/consult-packet")
def get_consult_packet(
    case_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Generate structured consult packet for receiving clinician."""
    svc = ConsultPacketService(db)
    return svc.generate_packet(case_id=case_id, requesting_user_id=user.id)

