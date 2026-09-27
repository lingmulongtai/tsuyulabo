from __future__ import annotations

import json
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from tsuyulabo_api.domain.genetics import wild_type


def test_legacy_adults_get_sex_appropriate_wild_genotypes(tmp_path: Path) -> None:
    path = tmp_path / "genetics.db"
    config = Config(str(Path(__file__).parents[1] / "alembic.ini"))
    config.attributes["database_url"] = f"sqlite+aiosqlite:///{path}"
    command.upgrade(config, "0005")
    engine = create_engine(f"sqlite:///{path}")
    with engine.begin() as connection:
        # Minimal legacy records; raw SQLite connection does not enable FK checks.
        for sex in ("f", "m"):
            connection.execute(
                text("""INSERT INTO adults
                (id, user_id, week_id, name, sex, strain, stars, traits, subskills,
                 level, exp, energy, brain_params, skills, created_at)
                VALUES (:sex, 'owner', :sex, 'legacy', :sex, 'white', 3, '[]', '[]',
                        1, 0, 100, '{}', '{}', '2026-01-01')"""),
                {"sex": sex},
            )
    command.upgrade(config, "head")
    with engine.connect() as connection:
        for sex, genotype, strain in connection.execute(
            text("SELECT sex, genotype, strain FROM adults")
        ):
            assert json.loads(genotype) == wild_type(sex)
            assert strain == "white"
    engine.dispose()
