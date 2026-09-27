"""Store weekly race geometry and replaceable entry pointers."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "maze_races",
        sa.Column("week", sa.String(8), primary_key=True),
        sa.Column("maze", sa.JSON(), nullable=False),
        sa.Column("deadline", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "maze_entries",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("week", sa.String(8), sa.ForeignKey("maze_races.week"), nullable=False),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("adult_id", sa.String(36), sa.ForeignKey("adults.id"), nullable=False),
        sa.Column("job_id", sa.String(36), sa.ForeignKey("jobs.id"), nullable=False),
        sa.Column("placements", sa.JSON(), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "maze_slots",
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), primary_key=True),
        sa.Column("week", sa.String(8), sa.ForeignKey("maze_races.week"), primary_key=True),
        sa.Column("entry_id", sa.String(36), sa.ForeignKey("maze_entries.id"), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("maze_slots")
    op.drop_table("maze_entries")
    op.drop_table("maze_races")
