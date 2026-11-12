"""Simulation runner — executes 30 Monte Carlo seeds and exports results to JSON & CSV."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from sim.engine import SimulationEngine
from sim.fairness import analyze_fairness_comparison
from sim.metrics import compute_arm_metrics, calculate_ci95
from sim.sensitivity import generate_breakeven_capacity_curve, generate_tornado_analysis


def run_simulation(cohort_size: int = 5000, seeds_count: int = 30, output_dir: Path | None = None) -> dict:
    if output_dir is None:
        output_dir = Path(__file__).resolve().parent / "results"
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Running CareLoop simulation: N={cohort_size} per arm across {seeds_count} Monte Carlo replicates...")

    base_closed_90 = []
    loop_closed_90 = []
    base_ref_conv = []
    loop_ref_conv = []
    base_apt_comp = []
    loop_apt_comp = []
    base_days = []
    loop_days = []

    # Final detailed records from representative seed 42
    rep_engine = SimulationEngine(seed=42, cohort_size=cohort_size)
    rep_base_records, rep_loop_records = rep_engine.run()

    for s in range(seeds_count):
        engine = SimulationEngine(seed=42 + s, cohort_size=cohort_size)
        base_recs, loop_recs = engine.run()

        bm = compute_arm_metrics(base_recs)
        lm = compute_arm_metrics(loop_recs)

        base_closed_90.append(bm["closed_90d_pct"])
        loop_closed_90.append(lm["closed_90d_pct"])
        base_ref_conv.append(bm["referral_conversion_rate"])
        loop_ref_conv.append(lm["referral_conversion_rate"])
        base_apt_comp.append(bm["appointment_completion_rate"])
        loop_apt_comp.append(lm["appointment_completion_rate"])
        base_days.append(bm["median_days_to_closure"])
        loop_days.append(lm["median_days_to_closure"])

    # Aggregate CI95
    headline = {
        "closed_90d_pct": {
            "baseline": calculate_ci95(base_closed_90),
            "careloop": calculate_ci95(loop_closed_90),
            "absolute_improvement": round(calculate_ci95(loop_closed_90)["mean"] - calculate_ci95(base_closed_90)["mean"], 3),
        },
        "referral_conversion_rate": {
            "baseline": calculate_ci95(base_ref_conv),
            "careloop": calculate_ci95(loop_ref_conv),
        },
        "appointment_completion_rate": {
            "baseline": calculate_ci95(base_apt_comp),
            "careloop": calculate_ci95(loop_apt_comp),
        },
        "median_days_to_closure": {
            "baseline": calculate_ci95(base_days),
            "careloop": calculate_ci95(loop_days),
            "days_saved": round(calculate_ci95(base_days)["mean"] - calculate_ci95(loop_days)["mean"], 1),
        },
    }

    fairness = analyze_fairness_comparison(rep_base_records, rep_loop_records)
    tornado = generate_tornado_analysis()
    capacity_curve = generate_breakeven_capacity_curve()

    full_results = {
        "metadata": {
            "cohort_size_per_arm": cohort_size,
            "replicates": seeds_count,
            "disclaimer": "MODELLED RESULTS, NOT CLINICAL EVIDENCE. Simulated under explicitly parameterized assumptions.",
        },
        "headline_metrics": headline,
        "representative_baseline": compute_arm_metrics(rep_base_records),
        "representative_careloop": compute_arm_metrics(rep_loop_records),
        "fairness_demographic_cuts": fairness,
        "tornado_sensitivity": tornado,
        "capacity_breakeven_curve": capacity_curve,
    }

    # Write JSON
    json_path = output_dir / "simulation_results.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(full_results, f, indent=2)

    # Write summary CSV
    csv_path = output_dir / "headline_comparison.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Metric", "Baseline (Mean [95% CI])", "CareLoop (Mean [95% CI])", "Difference"])
        for k, v in headline.items():
            if "baseline" in v and "careloop" in v:
                b_str = f"{v['baseline']['mean']} [{v['baseline']['ci_lower']} - {v['baseline']['ci_upper']}]"
                l_str = f"{v['careloop']['mean']} [{v['careloop']['ci_lower']} - {v['careloop']['ci_upper']}]"
                diff = round(v['careloop']['mean'] - v['baseline']['mean'], 3)
                writer.writerow([k, b_str, l_str, diff])

    print(f"Simulation complete! Saved to {json_path} and {csv_path}")
    return full_results


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--cohort", type=int, default=5000)
    parser.add_argument("--seeds", type=int, default=30)
    args = parser.parse_args()
    run_simulation(cohort_size=args.cohort, seeds_count=args.seeds)
