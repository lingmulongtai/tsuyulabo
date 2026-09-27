"""Store one scored circuit attempt per user and shared day."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "daily_circuit_attempts",
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), primary_key=True),
        sa.Column("day", sa.Date(), primary_key=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("elapsed_ms", sa.Integer(), nullable=True),
        sa.Column("shizuku", sa.Integer(), nullable=True),
        sa.CheckConstraint("elapsed_ms >= 0", name="nonnegative_time"),
    )
    op.create_index(
        "ix_daily_circuit_ranking", "daily_circuit_attempts", ["day", "elapsed_ms", "submitted_at"]
    )


def downgrade() -> None:
    op.drop_index("ix_daily_circuit_ranking", table_name="daily_circuit_attempts")
    op.drop_table("daily_circuit_attempts")
