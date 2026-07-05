"""Add Module 1 behavior architecture authoring fields.

Revision ID: 0005
Revises: 0004
Create Date: 2026-06-26
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

from app.db.base import JSONColumn


revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("scenarios", sa.Column("engagement_levels", JSONColumn, nullable=True))
    op.add_column("scenarios", sa.Column("engagement_increase_rules", JSONColumn, nullable=True))
    op.add_column("scenarios", sa.Column("engagement_decrease_rules", JSONColumn, nullable=True))
    op.add_column("scenarios", sa.Column("emotional_cue_progression", JSONColumn, nullable=True))
    op.add_column("scenarios", sa.Column("silence_response_rules", JSONColumn, nullable=True))
    op.add_column("scenarios", sa.Column("counselor_skill_detection", JSONColumn, nullable=True))
    op.add_column("scenarios", sa.Column("session_success_indicators", JSONColumn, nullable=True))
    op.add_column("scenarios", sa.Column("competency_scale", JSONColumn, nullable=True))
    op.add_column("scenarios", sa.Column("evaluation_focus_sections", JSONColumn, nullable=True))
    op.add_column("scenarios", sa.Column("reflection_questions", JSONColumn, nullable=True))


def downgrade() -> None:
    op.drop_column("scenarios", "reflection_questions")
    op.drop_column("scenarios", "evaluation_focus_sections")
    op.drop_column("scenarios", "competency_scale")
    op.drop_column("scenarios", "session_success_indicators")
    op.drop_column("scenarios", "counselor_skill_detection")
    op.drop_column("scenarios", "silence_response_rules")
    op.drop_column("scenarios", "emotional_cue_progression")
    op.drop_column("scenarios", "engagement_decrease_rules")
    op.drop_column("scenarios", "engagement_increase_rules")
    op.drop_column("scenarios", "engagement_levels")
