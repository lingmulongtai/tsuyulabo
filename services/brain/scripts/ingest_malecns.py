"""Build small measured circuits from local MaleCNS v1.0 Feather files, offline.

Install tsuyu-brain[ingest]. Run --inspect first to inspect the actual schemas.
Raw data is never copied to the output. See services/brain/README.md for attribution.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, default=Path("data/raw/malecns-v1.0"))
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "src/tsuyu_brain/connectome/malecns_v1",
    )
    parser.add_argument("--inspect", action="store_true")
    parser.add_argument("--seed", type=int, default=1729)
    parser.add_argument("--scale", action="append", default=[], metavar="CIRCUIT=FLOAT")
    args = parser.parse_args()
    # Optional Arrow/pandas imports never enter normal runtime or --help.
    from tsuyu_brain.connectome.malecns_ingest import build, inspect_sources

    if args.inspect:
        print(json.dumps(inspect_sources(args.raw), indent=2))
        return
    scales = {}
    for item in args.scale:
        name, value = item.split("=", 1)
        scales[name] = float(value)
    manifest = build(args.raw, args.output, scales=scales, seed=args.seed)
    print(json.dumps({name: row["neurons"] for name, row in manifest["circuits"].items()}))


if __name__ == "__main__":
    main()
