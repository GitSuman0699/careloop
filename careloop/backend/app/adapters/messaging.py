"""Mock Referral, Scheduling, and Messaging adapters."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from app.core.clock import get_clock


class ReferralAdapter:
    """Mock interface to e-Referral platforms."""

    def __init__(self):
        self.clock = get_clock()

    def transmit_referral(
        self, case_id: str, from_provider_id: str, to_provider_id: str, packet_data: dict
    ) -> Dict[str, Any]:
        return {
            "transmission_id": f"REF-TX-{case_id[:8]}",
            "transmitted_at": self.clock.now().isoformat(),
            "status": "SENT",
            "acknowledgement": "RECEIVED_BY_ENDPOINT",
        }


class SchedulingAdapter:
    """Mock interface to Hospital Scheduling and PAS engines."""

    def __init__(self):
        self.clock = get_clock()

    def get_available_slots(self, provider_id: str, days_ahead: int = 14) -> List[Dict[str, Any]]:
        now = self.clock.now()
        slots = []
        for i in range(1, 6):
            slot_time = now + timedelta(days=i * 2, hours=2)
            slots.append({
                "slot_id": f"SLOT-{provider_id[:4]}-{i}",
                "provider_id": provider_id,
                "slot_at": slot_time.isoformat(),
                "specialty": "Gastroenterology / Endoscopy",
            })
        return slots


class MessagingGatewayAdapter:
    """Mock interface to SMS/WhatsApp gateway."""

    def __init__(self):
        self.clock = get_clock()

    def send_sms(self, to_phone: str, body: str) -> Dict[str, Any]:
        return {
            "gateway_message_id": f"GW-{to_phone[-4:]}-{int(self.clock.now().timestamp())}",
            "status": "DELIVERED",
            "delivered_at": self.clock.now().isoformat(),
        }

