"""Fairness analysis — evaluates outcome parity across demographic subgroups with small-cell suppression."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List


def compute_fairness_cuts(
    records: List[Dict[str, Any]],
    demographic_key: str,
    min_cell_size: int = 20,
) -> List[Dict[str, Any]]:
    """Compute 90-day closure rate for each group of demographic_key.
    
    Suppresses groups with total count < min_cell_size.
    Reports absolute gap and ratio relative to the best performing group.
    """
    grouped = defaultdict(list)
    for r in records:
        val = r.get(demographic_key, "Unknown")
        grouped[val].append(r)

    subgroup_rates = {}
    for group_name, group_records in grouped.items():
        if len(group_records) < min_cell_size:
            continue
        closed_90 = len([p for p in group_records if p.get("days_to_closure", 999) <= 90])
        rate = closed_90 / len(group_records)
        subgroup_rates[group_name] = {
            "group": group_name,
            "sample_size": len(group_records),
            "closed_90d_rate": round(rate, 4),
        }

    if not subgroup_rates:
        return []

    best_rate = max(d["closed_90d_rate"] for d in subgroup_rates.values())

    results = []
    for g, data in subgroup_rates.items():
        rate = data["closed_90d_rate"]
        abs_gap = round(best_rate - rate, 4)
        ratio = round(rate / best_rate, 4) if best_rate > 0 else 1.0
        results.append({
            "demographic_field": demographic_key,
            "group": g,
            "sample_size": data["sample_size"],
            "closed_90d_rate": rate,
            "absolute_gap_vs_best": abs_gap,
            "disparity_ratio_vs_best": ratio,
        })

    return sorted(results, key=lambda x: x["closed_90d_rate"], reverse=True)


def analyze_fairness_comparison(
    baseline_records: List[Dict[str, Any]],
    careloop_records: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Compare fairness cuts between Baseline and CareLoop arms across all demographic attributes."""
    demographics = ["language", "age_band", "sex", "nationality_group", "care_setting"]
    comparison = {}

    for demo in demographics:
        base_cuts = {c["group"]: c for c in compute_fairness_cuts(baseline_records, demo)}
        loop_cuts = {c["group"]: c for c in compute_fairness_cuts(careloop_records, demo)}

        groups = sorted(set(base_cuts.keys()) | set(loop_cuts.keys()))
        group_comparisons = []
        for g in groups:
            b = base_cuts.get(g, {})
            l = loop_cuts.get(g, {})
            b_rate = b.get("closed_90d_rate", 0.0)
            l_rate = l.get("closed_90d_rate", 0.0)
            abs_improvement = round(l_rate - b_rate, 4)
            group_comparisons.append({
                "group": g,
                "baseline_rate": b_rate,
                "careloop_rate": l_rate,
                "improvement": abs_improvement,
                "baseline_gap": b.get("absolute_gap_vs_best", 0.0),
                "careloop_gap": l.get("absolute_gap_vs_best", 0.0),
            })
        comparison[demo] = group_comparisons

    return comparison
