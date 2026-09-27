"""Store consensual friend mating proposals and hidden pending eggs."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "mating_proposals",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("proposer_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("recipient_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("mother_id", sa.String(36), sa.ForeignKey("adults.id"), nullable=False),
        sa.Column("father_id", sa.String(36), sa.ForeignKey("adults.id"), nullable=False),
        sa.Column("week_boundary", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.UniqueConstraint("mother_id", "father_id", "week_boundary"),
        sa.CheckConstraint("proposer_id <> recipient_id", name="different_players"),
        sa.CheckConstraint("status IN ('pending', 'accepted', 'declined')", name="status"),
    )
    for column in ("proposer_id", "recipient_id"):
        op.create_index(f"ix_mating_proposals_{column}", "mating_proposals", [column])
    op.create_table(
        "pending_eggs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "proposal_id", sa.String(36), sa.ForeignKey("mating_proposals.id"), nullable=False
        ),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("genotype", sa.JSON(), nullable=False),
        sa.Column("lethal_redraws", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_week_id", sa.String(36), sa.ForeignKey("weeks.id"), unique=True),
        sa.UniqueConstraint("proposal_id", "user_id"),
        sa.CheckConstraint("lethal_redraws >= 0", name="redraws_nonnegative"),
    )
    op.create_index("ix_pending_eggs_user_id", "pending_eggs", ["user_id"])


def downgrade() -> None:
    op.drop_table("pending_eggs")
    op.drop_table("mating_proposals")
