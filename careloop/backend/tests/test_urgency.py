"""Tests for red-flag urgency evaluation."""

from __future__ import annotations

import pytest

from app.domain.pathway_loader import PathwayConfig, RedFlagRule
from app.domain.urgency import evaluate_red_flags


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_pathway_with_rules(rules: list[dict], urgency_tiers: list[str] | None = None) -> PathwayConfig:
    """Build an in-memory PathwayConfig with the given red flag rules."""
    if urgency_tiers is None:
        urgency_tiers = ["routine_actionable", "priority", "urgent"]
    return PathwayConfig.model_validate(
        {
            "id": "test_urgency_pathway",
            "title": "Test Urgency Pathway",
            "version": "0.1.0",
            "steps": [
                {"id": "RESULT_ISSUED", "label": "Result issued", "next": ["CLOSED"]},
                {"id": "CLOSED", "label": "Closed", "next": []},
            ],
            "closure": {"requires_human_approval": True, "allowed_types": ["completed"]},
            "urgency_tiers": urgency_tiers,
            "red_flag_rules": rules,
        }
    )


@pytest.fixture()
def fit_pathway_with_rules() -> PathwayConfig:
    """A pathway with realistic FIT red-flag rules."""
    return _make_pathway_with_rules(
        rules=[
            {
                "id": "rf_rectal_bleeding",
                "description": "Active rectal bleeding reported",
                "condition_field": "rectal_bleeding",
                "condition_op": "eq",
                "condition_value": True,
                "upgrade_to": "urgent",
            },
            {
                "id": "rf_weight_loss",
                "description": "Unexplained weight loss > 5%",
                "condition_field": "weight_loss_pct",
                "condition_op": "gt",
                "condition_value": 5.0,
                "upgrade_to": "urgent",
            },
            {
                "id": "rf_iron_deficiency",
                "description": "Iron-deficiency anaemia",
                "condition_field": "iron_deficiency",
                "condition_op": "eq",
                "condition_value": True,
                "upgrade_to": "priority",
            },
            {
                "id": "rf_family_history",
                "description": "First-degree relative with colorectal cancer",
                "condition_field": "family_history_crc",
                "condition_op": "eq",
                "condition_value": True,
                "upgrade_to": "priority",
            },
        ]
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestNoRedFlags:
    def test_no_red_flags_returns_none(self, fit_pathway_with_rules):
        """When no rules fire, returns (None, [])."""
        answers = {
            "rectal_bleeding": False,
            "weight_loss_pct": 2.0,
            "iron_deficiency": False,
            "family_history_crc": False,
        }
        tier, triggered = evaluate_red_flags(fit_pathway_with_rules, answers)
        assert tier is None
        assert triggered == []

    def test_no_answers_returns_none(self, fit_pathway_with_rules):
        """Empty answers dict fires no rules."""
        tier, triggered = evaluate_red_flags(fit_pathway_with_rules, {})
        assert tier is None
        assert triggered == []

    def test_no_rules_pathway_returns_none(self):
        """Pathway with no red flag rules always returns (None, [])."""
        pathway = _make_pathway_with_rules(rules=[])
        tier, triggered = evaluate_red_flags(pathway, {"any_field": True})
        assert tier is None
        assert triggered == []


class TestSingleRedFlag:
    def test_red_flag_sets_urgent(self, fit_pathway_with_rules):
        """Active rectal bleeding triggers 'urgent' tier upgrade."""
        answers = {"rectal_bleeding": True}
        tier, triggered = evaluate_red_flags(fit_pathway_with_rules, answers)
        assert tier == "urgent"
        assert "rf_rectal_bleeding" in triggered

    def test_red_flag_weight_loss_gt_threshold(self, fit_pathway_with_rules):
        """weight_loss_pct > 5.0 triggers 'urgent'."""
        answers = {"weight_loss_pct": 7.5}
        tier, triggered = evaluate_red_flags(fit_pathway_with_rules, answers)
        assert tier == "urgent"
        assert "rf_weight_loss" in triggered

    def test_red_flag_weight_loss_at_threshold_does_not_trigger(self, fit_pathway_with_rules):
        """weight_loss_pct == 5.0 does NOT trigger (op is 'gt', not 'gte')."""
        answers = {"weight_loss_pct": 5.0}
        tier, triggered = evaluate_red_flags(fit_pathway_with_rules, answers)
        assert "rf_weight_loss" not in triggered

    def test_red_flag_sets_priority(self, fit_pathway_with_rules):
        """Iron deficiency triggers 'priority' tier upgrade."""
        answers = {"iron_deficiency": True}
        tier, triggered = evaluate_red_flags(fit_pathway_with_rules, answers)
        assert tier == "priority"
        assert "rf_iron_deficiency" in triggered


class TestMultipleRedFlags:
    def test_multiple_red_flags(self, fit_pathway_with_rules):
        """Multiple triggers are all reported; highest tier wins."""
        answers = {
            "rectal_bleeding": True,  # → urgent
            "iron_deficiency": True,  # → priority
            "family_history_crc": True,  # → priority
        }
        tier, triggered = evaluate_red_flags(fit_pathway_with_rules, answers)
        assert tier == "urgent"  # highest tier
        assert "rf_rectal_bleeding" in triggered
        assert "rf_iron_deficiency" in triggered
        assert "rf_family_history" in triggered

    def test_multiple_priority_flags_stay_priority(self, fit_pathway_with_rules):
        """Multiple 'priority' rules fire but no 'urgent' — stays at priority."""
        answers = {
            "iron_deficiency": True,
            "family_history_crc": True,
        }
        tier, triggered = evaluate_red_flags(fit_pathway_with_rules, answers)
        assert tier == "priority"
        assert len(triggered) == 2

    def test_urgent_beats_priority(self, fit_pathway_with_rules):
        """When both priority and urgent rules fire, 'urgent' is returned."""
        answers = {
            "rectal_bleeding": True,  # urgent
            "family_history_crc": True,  # priority
        }
        tier, triggered = evaluate_red_flags(fit_pathway_with_rules, answers)
        assert tier == "urgent"


class TestOperators:
    def test_eq_operator(self):
        """eq operator matches exact equality."""
        pathway = _make_pathway_with_rules([
            {"id": "r1", "description": "d", "condition_field": "status",
             "condition_op": "eq", "condition_value": "positive", "upgrade_to": "urgent"},
        ])
        tier, triggered = evaluate_red_flags(pathway, {"status": "positive"})
        assert tier == "urgent"
        tier2, _ = evaluate_red_flags(pathway, {"status": "negative"})
        assert tier2 is None

    def test_neq_operator(self):
        """neq operator fires when values differ."""
        pathway = _make_pathway_with_rules([
            {"id": "r1", "description": "d", "condition_field": "status",
             "condition_op": "neq", "condition_value": "normal", "upgrade_to": "priority"},
        ])
        tier, _ = evaluate_red_flags(pathway, {"status": "abnormal"})
        assert tier == "priority"

    def test_gte_operator(self):
        """gte operator fires when field_value >= condition_value."""
        pathway = _make_pathway_with_rules([
            {"id": "r1", "description": "d", "condition_field": "hba1c",
             "condition_op": "gte", "condition_value": 48, "upgrade_to": "urgent"},
        ])
        tier, _ = evaluate_red_flags(pathway, {"hba1c": 48})
        assert tier == "urgent"
        tier2, _ = evaluate_red_flags(pathway, {"hba1c": 47})
        assert tier2 is None

    def test_in_operator(self):
        """in operator fires when field value is in the condition list."""
        pathway = _make_pathway_with_rules([
            {"id": "r1", "description": "d", "condition_field": "symptom",
             "condition_op": "in", "condition_value": ["bleeding", "anaemia"], "upgrade_to": "urgent"},
        ])
        tier, _ = evaluate_red_flags(pathway, {"symptom": "bleeding"})
        assert tier == "urgent"
        tier2, _ = evaluate_red_flags(pathway, {"symptom": "fatigue"})
        assert tier2 is None

    def test_contains_operator(self):
        """contains operator fires when condition_value is in the field list."""
        pathway = _make_pathway_with_rules([
            {"id": "r1", "description": "d", "condition_field": "symptoms",
             "condition_op": "contains", "condition_value": "bleeding", "upgrade_to": "urgent"},
        ])
        tier, _ = evaluate_red_flags(pathway, {"symptoms": ["bleeding", "fatigue"]})
        assert tier == "urgent"
