from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_export_dry_run_is_dependency_free_and_preserves_base(tmp_path):
    adapter = tmp_path / "adapter"
    adapter.mkdir()
    (adapter / "adapter_config.json").write_text(
        json.dumps({"peft_type": "LORA", "base_model_name_or_path": "Qwen/Qwen3.5-2B"})
    )
    (adapter / "adapter_model.safetensors").write_bytes(b"fixture")
    llama = tmp_path / "llama"
    (llama / "build/bin").mkdir(parents=True)
    (llama / "convert_hf_to_gguf.py").touch()
    (llama / "build/bin/llama-quantize").touch()
    command = [
        sys.executable,
        "-S",
        str(ROOT / "ml/shiori-lora/export.py"),
        "--dry-run",
        "--adapter",
        str(adapter),
        "--out",
        str(tmp_path / "out"),
        "--llama-cpp",
        str(llama),
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    plan = json.loads(result.stdout)
    assert plan["commands"][0][-1] == "--no-mtp"
    assert plan["commands"][1][-2:] == ["Q4_K_M", "2"]
    assert not (tmp_path / "out").exists()
    result = subprocess.run(command + ["--base", "Qwen/Qwen3.5-4B"], capture_output=True, text=True)
    assert result.returncode != 0 and "differs" in result.stderr
