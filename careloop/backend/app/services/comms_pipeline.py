"""Patient communication pipeline — template selection, optional AI rewrite, validation, and fallbacks."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from sqlalchemy.orm import Session

from app.ai.guardrails import MessageValidator
from app.ai.provider import AIProvider
from app.ai.anthropic_provider import get_ai_provider
from app.core.clock import get_clock
from app.core.config import get_config_dir
from app.core.ids import generate_id
from app.db.models import AIAction, AIActionKind, Case, Message, MessageStatus, Patient


class CommsPipeline:
    """Manages patient notification drafting, AI rewrites, validation, and queueing."""

    def __init__(self, db: Session, ai_provider: Optional[AIProvider] = None):
        self.db = db
        self.clock = get_clock()
        self.ai = ai_provider or get_ai_provider()
        self.validator = MessageValidator()
        self._load_templates()

    def _load_templates(self):
        templates_dir = get_config_dir() / "templates"
        en_path = templates_dir / "messages.en.json"
        ar_path = templates_dir / "messages.ar.json"

        self.en_templates = {}
        self.ar_templates = {}

        if en_path.exists():
            with open(en_path, "r", encoding="utf-8") as f:
                self.en_templates = json.load(f)
        if ar_path.exists():
            with open(ar_path, "r", encoding="utf-8") as f:
                self.ar_templates = json.load(f)

    def select_template(self, template_id: str, language: str = "en") -> dict:
        """Select template by ID and language."""
        store = self.ar_templates if language == "ar" else self.en_templates
        if template_id in store:
            return store[template_id]
        # fallback to English
        return self.en_templates.get(template_id, {
            "subject": "CareLoop Notification",
            "body": "Dear {{patient_name}}, please review your CareLoop record for an update on your care pathway.",
            "channels": {"app": {"format": "full"}, "sms": {"body": "CareLoop update: please open app."}},
        })

    def fill_template(self, template_str: str, data: dict) -> str:
        """Deterministic placeholder substitution."""
        text = template_str
        for k, v in data.items():
            text = text.replace(f"{{{{{k}}}}}", str(v))
        return text

    def draft_message(
        self,
        case_id: str,
        patient_id: str,
        template_id: str,
        context_data: dict,
        channel: str = "app",
        language: str = "en",
        use_ai_rewrite: bool = False,
    ) -> Message:
        """Draft a message with template and optional safe AI rewrite."""
        raw_tmpl = self.select_template(template_id, language)

        if channel == "sms" and "channels" in raw_tmpl and "sms" in raw_tmpl["channels"]:
            body_template = raw_tmpl["channels"]["sms"].get("body", raw_tmpl.get("body", ""))
        else:
            body_template = raw_tmpl.get("body", "")

        # 1. Deterministic fill
        deterministic_body = self.fill_template(body_template, context_data)
        final_body = deterministic_body
        ai_action_id = None
        validator_result = {"passed": True, "violations": []}

        # 2. Optional AI rewrite
        if use_ai_rewrite:
            ai_output = self.ai.rewrite_message(
                template_text=deterministic_body,
                target_reading_level="simple",
                language=language,
            )

            # 3. Validate AI output
            is_valid, violations = self.validator.validate_patient_message(ai_output)
            input_hash = hashlib.sha256(deterministic_body.encode("utf-8")).hexdigest()

            ai_action = AIAction(
                id=generate_id(),
                kind=AIActionKind.message_rewrite,
                provider="mock_or_llm",
                model="claude-sonnet-or-mock",
                input_hash=input_hash,
                output_text=ai_output,
                validator_passed=is_valid,
                fallback_used=not is_valid,
                reviewed_by=None,
                reviewed_at=None,
            )
            self.db.add(ai_action)
            self.db.flush()
            ai_action_id = ai_action.id

            if is_valid:
                final_body = ai_output
                validator_result = {"passed": True, "violations": []}
            else:
                # Fallback to deterministic template!
                final_body = deterministic_body
                validator_result = {"passed": False, "violations": violations, "fallback_used": True}

        # 4. Save Message
        now = self.clock.now()
        message = Message(
            id=generate_id(),
            case_id=case_id,
            patient_id=patient_id,
            channel=channel,
            language=language,
            template_id=template_id,
            body=final_body,
            status=MessageStatus.delivered,
            sent_at=now,
            delivered_at=now,
            validator_result_json=json.dumps(validator_result),
            ai_action_id=ai_action_id,
        )
        self.db.add(message)
        self.db.flush()
        return message
