"""Tests for the assumptions config loader."""

from __future__ import annotations

import pytest

from app.core.config import (
    get_assumption,
    get_assumption_value,
    reload_assumptions,
)


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear lru_cache before each test so changes take effect."""
    reload_assumptions()
    yield
    reload_assumptions()


class TestLoadAssumptions:
    def test_load_assumptions(self):
        """assumptions.yaml loads without raising an error."""
        entry = get_assumption("fit.notify_within_days")
        assert entry is not None

    def test_get_assumption_returns_dict(self):
        """get_assumption returns a dict with value, unit, source, status fields."""
        entry = get_assumption("fit.notify_within_days")
        assert isinstance(entry, dict)
        for field in ("value", "unit", "source", "status"):
            assert field in entry, f"Missing field: {field}"

    def test_get_assumption_value_returns_number(self):
        """get_assumption_value returns a numeric value."""
        value = get_assumption_value("fit.notify_within_days")
        assert isinstance(value, (int, float))

    def test_all_assumptions_are_placeholder(self):
        """Every assumption has status == PLACEHOLDER (all are unvalidated)."""
        from app.core.config import _load_assumptions
        all_assumptions = _load_assumptions()
        for key, entry in all_assumptions.items():
            assert entry.get("status") == "PLACEHOLDER", (
                f"Assumption '{key}' has status={entry.get('status')!r}, expected PLACEHOLDER"
            )

    def test_missing_assumption_raises(self):
        """get_assumption raises KeyError for an unknown key."""
        with pytest.raises(KeyError, match="Unknown assumption key"):
            get_assumption("does.not.exist")

    def test_known_assumption_keys_present(self):
        """Spot-check that expected keys exist."""
        known_keys = [
            "fit.positivity_rate",
            "fit.notify_within_days",
            "breast.recall_rate",
            "cardiometabolic.hba1c_threshold_mmol",
            "sla.max_open_cases_per_navigator",
            "navigator.avg_contact_attempts",
            "simulation.population_size",
            "baseline_leakage.no_notification",
            "intervention_effects.navigator_reduces_no_show",
            "fairness.disparity_alert_threshold",
        ]
        for key in known_keys:
            entry = get_assumption(key)
            assert entry is not None, f"Missing assumption: {key}"

    def test_get_assumption_value_fit_notify(self):
        """fit.notify_within_days has value 3."""
        value = get_assumption_value("fit.notify_within_days")
        assert value == 3
