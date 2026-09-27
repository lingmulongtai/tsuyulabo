"""Store deterministic territory bouts and their replay."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0012"
down_revision = "0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sumo_bouts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("adult_id", sa.String(36), sa.ForeignKey("adults.id"), nullable=False),
        sa.Column("opponent_id", sa.String(36), sa.ForeignKey("adults.id")),
        sa.Column("opponent_name", sa.String(80), nullable=False),
        sa.Column("game_day", sa.String(10), nullable=False),
        sa.Column("daily_index", sa.Integer(), nullable=False),
        sa.Column("won", sa.Boolean(), nullable=False),
        sa.Column("reward", sa.Integer(), nullable=False),
        sa.Column("replay", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("user_id", "game_day", "daily_index"),
    )
    op.create_index("ix_sumo_bouts_user_id", "sumo_bouts", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_sumo_bouts_user_id", table_name="sumo_bouts")
    op.drop_table("sumo_bouts")
