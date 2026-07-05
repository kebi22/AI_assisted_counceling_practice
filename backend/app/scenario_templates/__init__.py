"""Scenario template definitions and registry."""

from app.scenario_templates.registry import (
    DEFAULT_TEMPLATE_KEY,
    SCENARIO_TEMPLATE_REGISTRY,
    get_template,
)

__all__ = ["DEFAULT_TEMPLATE_KEY", "SCENARIO_TEMPLATE_REGISTRY", "get_template"]
