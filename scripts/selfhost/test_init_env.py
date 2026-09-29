from __future__ import annotations

import base64
import importlib.util
from pathlib import Path

import pytest
from cryptography.hazmat.primitives.asymmetric import ec

spec = importlib.util.spec_from_file_location("init_env", Path(__file__).with_name("init_env.py"))
assert spec and spec.loader
init_env = importlib.util.module_from_spec(spec)
spec.loader.exec_module(init_env)


def parse(text: str) -> dict[str, str]:
    pairs = (line.split("=", 1) for line in text.splitlines() if line and not line.startswith("#"))
    return dict(pairs)


def decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def test_render_uses_fresh_matching_secrets() -> None:
    first, second = parse(init_env.render()), parse(init_env.render())
    assert first["JWT_SECRET"] != second["JWT_SECRET"]
    assert len(first["JWT_SECRET"].encode()) >= 32
    assert f":{first['POSTGRES_PASSWORD']}@postgres:" in first["DATABASE_URL"]
    assert first["CORS_ORIGINS"] == "'[\"https://tsuyulabo.vercel.app\"]'"


def test_vapid_keys_form_a_p256_pair() -> None:
    public, private = init_env.vapid_keys()
    key = ec.derive_private_key(int.from_bytes(decode(private), "big"), ec.SECP256R1())
    numbers = key.public_key().public_numbers()
    point = decode(public)
    assert len(point) == 65 and point[0] == 4
    assert int.from_bytes(point[1:33], "big") == numbers.x


def test_main_refuses_to_replace_existing_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "selfhost.env"
    target.write_text("JWT_SECRET=live\n", encoding="utf-8")
    monkeypatch.setattr("sys.argv", ["init_env.py", "--path", str(target)])
    with pytest.raises(SystemExit, match="refusing"):
        init_env.main()
    assert target.read_text(encoding="utf-8") == "JWT_SECRET=live\n"
