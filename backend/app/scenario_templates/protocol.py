"""Protocol for reusable scenario template families."""

from __future__ import annotations

from typing import Any, Protocol

from pydantic import BaseModel


class ScenarioTemplateDefinition(Protocol):
    """Contract every developer-owned scenario family must satisfy."""

    key: str
    version: str
    display_name: str
    supported_modalities: list[str]
    output_schema_version: str
    authoring_schema: type[BaseModel]

    def default_rubric(self) -> list[dict[str, Any]]: ...

    def default_safety_policy(self) -> dict[str, Any]: ...

    def template_content(self) -> dict[str, Any]: ...

    def initial_state(self, profile: BaseModel) -> dict[str, Any]: ...

    def allowed_disclosures(
        self,
        profile: BaseModel,
        current_state: dict[str, Any],
        *,
        has_direct_question: bool = False,
    ) -> list[str]: ...

    def build_client_prompt(self, profile: BaseModel) -> str: ...

    def build_evaluator_prompt(
        self, rubric: list[dict[str, Any]], learning_objectives: list[dict[str, Any]]
    ) -> str: ...
