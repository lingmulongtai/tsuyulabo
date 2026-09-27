from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from tsuyulabo_api.domain import constants as c
from tsuyulabo_api.domain.eclosion import odds as adjusted_odds

router = APIRouter(prefix="/v1/odds")


@router.get("")
async def odds() -> dict[str, Any]:
    return {
        "tiers": list(c.TIER_COLORS),
        "eclosion": c.ODDS,
        "adjusted": {
            rank: {
                "temperature": adjusted_odds(rank, 80),
                "pupation": adjusted_odds(rank, 0, True),
                "both": adjusted_odds(rank, 80, True),
            }
            for rank in c.ODDS
        },
        "temperature_bonus": {
            "threshold": c.TEMPERATURE_BONUS_THRESHOLD,
            "shift": c.TEMPERATURE_ODDS_SHIFT,
        },
        "pupation_bonus": {"shift": c.SITE_ODDS_SHIFT},
        "great_success": {
            "base": c.GREAT_BASE_CHANCE,
            "score_divisor": c.GREAT_SCORE_DIVISOR,
            "base_cap": c.GREAT_BASE_CAP,
            "team_cap": c.TEAM_GREAT_BONUS_CAP,
            "day7_multiplier": c.FINAL_DAY_MULTIPLIER,
            "final_cap": c.GREAT_FINAL_CAP,
        },
        "hirameki": {"base": c.HIRAMEKI_CHANCE, "three_stars": c.HIRAMEKI_THREE_STAR_CHANCE},
    }
