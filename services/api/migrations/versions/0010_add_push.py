"""Persist browser subscriptions, preferences and delivery deduplication."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0010"
# The commander will rebase this onto 0009 from the parallel branch.
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "notification_preferences",
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), primary_key=True),
        sa.Column("preferences", sa.JSON(), nullable=False),
    )
    op.create_table(
        "push_subscriptions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("endpoint", sa.String(2048), nullable=False, unique=True),
        sa.Column("p256dh", sa.String(100), nullable=False),
        sa.Column("auth", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_push_subscriptions_user_id", "push_subscriptions", ["user_id"])
    op.create_table(
        "push_deliveries",
        sa.Column(
            "subscription_id",
            sa.String(36),
            sa.ForeignKey("push_subscriptions.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("event_key", sa.String(160), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("push_deliveries")
    op.drop_table("push_subscriptions")
    op.drop_table("notification_preferences")
