"""Store hidden eggs, adult genotypes and parental use."""

from __future__ import annotations

import json

import sqlalchemy as sa
from alembic import op

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("weeks", sa.Column("egg_genotype", sa.JSON(), nullable=True))
    op.add_column("weeks", sa.Column("mother_id", sa.String(36), nullable=True))
    op.add_column("weeks", sa.Column("father_id", sa.String(36), nullable=True))
    op.add_column(
        "weeks", sa.Column("lethal_redraws", sa.Integer(), nullable=False, server_default="0")
    )
    op.add_column("adults", sa.Column("genotype", sa.JSON(), nullable=True))
    op.add_column("adults", sa.Column("mutation", sa.JSON(), nullable=True))
    op.add_column(
        "adults", sa.Column("last_parent_week", sa.DateTime(timezone=True), nullable=True)
    )
    # Frozen migration data: do not import the evolving domain implementation.
    for sex in ("f", "m"):
        genotype = {
            "sex": sex,
            "w": ["+"] * (2 if sex == "f" else 1),
            "y": ["+"] * (2 if sex == "f" else 1),
            "e": ["+", "+"],
            "Cy": ["+", "+"],
            "vg": ["+", "+"],
        }
        op.execute(
            sa.text("UPDATE adults SET genotype = :genotype WHERE sex = :sex").bindparams(
                sa.bindparam("genotype", json.dumps(genotype), literal_execute=True),
                sa.bindparam("sex", sex, literal_execute=True),
            )
        )
    with op.batch_alter_table("adults") as batch:
        batch.alter_column("genotype", existing_type=sa.JSON(), nullable=False)


def downgrade() -> None:
    for name in ("last_parent_week", "mutation", "genotype"):
        op.drop_column("adults", name)
    for name in ("lethal_redraws", "father_id", "mother_id", "egg_genotype"):
        op.drop_column("weeks", name)
