"""Governance and Audit logging router."""

from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.auth import require_permission
from app.db.models import AIAction, AuditLog, Consent, User
from app.db.session import get_db

router = APIRouter(tags=["governance"])


@router.get("/audit")
def list_audit_logs(
    limit: int = 100,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("read_audit_log")),
):
    """Retrieve immutable audit logs."""
    logs = db.query(AuditLog).order_by(AuditLog.at.desc()).limit(limit).all()
    return [
        {
            "id": l.id,
            "actor_id": l.actor_id,
            "role": l.role,
            "action": l.action.value if hasattr(l.action, "value") else str(l.action),
            "object_type": l.object_type,
            "object_id": l.object_id,
            "at": l.at.isoformat(),
            "purpose": l.purpose,
        }
        for l in logs
    ]


@router.get("/ai-actions")
def list_ai_actions(
    limit: int = 100,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("read_audit_log")),
):
    """Retrieve AI actions log with validator passed / fallback flags."""
    actions = db.query(AIAction).order_by(AIAction.id.desc()).limit(limit).all()
    return [
        {
            "id": a.id,
            "kind": a.kind.value if hasattr(a.kind, "value") else str(a.kind),
            "provider": a.provider,
            "model": a.model,
            "input_hash": a.input_hash,
            "output_text": a.output_text,
            "validator_passed": a.validator_passed,
            "fallback_used": a.fallback_used,
            "reviewed_by": a.reviewed_by,
            "reviewed_at": a.reviewed_at.isoformat() if a.reviewed_at else None,
        }
        for a in actions
    ]


@router.get("/consents")
def list_consents(
    patient_id: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("read_audit_log")),
):
    """List consent records."""
    q = db.query(Consent)
    if patient_id:
        q = q.filter(Consent.patient_id == patient_id)
    consents = q.order_by(Consent.granted_at.desc()).limit(100).all()
    return [
        {
            "id": c.id,
            "patient_id": c.patient_id,
            "channel": c.channel,
            "purpose": c.purpose,
            "granted_at": c.granted_at.isoformat(),
            "revoked_at": c.revoked_at.isoformat() if c.revoked_at else None,
        }
        for c in consents
    ]
