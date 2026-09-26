from __future__ import annotations

import runpy
from pathlib import Path

from tsuyu_brain.connectome.npz_io import load_npz_circuit


def test_local_ingest_skeleton(tmp_path: Path) -> None:
    script = Path(__file__).parents[1] / "scripts/ingest_malecns.py"
    ingest = runpy.run_path(str(script))["ingest"]
    neurons, edges = tmp_path / "neurons.csv", tmp_path / "edges.csv"
    neurons.write_text("body_id,group,sign\n1,GRN,1\n2,MN9,1\n", encoding="utf-8")
    edges.write_text("pre,post,synapses\n1,2,10\n1,2,5\n9,2,7\n", encoding="utf-8")
    output = tmp_path / "feeding.npz"
    ingest(neurons, edges, output, "feeding", ("GRN",), ("MN9",), 0.2)
    circuit = load_npz_circuit(output)
    assert circuit.weights[0, 1] == 3
    assert circuit.version == "malecns-v1.0-unvalidated"
