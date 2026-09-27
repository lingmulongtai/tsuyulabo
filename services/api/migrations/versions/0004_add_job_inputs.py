"""retain job inputs for dispatch and recovery"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("jobs", sa.Column("params", sa.JSON(), nullable=False, server_default="{}"))


def downgrade() -> None:
    op.drop_column("jobs", "params")
