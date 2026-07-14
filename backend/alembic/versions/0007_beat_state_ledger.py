"""Add beat state ledger to session state.

Revision ID: 0007_beat_state_ledger
Revises: 0006
Create Date: 2026-07-09
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

from app.db.base import JSONColumn


revision = "0007_beat_state_ledger"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "session_states",
        sa.Column("beat_states", JSONColumn, nullable=False, server_default="[]"),
    )
    op.alter_column("session_states", "beat_states", server_default=None)


def downgrade() -> None:
    op.drop_column("session_states", "beat_states")
