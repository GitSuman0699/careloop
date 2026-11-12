"""Discrete-event simulation engine — compares Baseline fragmented care vs CareLoop."""

from __future__ import annotations

import random
from typing import Any, Dict, List, Tuple

from sim.params import SimParams


class SimulationEngine:
    """Discrete-event Monte Carlo simulator for screening-to-care loop."""

    def __init__(self, seed: int = 42, cohort_size: int = 5000):
        self.seed = seed
        self.cohort_size = cohort_size
        self.params = SimParams()

    def generate_population(self, rng: random.Random) -> List[Dict[str, Any]]:
        """Generate synthetic patient population with realistic demographic distributions."""
        population = []
        languages = ["en", "ar", "ur", "other"]
        lang_weights = [0.55, 0.30, 0.10, 0.05]

        age_bands = ["45-54", "55-64", "65-74", "75+"]
        age_weights = [0.25, 0.40, 0.25, 0.10]

        nationality_groups = ["Group_A", "Group_B", "Group_C"]
        care_settings = ["urban_clinic", "regional_hospital", "primary_centre"]

        for i in range(self.cohort_size):
            lang = rng.choices(languages, weights=lang_weights, k=1)[0]
            age = rng.choices(age_bands, weights=age_weights, k=1)[0]
            sex = rng.choice(["F", "M"])
            nat = rng.choice(nationality_groups)
            setting = rng.choice(care_settings)

            population.append({
                "patient_id": f"SIM-PT-{i:05d}",
                "language": lang,
                "age_band": age,
                "sex": sex,
                "nationality_group": nat,
                "care_setting": setting,
            })
        return population

    def simulate_baseline_arm(
        self, population: List[Dict[str, Any]], rng: random.Random
    ) -> List[Dict[str, Any]]:
        """Simulate baseline fragmented pathway without CareLoop orchestration."""
        records = []
        for p in population:
            rec = dict(p)
            rec["arm"] = "baseline"

            # Language gap penalty for baseline
            lang_penalty = 1.35 if p["language"] != "en" else 1.0

            # Step 1: Notification
            leak_notif = self.params.leak_no_notification * lang_penalty
            if rng.random() < leak_notif:
                rec["status"] = "LEAKED_NOTIFICATION"
                rec["leakage_step"] = "notification"
                rec["days_to_notify"] = None
                records.append(rec)
                continue

            days_notify = rng.randint(2, 12)
            rec["days_to_notify"] = days_notify

            # Step 2: Acknowledgement
            leak_ack = self.params.leak_no_ack * lang_penalty
            if rng.random() < leak_ack:
                rec["status"] = "LEAKED_ACKNOWLEDGEMENT"
                rec["leakage_step"] = "acknowledgement"
                records.append(rec)
                continue

            days_ack = days_notify + rng.randint(3, 14)

            # Step 3: Confirmation
            if rng.random() < self.params.leak_no_confirmation:
                rec["status"] = "LEAKED_CONFIRMATION"
                rec["leakage_step"] = "confirmation"
                records.append(rec)
                continue

            days_conf = days_ack + rng.randint(2, 10)

            # Step 4: Referral
            if rng.random() < self.params.leak_referral_not_sent:
                rec["status"] = "LEAKED_REFERRAL_NOT_SENT"
                rec["leakage_step"] = "referral_issuance"
                records.append(rec)
                continue

            if rng.random() < self.params.leak_referral_rejected:
                rec["status"] = "LEAKED_REFERRAL_REJECTED"
                rec["leakage_step"] = "referral_rejection"
                records.append(rec)
                continue

            rec["referral_sent"] = True
            days_ref = days_conf + rng.randint(7, 21)

            # Step 5: Appointment Booking & Attendance
            rec["appointment_booked"] = True
            days_apt = days_ref + rng.randint(14, 45)

            if rng.random() < self.params.leak_no_show:
                rec["status"] = "NO_SHOW_UNREBOOKED"
                rec["leakage_step"] = "appointment_attendance"
                records.append(rec)
                continue

            rec["appointment_attended"] = True

            # Step 6: Follow-up loss
            if rng.random() < self.params.leak_loss_to_follow_up:
                rec["status"] = "LOST_TO_FOLLOWUP"
                rec["leakage_step"] = "closure_documentation"
                records.append(rec)
                continue

            # Fully closed with care documented
            rec["status"] = "CLOSED"
            rec["days_to_closure"] = days_apt + rng.randint(3, 14)
            rec["teachback_passed"] = rng.random() < 0.45  # low baseline teachback
            records.append(rec)

        return records

    def simulate_careloop_arm(
        self, population: List[Dict[str, Any]], rng: random.Random
    ) -> List[Dict[str, Any]]:
        """Simulate pathway orchestrated with CareLoop single-ownership and SLA engine."""
        records = []
        for p in population:
            rec = dict(p)
            rec["arm"] = "careloop"

            # Multichannel and language-matched messaging eliminates the language penalty
            # and reduces notification leakage by 70%
            leak_notif = self.params.leak_no_notification * 0.30
            if rng.random() < leak_notif:
                rec["status"] = "LEAKED_NOTIFICATION"
                rec["leakage_step"] = "notification"
                records.append(rec)
                continue

            days_notify = rng.randint(1, 4)  # strict SLA compliance
            rec["days_to_notify"] = days_notify

            # Multilingual acknowledgement retry policy
            leak_ack = self.params.leak_no_ack * (1.0 - self.params.eff_multilingual_ack) * 0.50
            if rng.random() < leak_ack:
                rec["status"] = "LEAKED_ACKNOWLEDGEMENT"
                rec["leakage_step"] = "acknowledgement"
                records.append(rec)
                continue

            days_ack = days_notify + rng.randint(1, 5)

            # Confirmation recovery via navigator call task
            leak_conf = self.params.leak_no_confirmation * 0.35
            if rng.random() < leak_conf:
                rec["status"] = "LEAKED_CONFIRMATION"
                rec["leakage_step"] = "confirmation"
                records.append(rec)
                continue

            days_conf = days_ack + rng.randint(1, 4)

            # Referral tracking: auto-returns rejected referrals so they are re-routed
            rec["referral_sent"] = True
            days_ref = days_conf + rng.randint(3, 8)

            # Appointment reminder & 2-way rescheduling reduces no-shows
            rec["appointment_booked"] = True
            days_apt = days_ref + rng.randint(10, 24)

            leak_noshow = self.params.leak_no_show * (1.0 - self.params.eff_navigator_no_show) * (1.0 - self.params.eff_sms_reminder)
            if rng.random() < leak_noshow:
                rec["status"] = "NO_SHOW_UNREBOOKED"
                rec["leakage_step"] = "appointment_attendance"
                records.append(rec)
                continue

            rec["appointment_attended"] = True

            # Documented human-approved closure with evidence checklist
            leak_followup = self.params.leak_loss_to_follow_up * 0.20
            if rng.random() < leak_followup:
                rec["status"] = "LOST_TO_FOLLOWUP"
                rec["leakage_step"] = "closure_documentation"
                records.append(rec)
                continue

            rec["status"] = "CLOSED"
            rec["days_to_closure"] = days_apt + rng.randint(2, 6)
            rec["teachback_passed"] = rng.random() < 0.82  # high teachback comprehension
            records.append(rec)

        return records

    def run(self) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Execute full paired simulation run."""
        rng = random.Random(self.seed)
        pop = self.generate_population(rng)

        # Use same random seed state for paired comparison
        rng_base = random.Random(self.seed)
        base_records = self.simulate_baseline_arm(pop, rng_base)

        rng_loop = random.Random(self.seed)
        loop_records = self.simulate_careloop_arm(pop, rng_loop)

        return base_records, loop_records
