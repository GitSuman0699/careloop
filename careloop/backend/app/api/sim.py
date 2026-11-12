"""Simulation API router — serves simulation runs, headline comparisons, fairness cuts, and sensitivity."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.auth import require_permission
from app.db.models import SimRun, User
from app.db.session import get_db
from sim.run import run_simulation

router = APIRouter(prefix="/sim", tags=["simulation"])


@router.get("/results")
def get_latest_simulation_results():
    """Retrieve the latest pre-computed or generated simulation results."""
    results_path = Path(__file__).resolve().parents[2] / "sim" / "results" / "simulation_results.json"
    if results_path.exists():
        with open(results_path, "r", encoding="utf-8") as f:
            return json.load(f)

    # If file doesn't exist yet, run on-demand
    return run_simulation(cohort_size=5000, seeds_count=30)


@router.post("/run")
def trigger_simulation(
    cohort_size: int = 5000,
    seeds_count: int = 30,
    user: User = Depends(require_permission("run_simulation")),
):
    """Trigger a fresh simulation execution."""
    results = run_simulation(cohort_size=cohort_size, seeds_count=seeds_count)
    return {"status": "completed", "results": results}
