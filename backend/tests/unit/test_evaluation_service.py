"""Unit tests for evaluation validation rules."""

import pytest
from pydantic import ValidationError

from app.schemas.evaluation import (
    EvaluationResult,
    RubricCriterionScore,
    TranscriptEvidence,
)


def _scores(value: int = 4) -> dict[str, RubricCriterionScore]:
    return {
        "empathy": RubricCriterionScore(
            score=value,
            label="Empathy",
            description="Ability to acknowledge client feelings",
        ),
        "reflection": RubricCriterionScore(score=value, label="Reflection"),
    }


def test_rubric_score_out_of_range_rejected():
    with pytest.raises(ValidationError):
        RubricCriterionScore(score=6, max_score=5)


def test_legacy_integer_rubric_scores_are_normalized():
    result = EvaluationResult(
        overall_score=4.0,
        rubric_scores={"empathy": 4},
        strengths=["ok"],
        areas_for_growth=["ok"],
        evidence_from_transcript=[],
        suggested_improved_response="x",
    )
    assert result.rubric_scores["empathy"].score == 4
    assert result.rubric_scores["empathy"].max_score == 5


def test_overall_score_out_of_range_rejected():
    with pytest.raises(ValidationError):
        EvaluationResult(
            overall_score=9.0,
            rubric_scores=_scores(),
            strengths=["ok"],
            areas_for_growth=["ok"],
            evidence_from_transcript=[],
            suggested_improved_response="x",
        )


def test_empty_strengths_rejected():
    with pytest.raises(ValidationError):
        EvaluationResult(
            overall_score=4.0,
            rubric_scores=_scores(),
            strengths=[],
            areas_for_growth=["ok"],
            evidence_from_transcript=[],
            suggested_improved_response="x",
        )


def test_valid_evaluation_accepted():
    result = EvaluationResult(
        overall_score=4.2,
        rubric_scores=_scores(),
        strengths=["You showed empathy."],
        areas_for_growth=["Use more reflections."],
        evidence_from_transcript=[TranscriptEvidence(quote="q", feedback="f")],
        suggested_improved_response="Consider reflecting feelings first.",
        specialized_analyses={"engagement_progression": {"summary": "Improved"}},
        missed_opportunities=[{"turn": 2, "description": "Explore emotion"}],
        faculty_review_recommended=True,
    )
    assert result.overall_score == 4.2
    assert result.specialized_analyses["engagement_progression"]["summary"] == "Improved"
    assert result.missed_opportunities[0]["turn"] == 2
    assert result.faculty_review_recommended is True
