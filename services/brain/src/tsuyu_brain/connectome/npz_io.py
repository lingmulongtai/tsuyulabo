"""Local sparse-matrix interchange for small, manually curated circuit extracts."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import torch
from scipy import sparse

from tsuyu_brain.circuit import Circuit


def save_circuit(circuit: Circuit, path: Path, provenance: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    sparse.save_npz(path, sparse.csr_matrix(circuit.weights.detach().cpu().numpy()))
    metadata = {
        "name": circuit.name,
        "version": circuit.version,
        "groups": {name: [group.start, group.stop] for name, group in circuit.groups.items()},
        "signs": circuit.signs.tolist(),
        "input_groups": circuit.input_groups,
        "output_groups": circuit.output_groups,
        "projections": circuit.projections,
        "tonic": circuit.tonic,
        "provenance": provenance,
    }
    path.with_suffix(".json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")


def load_npz_circuit(path: Path) -> Circuit:
    metadata = json.loads(path.with_suffix(".json").read_text(encoding="utf-8"))
    matrix = sparse.load_npz(path)
    if matrix.shape[0] > 2000 or matrix.shape[0] != matrix.shape[1]:
        raise ValueError("only small square per-circuit extracts are supported")
    return Circuit(
        name=metadata["name"],
        version=metadata["version"],
        groups={name: slice(*bounds) for name, bounds in metadata["groups"].items()},
        weights=torch.from_numpy(np.asarray(matrix.toarray(), dtype=np.float32)),
        signs=torch.tensor(metadata["signs"], dtype=torch.float32),
        input_groups=tuple(metadata["input_groups"]),
        output_groups=tuple(metadata["output_groups"]),
        projections=tuple(tuple(pair) for pair in metadata["projections"]),
        tonic=metadata["tonic"],
    )
