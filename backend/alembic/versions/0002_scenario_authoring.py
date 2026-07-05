"""scenario_authoring_fields

Adds faculty-authoring columns to ``scenarios``: a lifecycle ``status``, the
structured JSONB input fields, and the separately-stored generated prompt.
Existing active scenarios are marked ``published`` so the student flow is
unaffected.

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-17

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _jsonb() -> postgresql.JSONB:
    return postgresql.JSONB(astext_type=sa.Text())


def upgrade() -> None:
    op.add_column(
        "scenarios",
        sa.Column("status", sa.String(length=32), nullable=False, server_default="draft"),
    )
    op.create_index("ix_scenarios_status", "scenarios", ["status"])
    op.add_column("scenarios", sa.Column("estimated_turns", sa.Integer(), nullable=True))

    for column in (
        "client_identity",
        "presenting_concern",
        "cultural_considerations",
        "resistance_configuration",
        "disclosure_rules",
        "emotional_tone",
        "hidden_information",
        "learning_objectives",
        "rubric_items",
        "safety_rules",
    ):
        op.add_column("scenarios", sa.Column(column, _jsonb(), nullable=True))

    op.add_column("scenarios", sa.Column("generated_prompt", sa.Text(), nullable=True))
    op.add_column("scenarios", sa.Column("prompt_version", sa.String(length=64), nullable=True))
    op.add_column(
        "scenarios",
        sa.Column("prompt_generated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column("scenarios", sa.Column("published_by", sa.String(length=255), nullable=True))
    op.add_column(
        "scenarios",
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Existing scenarios were already live for students.
    op.execute(
        "UPDATE scenarios SET status = 'published', published_at = now() "
        "WHERE is_active = true"
    )


def downgrade() -> None:
    for column in (
        "published_at",
        "published_by",
        "prompt_generated_at",
        "prompt_version",
        "generated_prompt",
        "safety_rules",
        "rubric_items",
        "learning_objectives",
        "hidden_information",
        "emotional_tone",
        "disclosure_rules",
        "resistance_configuration",
        "cultural_considerations",
        "presenting_concern",
        "client_identity",
        "estimated_turns",
    ):
        op.drop_column("scenarios", column)
    op.drop_index("ix_scenarios_status", table_name="scenarios")
    op.drop_column("scenarios", "status")
