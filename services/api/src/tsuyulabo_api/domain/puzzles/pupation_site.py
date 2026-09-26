from __future__ import annotations

from random import Random

from .. import constants as c
from .common import JsonObject, VerifyResult


def generate(rng: Random, context: JsonObject) -> tuple[JsonObject, JsonObject]:
    categories = list(range(len(c.SITE_IDS)))
    rng.shuffle(categories)
    options = []
    for option_id, category in zip(c.SITE_IDS, categories, strict=True):
        label, detail = rng.choice(c.SITE_TEXT_POOLS[category])
        options.append({"id": option_id, "label": label, "detail": detail})
    winner = rng.randrange(len(options))
    hinted = (
        winner
        if rng.random() < c.SITE_HINT_ACCURACY
        else rng.choice([i for i in range(len(options)) if i != winner])
    )
    return {"options": options, "hint": c.SITE_HINTS[categories[hinted]]}, {
        "winning_id": options[winner]["id"],
        "hinted_id": options[hinted]["id"],
    }


def verify(params: JsonObject, submission: JsonObject) -> VerifyResult:
    if submission.get("choice") not in [option["id"] for option in params["options"]]:
        return VerifyResult(False, "out_of_bounds")
    return VerifyResult(True)


def roll(rng: Random, params: JsonObject, secret: JsonObject, submission: JsonObject) -> JsonObject:
    """Luck is fixed at issuance; retries never reroll the winning option."""
    if not verify(params, submission).valid:
        raise ValueError("invalid choice")
    hit = submission["choice"] == secret["winning_id"]
    return {"hit": hit, "effects": {"eclosion_bonus": hit}}
