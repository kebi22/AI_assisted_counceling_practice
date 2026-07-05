"""Shared identifiers and ordering helpers for scenario runtime state."""

from __future__ import annotations

import re

from app.schemas.scenario_authoring import DisclosureItem, ScenarioAuthoringData


STAGE_ORDER = {"early": 1, "mid": 2, "later": 3}


def disclosure_key(item: DisclosureItem) -> str:
    """Return a stable runtime key, including for legacy disclosures without one."""
    if item.key and item.key.strip():
        return item.key.strip()
    slug = re.sub(r"[^a-z0-9]+", "_", item.label.lower()).strip("_")
    return slug or "disclosure"


def all_disclosure_items(scenario: ScenarioAuthoringData) -> list[DisclosureItem]:
    rules = scenario.disclosure_rules
    return [*rules.immediate, *rules.after_rapport, *rules.on_direct_question]

