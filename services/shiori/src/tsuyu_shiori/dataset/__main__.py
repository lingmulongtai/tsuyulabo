"""Generate offline oracle SFT data: python -m tsuyu_shiori.dataset."""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from .export import export_dataset


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("data/shiori-sft"))
    parser.add_argument("--train-size", type=int, default=4000)
    parser.add_argument("--valid-size", type=int, default=400)
    args = parser.parse_args()
    try:
        stats = asyncio.run(export_dataset(args.out, args.train_size, args.valid_size))
    except ValueError as exc:
        parser.error(str(exc))
    print(json.dumps(stats, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
