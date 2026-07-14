"""Add session modality and nonverbal summary for audio/video modes.

Revision ID: 0008_session_modality
Revises: 0007_beat_state_ledger
Create Date: 2026-07-05
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

from app.db.base import JSONColumn


revision = "0008_session_modality"
down_revision = "0007_beat_state_ledger"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "simulation_sessions",
        sa.Column(
            "modality", sa.String(length=16), nullable=False, server_default="text"
        ),
    )
    op.create_index(
        "ix_simulation_sessions_modality", "simulation_sessions", ["modality"]
    )
    op.add_column(
        "simulation_sessions",
        sa.Column("nonverbal_summary", JSONColumn, nullable=True),
    )


def downgrade() -> None:
    op.drop_column("simulation_sessions", "nonverbal_summary")
    op.drop_index("ix_simulation_sessions_modality", table_name="simulation_sessions")
    op.drop_column("simulation_sessions", "modality")
