"""Pathway loader — reads pathway JSON configs and validates them with Pydantic."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from app.core.config import get_config_dir


# ---------------------------------------------------------------------------
# Pydantic sub-models
# ---------------------------------------------------------------------------
class RedFlagRule(BaseModel):
    id: str
    description: str
    condition_field: str
    condition_op: str  # e.g. "eq", "gt", "in"
    condition_value: Any
    upgrade_to: str


class SLARef(BaseModel):
    warn: str  # assumption key or literal
    breach: str


class StepConfig(BaseModel):
    id: str
    label: str
    next: list[str] = Field(default_factory=list)
    sla: Optional[SLARef] = None
    sla_key: Optional[str] = None  # alternative flat key used in JSON files
    owner_role: Optional[str] = None
    auto: bool = False
    auto_transition: bool = False  # alias used in JSON files
    description: Optional[str] = None

    @field_validator("next", mode="before")
    @classmethod
    def coerce_next(cls, v: Any) -> list[str]:
        if v is None:
            return []
        if isinstance(v, str):
            return [v]
        return [x for x in v if x is not None]

    def model_post_init(self, __context: Any) -> None:
        # Normalise next: accept a bare string from JSON
        if isinstance(self.next, str):
            object.__setattr__(self, "next", [self.next] if self.next else [])


class ClosureConfig(BaseModel):
    requires_human_approval: bool = True
    allowed_types: list[str] = Field(default_factory=list)


class EscalationTier(BaseModel):
    tier: int
    trigger: str  # e.g. "sla_breach", "red_flag"
    assign_to_role: str
    description: Optional[str] = None


class EscalationConfig(BaseModel):
    tiers: list[EscalationTier] = Field(default_factory=list)


class PathwayConfig(BaseModel):
    id: str = ""
    pathway_id: str = ""  # alias used in some JSON files
    title: str = ""
    name: str = ""  # alias used in some JSON files
    version: str = "0.1"
    clinical_review_status: str = "PLACEHOLDER_NEEDS_CLINICAL_REVIEW"
    sources: list[str] = Field(default_factory=list)
    urgency_tiers: list[Any] = Field(default_factory=list)
    red_flag_rules: list[Any] = Field(default_factory=list)
    steps: list[StepConfig] = Field(default_factory=list)
    side_states: list[Any] = Field(default_factory=list)
    closure: ClosureConfig = Field(default_factory=ClosureConfig)
    escalation: EscalationConfig = Field(default_factory=EscalationConfig)
    escalation_tiers: list[Any] = Field(default_factory=list)

    def model_post_init(self, __context: Any) -> None:
        # Normalise id: prefer pathway_id if id is missing
        if not self.id and self.pathway_id:
            object.__setattr__(self, "id", self.pathway_id)
        # Normalise title: prefer name if title is missing
        if not self.title and self.name:
            object.__setattr__(self, "title", self.name)
        # Filter None out of step.next lists
        for step in self.steps:
            cleaned = [n for n in step.next if n is not None]
            object.__setattr__(step, "next", cleaned)
        # Parse red_flag_rules: coerce raw dicts into RedFlagRule objects
        parsed_rules = []
        for r in self.red_flag_rules:
            if isinstance(r, dict):
                try:
                    parsed_rules.append(RedFlagRule.model_validate(r))
                except Exception:
                    parsed_rules.append(r)  # keep raw if schema doesn't match
            else:
                parsed_rules.append(r)
        object.__setattr__(self, "red_flag_rules", parsed_rules)

    def step_ids(self) -> list[str]:
        """Return an ordered list of step IDs."""
        return [s.id for s in self.steps]

    def get_urgency_tier_ids(self) -> list[str]:
        """Return urgency tier IDs as strings (handles both str and dict entries)."""
        ids = []
        for t in self.urgency_tiers:
            if isinstance(t, str):
                ids.append(t)
            elif isinstance(t, dict):
                ids.append(t.get("id", str(t)))
        return ids


# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------
_PATHWAYS_DIR: Path | None = None


def _pathways_dir() -> Path:
    global _PATHWAYS_DIR
    if _PATHWAYS_DIR is None:
        _PATHWAYS_DIR = get_config_dir() / "pathways"
    return _PATHWAYS_DIR


def list_pathways() -> list[str]:
    """Return the IDs (file stems) of all available pathway JSON files."""
    d = _pathways_dir()
    if not d.exists():
        return []
    return sorted(p.stem for p in d.glob("*.json"))


def load_pathway(pathway_id: str) -> PathwayConfig:
    """Load and validate a pathway configuration from its JSON file.

    Raises ``FileNotFoundError`` if the file does not exist, and
    ``pydantic.ValidationError`` on schema violations.
    """
    path = _pathways_dir() / f"{pathway_id}.json"
    if not path.exists():
        raise FileNotFoundError(f"Pathway config not found: {path}")
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    return PathwayConfig.model_validate(data)


def get_valid_transitions(pathway_id: str) -> dict[str, list[str]]:
    """Return ``{state: [allowed_next_states]}`` for a pathway."""
    cfg = load_pathway(pathway_id)
    transitions: dict[str, list[str]] = {}
    for step in cfg.steps:
        transitions[step.id] = list(step.next)
    return transitions
