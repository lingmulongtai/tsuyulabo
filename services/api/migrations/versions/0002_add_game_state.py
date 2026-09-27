"""persist lazy care evaluation and portable brain snapshots"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    for table, name, default in (
        ("larva_states", "miss_keys", "[]"),
        ("larva_states", "brain_snapshot", "{}"),
        ("larva_states", "skills", "{}"),
        ("adults", "preferences", "{}"),
        ("adults", "brain_snapshot", "{}"),
        ("adults", "gathering", "{}"),
    ):
        op.add_column(table, sa.Column(name, sa.JSON(), nullable=False, server_default=default))


def downgrade() -> None:
    for table, columns in (
        ("adults", ("gathering", "brain_snapshot", "preferences")),
        ("larva_states", ("skills", "brain_snapshot", "miss_keys")),
    ):
        for column in columns:
            op.drop_column(table, column)
