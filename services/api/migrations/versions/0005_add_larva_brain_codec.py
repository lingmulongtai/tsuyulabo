"""store compact larval brain states and cached preferences"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "larva_states", sa.Column("brain_params", sa.JSON(), nullable=False, server_default="{}")
    )
    op.add_column("larva_states", sa.Column("learned_weights", sa.LargeBinary(), nullable=True))
    op.add_column(
        "larva_states", sa.Column("preferences", sa.JSON(), nullable=False, server_default="{}")
    )
    op.execute("UPDATE adults SET sex = lower(sex)")


def downgrade() -> None:
    for name in ("preferences", "learned_weights", "brain_params"):
        op.drop_column("larva_states", name)
