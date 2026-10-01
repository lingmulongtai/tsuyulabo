from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from tsuyu_shiori.dataset.export import export_dataset

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "ml/shiori-lora/train.py"


@pytest.mark.asyncio
async def test_dry_run_does_not_import_training_libraries(tmp_path):
    await export_dataset(tmp_path / "data", 1, 1)
    result = subprocess.run(
        [
            sys.executable,
            "-S",
            str(SCRIPT),
            "--dry-run",
            "--data",
            str(tmp_path / "data"),
            "--out",
            str(tmp_path / "adapter"),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert '"dry_run": true' in result.stdout
    assert not (tmp_path / "adapter").exists()
    invalid = subprocess.run(
        [
            sys.executable,
            "-S",
            str(SCRIPT),
            "--dry-run",
            "--data",
            str(tmp_path / "data"),
            "--out",
            str(tmp_path / "adapter"),
            "--lr",
            "nan",
        ],
        capture_output=True,
        text=True,
    )
    assert invalid.returncode != 0 and "--lr" in invalid.stderr
    output_file = tmp_path / "existing-file"
    output_file.write_text("keep")
    invalid = subprocess.run(
        [
            sys.executable,
            "-S",
            str(SCRIPT),
            "--dry-run",
            "--data",
            str(tmp_path / "data"),
            "--out",
            str(output_file),
        ],
        capture_output=True,
        text=True,
    )
    assert invalid.returncode == 2 and "absent or empty" in invalid.stderr


def test_sparse_loss_matches_full_masked_causal_loss(monkeypatch):
    import torch

    monkeypatch.syspath_prepend(str(SCRIPT.parent))
    spec = importlib.util.spec_from_file_location("lora_train", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    logits = torch.arange(30, dtype=torch.float32).reshape(1, 6, 5).requires_grad_()
    labels = torch.tensor([[-100, -100, 2, 3, -100, 1]])

    class Model:
        def __call__(self, **kwargs):
            assert kwargs["use_cache"] is False
            assert kwargs["logits_to_keep"].tolist() == [1, 2, 4]
            return SimpleNamespace(logits=logits[:, kwargs["logits_to_keep"], :])

    loss, _ = module.assistant_loss(torch, Model(), {"labels": labels})
    expected = torch.nn.functional.cross_entropy(
        logits[:, :-1, :].reshape(-1, 5), labels[:, 1:].reshape(-1)
    )
    assert torch.allclose(loss, expected)
    loss.backward()
    assert logits.grad[0, 0].abs().sum() == 0
    assert logits.grad[0, 1].abs().sum() > 0
