"""Measured three-hop visual paths and explicit homeostasis for their LIF reduction."""

from __future__ import annotations

from dataclasses import replace

import pandas as pd
import torch

from tsuyu_brain.circuit import Circuit
from tsuyu_brain.connectome.malecns_selection import Selection


def visual_frontiers(selection: Selection, edges: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    sensory = pd.concat([selection.groups[g] for g in selection.inputs]).bodyId
    output = pd.concat([selection.groups[g] for g in ("DNa02_L", "DNa02_R")]).bodyId
    incoming = edges[edges.body_pre.isin(sensory)].groupby("body_post").weight.sum()
    outgoing = edges[edges.body_post.isin(output)].groupby("body_pre").weight.sum()
    return incoming, outgoing


def add_visual_relays(
    selection: Selection,
    rows: pd.DataFrame,
    ends: pd.DataFrame,
    middle: pd.DataFrame,
    budget: int = 192,
) -> Selection:
    """Retain complete pairs on real sensory->a->b->DNa02 paths, up to budget.

    Rank by min(summed sensory->a counts, a->b count, summed b->DNa02 counts).
    Ties use body IDs; selection never sees simulated rates, signs, or valence.
    Unannotated or unresolved-transmitter bodies cannot be retained.
    """
    incoming, outgoing = visual_frontiers(selection, ends)
    valid = rows[rows.sign.notna() & rows.type.notna()].bodyId
    candidates = middle[
        middle.body_pre.isin(incoming.index)
        & middle.body_post.isin(outgoing.index)
        & middle.body_pre.isin(valid)
        & middle.body_post.isin(valid)
    ].copy()
    candidates["incoming"] = candidates.body_pre.map(incoming)
    candidates["outgoing"] = candidates.body_post.map(outgoing)
    candidates["score"] = candidates[["incoming", "weight", "outgoing"]].min(axis=1)
    used = set(pd.concat(list(selection.groups.values())).bodyId)
    retained: set[int] = set()
    for row in candidates.sort_values(
        ["score", "body_pre", "body_post"], ascending=[False, True, True]
    ).itertuples():
        pair = {row.body_pre, row.body_post} - used
        if len(retained | pair) <= budget:
            retained |= pair
    groups = dict(selection.groups)
    groups["visual_relay"] = rows[rows.bodyId.isin(retained)].sort_values("bodyId")
    rules = dict(selection.rules)
    rules["visual_relay"] = (
        f"up to {budget} annotated bodies on complete sensory->a->b->DNa02 paths; "
        "rank min(sum sensory->a, a->b, sum b->DNa02) descending; tie by a,b bodyId; "
        "retain complete pairs, then all induced edges; no pooled or synthetic bodies"
    )
    return replace(
        selection,
        groups=groups,
        rules=rules,
        todos=("TODO: longer visual paths and omitted boundary input remain unmodeled.",),
    )


def normalize_steering(circuit: Circuit, budget: float = 4.0) -> tuple[Circuit, dict[str, object]]:
    """Balance each target's available E/I afferents; retain inhibitory photos.

    A shared near-threshold background current permits inhibitory sensory signals
    to propagate as disinhibition. It represents omitted background input, not an
    observed edge or a transmitter-sign reversal. Absent sign strata stay absent.
    """
    weights = circuit.weights.clone()
    factors = {}
    for sign in (-1, 1):
        mask = circuit.signs == sign
        block = weights[mask]
        totals = block.abs().sum(0)
        gains = torch.where(totals > 0, budget / totals.clamp_min(1e-12), 1.0)
        weights[mask] = block * gains
        factors[str(sign)] = gains.tolist()
    tonic = {group: 1.15 for group in ("visual_relay", "DNa02_L", "DNa02_R")}
    return replace(circuit.with_weights(weights), tonic=tonic), {
        "method": "equal available excitatory and inhibitory magnitude per target",
        "reason": "bounded induced subgraph loses afferent balance and spontaneous boundary drive",
        "sign_budget": budget,
        "sign_budget_reason": "4 retains unilateral responses; seed-19 budget 2 responses "
        "are weak and budget 8 produces large spontaneous walking drive",
        "source_sign_factors": factors,
        "tonic": tonic,
        "tonic_reason": "same 1.15 near-threshold background current as the walking model; "
        "inhibitory histamine paths need active relays to convey disinhibition",
    }
