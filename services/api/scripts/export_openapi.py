"""Export the API contract without starting services or importing the brain engine."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from tsuyulabo_api.app import create_app
from tsuyulabo_api.settings import Settings

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_OUTPUT = REPO_ROOT / "apps/web/src/lib/api/openapi.json"


async def export(output: Path = DEFAULT_OUTPUT) -> dict:
    # Isolate schema generation from a developer's deployment environment.
    app = create_app(
        Settings(
            database_url="sqlite+aiosqlite:///:memory:",
            redis_url=None,
            brain_mode="inline",
            _env_file=None,
        )
    )
    try:
        schema = app.openapi()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(schema, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return schema
    finally:
        await app.state.job_queue.close()
        await app.state.engine.dispose()


if __name__ == "__main__":
    asyncio.run(export())
