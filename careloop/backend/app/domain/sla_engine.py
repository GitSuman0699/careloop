"""SLA engine — tracks service level agreements, warnings, breaches and escalations."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy.orm import Session

from app.core.clock import get_clock
from app.core.config import get_assumption_value
from app.db.models import (
    Case,
    Escalation,
    SLATimer,
    SLAStatus,
    User,
    UserRole,
)
from app.core.ids import generate_id


class SLAEngine:
    """Evaluates and updates SLA timers and escalations."""

    def __init__(self, db: Session):
        self.db = db
        self.clock = get_clock()

    def create_timer(
        self, case_id: str, step: str, sla_days: float, warn_pct: float = 75.0
    ) -> SLATimer:
        """Create a new SLA timer for a case at a given step."""
        now = self.clock.now()
        total_seconds = sla_days * 86400.0
        warn_seconds = total_seconds * (warn_pct / 100.0)

        due_at = now + timedelta(seconds=total_seconds)
        warn_at = now + timedelta(seconds=warn_seconds)

        timer = SLATimer(
            id=generate_id(),
            case_id=case_id,
            step=step,
            due_at=due_at,
            warn_at=warn_at,
            status=SLAStatus.running,
        )
        self.db.add(timer)
        self.db.flush()
        return timer

    def complete_timer(self, case_id: str, step: str) -> Optional[SLATimer]:
        """Mark a running timer for a step as met."""
        timer = (
            self.db.query(SLATimer)
            .filter(
                SLATimer.case_id == case_id,
                SLATimer.step == step,
                SLATimer.status.in_([SLAStatus.running, SLAStatus.warned]),
            )
            .first()
        )
        if timer:
            timer.status = SLAStatus.met
            self.db.flush()
        return timer

    def tick(self) -> dict:
        """Evaluate all active SLA timers against the clock."""
        now = self.clock.now()
        warned_count = 0
        breached_count = 0
        escalations_created = 0

        # Check running timers that should warn
        timers_to_warn = (
            self.db.query(SLATimer)
            .filter(
                SLATimer.status == SLAStatus.running,
                SLATimer.warn_at <= now,
                SLATimer.due_at > now,
            )
            .all()
        )
        for t in timers_to_warn:
            t.status = SLAStatus.warned
            warned_count += 1

        # Check running or warned timers that have breached
        timers_to_breach = (
            self.db.query(SLATimer)
            .filter(
                SLATimer.status.in_([SLAStatus.running, SLAStatus.warned]),
                SLATimer.due_at <= now,
            )
            .all()
        )
        for t in timers_to_breach:
            t.status = SLAStatus.breached
            breached_count += 1

            # Auto-raise Tier 1 Escalation if not already raised for this breach
            existing_esc = (
                self.db.query(Escalation)
                .filter(
                    Escalation.case_id == t.case_id,
                    Escalation.tier == 1,
                    Escalation.reason.like(f"%SLA breach on step {t.step}%"),
                    Escalation.resolved_at.is_(None),
                )
                .first()
            )
            if not existing_esc:
                esc = Escalation(
                    id=generate_id(),
                    case_id=t.case_id,
                    tier=1,
                    reason=f"SLA breach on step {t.step}: due at {t.due_at.isoformat()}",
                    raised_at=now,
                )
                self.db.add(esc)
                escalations_created += 1

                # If case is urgent or priority, also raise Tier 2 for clinical lead visibility
                case = self.db.query(Case).filter(Case.id == t.case_id).first()
                if case and case.urgency_tier in ["urgent", "priority"]:
                    t2_esc = Escalation(
                        id=generate_id(),
                        case_id=t.case_id,
                        tier=2,
                        reason=f"High urgency SLA breach ({case.urgency_tier}) on step {t.step}",
                        raised_at=now,
                    )
                    self.db.add(t2_esc)
                    escalations_created += 1

        self.db.flush()
        return {
            "evaluated_at": now.isoformat(),
            "warned": warned_count,
            "breached": breached_count,
            "escalations_created": escalations_created,
        }

    def get_exception_queues(self) -> dict:
        """Derive actionable exception queues from the ledger."""
        now = self.clock.now()

        # 1. Overdue: cases with breached SLA timers
        overdue_cases = (
            self.db.query(Case)
            .join(SLATimer, Case.id == SLATimer.case_id)
            .filter(
                SLATimer.status == SLAStatus.breached,
                Case.closed_at.is_(None),
            )
            .distinct()
            .all()
        )

        # 2. Unassigned: open cases without an owner
        unassigned_cases = (
            self.db.query(Case)
            .filter(
                Case.owner_id.is_(None),
                Case.closed_at.is_(None),
            )
            .all()
        )

        # 3. Urgent: cases marked urgent
        urgent_cases = (
            self.db.query(Case)
            .filter(
                Case.urgency_tier == "urgent",
                Case.closed_at.is_(None),
            )
            .all()
        )

        # 4. Unreachable
        unreachable_cases = (
            self.db.query(Case)
            .filter(
                Case.current_state == "PATIENT_UNREACHABLE",
                Case.closed_at.is_(None),
            )
            .all()
        )

        # 5. Rejected referrals
        rejected_cases = (
            self.db.query(Case)
            .filter(
                Case.current_state == "REFERRAL_REJECTED",
                Case.closed_at.is_(None),
            )
            .all()
        )

        return {
            "overdue_count": len(overdue_cases),
            "unassigned_count": len(unassigned_cases),
            "urgent_count": len(urgent_cases),
            "unreachable_count": len(unreachable_cases),
            "rejected_count": len(rejected_cases),
        }

