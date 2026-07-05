"""evaluation_version_metadata

Stores the scenario/template version metadata and state-aware analyses used to
produce an evaluation. Columns are nullable so historical evaluations remain
valid.

Revision ID: 0004
Revises: 0003
Create Date: 2026-06-24

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _jsonb() -> postgresql.JSONB:
    return postgresql.JSONB(astext_type=sa.Text())


def upgrade() -> None:
    op.add_column(
        "evaluations", sa.Column("scenario_version_id", sa.Uuid(), nullable=True)
    )
    op.add_column("evaluations", sa.Column("template_key", sa.String(length=120), nullable=True))
    op.add_column(
        "evaluations", sa.Column("template_version", sa.String(length=64), nullable=True)
    )
    op.add_column(
        "evaluations", sa.Column("rubric_version", sa.String(length=64), nullable=True)
    )
    op.add_column(
        "evaluations",
        sa.Column("output_schema_version", sa.String(length=64), nullable=True),
    )
    op.add_column("evaluations", sa.Column("specialized_analyses", _jsonb(), nullable=True))
    op.add_column("evaluations", sa.Column("missed_opportunities", _jsonb(), nullable=True))
    op.add_column(
        "evaluations",
        sa.Column(
            "faculty_review_recommended",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.create_index(
        "ix_evaluations_scenario_version_id",
        "evaluations",
        ["scenario_version_id"],
    )
    op.create_foreign_key(
        "fk_evaluations_scenario_version_id",
        "evaluations",
        "scenario_versions",
        ["scenario_version_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_evaluations_scenario_version_id", "evaluations", type_="foreignkey"
    )
    op.drop_index("ix_evaluations_scenario_version_id", table_name="evaluations")
    op.drop_column("evaluations", "faculty_review_recommended")
    op.drop_column("evaluations", "missed_opportunities")
    op.drop_column("evaluations", "specialized_analyses")
    op.drop_column("evaluations", "output_schema_version")
    op.drop_column("evaluations", "rubric_version")
    op.drop_column("evaluations", "template_version")
    op.drop_column("evaluations", "template_key")
    op.drop_column("evaluations", "scenario_version_id")
