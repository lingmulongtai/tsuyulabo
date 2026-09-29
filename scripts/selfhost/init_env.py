"""Create the self-host env file with fresh secrets: uv run python scripts/selfhost/init_env.py.

The file lives outside the repo (and outside OneDrive) and is never overwritten, because replacing
the secrets would lock the running database out and sign every player out.
"""

from __future__ import annotations

import argparse
import base64
import secrets
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec

DEFAULT_PATH = Path.home() / ".tsuyulabo" / "selfhost.env"
DEFAULT_ORIGIN = "https://tsuyulabo.vercel.app"


def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def vapid_keys() -> tuple[str, str]:
    """Return (public, private) in the raw base64url form browsers and pywebpush accept."""
    key = ec.generate_private_key(ec.SECP256R1())
    private = key.private_numbers().private_value.to_bytes(32, "big")
    public = key.public_key().public_bytes(
        serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint
    )
    return b64url(public), b64url(private)


def render(origin: str = DEFAULT_ORIGIN) -> str:
    # Hex keeps the password safe inside the database URL without escaping.
    password = secrets.token_hex(24)
    public, private = vapid_keys()
    lines = [
        "# Tsuyu Labo self-host secrets (docs/selfhost.md). Keep out of git and OneDrive.",
        "POSTGRES_USER=tsuyu",
        "POSTGRES_DB=tsuyulabo",
        f"POSTGRES_PASSWORD={password}",
        f"DATABASE_URL=postgresql+asyncpg://tsuyu:{password}@postgres:5432/tsuyulabo",
        "REDIS_URL=redis://redis:6379/0",
        f"JWT_SECRET={secrets.token_hex(32)}",
        f"CORS_ORIGINS='[\"{origin}\"]'",
        f"VAPID_PUBLIC_KEY={public}",
        f"VAPID_PRIVATE_KEY={private}",
        # A URL rather than an email keeps personal addresses away from push services.
        f"VAPID_SUBJECT={origin}",
        "SHIORI_PROVIDER=mock",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path", type=Path, default=DEFAULT_PATH)
    parser.add_argument("--origin", default=DEFAULT_ORIGIN, help="web origin allowed by CORS")
    args = parser.parse_args()
    if args.path.exists():
        raise SystemExit(f"{args.path} already exists; refusing to replace live secrets")
    args.path.parent.mkdir(parents=True, exist_ok=True)
    args.path.write_text(render(args.origin), encoding="utf-8")
    print(f"wrote {args.path}")


if __name__ == "__main__":
    main()
