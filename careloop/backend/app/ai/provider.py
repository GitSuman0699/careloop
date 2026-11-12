"""AI Provider abstract interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class AIProvider(ABC):
    """Abstract interface for CareLoop advisory AI models."""

    @abstractmethod
    def rewrite_message(
        self,
        template_text: str,
        target_reading_level: str = "simple",
        language: str = "en",
    ) -> str:
        """Rewrite a patient message for clearer reading level while maintaining required facts."""
        pass

    @abstractmethod
    def summarize_consult(self, case_events: list[dict], clinical_notes: str = "") -> str:
        """Summarize case history for receiving clinician."""
        pass

    @abstractmethod
    def assist_closure_proposal(self, evidence_list: list[dict], case_summary: dict) -> str:
        """Draft closure basis summary for clinician review."""
        pass

    @abstractmethod
    def classify_delay_reason(self, note: str) -> str:
        """Classify a free-text delay note into a standard taxonomy category."""
        pass
