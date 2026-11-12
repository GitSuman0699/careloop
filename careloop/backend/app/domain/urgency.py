"""Urgency evaluation and red-flag detection — pure functions."""

from __future__ import annotations

from typing import Any

from app.domain.pathway_loader import PathwayConfig


def evaluate_red_flags(
    pathway_config: PathwayConfig, answers: dict[str, Any]
) -> tuple[str | None, list[str]]:
    """Evaluate red-flag rules against *answers* and determine urgency upgrade.

    Returns ``(new_urgency_tier_or_None, list_of_triggered_rule_ids)``.
    If no rules fire, returns ``(None, [])``.

    Supported operators in ``condition_op``:
    * ``eq``  — exact equality
    * ``neq`` — not equal
    * ``gt``  — greater than (numeric)
    * ``gte`` — greater than or equal (numeric)
    * ``lt``  — less than (numeric)
    * ``lte`` — less than or equal (numeric)
    * ``in``  — value is contained in a list
    * ``contains`` — answer list contains the condition value
    """
    triggered: list[str] = []
    highest_tier: str | None = None

    tier_order = {t: i for i, t in enumerate(pathway_config.get_urgency_tier_ids())}

    for rule in pathway_config.red_flag_rules:
        # rule may be a RedFlagRule object or a raw dict
        if isinstance(rule, dict):
            field = rule.get("condition_field")
            op = rule.get("condition_op", "eq")
            cval = rule.get("condition_value")
            upgrade_to = rule.get("upgrade_to", "")
            rule_id = rule.get("id", "")
        else:
            field = rule.condition_field
            op = rule.condition_op
            cval = rule.condition_value
            upgrade_to = rule.upgrade_to
            rule_id = rule.id

        field_value = answers.get(field)
        if field_value is None:
            continue

        if _check_condition(op, field_value, cval):
            triggered.append(rule_id)
            if highest_tier is None:
                highest_tier = upgrade_to
            else:
                cur_rank = tier_order.get(highest_tier, -1)
                new_rank = tier_order.get(upgrade_to, -1)
                if new_rank > cur_rank:
                    highest_tier = upgrade_to

    return (highest_tier, triggered)


def _check_condition(op: str, field_value: Any, condition_value: Any) -> bool:
    """Evaluate a single condition operator."""
    if op == "eq":
        return field_value == condition_value
    if op == "neq":
        return field_value != condition_value
    if op == "gt":
        return float(field_value) > float(condition_value)
    if op == "gte":
        return float(field_value) >= float(condition_value)
    if op == "lt":
        return float(field_value) < float(condition_value)
    if op == "lte":
        return float(field_value) <= float(condition_value)
    if op == "in":
        return field_value in condition_value
    if op == "contains":
        return condition_value in field_value
    return False
