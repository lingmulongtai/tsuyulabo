"""Read the bundled measured circuits; no Arrow, pandas, or raw data at runtime."""

from __future__ import annotations

import hashlib
import json
from functools import lru_cache
from pathlib import Path

from tsuyu_brain.connectome import data_directory


@lru_cache(maxsize=1)
def manifest() -> dict[str, object]:
    data = json.loads((data_directory() / "manifest.json").read_text(encoding="utf-8"))
    if data["version"] != "malecns-v1.0":
        raise ValueError("unexpected MaleCNS manifest version")
    return data


def verified_path(name: str) -> Path:
    if name not in manifest()["circuits"]:
        raise ValueError(f"unknown circuit: {name}")
    info = manifest()["circuits"][name]
    for filename in (f"{name}.npz", f"{name}.json"):
        path = data_directory() / filename
        if hashlib.sha256(path.read_bytes()).hexdigest() != info["files"][filename]:
            raise ValueError(f"MaleCNS artifact checksum mismatch: {filename}")
    return data_directory() / f"{name}.npz"


@lru_cache(maxsize=5)
def neuron_metadata(name: str) -> list[dict[str, object]]:
    path = verified_path(name).with_suffix(".json")
    return json.loads(path.read_text(encoding="utf-8"))["neurons"]
