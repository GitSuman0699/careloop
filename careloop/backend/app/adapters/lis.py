"""Mock LIS adapter — ingests laboratory results and transforms them into standardized findings."""

from __future__ import annotations

from typing import Dict, Any
from app.core.clock import get_clock


class LISAdapter:
    """Mock interface to Laboratory Information Systems."""

    def __init__(self):
        self.clock = get_clock()

    def parse_hl7_oru_r01(self, hl7_payload: str) -> Dict[str, Any]:
        """Mock parsing of an HL7 v2 ORU^R01 observation result message."""
        now = self.clock.now()
        return {
            "source": "MOCK_LIS_ADAPTER",
            "parsed_at": now.isoformat(),
            "status": "ACTIONABLE",
            "test_type": "FIT",
            "raw_payload_preview": hl7_payload[:80] if hl7_payload else "",
        }
