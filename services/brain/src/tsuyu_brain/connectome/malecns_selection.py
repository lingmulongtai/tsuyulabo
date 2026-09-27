"""Offline, explicit MaleCNS v1.0 selections. Requires the optional ingest extra."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

SEED = 1729
GLOMERULI = ("DM1", "DM2", "DM3", "DM4", "VA2", "VM2", "DL1", "DC2")
# Functional pooling, not a claim that transmitter determines behavioral valence.
# Aso et al. 2014, doi:10.7554/eLife.04580; Li et al. 2020, doi:10.7554/eLife.62576.
MBON_APPROACH = ("MBON11", "MBON12", "MBON14")
MBON_AVOID = ("MBON01", "MBON03", "MBON04", "MBON05", "MBON06")
SIGNS = {"acetylcholine": 1, "gaba": -1, "glutamate": -1, "histamine": -1, "dopamine": 1}
ANNOTATION_COLUMNS = (
    "bodyId",
    "type",
    "instance",
    "somaSide",
    "rootSide",
    "class",
    "subclass",
    "synonyms",
    "hemibrainType",
    "flywireType",
    "receptorType",
    "superclass",
)


@dataclass(frozen=True)
class Selection:
    name: str
    groups: dict[str, pd.DataFrame]
    inputs: tuple[str, ...]
    outputs: tuple[str, ...]
    rules: dict[str, str]
    todos: tuple[str, ...] = ()


def resolve_transmitters(annotations: pd.DataFrame, transmitters: pd.DataFrame) -> pd.DataFrame:
    """Use body predictions; fall back to supplied consensus only when unresolved.

    Dopamine is represented as positive current (including predicted dopaminergic KCs).
    This is an explicit LIF approximation, not a receptor-level physiological claim.
    Unknown signs are excluded, never assigned an invented polarity.
    """
    if annotations.bodyId.duplicated().any() or transmitters.body.duplicated().any():
        raise ValueError("duplicate body IDs")
    rows = annotations.merge(transmitters, left_on="bodyId", right_on="body", how="left")
    known = rows.predicted_nt.isin(SIGNS)
    rows["effective_nt"] = rows.predicted_nt.where(known, rows.consensus_nt)
    rows["nt_source"] = np.where(known, "predicted_nt", "consensus_nt")
    rows["sign"] = rows.effective_nt.map(SIGNS)
    return rows.sort_values("bodyId").reset_index(drop=True)


def select_circuits(rows: pd.DataFrame, seed: int = SEED) -> list[Selection]:
    """Select actual bodies before inspecting any simulation outcomes."""
    available = rows[rows.sign.notna()]

    def types(*names: str) -> pd.DataFrame:
        return available[available.type.isin(names)].copy()

    def sample(frame: pd.DataFrame, maximum: int) -> pd.DataFrame:
        frame = frame.sort_values("bodyId")
        if len(frame) > maximum:
            indices = np.random.default_rng(seed).choice(len(frame), maximum, replace=False)
            frame = frame.iloc[indices]
        return frame.sort_values("bodyId").copy()

    orn = types(*(f"ORN_{name}" for name in GLOMERULI)).sort_values(["type", "bodyId"])
    pn = available[
        available.type.fillna("").str.fullmatch("(" + "|".join(GLOMERULI) + r")_(ad|l|v|lv)PN")
    ].copy()
    kc = sample(available[available.type.fillna("").str.startswith("KC")], 200)
    # Sensory photoreceptors are retained; no fictitious direct visual->KC edge is added.
    visual = sample(types("R8p"), 32)
    reward_pam = (1, 2, 4, 5, 6, 7, 8, 9, 10, 11, 15)
    mb = Selection(
        "olfaction_mb",
        {
            "ORN": orn,
            "PN": pn,
            "KC": kc,
            "APL": types("APL"),
            "MBON_ap": types(*MBON_APPROACH),
            "MBON_av": types(*MBON_AVOID),
            "PAM": types(*(f"PAM{i:02}" for i in reward_pam)),
            "PPL1": types("PPL101", "PPL103", "PPL106"),
            "visual": visual,
        },
        ("ORN", "visual", "PAM", "PPL1"),
        ("MBON_ap", "MBON_av"),
        {
            "ORN": "exact ORN_ types for " + ", ".join(GLOMERULI),
            "PN": "same glomeruli; exact uniglomerular _(ad|l|v|lv)PN suffix",
            "KC": "type starts KC; uniform seeded sample of 200 bodies",
            "APL": "type APL",
            "MBON_ap": ", ".join(MBON_APPROACH),
            "MBON_av": ", ".join(MBON_AVOID),
            "PAM": "reward-associated PAM01,02,04,05,06,07,08,09,10,11,15",
            "PPL1": "punishment-associated PPL101,103,106",
            "visual": "32 seeded R8p photoreceptors; no fabricated relay",
        },
        (
            "TODO: reconstruct visual relays to visual KCs; blue_light is incomplete.",
            "TODO: validate fruit-cue glomerular mixtures; "
            "current cue mapping is a game convention.",
            "TODO: review predicted dopamine in KCs against consensus acetylcholine; "
            "both map to positive current here.",
        ),
    )
    feeding = Selection(
        "feeding",
        {
            "Gr64f": types("LB3b", "LB3c"),
            "Gr66a": types("LB1a", "LB1b", "LB1c", "LB1d"),
            "feeding_interneuron": types(
                "GNG108", "GNG120", "GNG175", "ANXXX462a", "DNge080", "DNg67"
            ),
            "MN9": types("MN9"),
        },
        ("Gr64f", "Gr66a"),
        ("MN9",),
        {
            "Gr64f": "LB3b/c, putative Gr64f sweet GRNs (Tastekin et al. 2026 Fig 2E)",
            "Gr66a": "LB1a-d, putative bitter GRNs mapped using Gr33a (same Fig 2E)",
            "feeding_interneuron": "GNG108/Roundup, GNG120/Roundtree, GNG175/Usnea, "
            "ANXXX462a/Clavicle, DNge080/Rounddown, DNg67/Fudog; plus two-hop bridges",
            "MN9": "type MN9",
        },
        (
            "TODO: verify Gr66a expression per body; Gr66a is a game input alias for "
            "LB1a-d bitter GRNs, not a molecular annotation in this release.",
        ),
    )
    escape = Selection(
        "escape",
        {name: types(name) for name in ("LPLC2", "LC4", "DNp01")},
        ("LPLC2", "LC4"),
        ("DNp01",),
        {name: f"exact type {name}" for name in ("LPLC2", "LC4", "DNp01")},
    )
    photos = types("R8p", "R8y")
    steering_groups = {
        f"photoreceptor_{side}": sample(photos[photos.rootSide.eq(side)], 64) for side in ("L", "R")
    }
    dna02 = types("DNa02")
    steering_groups.update({f"DNa02_{side}": dna02[dna02.somaSide.eq(side)] for side in ("L", "R")})
    steering_groups["walking_DN"] = types("DNp09")
    steering = Selection(
        "steering",
        steering_groups,
        ("photoreceptor_L", "photoreceptor_R"),
        ("DNa02_L", "DNa02_R", "walking_DN"),
        {
            "photoreceptor_L": "64 seeded R8p/y; rootSide L",
            "photoreceptor_R": "64 seeded R8p/y; rootSide R",
            "DNa02_L": "DNa02, somaSide L",
            "DNa02_R": "DNa02, somaSide R",
            "walking_DN": "DNp09 (Braun et al. 2024); model tonic drive retained",
        },
        (
            "TODO: include the multi-stage visual steering pathway; direct photoreceptor "
            "to DNa02 wiring is not assumed.",
        ),
    )
    jo = available[available.type.fillna("").str.match(r"JO-(C|E|F|mz)")].copy()
    grooming = Selection(
        "grooming",
        {"JO": jo, "aDN": types("DNg62", "DNge078")},
        ("JO",),
        ("aDN",),
        {
            "JO": "JO-C*, JO-E*, JO-F*, JO-mz; exclude JO-unclear",
            "aDN": "DNg62/aDN1 and DNge078/aDN2 (annotation synonyms Hampel 2015)",
        },
        ("TODO: verify identities of graph-selected grooming interneurons against aBN1/2.",),
    )
    return [mb, feeding, escape, steering, grooming]
