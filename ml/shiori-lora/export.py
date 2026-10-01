"""Merge a Qwen3.5 adapter on CPU, convert to GGUF and quantize for Windows Ollama."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


def commands(out: Path, llama: Path) -> list[list[str]]:
    return [
        [
            sys.executable,
            str(llama / "convert_hf_to_gguf.py"),
            str(out / "merged"),
            "--outfile",
            str(out / "shiori-bf16.gguf"),
            "--outtype",
            "bf16",
            "--no-mtp",
        ],
        [
            str(llama / "build/bin/llama-quantize"),
            str(out / "shiori-bf16.gguf"),
            str(out / "shiori-Q4_K_M.gguf"),
            "Q4_K_M",
            "2",
        ],
    ]


def merge(base: str, adapter: Path, out: Path) -> None:
    import torch
    from peft import PeftModel
    from transformers import AutoTokenizer, Qwen3_5ForConditionalGeneration

    torch.set_num_threads(2)
    # Merge from full precision base weights, never the training NF4 representation.
    model = Qwen3_5ForConditionalGeneration.from_pretrained(
        base,
        dtype=torch.bfloat16,
        device_map={"": "cpu"},
        low_cpu_mem_usage=True,
        trust_remote_code=False,
    )
    model = PeftModel.from_pretrained(model, adapter).merge_and_unload(safe_merge=True)
    model.save_pretrained(out, safe_serialization=True, max_shard_size="2GB")
    AutoTokenizer.from_pretrained(adapter, trust_remote_code=False).save_pretrained(out)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", help="must match the original adapter base")
    parser.add_argument("--adapter", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--llama-cpp", type=Path, required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        config: dict[str, Any] = json.loads(
            (args.adapter / "adapter_config.json").read_text(encoding="utf-8")
        )
        base = args.base or config["base_model_name_or_path"]
        if args.base and args.base != config["base_model_name_or_path"]:
            raise ValueError("--base differs from adapter base; use its original directory/repo")
        if (
            config.get("peft_type") != "LORA"
            or not (args.adapter / "adapter_model.safetensors").is_file()
        ):
            raise ValueError("expected a safetensors LoRA adapter")
        if args.out.exists() and (not args.out.is_dir() or any(args.out.iterdir())):
            raise ValueError("--out must be absent or empty")
        if not (args.llama_cpp / "convert_hf_to_gguf.py").is_file():
            raise ValueError("llama.cpp converter is missing")
        if not (args.llama_cpp / "build/bin/llama-quantize").is_file():
            raise ValueError("build llama.cpp llama-quantize first")
    except (ValueError, KeyError, OSError) as exc:
        parser.error(str(exc))
    planned = commands(args.out.resolve(), args.llama_cpp.resolve())
    print(
        json.dumps(
            {"base": base, "merge_on": "cpu", "commands": planned, "dry_run": args.dry_run},
            indent=2,
        )
    )
    if args.dry_run:
        return
    args.out.mkdir(parents=True, exist_ok=True)
    merge(base, args.adapter, args.out / "merged")
    for command in planned:
        subprocess.run(command, check=True)
    revision = subprocess.run(
        ["git", "-C", str(args.llama_cpp), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    (args.out / "export.json").write_text(
        json.dumps({"base": base, "llama_cpp_revision": revision, "commands": planned}, indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
