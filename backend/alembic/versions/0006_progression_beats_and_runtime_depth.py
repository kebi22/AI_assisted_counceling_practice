"""Add progression beats and richer session-state counters.

Revision ID: 0006
Revises: 0005
Create Date: 2026-06-28
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

from app.db.base import JSONColumn


revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("scenarios", sa.Column("opening_message", sa.Text(), nullable=True))
    op.add_column("scenarios", sa.Column("progression_beats", JSONColumn, nullable=True))
    op.add_column(
        "session_states",
        sa.Column("emotional_depth", sa.Integer(), nullable=False, server_default="1"),
    )
    op.add_column(
        "session_states",
        sa.Column("rupture_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "session_states",
        sa.Column("repair_count", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("session_states", "repair_count")
    op.drop_column("session_states", "rupture_count")
    op.drop_column("session_states", "emotional_depth")
    op.drop_column("scenarios", "progression_beats")
    op.drop_column("scenarios", "opening_message")
