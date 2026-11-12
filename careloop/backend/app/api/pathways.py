"""Pathways router — pathway configurations and visualization metadata."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.domain.pathway_loader import list_pathways, load_pathway

router = APIRouter(prefix="/pathways", tags=["pathways"])


@router.get("")
def get_pathways():
    """List all available pathway configurations."""
    pathway_ids = list_pathways()
    results = []
    for pid in pathway_ids:
        try:
            cfg = load_pathway(pid)
            results.append({
                "id": cfg.id,
                "title": cfg.title,
                "version": cfg.version,
                "clinical_review_status": cfg.clinical_review_status,
                "steps_count": len(cfg.steps),
                "urgency_tiers": cfg.urgency_tiers,
            })
        except Exception:
            results.append({"id": pid, "title": pid, "error": "Failed to parse"})
    return results


@router.get("/{pathway_id}")
def get_pathway_detail(pathway_id: str):
    """Retrieve full configuration for a pathway."""
    try:
        cfg = load_pathway(pathway_id)
        return cfg.model_dump()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Pathway not found")
