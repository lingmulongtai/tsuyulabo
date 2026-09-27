from __future__ import annotations

import importlib.util
import json
from pathlib import Path


async def test_export_is_repeatable_and_documents_idempotency(tmp_path: Path) -> None:
    source = Path(__file__).parents[1] / "scripts/export_openapi.py"
    spec = importlib.util.spec_from_file_location("export_openapi", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    target = tmp_path / "openapi.json"
    first = await module.export(target)
    original = target.read_bytes()
    assert json.loads(original) == first
    assert await module.export(target) == first
    assert target.read_bytes() == original
    for path in first["paths"].values():
        for method, operation in path.items():
            if method in {"post", "put", "patch", "delete"}:
                assert any(
                    p["name"] == "Idempotency-Key" and p["required"]
                    for p in operation["parameters"]
                )
