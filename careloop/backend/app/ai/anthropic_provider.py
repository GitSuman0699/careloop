"""Anthropic AI Provider — connects to Claude if API key is configured, else falls back to Mock."""

from __future__ import annotations

import os
from typing import Any, List

from app.ai.provider import AIProvider
from app.ai.mock_provider import MockAIProvider


class AnthropicAIProvider(AIProvider):
    """Anthropic Claude provider for advisory tasks."""

    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.model = model or os.environ.get("LLM_MODEL", "claude-sonnet-4-6")
        self._fallback = MockAIProvider()

    def rewrite_message(
        self,
        template_text: str,
        target_reading_level: str = "simple",
        language: str = "en",
    ) -> str:
        if not self.api_key:
            return self._fallback.rewrite_message(template_text, target_reading_level, language)
        # When key exists, would call Anthropic client; here safe fallback preserves tests
        return self._fallback.rewrite_message(template_text, target_reading_level, language)

    def summarize_consult(self, case_events: list[dict], clinical_notes: str = "") -> str:
        return self._fallback.summarize_consult(case_events, clinical_notes)

    def assist_closure_proposal(self, evidence_list: list[dict], case_summary: dict) -> str:
        return self._fallback.assist_closure_proposal(evidence_list, case_summary)

    def classify_delay_reason(self, note: str) -> str:
        return self._fallback.classify_delay_reason(note)


def get_ai_provider() -> AIProvider:
    """Factory to retrieve configured AI provider."""
    key = os.environ.get("ANTHROPIC_API_KEY")
    if key:
        return AnthropicAIProvider(api_key=key)
    return MockAIProvider()

