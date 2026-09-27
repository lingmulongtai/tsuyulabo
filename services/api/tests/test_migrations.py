from __future__ import annotations

from io import StringIO
from pathlib import Path

from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import create_engine, inspect
from tsuyulabo_api.db.models import Base


def test_upgrade_matches_models_and_downgrade(tmp_path: Path) -> None:
    path = tmp_path / "migration.db"
    config = Config(str(Path(__file__).parents[1] / "alembic.ini"))
    config.attributes["database_url"] = f"sqlite+aiosqlite:///{path}"
    command.upgrade(config, "head")
    engine = create_engine(f"sqlite:///{path}")
    with engine.connect() as connection:
        context = MigrationContext.configure(connection, opts={"compare_type": True})
        assert compare_metadata(context, Base.metadata) == []
        assert len(inspect(connection).get_table_names()) == 27
    engine.dispose()
    command.downgrade(config, "base")
    with engine.connect() as connection:
        assert inspect(connection).get_table_names() == ["alembic_version"]
    engine.dispose()


def test_postgres_migration_sql_includes_vector_and_circular_foreign_keys() -> None:
    output = StringIO()
    config = Config(str(Path(__file__).parents[1] / "alembic.ini"), output_buffer=output)
    config.attributes["database_url"] = "postgresql+asyncpg://localhost/tsuyulabo"
    command.upgrade(config, "head", sql=True)
    sql = output.getvalue()
    assert "CREATE EXTENSION IF NOT EXISTS vector" in sql
    assert "VECTOR(384)" in sql
    assert "ALTER TABLE users ADD CONSTRAINT fk_users_favorite_adult_id_adults" in sql
    assert "ALTER TABLE weeks ADD CONSTRAINT fk_weeks_adult_id_adults" in sql
