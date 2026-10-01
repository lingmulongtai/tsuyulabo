"""Preserve the Windows Ollama base's exact TEMPLATE, SYSTEM and parameters."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


def compose(base: str, gguf: str) -> str:
    # Ollama 0.34 ships qwen3.5 with a one-line TEMPLATE plus built-in RENDERER/PARSER for tools.
    native = re.search(r"(?m)^(RENDERER|PARSER)\s+\S", base) and re.search(r"(?m)^TEMPLATE\s", base)
    if not (native or 'TEMPLATE """' in base) or not re.search(r"(?m)^FROM\s+", base):
        raise ValueError("capture ollama show BASE --modelfile, including its TEMPLATE")
    if re.search(r"(?m)^ADAPTER\s+", base):
        raise ValueError("expected an unadapted base Modelfile")
    if any(c in gguf for c in ('"', "\n", "\r")):
        raise ValueError("invalid GGUF path")
    if 'TEMPLATE """' not in base:
        # No multi-line template text to protect: swap the first top-level FROM only.
        return re.sub(r"(?m)^FROM[^\r\n]*", lambda _: f'FROM "{gguf}"', base, count=1)
    # Replace exactly the top-level FROM before TEMPLATE; do not touch template text.
    prefix, template = base.split('TEMPLATE """', 1)
    prefix, count = re.subn(r"(?m)^FROM[^\r\n]*", lambda _: f'FROM "{gguf}"', prefix, count=1)
    if count != 1:
        raise ValueError("base FROM must precede TEMPLATE")
    return prefix + 'TEMPLATE """' + template


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-modelfile", type=Path, required=True)
    parser.add_argument("--gguf", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        parser.error("--out already exists; choose a new Modelfile")
    try:
        if not args.gguf.is_file():
            raise ValueError("GGUF is missing")
        base = args.base_modelfile.read_text(encoding="utf-8-sig")
        text = compose(base, args.gguf.resolve().as_posix())
        args.out.write_text(text, encoding="utf-8")
    except (OSError, ValueError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
