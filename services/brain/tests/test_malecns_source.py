"""Optional offline audit against the actual, never-committed Feather inputs."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
from scipy import sparse
from tsuyu_brain.connectome import data_directory

pytest.importorskip("pyarrow", reason="raw-data audit requires the ingest extra")
pytest.importorskip("pandas")

import pyarrow.dataset as ds
from tsuyu_brain.connectome.malecns_ingest import scan_edges, sha256


@pytest.mark.eval
def test_committed_edges_equal_raw_synapse_counts() -> None:
    raw = Path(__file__).resolve().parents[3] / "data/raw/malecns-v1.0"
    if not raw.is_dir():
        pytest.skip("raw MaleCNS inputs are intentionally not distributed with the package")
    manifest = json.loads((data_directory() / "manifest.json").read_text())
    for source in manifest["sources"].values():
        assert sha256(raw / source["file"]) == source["sha256"]
    metadata = {
        name: json.loads((data_directory() / f"{name}.json").read_text())
        for name in manifest["circuits"]
    }
    ids = sorted({row["bodyId"] for data in metadata.values() for row in data["neurons"]})
    edges = scan_edges(
        raw / manifest["sources"]["weights"]["file"],
        ds.field("body_pre").isin(ids) & ds.field("body_post").isin(ids),
    )
    for name, data in metadata.items():
        index = {row["bodyId"]: i for i, row in enumerate(data["neurons"])}
        expected = np.zeros((len(index), len(index)), dtype=np.int64)
        for pre, post, count in edges.itertuples(index=False, name=None):
            if pre in index and post in index:
                expected[index[pre], index[post]] += count
        actual = sparse.load_npz(data_directory() / f"{name}.npz").toarray()
        info = manifest["circuits"][name]
        expected = (expected * np.array(data["signs"])[:, None] * info["scale"]).astype(np.float32)
        normalization = info.get("normalization", {})
        for projection, gains in normalization.get("projection_factors", {}).items():
            source, target = projection.split("->")
            expected[slice(*data["groups"][source]), slice(*data["groups"][target])] *= np.array(
                gains, dtype=np.float32
            )
        for sign, gains in normalization.get("source_sign_factors", {}).items():
            expected[np.array(data["signs"]) == int(sign)] *= np.array(gains, dtype=np.float32)
        np.testing.assert_array_equal(actual, expected)
