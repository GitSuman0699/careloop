"""Simulation parameters loader."""

from __future__ import annotations

from typing import Any, Dict
from app.core.config import get_assumption_value


class SimParams:
    """Convenient typed access to simulation assumptions."""

    def __init__(self):
        # Simulation scale
        self.cohort_size = int(get_assumption_value("simulation.population_size") // 2) or 5000
        self.sim_duration_days = int(get_assumption_value("simulation.sim_duration_days") or 365)

        # Baseline leakage probabilities
        self.leak_no_notification = float(get_assumption_value("baseline_leakage.no_notification") or 0.05)
        self.leak_no_ack = float(get_assumption_value("baseline_leakage.no_acknowledgement") or 0.10)
        self.leak_no_confirmation = float(get_assumption_value("baseline_leakage.no_confirmation") or 0.08)
        self.leak_referral_not_sent = float(get_assumption_value("baseline_leakage.referral_not_sent") or 0.03)
        self.leak_referral_rejected = float(get_assumption_value("baseline_leakage.referral_rejected") or 0.02)
        self.leak_no_show = float(get_assumption_value("baseline_leakage.appointment_no_show") or 0.12)
        self.leak_loss_to_follow_up = float(get_assumption_value("baseline_leakage.loss_to_follow_up") or 0.07)

        # Intervention relative risk reductions
        self.eff_navigator_no_show = float(get_assumption_value("intervention_effects.navigator_reduces_no_show") or 0.40)
        self.eff_sms_reminder = float(get_assumption_value("intervention_effects.sms_reminder_reduces_no_show") or 0.25)
        self.eff_auto_escalation = float(get_assumption_value("intervention_effects.auto_escalation_reduces_delay") or 0.30)
        self.eff_multilingual_ack = float(get_assumption_value("intervention_effects.multilingual_increases_acknowledgement") or 0.15)

        # Navigator capacity limits
        self.max_caseload = int(get_assumption_value("sla.max_open_cases_per_navigator") or 120)
        self.disparity_threshold = float(get_assumption_value("fairness.disparity_alert_threshold") or 0.10)

