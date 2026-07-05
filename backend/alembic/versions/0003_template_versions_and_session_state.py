"""template_versions_and_session_state

Adds template metadata, immutable published scenario versions, and per-session
client state. Existing scenarios and sessions are backfilled conservatively so
the current simulator flow remains usable while the stateful engine is rolled
in over later phases.

Revision ID: 0003
Revises: 0002
Create Date: 2026-06-24

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _jsonb() -> postgresql.JSONB:
    return postgresql.JSONB(astext_type=sa.Text())


def upgrade() -> None:
    op.add_column(
        "scenarios",
        sa.Column(
            "template_key",
            sa.String(length=120),
            nullable=False,
            server_default="microskills_progressive_disclosure",
        ),
    )
    op.add_column(
        "scenarios",
        sa.Column(
            "template_version",
            sa.String(length=64),
            nullable=False,
            server_default="1.0.0",
        ),
    )
    op.add_column("scenarios", sa.Column("current_version_id", sa.Uuid(), nullable=True))

    op.create_table(
        "scenario_versions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("scenario_id", sa.Uuid(), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("template_key", sa.String(length=120), nullable=False),
        sa.Column("template_version", sa.String(length=64), nullable=False),
        sa.Column("prompt_version", sa.String(length=64), nullable=False),
        sa.Column("rubric_version", sa.String(length=64), nullable=False),
        sa.Column("output_schema_version", sa.String(length=64), nullable=False),
        sa.Column("rendered_client_prompt", sa.Text(), nullable=False),
        sa.Column("rendered_evaluator_prompt", sa.Text(), nullable=False),
        sa.Column("authoring_snapshot", _jsonb(), nullable=False),
        sa.Column("rubric_snapshot", _jsonb(), nullable=False),
        sa.Column("safety_policy_snapshot", _jsonb(), nullable=False),
        sa.Column("learning_objectives_snapshot", _jsonb(), nullable=False),
        sa.Column("published_by", sa.String(length=255), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["scenario_id"], ["scenarios.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "scenario_id",
            "version_number",
            name="uq_scenario_version_number",
        ),
    )
    op.create_index(
        "ix_scenario_versions_scenario_id", "scenario_versions", ["scenario_id"]
    )
    op.create_foreign_key(
        "fk_scenarios_current_version_id",
        "scenarios",
        "scenario_versions",
        ["current_version_id"],
        ["id"],
    )

    op.add_column(
        "simulation_sessions",
        sa.Column("scenario_version_id", sa.Uuid(), nullable=True),
    )
    op.create_index(
        "ix_simulation_sessions_scenario_version_id",
        "simulation_sessions",
        ["scenario_version_id"],
    )
    op.create_foreign_key(
        "fk_simulation_sessions_scenario_version_id",
        "simulation_sessions",
        "scenario_versions",
        ["scenario_version_id"],
        ["id"],
    )

    op.create_table(
        "session_states",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("engagement_level", sa.Integer(), nullable=False),
        sa.Column("trust_level", sa.Integer(), nullable=False),
        sa.Column("disclosure_stage", sa.Integer(), nullable=False),
        sa.Column("session_stage", sa.String(length=32), nullable=False),
        sa.Column("revealed_information", _jsonb(), nullable=False),
        sa.Column("emotional_cues", _jsonb(), nullable=False),
        sa.Column("state_history", _jsonb(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["session_id"], ["simulation_sessions.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("session_id", name="uq_session_state_session"),
    )
    op.create_index("ix_session_states_session_id", "session_states", ["session_id"])


def downgrade() -> None:
    op.drop_index("ix_session_states_session_id", table_name="session_states")
    op.drop_table("session_states")

    op.drop_constraint(
        "fk_simulation_sessions_scenario_version_id",
        "simulation_sessions",
        type_="foreignkey",
    )
    op.drop_index(
        "ix_simulation_sessions_scenario_version_id",
        table_name="simulation_sessions",
    )
    op.drop_column("simulation_sessions", "scenario_version_id")

    op.drop_constraint("fk_scenarios_current_version_id", "scenarios", type_="foreignkey")
    op.drop_index("ix_scenario_versions_scenario_id", table_name="scenario_versions")
    op.drop_table("scenario_versions")
    op.drop_column("scenarios", "current_version_id")
    op.drop_column("scenarios", "template_version")
    op.drop_column("scenarios", "template_key")
