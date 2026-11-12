"""Statistical and outcome metric calculations for simulation runs."""

from __future__ import annotations

import math
from typing import Any, Dict, List, Sequence


def calculate_median(values: Sequence[float]) -> float:
    if not values:
        return 0.0
    sorted_v = sorted(values)
    n = len(sorted_v)
    mid = n // 2
    if n % 2 == 1:
        return float(sorted_v[mid])
    return (sorted_v[mid - 1] + sorted_v[mid]) / 2.0


def calculate_iqr(values: Sequence[float]) -> Dict[str, float]:
    if not values:
        return {"q25": 0.0, "q75": 0.0, "iqr": 0.0}
    sorted_v = sorted(values)
    n = len(sorted_v)
    q25 = sorted_v[int(n * 0.25)]
    q75 = sorted_v[int(n * 0.75)]
    return {"q25": float(q25), "q75": float(q75), "iqr": float(q75 - q25)}


def calculate_ci95(values: Sequence[float]) -> Dict[str, float]:
    if not values:
        return {"mean": 0.0, "ci_lower": 0.0, "ci_upper": 0.0}
    n = len(values)
    mean = sum(values) / n
    if n < 2:
        return {"mean": mean, "ci_lower": mean, "ci_upper": mean}
    variance = sum((x - mean) ** 2 for x in values) / (n - 1)
    std_err = math.sqrt(variance / n)
    margin = 1.96 * std_err
    return {
        "mean": round(mean, 3),
        "ci_lower": round(max(0.0, mean - margin), 3),
        "ci_upper": round(mean + margin, 3),
    }


def compute_arm_metrics(patient_records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compute headline evaluation metrics for one simulation arm."""
    total = len(patient_records)
    if total == 0:
        return {}

    completed = [p for p in patient_records if p.get("status") == "CLOSED"]
    closed_rate = len(completed) / total

    completed_30d = len([p for p in completed if p.get("days_to_closure", 999) <= 30])
    completed_60d = len([p for p in completed if p.get("days_to_closure", 999) <= 60])
    completed_90d = len([p for p in completed if p.get("days_to_closure", 999) <= 90])

    unresolved_90d = total - completed_90d

    # Times to milestones (in days)
    days_to_notify = [p["days_to_notify"] for p in patient_records if p.get("days_to_notify") is not None]
    days_to_care = [p["days_to_closure"] for p in completed if p.get("days_to_closure") is not None]

    # Referral and appointment completion
    referred = [p for p in patient_records if p.get("referral_sent", False)]
    apt_booked = [p for p in patient_records if p.get("appointment_booked", False)]
    apt_attended = [p for p in patient_records if p.get("appointment_attended", False)]

    ref_conversion = len(apt_booked) / len(referred) if referred else 0.0
    apt_completion = len(apt_attended) / len(apt_booked) if apt_booked else 0.0

    # Teachback proxy
    teachback_passed = len([p for p in patient_records if p.get("teachback_passed", False)])
    teachback_rate = teachback_passed / total

    return {
        "cohort_size": total,
        "closure_rate": round(closed_rate, 4),
        "closed_30d_pct": round(completed_30d / total, 4),
        "closed_60d_pct": round(completed_60d / total, 4),
        "closed_90d_pct": round(completed_90d / total, 4),
        "unresolved_90d_count": unresolved_90d,
        "referral_conversion_rate": round(ref_conversion, 4),
        "appointment_completion_rate": round(apt_completion, 4),
        "median_days_to_notify": calculate_median(days_to_notify),
        "median_days_to_closure": calculate_median(days_to_care),
        "iqr_days_to_closure": calculate_iqr(days_to_care),
        "teachback_pass_rate": round(teachback_rate, 4),
    }
