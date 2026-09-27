"""persist behavior discoveries"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users", sa.Column("observed_behaviors", sa.JSON(), nullable=False, server_default="[]")
    )


def downgrade() -> None:
    op.drop_column("users", "observed_behaviors")
