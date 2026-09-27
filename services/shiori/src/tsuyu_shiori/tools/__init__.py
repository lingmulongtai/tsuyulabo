from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import asdict, dataclass, field
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from tsuyu_shiori.rag import BM25Retriever, Retriever
from tsuyu_shiori.records import Lab, Record, RecordStore

Cue = Literal["banana", "apple_vinegar", "yeast", "grape", "blue_light"]


class Arguments(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class CareArguments(Arguments):
    week_id: str
    kinds: list[str] | None = None


class AssociationArguments(Arguments):
    fly_id: str
    cue: Cue


class ExperimentArguments(AssociationArguments):
    trials: int = Field(default=20, ge=1, le=1000)
    seed: int = Field(default=0, ge=0, le=2**32 - 1)


class PaperArguments(Arguments):
    query: str = Field(min_length=1, max_length=1000)
    k: int = Field(default=3, ge=1, le=20)


ARGUMENTS: dict[str, type[Arguments]] = {
    "get_care_events": CareArguments,
    "get_association": AssociationArguments,
    "run_odor_choice": ExperimentArguments,
    "search_papers": PaperArguments,
}
DESCRIPTIONS = {
    "get_care_events": "Read this week's care records and sleep sessions; cite returned IDs.",
    "get_association": "Read the latest measured association for this fly and cue.",
    "run_odor_choice": "Run and persist an experiment on a private copy of this fly's brain.",
    "search_papers": "Retrieve cited research summaries, not observations of the player's fly.",
}
SCHEMAS = [
    {"name": name, "description": DESCRIPTIONS[name], "parameters": model.model_json_schema()}
    for name, model in ARGUMENTS.items()
]


@dataclass
class ToolContext:
    store: RecordStore
    lab: Lab
    week_id: str
    fly_id: str
    retriever: Retriever = field(default_factory=BM25Retriever)
    # Feature-specific temporal filtering; callers pass aware UTC boundaries.
    care_since: str | None = None
    care_until: str | None = None
    sleep_since: str | None = None


async def get_care_events(
    context: ToolContext, week_id: str, kinds: list[str] | None = None
) -> dict[str, Any]:
    if week_id != context.week_id:
        raise ValueError("week is outside this conversation")
    records = await context.store.care_events(week_id, kinds)
    sleeps = await context.store.sleep_sessions(week_id)

    def in_window(record: Record, since: str | None, until: str | None = None) -> bool:
        from datetime import datetime

        if since is None and until is None:
            return True
        if record.occurred_at is None:
            return False
        return (since is None or record.occurred_at >= datetime.fromisoformat(since)) and (
            until is None or record.occurred_at < datetime.fromisoformat(until)
        )

    return {
        "records": [
            r.to_dict() for r in records if in_window(r, context.care_since, context.care_until)
        ],
        "sleep_sessions": [r.to_dict() for r in sleeps if in_window(r, context.sleep_since)],
    }


async def get_association(context: ToolContext, fly_id: str, cue: str) -> dict[str, Any]:
    if fly_id != context.fly_id:
        raise ValueError("fly is outside this conversation")
    record = await context.store.association(fly_id, cue)
    return {"records": [record.to_dict()] if record else []}


async def run_odor_choice(
    context: ToolContext, fly_id: str, cue: str, trials: int = 20, seed: int = 0
) -> dict[str, Any]:
    if fly_id != context.fly_id:
        raise ValueError("fly is outside this conversation")
    record = await context.lab.run_odor_choice(fly_id, cue, trials, seed)
    return {"records": [record.to_dict()]}


async def search_papers(context: ToolContext, query: str, k: int = 3) -> dict[str, Any]:
    return {"papers": [asdict(paper) for paper in await context.retriever.search(query, k)]}


async def execute(context: ToolContext, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    if name not in ARGUMENTS:
        raise ValueError("unknown tool")
    validated = ARGUMENTS[name].model_validate(arguments).model_dump()
    functions: dict[str, Callable[..., Awaitable[dict[str, Any]]]] = {
        "get_care_events": get_care_events,
        "get_association": get_association,
        "run_odor_choice": run_odor_choice,
        "search_papers": search_papers,
    }
    return await functions[name](context, **validated)
