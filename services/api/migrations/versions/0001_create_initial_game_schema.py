"""create initial game schema"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    if op.get_bind().dialect.name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "idempotency_keys",
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("key", sa.String(length=36), nullable=False),
        sa.Column("method", sa.String(length=10), nullable=False),
        sa.Column("path", sa.String(length=500), nullable=False),
        sa.Column("status_code", sa.Integer(), nullable=True),
        sa.Column("response", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("user_id", "key", name=op.f("pk_idempotency_keys")),
    )
    op.create_index(
        op.f("ix_idempotency_keys_created_at"), "idempotency_keys", ["created_at"], unique=False
    )
    op.create_table(
        "ledger_accounts",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("owner", sa.String(length=100), nullable=False),
        sa.Column("currency", sa.String(length=24), nullable=False),
        sa.Column("balance", sa.BigInteger(), nullable=False),
        sa.CheckConstraint(
            "balance >= 0 OR owner LIKE 'system:%'", name=op.f("ck_ledger_accounts_user_balance")
        ),
        sa.CheckConstraint(
            "currency IN ('shizuku', 'research_points', 'kohaku')",
            name=op.f("ck_ledger_accounts_currency"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ledger_accounts")),
        sa.UniqueConstraint("owner", "currency", name=op.f("uq_ledger_accounts_owner")),
    )
    op.create_table(
        "papers",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("authors", sa.JSON(), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("doi", sa.String(length=300), nullable=True),
        sa.Column("chunk", sa.Text(), nullable=False),
        sa.Column("embedding", sa.JSON().with_variant(Vector(384), "postgresql"), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_papers")),
    )
    op.create_index(op.f("ix_papers_doi"), "papers", ["doi"], unique=False)
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("display_name", sa.String(length=40), nullable=False),
        sa.Column("friend_code", sa.String(length=8), nullable=False),
        sa.Column("title", sa.String(length=100), nullable=True),
        sa.Column("favorite_adult_id", sa.String(length=36), nullable=True),
        sa.Column("dev_time_offset_s", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["favorite_adult_id"],
            ["adults.id"],
            name="fk_users_favorite_adult_id_adults",
            use_alter=True,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("friend_code", name=op.f("uq_users_friend_code")),
    )
    op.create_table(
        "experiments",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("adult_or_week_id", sa.String(length=36), nullable=False),
        sa.Column("kind", sa.String(length=40), nullable=False),
        sa.Column("params", sa.JSON(), nullable=False),
        sa.Column("result", sa.JSON(), nullable=True),
        sa.Column("seq", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_experiments_user_id_users")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_experiments")),
        sa.UniqueConstraint("user_id", "seq", name=op.f("uq_experiments_user_id")),
    )
    op.create_index(op.f("ix_experiments_user_id"), "experiments", ["user_id"], unique=False)
    op.create_table(
        "friendships",
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("friend_id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("user_id <> friend_id", name=op.f("ck_friendships_different_users")),
        sa.ForeignKeyConstraint(
            ["friend_id"], ["users.id"], name=op.f("fk_friendships_friend_id_users")
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_friendships_user_id_users")
        ),
        sa.PrimaryKeyConstraint("user_id", "friend_id", name=op.f("pk_friendships")),
    )
    op.create_table(
        "gifts",
        sa.Column("from", sa.String(length=36), nullable=False),
        sa.Column("to", sa.String(length=36), nullable=False),
        sa.Column("material", sa.String(length=40), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("day", sa.Date(), nullable=False),
        sa.CheckConstraint("amount BETWEEN 1 AND 5", name=op.f("ck_gifts_amount_range")),
        sa.ForeignKeyConstraint(["from"], ["users.id"], name=op.f("fk_gifts_from_users")),
        sa.ForeignKeyConstraint(["to"], ["users.id"], name=op.f("fk_gifts_to_users")),
        sa.PrimaryKeyConstraint("from", "day", name=op.f("pk_gifts")),
    )
    op.create_table(
        "inventory",
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("material", sa.String(length=40), nullable=False),
        sa.Column("amount", sa.BigInteger(), nullable=False),
        sa.CheckConstraint("amount >= 0", name=op.f("ck_inventory_nonnegative_amount")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_inventory_user_id_users")),
        sa.PrimaryKeyConstraint("user_id", "material", name=op.f("pk_inventory")),
    )
    op.create_table(
        "jobs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("kind", sa.String(length=80), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("result", sa.JSON(), nullable=True),
        sa.Column("error", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('pending', 'running', 'succeeded', 'failed')", name=op.f("ck_jobs_status")
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_jobs_user_id_users")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_jobs")),
    )
    op.create_index(op.f("ix_jobs_user_id"), "jobs", ["user_id"], unique=False)
    op.create_table(
        "ledger_entries",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("tx_id", sa.String(length=36), nullable=False),
        sa.Column("account_id", sa.String(length=36), nullable=False),
        sa.Column("amount", sa.BigInteger(), nullable=False),
        sa.Column("reason", sa.String(length=100), nullable=False),
        sa.Column("ref", sa.String(length=200), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["ledger_accounts.id"],
            name=op.f("fk_ledger_entries_account_id_ledger_accounts"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ledger_entries")),
        sa.UniqueConstraint("tx_id", "account_id", name=op.f("uq_ledger_entries_tx_id")),
    )
    op.create_index(
        op.f("ix_ledger_entries_account_id"), "ledger_entries", ["account_id"], unique=False
    )
    op.create_index(op.f("ix_ledger_entries_tx_id"), "ledger_entries", ["tx_id"], unique=False)
    op.create_table(
        "likes",
        sa.Column("from", sa.String(length=36), nullable=False),
        sa.Column("to", sa.String(length=36), nullable=False),
        sa.Column("day", sa.Date(), nullable=False),
        sa.ForeignKeyConstraint(["from"], ["users.id"], name=op.f("fk_likes_from_users")),
        sa.ForeignKeyConstraint(["to"], ["users.id"], name=op.f("fk_likes_to_users")),
        sa.PrimaryKeyConstraint("from", "to", "day", name=op.f("pk_likes")),
    )
    op.create_table(
        "notifications",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("kind", sa.String(length=40), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_notifications_user_id_users")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_notifications")),
    )
    op.create_index(op.f("ix_notifications_user_id"), "notifications", ["user_id"], unique=False)
    op.create_table(
        "shiori_messages",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("role", sa.String(length=24), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("evidence", sa.JSON(), nullable=False),
        sa.Column("cost", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_shiori_messages_user_id_users")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_shiori_messages")),
    )
    op.create_index(
        op.f("ix_shiori_messages_user_id"), "shiori_messages", ["user_id"], unique=False
    )
    op.create_table(
        "sleep_sessions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("bonus", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_sleep_sessions_user_id_users")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sleep_sessions")),
    )
    op.create_index(op.f("ix_sleep_sessions_user_id"), "sleep_sessions", ["user_id"], unique=False)
    op.create_table(
        "weeks",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("rank", sa.String(length=16), nullable=True),
        sa.Column("points", sa.Integer(), nullable=False),
        sa.Column("care_miss", sa.Integer(), nullable=False),
        sa.Column("eclosed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("adult_id", sa.String(length=36), nullable=True),
        sa.CheckConstraint("status IN ('active', 'eclosed')", name=op.f("ck_weeks_status")),
        sa.ForeignKeyConstraint(
            ["adult_id"], ["adults.id"], name="fk_weeks_adult_id_adults", use_alter=True
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_weeks_user_id_users")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_weeks")),
    )
    op.create_index(op.f("ix_weeks_user_id"), "weeks", ["user_id"], unique=False)
    op.create_table(
        "adults",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("week_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=40), nullable=False),
        sa.Column("sex", sa.String(length=1), nullable=False),
        sa.Column("strain", sa.String(length=40), nullable=False),
        sa.Column("stars", sa.Integer(), nullable=False),
        sa.Column("traits", sa.JSON(), nullable=False),
        sa.Column("subskills", sa.JSON(), nullable=False),
        sa.Column("level", sa.Integer(), nullable=False),
        sa.Column("exp", sa.Integer(), nullable=False),
        sa.Column("energy", sa.Double(), nullable=False),
        sa.Column("brain_params", sa.JSON(), nullable=False),
        sa.Column("learned_weights", sa.LargeBinary(), nullable=True),
        sa.Column("skills", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_adults_user_id_users")),
        sa.ForeignKeyConstraint(["week_id"], ["weeks.id"], name=op.f("fk_adults_week_id_weeks")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_adults")),
        sa.UniqueConstraint("week_id", name=op.f("uq_adults_week_id")),
    )
    op.create_index(op.f("ix_adults_user_id"), "adults", ["user_id"], unique=False)
    op.create_table(
        "care_events",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("week_id", sa.String(length=36), nullable=False),
        sa.Column("seq", sa.Integer(), nullable=False),
        sa.Column("kind", sa.String(length=40), nullable=False),
        sa.Column("research_day", sa.Integer(), nullable=False),
        sa.Column("slot", sa.String(length=16), nullable=True),
        sa.Column("score", sa.Double(), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_care_events_user_id_users")
        ),
        sa.ForeignKeyConstraint(
            ["week_id"], ["weeks.id"], name=op.f("fk_care_events_week_id_weeks")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_care_events")),
        sa.UniqueConstraint("user_id", "seq", name=op.f("uq_care_events_user_id")),
    )
    op.create_index(op.f("ix_care_events_user_id"), "care_events", ["user_id"], unique=False)
    op.create_index(op.f("ix_care_events_week_id"), "care_events", ["week_id"], unique=False)
    op.create_table(
        "larva_states",
        sa.Column("week_id", sa.String(length=36), nullable=False),
        sa.Column("hunger", sa.Double(), nullable=False),
        sa.Column("cleanliness", sa.Double(), nullable=False),
        sa.Column("growth", sa.Double(), nullable=False),
        sa.Column("hunger_zero_since", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_computed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("stage", sa.String(length=24), nullable=False),
        sa.ForeignKeyConstraint(
            ["week_id"], ["weeks.id"], name=op.f("fk_larva_states_week_id_weeks")
        ),
        sa.PrimaryKeyConstraint("week_id", name=op.f("pk_larva_states")),
    )
    op.create_table(
        "puzzles",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("week_id", sa.String(length=36), nullable=False),
        sa.Column("kind", sa.String(length=40), nullable=False),
        sa.Column("params", sa.JSON(), nullable=False),
        sa.Column("secret", sa.JSON(), nullable=False),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("result", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_puzzles_user_id_users")),
        sa.ForeignKeyConstraint(["week_id"], ["weeks.id"], name=op.f("fk_puzzles_week_id_weeks")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_puzzles")),
    )
    op.create_index(op.f("ix_puzzles_user_id"), "puzzles", ["user_id"], unique=False)
    op.create_index(op.f("ix_puzzles_week_id"), "puzzles", ["week_id"], unique=False)
    op.create_table(
        "team_slots",
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("slot", sa.Integer(), nullable=False),
        sa.Column("adult_id", sa.String(length=36), nullable=False),
        sa.Column("bag", sa.JSON(), nullable=False),
        sa.Column("last_computed_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("slot BETWEEN 0 AND 4", name=op.f("ck_team_slots_slot_range")),
        sa.ForeignKeyConstraint(
            ["adult_id"], ["adults.id"], name=op.f("fk_team_slots_adult_id_adults")
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_team_slots_user_id_users")
        ),
        sa.PrimaryKeyConstraint("user_id", "slot", name=op.f("pk_team_slots")),
        sa.UniqueConstraint("adult_id", name=op.f("uq_team_slots_adult_id")),
    )

    if op.get_bind().dialect.name == "postgresql":
        op.create_foreign_key(
            "fk_users_favorite_adult_id_adults", "users", "adults", ["favorite_adult_id"], ["id"]
        )
        op.create_foreign_key("fk_weeks_adult_id_adults", "weeks", "adults", ["adult_id"], ["id"])


def downgrade() -> None:
    if op.get_bind().dialect.name == "postgresql":
        op.drop_constraint("fk_users_favorite_adult_id_adults", "users", type_="foreignkey")
        op.drop_constraint("fk_weeks_adult_id_adults", "weeks", type_="foreignkey")

    op.drop_table("team_slots")
    op.drop_index(op.f("ix_puzzles_week_id"), table_name="puzzles")
    op.drop_index(op.f("ix_puzzles_user_id"), table_name="puzzles")
    op.drop_table("puzzles")
    op.drop_table("larva_states")
    op.drop_index(op.f("ix_care_events_week_id"), table_name="care_events")
    op.drop_index(op.f("ix_care_events_user_id"), table_name="care_events")
    op.drop_table("care_events")
    op.drop_index(op.f("ix_adults_user_id"), table_name="adults")
    op.drop_table("adults")
    op.drop_index(op.f("ix_weeks_user_id"), table_name="weeks")
    op.drop_table("weeks")
    op.drop_index(op.f("ix_sleep_sessions_user_id"), table_name="sleep_sessions")
    op.drop_table("sleep_sessions")
    op.drop_index(op.f("ix_shiori_messages_user_id"), table_name="shiori_messages")
    op.drop_table("shiori_messages")
    op.drop_index(op.f("ix_notifications_user_id"), table_name="notifications")
    op.drop_table("notifications")
    op.drop_table("likes")
    op.drop_index(op.f("ix_ledger_entries_tx_id"), table_name="ledger_entries")
    op.drop_index(op.f("ix_ledger_entries_account_id"), table_name="ledger_entries")
    op.drop_table("ledger_entries")
    op.drop_index(op.f("ix_jobs_user_id"), table_name="jobs")
    op.drop_table("jobs")
    op.drop_table("inventory")
    op.drop_table("gifts")
    op.drop_table("friendships")
    op.drop_index(op.f("ix_experiments_user_id"), table_name="experiments")
    op.drop_table("experiments")
    op.drop_table("users")
    op.drop_index(op.f("ix_papers_doi"), table_name="papers")
    op.drop_table("papers")
    op.drop_table("ledger_accounts")
    op.drop_index(op.f("ix_idempotency_keys_created_at"), table_name="idempotency_keys")
    op.drop_table("idempotency_keys")
