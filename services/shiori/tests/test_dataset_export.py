from __future__ import annotations

import hashlib
import json

import pytest
from tsuyu_shiori.dataset.export import eval_questions, export_dataset
from tsuyu_shiori.dataset.questions import questions
from tsuyu_shiori.dataset.traces import replay
from tsuyu_shiori.dataset.world import build_world


@pytest.mark.asyncio
async def test_export_splits_provenance_and_jsonl(tmp_path):
    stats = await export_dataset(tmp_path, 100, 100)
    original = {p.name: p.read_bytes() for p in tmp_path.iterdir()}
    assert stats == await export_dataset(tmp_path, 100, 100)
    assert original == {p.name: p.read_bytes() for p in tmp_path.iterdir()}
    splits = stats["splits"]
    assert len(eval_questions()) == 61
    assert splits["test"]["examples"] == 159
    for left, right in (("train", "valid"), ("train", "test"), ("valid", "test")):
        assert not set(splits[left]["seeds"]) & set(splits[right]["seeds"])
    heldout = {q.template_id for q in questions(2)}
    assert not heldout & set(splits["train"]["templates"] + splits["valid"]["templates"])
    for split in splits:
        rows = (tmp_path / f"{split}.jsonl").read_text(encoding="utf-8").splitlines()
        metadata = (tmp_path / f"{split}.meta.jsonl").read_text(encoding="utf-8").splitlines()
        for row, meta in zip(rows, metadata, strict=True):
            example, provenance = json.loads(row), json.loads(meta)
            assert provenance["sha256"] == hashlib.sha256(row.encode()).hexdigest()
            assert set(example) == {"messages", "tools"}
            assert example["messages"][0]["role"] == "system"
            assert example["messages"][-1]["role"] == "assistant"
            await replay(example, build_world(provenance["seed"]))
