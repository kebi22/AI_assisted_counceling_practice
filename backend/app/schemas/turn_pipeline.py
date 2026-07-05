"""Structured contracts for one simulated-client turn."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator


DisclosureSemanticStatus = Literal[
    "not_present",
    "related_only",
    "partially_implied",
    "substantially_revealed",
    "explicitly_revealed",
]

CueResponseStatus = Literal[
    "no_active_cue",
    "ignored",
    "topic_only",
    "acknowledged",
    "accurately_reflected",
    "deepened",
    "misattuned",
    "redirected",
    "uncertain",
]


class CueResponseAnalysis(BaseModel):
    """Semantic relationship between one counselor response and one active cue."""

    cue: str | None = None
    cue_key: str | None = None
    status: CueResponseStatus = "no_active_cue"
    confidence: float = Field(default=0, ge=0, le=100)
    client_evidence: str = ""
    counselor_evidence: str = ""
    rationale: str = ""
    analyzer: str = "conservative-no-semantic-fallback-v1"

    @field_validator("confidence")
    @classmethod
    def _normalize_confidence(cls, value: float) -> float:
        return value / 100 if value > 1 else value


class SemanticDisclosureFinding(BaseModel):
    disclosure_key: str
    status: DisclosureSemanticStatus
    confidence: float = Field(..., ge=0, le=100)
    evidence: str = ""
    reason: str = ""

    @field_validator("confidence")
    @classmethod
    def _normalize_confidence(cls, value: float) -> float:
        return value / 100 if value > 1 else value


class SemanticCueFinding(BaseModel):
    cue: str
    status: Literal["not_present", "expressed", "deepened"]
    confidence: float = Field(..., ge=0, le=100)
    evidence: str = ""
    reason: str = ""

    @field_validator("confidence")
    @classmethod
    def _normalize_confidence(cls, value: float) -> float:
        return value / 100 if value > 1 else value


class SemanticSafetyFinding(BaseModel):
    status: Literal["none", "ambiguous", "explicit"] = "none"
    category: str | None = None
    confidence: float = Field(default=0, ge=0, le=100)
    evidence: str = ""
    reason: str = ""

    @field_validator("confidence")
    @classmethod
    def _normalize_confidence(cls, value: float) -> float:
        return value / 100 if value > 1 else value


class SemanticClientResponseAnalysis(BaseModel):
    disclosures: list[SemanticDisclosureFinding] = Field(default_factory=list)
    cues: list[SemanticCueFinding] = Field(default_factory=list)
    safety: SemanticSafetyFinding = Field(default_factory=SemanticSafetyFinding)


class ClientResponsePlan(BaseModel):
    """Deterministic instructions given to the client roleplay model."""

    turn: int
    session_stage: str
    client_stance: str
    engagement_level: int = Field(..., ge=1, le=5)
    trust_level: int = Field(..., ge=1, le=5)
    emotional_depth: int = Field(default=1, ge=1, le=5)
    rupture_count: int = 0
    counselor_effect: str
    previous_cue_response: str | None = None
    active_emotional_cues: list[str] = Field(default_factory=list)
    permitted_emotional_cues: list[str] = Field(default_factory=list)
    selected_disclosure_key: str | None = None
    selected_progression_beat_key: str | None = None
    selected_disclosure_label: str | None = None
    selected_disclosure_content: str | None = None
    eligible_disclosure_keys: list[str] = Field(default_factory=list)
    blocked_disclosure_keys: list[str] = Field(default_factory=list)
    already_revealed_keys: list[str] = Field(default_factory=list)
    maximum_new_disclosures: int = 1


class ClientResponseValidation(BaseModel):
    """Result of checking generated client text against the response plan."""

    accepted: bool
    detected_disclosure_keys: list[str] = Field(default_factory=list)
    detected_emotional_cues: list[str] = Field(default_factory=list)
    unauthorized_emotional_cues: list[str] = Field(default_factory=list)
    unauthorized_disclosure_keys: list[str] = Field(default_factory=list)
    ambiguous_disclosure_keys: list[str] = Field(default_factory=list)
    violations: list[str] = Field(default_factory=list)
    disclosure_findings: list[SemanticDisclosureFinding] = Field(default_factory=list)
    cue_findings: list[SemanticCueFinding] = Field(default_factory=list)
    safety_finding: SemanticSafetyFinding = Field(default_factory=SemanticSafetyFinding)
    requires_safety_clarification: bool = False
    validator: str = "deterministic-token-fallback-v1"
