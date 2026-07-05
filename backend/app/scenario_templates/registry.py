"""Registry of developer-owned scenario template families."""

from __future__ import annotations

from app.core.exceptions import ResourceNotFoundError
from app.scenario_templates.microskills_progressive_disclosure import (
    Module1MicroskillsTemplate,
)
from app.scenario_templates.protocol import ScenarioTemplateDefinition

DEFAULT_TEMPLATE_KEY = "microskills_progressive_disclosure"

SCENARIO_TEMPLATE_REGISTRY: dict[str, ScenarioTemplateDefinition] = {
    DEFAULT_TEMPLATE_KEY: Module1MicroskillsTemplate(),
}


def get_template(template_key: str) -> ScenarioTemplateDefinition:
    try:
        return SCENARIO_TEMPLATE_REGISTRY[template_key]
    except KeyError as exc:
        raise ResourceNotFoundError(f"Scenario template '{template_key}' was not found.") from exc
