"""Reusable transcript and evaluation fixtures for tests."""

from app.schemas.evaluation import (
    EvaluationResult,
    RubricCriterionScore,
    TranscriptEvidence,
)

GOOD_STUDENT_MESSAGES = [
    "It sounds like work has been taking a real toll on you lately.",
    "What has felt most overwhelming for you recently?",
    "That makes a lot of sense given everything you're carrying.",
    "How have you been coping with those long days?",
]


def make_valid_evaluation_result() -> EvaluationResult:
    return EvaluationResult(
        overall_score=4.0,
        rubric_scores={
            "empathy": RubricCriterionScore(
                score=4,
                label="Empathy",
                description="Ability to acknowledge client feelings",
            ),
            "reflection": RubricCriterionScore(
                score=4,
                label="Reflection",
                description="Ability to reflect meaning or emotion",
            ),
            "open_ended_questions": RubricCriterionScore(
                score=4,
                label="Open-ended Questions",
                description="Ability to invite deeper sharing",
            ),
            "closed_question_balance": RubricCriterionScore(
                score=4,
                label="Closed Question Balance",
                description="Avoiding overuse of yes/no questions",
            ),
            "validation": RubricCriterionScore(
                score=4,
                label="Validation",
                description="Ability to respect and normalize client experience",
            ),
            "pacing": RubricCriterionScore(
                score=4,
                label="Pacing",
                description="Avoiding rushing, overloading, or premature advice",
            ),
        },
        strengths=["You acknowledged Jordan's feelings directly."],
        areas_for_growth=["Try a few more complex reflections."],
        evidence_from_transcript=[
            TranscriptEvidence(
                quote="It sounds like work has been taking a real toll on you lately.",
                feedback="Strong empathic reflection that builds trust.",
            )
        ],
        suggested_improved_response="It sounds like this has been weighing on you for a while.",
    )
