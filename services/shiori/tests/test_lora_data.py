from __future__ import annotations

import importlib.util
from copy import deepcopy
from pathlib import Path

import pytest
from tsuyu_shiori.dataset.export import export_dataset

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location("lora_data", ROOT / "ml/shiori-lora/data.py")
data = importlib.util.module_from_spec(spec)
spec.loader.exec_module(data)


@pytest.mark.asyncio
async def test_standalone_validation_rejects_broken_calls_and_provenance(tmp_path):
    await export_dataset(tmp_path, 2, 2)
    rows, _ = data.load_data(tmp_path)
    broken = deepcopy(rows["train"][0])
    broken["messages"][2]["tool_calls"][0]["function"]["arguments"] = "{}"
    with pytest.raises(ValueError, match="arguments must be"):
        data.validate_example(broken)
    broken = deepcopy(rows["train"][0])
    broken["messages"][3]["tool_call_id"] = "wrong"
    with pytest.raises(ValueError, match="pending call"):
        data.validate_example(broken)
    (tmp_path / "train.jsonl").write_text("{}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="count mismatch"):
        data.load_data(tmp_path)


def test_assistant_mask_keeps_tool_calls_but_excludes_tool_results():
    class Tokenizer:
        def apply_chat_template(self, messages, **kwargs):
            return "".join(f"<|im_start|>{m['role']}\n{m['content']}<|im_end|>" for m in messages)

        def __call__(self, text, **kwargs):
            return {
                "input_ids": list(map(ord, text)),
                "attention_mask": [1] * len(text),
                "offset_mapping": [(i, i + 1) for i in range(len(text))],
            }

    row = {
        "messages": [
            {"role": "system", "content": "secret"},
            {"role": "assistant", "content": "tool_call"},
            {"role": "tool", "content": "private"},
            {"role": "assistant", "content": "answer"},
        ],
        "tools": [],
    }
    encoded = data.encode_assistant(row, Tokenizer(), 300)
    supervised = "".join(chr(x) for x in encoded["labels"] if x != -100)
    assert supervised == "tool_call<|im_end|>answer<|im_end|>"
    with pytest.raises(ValueError, match="never truncate"):
        data.encode_assistant(row, Tokenizer(), 2)
