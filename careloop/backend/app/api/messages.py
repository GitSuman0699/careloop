"""Messages router — message logs and preview endpoint with validator diagnostics."""

from __future__ import annotations

import json
from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.ai.guardrails import MessageValidator
from app.ai.mock_provider import MockAIProvider
from app.db.models import Message, User
from app.db.session import get_db
from app.services.comms_pipeline import CommsPipeline

router = APIRouter(prefix="/messages", tags=["messages"])


class MessagePreviewRequest(BaseModel):
    template_id: str = "fit_positive_notification"
    context_data: dict = {
        "patient_name": "Test Patient",
        "navigator_name": "Sarah Jenkins",
        "navigator_phone": "+971 2 555 0100",
    }
    channel: str = "app"
    language: str = "en"
    use_ai_rewrite: bool = True
    simulate_adversarial: bool = False


@router.get("")
def list_messages(
    case_id: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = db.query(Message)
    if case_id:
        query = query.filter(Message.case_id == case_id)
    messages = query.order_by(Message.sent_at.desc()).limit(100).all()

    return [
        {
            "id": m.id,
            "case_id": m.case_id,
            "patient_id": m.patient_id,
            "channel": m.channel,
            "language": m.language,
            "template_id": m.template_id,
            "body": m.body,
            "status": m.status.value if hasattr(m.status, "value") else str(m.status),
            "sent_at": m.sent_at.isoformat() if m.sent_at else None,
            "validator_result": json.loads(m.validator_result_json) if m.validator_result_json else None,
            "ai_action_id": m.ai_action_id,
        }
        for m in messages
    ]


@router.post("/preview")
def preview_message(req: MessagePreviewRequest, db: Session = Depends(get_db)):
    """Preview deterministic template, AI rewrite attempt, and validator verdict."""
    ai = MockAIProvider(should_fail_validation=req.simulate_adversarial)
    pipeline = CommsPipeline(db, ai_provider=ai)

    raw_tmpl = pipeline.select_template(req.template_id, req.language)
    body_tmpl = raw_tmpl.get("body", "")
    deterministic_text = pipeline.fill_template(body_tmpl, req.context_data)

    ai_rewrite = None
    validator_passed = True
    violations = []
    fallback_used = False
    final_text = deterministic_text

    if req.use_ai_rewrite:
        ai_rewrite = ai.rewrite_message(deterministic_text, "simple", req.language)
        validator = MessageValidator()
        validator_passed, violations = validator.validate_patient_message(ai_rewrite)
        if validator_passed:
            final_text = ai_rewrite
        else:
            fallback_used = True
            final_text = deterministic_text

    return {
        "deterministic_template": deterministic_text,
        "ai_rewritten_draft": ai_rewrite,
        "validator_passed": validator_passed,
        "violations": violations,
        "fallback_used": fallback_used,
        "final_rendered_message": final_text,
    }

