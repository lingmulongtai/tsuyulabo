"""Offline MaleCNS v1.0 extraction skeleton. No network operations.

Normalized neurons CSV: body_id,group,sign (+1 or -1).
Normalized edges CSV: pre,post,synapses (nonnegative counts).
Manually select one circuit before invoking this script, keeping <= 2000 neurons.
TODO: adapt official Feather/neuPrint schemas to these CSV columns outside runtime.
TODO: review cell-type aliases, laterality, transmitter confidence and receptor signs.
TODO: calibrate synapse-count-to-current scale against independent physiological data.
TODO: validate real extracts before registering a new connectome/decoder version.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
from collections import defaultdict
from pathlib import Path

import torch
from tsuyu_brain.circuit import Circuit
from tsuyu_brain.connectome.npz_io import save_circuit


def ingest(
    neurons_path: Path,
    edges_path: Path,
    output: Path,
    name: str,
    inputs: tuple[str, ...],
    outputs: tuple[str, ...],
    weight_scale: float,
) -> Circuit:
    if not 0 < weight_scale < float("inf"):
        raise ValueError("weight_scale must be finite and positive")
    with neurons_path.open(encoding="utf-8", newline="") as stream:
        neurons = sorted(
            csv.DictReader(stream), key=lambda row: (row["group"], int(row["body_id"]))
        )
    if not 0 < len(neurons) <= 2000:
        raise ValueError("select a nonempty small per-circuit extract first")
    indices = {row["body_id"]: index for index, row in enumerate(neurons)}
    if len(indices) != len(neurons):
        raise ValueError("duplicate body ids")
    members: dict[str, list[int]] = defaultdict(list)
    for index, row in enumerate(neurons):
        members[row["group"]].append(index)
    groups = {name: slice(min(ids), max(ids) + 1) for name, ids in members.items()}
    signs = torch.tensor([float(row["sign"]) for row in neurons])
    weights = torch.zeros(len(neurons), len(neurons))
    with edges_path.open(encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            if row["pre"] not in indices or row["post"] not in indices:
                continue  # Boundary edges are deliberately excluded from this subcircuit.
            pre, post = indices[row["pre"]], indices[row["post"]]
            count = float(row["synapses"])
            if not 0 <= count < float("inf"):
                raise ValueError("invalid synapse count")
            weights[pre, post] += count * weight_scale * signs[pre]
    projections = tuple(
        (source, target)
        for source in groups
        for target in groups
        if weights[groups[source], groups[target]].count_nonzero()
    )
    circuit = Circuit(
        name,
        groups,
        weights,
        signs,
        inputs,
        outputs,
        version="malecns-v1.0-unvalidated",
        projections=projections,
    )
    save_circuit(
        circuit,
        output,
        {
            "dataset": "MaleCNS v1.0; male-cns:v1.0",
            "source": "https://male-cns.janelia.org/download/",
            "license": "CC-BY-4.0",
            "attribution": (
                "FlyEM (HHMI Janelia), University of Cambridge, MRC LMB, Google Research"
            ),
            "neurons_sha256": hashlib.sha256(neurons_path.read_bytes()).hexdigest(),
            "edges_sha256": hashlib.sha256(edges_path.read_bytes()).hexdigest(),
            "weight_scale": str(weight_scale),
            "status": "unvalidated; curated signs and omitted boundary edges are model assumptions",
        },
    )
    return circuit


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--neurons", type=Path, required=True)
    parser.add_argument("--edges", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--inputs", nargs="+", required=True)
    parser.add_argument("--outputs", nargs="+", required=True)
    parser.add_argument("--weight-scale", type=float, required=True)
    args = parser.parse_args()
    ingest(
        args.neurons,
        args.edges,
        args.output,
        args.name,
        tuple(args.inputs),
        tuple(args.outputs),
        args.weight_scale,
    )


if __name__ == "__main__":
    main()
