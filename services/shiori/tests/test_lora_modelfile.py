from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location(
    "lora_modelfile", ROOT / "ml/shiori-lora/modelfile.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_replace_from_preserves_native_tool_template_and_parameters():
    base = (
        'FROM old\nTEMPLATE """{{ .Tools }}\nFROM literal\n{{ .Messages }}"""\nPARAMETER stop end\n'
    )
    result = module.compose(base, "C:/models/shiori.gguf")
    assert result == base.replace("FROM old", 'FROM "C:/models/shiori.gguf"', 1)
    with pytest.raises(ValueError, match="TEMPLATE"):
        module.compose("FROM old", "new")
    with pytest.raises(ValueError, match="unadapted"):
        module.compose(base + "ADAPTER old\n", "new")
