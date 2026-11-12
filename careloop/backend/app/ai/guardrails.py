"""AI Guardrails and Validators — ensures AI outputs are safe, compliant, and never disclose diagnosis."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from app.core.config import get_config_dir


def load_banned_rules() -> Dict[str, Any]:
    """Load banned terms and regex patterns from config/templates/banned_terms.json."""
    path = get_config_dir() / "templates" / "banned_terms.json"
    if not path.exists():
        return {"banned_terms": [], "banned_patterns": []}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


class MessageValidator:
    """Validates patient-facing and consult-facing text for safety violations."""

    def __init__(self):
        rules = load_banned_rules()
        self.banned_terms = rules.get("banned_terms", [])
        self.banned_patterns = rules.get("banned_patterns", [])

        # Additional hard diagnosis disclosure phrases
        self.diagnosis_phrases = [
            "you have cancer",
            "positive for cancer",
            "malignant tumor",
            "diagnosed with",
            "you have a tumour",
            "you have a tumor",
            "your cancer",
            "positive for malignancy",
        ]

        # Numeric result patterns: e.g., "120 ug/g", "48 mmol/mol"
        self.numeric_result_pattern = re.compile(
            r"\b\d+(\.\d+)?\s*(ug/g|µg/g|mg/dL|mmol/mol|%|\bng/mL\b)", re.IGNORECASE
        )

    def validate_patient_message(self, text: str) -> Tuple[bool, List[str]]:
        """Validate text intended for a patient.
        
        Returns (is_valid, list_of_violations).
        """
        violations: List[str] = []
        lower_text = text.lower()

        # 1. Check explicit diagnosis disclosure phrases
        for phrase in self.diagnosis_phrases:
            if phrase in lower_text:
                violations.append(f"Diagnosis disclosure violation: contains '{phrase}'")

        # 2. Check banned terms
        for item in self.banned_terms:
            term = item.get("term", "").lower()
            severity = item.get("severity", "error")
            if severity == "error" and term and re.search(rf"\b{re.escape(term)}\b", lower_text):
                violations.append(f"Banned term violation: contains '{term}' ({item.get('context', '')})")

        # 3. Check banned regex patterns
        for pat in self.banned_patterns:
            regex_str = pat.get("regex")
            severity = pat.get("severity", "error")
            if severity == "error" and regex_str:
                if re.search(regex_str, text):
                    violations.append(f"Banned pattern violation: matched pattern '{regex_str}'")

        # 4. Check numeric laboratory results (should not be sent bare to patients)
        if self.numeric_result_pattern.search(text):
            violations.append("Raw numeric laboratory result detected in patient message")

        return (len(violations) == 0, violations)

