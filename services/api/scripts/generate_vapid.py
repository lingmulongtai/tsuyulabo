"""Append a fresh local VAPID key pair to .env without printing secrets."""

from __future__ import annotations

import argparse
import base64
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec


def generate(path: Path, subject: str) -> None:
    if not (subject.startswith("mailto:") or subject.startswith("https://")) or any(
        char in subject for char in "\r\n\"'"
    ):
        raise ValueError("subject must be a mailto: or https:// contact URI")
    previous = path.read_text(encoding="utf-8") if path.exists() else ""
    if any(line.strip().startswith("VAPID_") for line in previous.splitlines()):
        raise ValueError(".env already contains VAPID settings; refusing to rotate existing keys")
    key = ec.generate_private_key(ec.SECP256R1())
    private = key.private_bytes(
        serialization.Encoding.DER,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    public = key.public_key().public_bytes(
        serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint
    )

    def encode(value: bytes) -> str:
        return base64.urlsafe_b64encode(value).rstrip(b"=").decode()

    with path.open("a", encoding="utf-8") as output:
        output.write(
            f"\nVAPID_PUBLIC_KEY={encode(public)}\nVAPID_PRIVATE_KEY={encode(private)}\n"
            f"VAPID_SUBJECT='{subject}'\n"
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--subject", required=True, help="mailto:you@example.com")
    args = parser.parse_args()
    generate(Path(".env"), args.subject)
    print("VAPID settings appended to .env. Keep this file private.")
