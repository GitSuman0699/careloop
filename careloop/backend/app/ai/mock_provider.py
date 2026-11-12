"""Mock AI Provider — deterministic, offline-first implementation for reproducible tests & demos."""

from __future__ import annotations

import hashlib
from typing import Any, Dict, List

from app.ai.provider import AIProvider


class MockAIProvider(AIProvider):
    """Deterministic mock provider."""

    def __init__(self, should_fail_validation: bool = False):
        self.should_fail_validation = should_fail_validation

    def rewrite_message(
        self,
        template_text: str,
        target_reading_level: str = "simple",
        language: str = "en",
    ) -> str:
        if self.should_fail_validation:
            # Adversarial output intended to trigger validator failure
            return "Your screening test was positive. You have cancer and need an emergency operation immediately."

        if language == "ar":
            return f"[نص مبسط ومراجع للمريض]: {template_text}"
        return f"[Clearer rewrite]: {template_text.strip()}"

    def summarize_consult(self, case_events: list[dict], clinical_notes: str = "") -> str:
        count = len(case_events)
        return (
            f"Automated timeline summary: {count} events recorded across screening, notification, "
            f"and referral hand-offs. Patient flags reviewed; recommended consult preparation complete."
        )

    def assist_closure_proposal(self, evidence_list: list[dict], case_summary: dict) -> str:
        types = [e.get("evidence_type", "unknown") for e in evidence_list]
        return (
            f"Closure basis proposal: Case has reached completed care milestone with "
            f"{len(evidence_list)} evidence item(s) on file ({', '.join(types)}). "
            f"All follow-up obligations met. Recommended for clinician review and sign-off."
        )

    def classify_delay_reason(self, note: str) -> str:
        lower = note.lower()
        if "transport" in lower or "ride" in lower or "travel" in lower:
            return "transportation_barrier"
        if "work" in lower or "busy" in lower or "leave" in lower:
            return "scheduling_work_conflict"
        if "fear" in lower or "anxious" in lower or "scared" in lower:
            return "anxiety_or_fear"
        if "phone" in lower or "unreachable" in lower or "no answer" in lower:
            return "unreachable_contact_issue"
        return "provider_capacity_delay"
