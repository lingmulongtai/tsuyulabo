from __future__ import annotations

import json
from pathlib import Path

import pytest
import torch
from tsuyu_brain.connectome.npz_io import load_npz_circuit

pytest.importorskip("pyarrow", reason="offline ingestion needs tsuyu-brain[ingest]")
pytest.importorskip("pandas")

import pandas as pd
import pyarrow as pa
import pyarrow.dataset as ds
import pyarrow.feather as feather
from tsuyu_brain.connectome.malecns_ingest import FILES, build, scan_edges, sha256
from tsuyu_brain.connectome.malecns_selection import (
    ANNOTATION_COLUMNS,
    resolve_transmitters,
    select_circuits,
)


def test_project_filter_and_duplicate_counts(tmp_path: Path) -> None:
    annotations = []
    types = [
        "LB3b",
        "LB1a",
        "MN9",
        "GNG175",
        "LPLC2",
        "LC4",
        "DNp01",
        "ORN_DM1",
        "DM1_adPN",
        "KCg-m",
        "APL",
        "MBON11",
        "MBON01",
        "PAM01",
        "PPL101",
        "R8p",
        "DNa02",
        "DNp09",
        "JO-FV",
        "DNg62",
    ]
    for body, name in enumerate(types, 1):
        record = dict.fromkeys(ANNOTATION_COLUMNS)
        record.update(bodyId=body, type=name, instance=name + "_L", rootSide="L", somaSide="L")
        annotations.append(record)
    feather.write_feather(pa.Table.from_pylist(annotations), tmp_path / FILES["annotations"])
    nt = [
        {
            "body": body,
            "predicted_nt": "gaba" if name in {"GNG175", "APL"} else "acetylcholine",
            "consensus_nt": "acetylcholine",
        }
        for body, name in enumerate(types, 1)
    ]
    feather.write_feather(pa.Table.from_pylist(nt), tmp_path / FILES["transmitters"])
    edge_path = tmp_path / FILES["weights"]
    feather.write_feather(
        pa.table(
            {
                "body_pre": [1, 1, 4, 999],
                "body_post": [3, 3, 3, 3],
                "weight": [10, 5, 8, 200],
                "unused": ["x"] * 4,
            }
        ),
        edge_path,
    )
    selected = scan_edges(edge_path, ds.field("body_pre").isin([1, 4]))
    assert list(selected.columns) == ["body_pre", "body_post", "weight"]
    assert len(selected) == 3
    output = tmp_path / "out"
    manifest = build(tmp_path, output, scales={"feeding": 0.125})
    circuit = load_npz_circuit(output / "feeding.npz")
    assert circuit.weights[circuit.groups["Gr64f"], circuit.groups["MN9"]].item() == 1.875
    assert circuit.weights[circuit.groups["feeding_interneuron"], circuit.groups["MN9"]].min() == -1
    assert circuit.version == "malecns-v1.0"
    assert manifest["sources"]["weights"]["rows"] == 4
    before = sha256(output / "feeding.json")
    build(tmp_path, output, scales={"feeding": 0.125})
    assert sha256(output / "feeding.json") == before
    assert json.loads((output / "manifest.json").read_text()) == manifest
    assert not list(output.glob("*.feather"))
    with pytest.raises(ValueError, match="positive"):
        build(tmp_path, output, scales={"feeding": 0})


def test_prediction_polarity_fallback_and_sampling() -> None:
    names = ["KCg-m"] * 220 + ["ORN_DM1", "DM1_adPN", "DM1_lPN_extra", "MBON11", "MBON01"]
    annotations = pd.DataFrame(
        {"bodyId": range(len(names)), "type": names, "rootSide": "L", "somaSide": "L"}
    )
    nt = pd.DataFrame(
        {"body": range(len(names)), "predicted_nt": "dopamine", "consensus_nt": "acetylcholine"}
    )
    nt.loc[0, "predicted_nt"] = "glutamate"
    nt.loc[1, "predicted_nt"] = "unclear"
    nt.loc[2, ["predicted_nt", "consensus_nt"]] = "unclear"
    joined = resolve_transmitters(annotations, nt)
    assert joined.iloc[0]["sign"] == -1
    assert joined.iloc[1]["nt_source"] == "consensus_nt"
    first = select_circuits(joined)[0]
    again = select_circuits(joined.sample(frac=1, random_state=3))[0]
    assert len(first.groups["KC"]) == 200
    assert first.groups["KC"].bodyId.tolist() == again.groups["KC"].bodyId.tolist()
    assert 2 not in first.groups["KC"].bodyId.tolist()
    assert len(first.groups["PN"]) == 1
    assert torch.tensor(first.groups["KC"]["sign"].to_numpy()).isfinite().all()
