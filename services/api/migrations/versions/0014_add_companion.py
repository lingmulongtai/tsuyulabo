"""Persist individual diaries and dismissible hint cooldowns."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0014"
down_revision = "0013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    for name in ("diary_entries", "quiet_hints"):
        columns = [
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("week_id", sa.String(36), sa.ForeignKey("weeks.id"), nullable=False),
            sa.Column("text", sa.String(), nullable=False),
            sa.Column("evidence", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        ]
        if name == "diary_entries":
            columns += [
                sa.Column("day", sa.Date(), nullable=False),
                sa.Column("snapshot", sa.JSON(), nullable=False),
                sa.UniqueConstraint("user_id", "week_id", "day"),
            ]
        else:
            columns += [
                sa.Column("kind", sa.String(16), nullable=False),
                sa.Column("dismissed_at", sa.DateTime(timezone=True)),
            ]
        op.create_table(name, *columns)
        for key in ("user_id", "week_id"):
            op.create_index(f"ix_{name}_{key}", name, [key])


def downgrade() -> None:
    op.drop_table("quiet_hints")
    op.drop_table("diary_entries")
