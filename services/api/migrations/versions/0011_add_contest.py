"""Add cosmetic inventory and weekly friend contest."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "decorations",
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), primary_key=True),
        sa.Column("item_id", sa.String(40), primary_key=True),
        sa.Column("source", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "decoration_layouts",
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), primary_key=True),
        sa.Column("layout", sa.JSON(), nullable=False),
    )
    op.create_table(
        "contest_entries",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("week", sa.String(8), nullable=False),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("adult_id", sa.String(36), sa.ForeignKey("adults.id"), nullable=False),
        sa.Column("layout", sa.JSON(), nullable=False),
        sa.Column("entered_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("participation_paid", sa.Boolean(), nullable=False),
        sa.Column("placement_paid", sa.Boolean(), nullable=False),
        sa.UniqueConstraint("week", "user_id"),
    )
    op.create_index("ix_contest_entries_week", "contest_entries", ["week"])
    op.create_table(
        "contest_votes",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("week", sa.String(8), nullable=False),
        sa.Column("voter_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("entry_id", sa.String(36), sa.ForeignKey("contest_entries.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("voter_id", "entry_id"),
    )
    op.create_index("ix_contest_votes_week", "contest_votes", ["week"])


def downgrade() -> None:
    op.drop_table("contest_votes")
    op.drop_table("contest_entries")
    op.drop_table("decoration_layouts")
    op.drop_table("decorations")
