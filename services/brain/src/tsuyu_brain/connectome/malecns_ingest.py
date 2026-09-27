"""Memory-bounded Arrow ingestion, isolated from runtime dependencies."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.dataset as ds
import torch

from tsuyu_brain.circuit import Circuit
from tsuyu_brain.connectome.malecns_selection import (
    ANNOTATION_COLUMNS,
    SEED,
    Selection,
    resolve_transmitters,
    select_circuits,
)
from tsuyu_brain.connectome.npz_io import save_circuit

FILES = {
    "annotations": "body-annotations-male-cns-v1.0-minconf-0.5.feather",
    "transmitters": "body-neurotransmitters-male-cns-v1.0.feather",
    "weights": "connectome-weights-male-cns-v1.0-minconf-0.5.feather",
}
VERSION = "malecns-v1.0"
EDGE_COLUMNS = ["body_pre", "body_post", "weight"]


def sha256(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def inspect_sources(raw: Path) -> dict[str, dict[str, object]]:
    info = {}
    for name, filename in FILES.items():
        dataset = ds.dataset(raw / filename, format="ipc")
        info[name] = {
            "file": filename,
            "rows": dataset.count_rows(),
            "columns": {field.name: str(field.type) for field in dataset.schema},
        }
    return info


def scan_edges(path: Path, predicate: ds.Expression) -> pd.DataFrame:
    """Decode batches, push down the predicate, retain only matching edges.

    IPC still scans compressed batches; this is not indexed random access.
    Single-batch readahead bounds transient memory independently of file size.
    """
    scanner = ds.dataset(path, format="ipc").scanner(
        columns=EDGE_COLUMNS,
        filter=predicate,
        batch_size=65536,
        batch_readahead=1,
        fragment_readahead=1,
        use_threads=False,
    )
    frames = [batch.to_pandas() for batch in scanner.to_batches() if batch.num_rows]
    if not frames:
        return pd.DataFrame({name: pd.Series(dtype="int64") for name in EDGE_COLUMNS})
    result = pd.concat(frames, ignore_index=True)
    if (result.weight < 0).any() or not np.isfinite(result.weight).all():
        raise ValueError("synapse counts must be finite and nonnegative")
    return result


def add_bridges(selection: Selection, rows: pd.DataFrame, edges: pd.DataFrame) -> Selection:
    """Add at most 96 real two-hop sensory->interneuron->output bridges.

    Rank by min(total sensory input, total output synapses), tie by body ID.
    Selection is independent of signs or simulation/evaluation outcomes.
    """
    sensory = pd.concat([selection.groups[group] for group in selection.inputs]).bodyId
    outputs = pd.concat([selection.groups[group] for group in selection.outputs]).bodyId
    incoming = edges[edges.body_pre.isin(sensory)].groupby("body_post").weight.sum()
    outgoing = edges[edges.body_post.isin(outputs)].groupby("body_pre").weight.sum()
    scores = pd.concat([incoming.rename("incoming"), outgoing.rename("outgoing")], axis=1)
    scores = scores.dropna()
    scores["score"] = scores.min(axis=1)
    used = pd.concat(list(selection.groups.values())).bodyId
    candidates = rows[rows.sign.notna() & rows.type.notna() & ~rows.bodyId.isin(used)]
    candidates = candidates.merge(scores[["score"]], left_on="bodyId", right_index=True)
    candidates = candidates.sort_values(["score", "bodyId"], ascending=[False, True]).head(96)
    group = "feeding_interneuron" if selection.name == "feeding" else "grooming_interneuron"
    groups = dict(selection.groups)
    prior = groups.get(group, rows.iloc[:0])
    groups[group] = pd.concat([prior, candidates]).sort_values("bodyId")
    rules = dict(selection.rules)
    rules[group] = rules.get(group, "") + (
        "; add up to 96 annotated two-hop sensory->body->output bridges; "
        "rank min(sum sensory input, sum output counts) descending, bodyId ascending"
    )
    return replace(selection, groups=groups, rules=rules)


def make_circuit(
    selection: Selection,
    edges: pd.DataFrame,
    scale: float,
) -> tuple[Circuit, list[dict[str, object]]]:
    if not math.isfinite(scale) or scale <= 0:
        raise ValueError("scale must be finite and positive")
    groups, records, offset = {}, [], 0
    for name, frame in selection.groups.items():
        frame = frame.sort_values(["type", "bodyId"])
        groups[name] = slice(offset, offset + len(frame))
        offset += len(frame)
        fields = [
            "bodyId",
            "type",
            "instance",
            "predicted_nt",
            "consensus_nt",
            "effective_nt",
            "nt_source",
            "sign",
        ]
        records.extend(json.loads(frame[fields].to_json(orient="records")))
    if not 0 < offset <= 2000:
        raise ValueError("each circuit must have 1..2000 actual neurons")
    ids = pd.Index([record["bodyId"] for record in records])
    if not ids.is_unique:
        raise ValueError("a body occurs in more than one circuit group")
    signs = np.array([record["sign"] for record in records], dtype=np.float32)
    pre, post = ids.get_indexer(edges.body_pre), ids.get_indexer(edges.body_post)
    selected = (pre >= 0) & (post >= 0)
    weights = np.zeros((offset, offset), dtype=np.float32)
    np.add.at(
        weights,
        (pre[selected], post[selected]),
        edges.weight.to_numpy()[selected] * signs[pre[selected]] * scale,
    )
    projections = tuple(
        (a, b) for a in groups for b in groups if np.any(weights[groups[a], groups[b]])
    )
    return Circuit(
        selection.name,
        groups,
        torch.from_numpy(weights),
        torch.from_numpy(signs),
        selection.inputs,
        selection.outputs,
        VERSION,
        projections,
    ), records


def build(
    raw: Path,
    output: Path,
    *,
    scales: dict[str, float] | None = None,
    seed: int = SEED,
) -> dict[str, object]:
    sources = inspect_sources(raw)
    annotations = (
        ds.dataset(raw / FILES["annotations"], format="ipc")
        .to_table(columns=list(ANNOTATION_COLUMNS))
        .to_pandas()
    )
    transmitters = (
        ds.dataset(raw / FILES["transmitters"], format="ipc")
        .to_table(
            columns=["body", "predicted_nt", "consensus_nt"],
            filter=ds.field("body").isin(annotations.bodyId.to_numpy()),
        )
        .to_pandas()
    )
    rows = resolve_transmitters(annotations, transmitters)
    selections = select_circuits(rows, seed)
    scales = scales or {}
    if set(scales) - {s.name for s in selections}:
        raise ValueError("unknown circuit in scales")
    bridge_names = {"feeding", "grooming"}
    bridging = [s for s in selections if s.name in bridge_names]
    sensory = pd.concat([s.groups[g] for s in bridging for g in s.inputs]).bodyId
    targets = pd.concat([s.groups[g] for s in bridging for g in s.outputs]).bodyId
    path = raw / FILES["weights"]
    bridge_edges = scan_edges(
        path,
        ds.field("body_pre").isin(sensory.to_numpy())
        | ds.field("body_post").isin(targets.to_numpy()),
    )
    selections = [
        add_bridges(s, rows, bridge_edges) if s.name in bridge_names else s for s in selections
    ]
    del bridge_edges
    all_ids = pd.concat([frame for s in selections for frame in s.groups.values()]).bodyId.unique()
    edges = scan_edges(
        path, ds.field("body_pre").isin(all_ids) & ds.field("body_post").isin(all_ids)
    )
    for info in sources.values():
        info["sha256"] = sha256(raw / info["file"])
    manifest = {
        "version": VERSION,
        "dataset": "male-cns:v1.0",
        "seed": seed,
        "source": "https://male-cns.janelia.org/download/",
        "sources": sources,
        "license": "CC-BY-4.0",
        "license_url": "https://creativecommons.org/licenses/by/4.0/",
        "attribution": "FlyEM / HHMI Janelia; University of Cambridge; MRC LMB; Google Research",
        "citation": "Berg et al. (2026), Cell 189:5504-5526.e15, doi:10.1016/j.cell.2026.08.015",
        "sign_policy": "body predicted_nt; unresolved predictions fall back to consensus_nt; "
        "ACh +1, GABA -1, Glu -1, histamine -1, dopamine +1 current surrogate; "
        "remaining unknown transmitters excluded; receptor specificity unmodeled",
        "boundary": "induced subgraphs only; no fabricated neurons/edges; no edge normalization; "
        "weights = synapse count * presynaptic sign * one circuit scale",
        "storage": "compressed CSR float32 preserves scaled counts; already below 2 MB",
        "circuits": {},
    }
    output.mkdir(parents=True, exist_ok=True)
    for selection in selections:
        scale = scales.get(selection.name, 1 / 32)
        circuit, records = make_circuit(selection, edges, scale)
        target = output / f"{selection.name}.npz"
        save_circuit(circuit, target, {"dataset": "male-cns:v1.0", "license": "CC-BY-4.0"})
        metadata_path = target.with_suffix(".json")
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        metadata["neurons"] = records
        metadata_path.write_text(
            json.dumps(metadata, indent=2) + "\n", encoding="utf-8", newline="\n"
        )
        counts = {g: bounds.stop - bounds.start for g, bounds in circuit.groups.items()}
        todos = list(selection.todos)
        todos.extend(
            f"TODO: missing group {name}; no substitute invented"
            for name, count in counts.items()
            if count == 0
        )
        manifest["circuits"][selection.name] = {
            "neurons": len(records),
            "edges": int(circuit.weights.count_nonzero()),
            "group_counts": counts,
            "selection_rules": selection.rules,
            "selected_types": {
                g: frame.type.value_counts().sort_index().to_dict()
                for g, frame in selection.groups.items()
            },
            "scale": scale,
            "input_rate_hz": 180.0,
            "todos": todos,
            "files": {target.name: sha256(target), metadata_path.name: sha256(metadata_path)},
        }
    (output / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    return manifest
