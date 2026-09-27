from __future__ import annotations

import hashlib
import json
from collections.abc import Iterator
from pathlib import Path

import pytest
import torch
from tsuyu_brain.connectome import data_directory, load_circuit
from tsuyu_brain.connectome.malecns import manifest, verified_path
from tsuyu_brain.connectome.stimuli import cue_stimulus
from tsuyu_brain.connectome.toy_v0 import CIRCUIT_NAMES


@pytest.fixture(autouse=True)
def single_thread() -> Iterator[None]:
    previous = torch.get_num_threads()
    torch.set_num_threads(1)
    yield
    torch.set_num_threads(previous)


@pytest.mark.parametrize("name", CIRCUIT_NAMES)
def test_measured_artifact_contract(name: str) -> None:
    circuit = load_circuit(name, "malecns-v1.0")
    info = manifest()["circuits"][name]
    metadata = json.loads((data_directory() / f"{name}.json").read_text())
    n = info["neurons"]
    assert 0 < n <= 2000
    assert circuit.weights.shape == (n, n)
    assert circuit.version == "malecns-v1.0"
    assert set(circuit.groups) >= set(load_circuit(name, "toy-v0").groups)
    assert len({row["bodyId"] for row in metadata["neurons"]}) == n
    for group, region in circuit.groups.items():
        assert region.stop - region.start == info["group_counts"][group] >= 0
        if region.stop == region.start:
            assert any(f"missing group {group};" in todo for todo in info["todos"])
    assert (circuit.weights * circuit.signs[:, None] >= 0).all()
    sign_map = {"acetylcholine": 1, "dopamine": 1, "gaba": -1, "glutamate": -1, "histamine": -1}
    for index, row in enumerate(metadata["neurons"]):
        assert circuit.signs[index] == sign_map[row["effective_nt"]]
        assert row["effective_nt"] == row[row["nt_source"]]
    counts = circuit.weights.abs() / info["scale"]
    normalization = info.get("normalization", {})
    for projection, gains in normalization.get("projection_factors", {}).items():
        source, target = projection.split("->")
        counts[circuit.groups[source], circuit.groups[target]] /= torch.tensor(gains)
    for sign, gains in normalization.get("source_sign_factors", {}).items():
        mask = circuit.signs == int(sign)
        counts[mask] /= torch.tensor(gains)
    assert torch.allclose(counts, counts.round(), rtol=1e-6, atol=1e-4)
    for filename, digest in info["files"].items():
        assert hashlib.sha256((data_directory() / filename).read_bytes()).hexdigest() == digest
        if filename.endswith(".json"):
            assert b"\r\n" not in (data_directory() / filename).read_bytes()


def test_provenance_and_small_bundle() -> None:
    assert manifest()["license"] == "CC-BY-4.0"
    assert manifest()["sources"]["weights"]["rows"] == 151856684
    for source in manifest()["sources"].values():
        assert len(bytes.fromhex(source["sha256"])) == 32
        assert source["file"].endswith(".feather")
    assert sum(p.stat().st_size for p in data_directory().glob("*") if p.is_file()) < 2_000_000
    assert not list(data_directory().glob("*.feather"))
    for cue in ("banana", "apple_vinegar", "yeast", "grape"):
        stimulus = cue_stimulus(cue, "malecns-v1.0")["ORN"]
        assert stimulus.sum() > 1  # Population encoding, not one toy neuron.
        assert set(stimulus.tolist()) == {0.0, 1.0}
    with pytest.raises(ValueError, match="unknown circuit"):
        load_circuit("../feeding", "malecns-v1.0")


def test_corrupted_artifact_is_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from tsuyu_brain.connectome import malecns

    malecns.manifest()
    (tmp_path / "feeding.npz").write_bytes(b"corrupt")
    monkeypatch.setattr(malecns, "data_directory", lambda: tmp_path)
    with pytest.raises(ValueError, match="checksum"):
        verified_path("feeding")
