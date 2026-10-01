from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import asdict, dataclass, field
from typing import Any

from tsuyu_shiori.rag import BM25Retriever, Retriever
from tsuyu_shiori.records import Lab, Record, RecordStore

from .compact import compact_result, newest_records
from .filters import select_records
from .schemas import (
    Arguments,
    AssociationArguments,
    CareArguments,
    ExperimentArguments,
    PaperArguments,
)

ARGUMENTS: dict[str, type[Arguments]] = {
    "get_care_events": CareArguments,
    "count_care_events": CareArguments,
    "get_association": AssociationArguments,
    "run_odor_choice": ExperimentArguments,
    "search_papers": PaperArguments,
}
DESCRIPTIONS = {
    "get_care_events": "Read compact care and sleep records, newest first (maximum 20 total). "
    "total is the filtered total; truncated means some records are omitted. "
    "Use count_care_events for exact counts. Filter by kinds for a specific topic.",
    "count_care_events": "Count matching care and sleep records exactly, before truncation. "
    "Returns count, applied filters and up to 4 citation IDs. For zero matches, IDs refer to "
    "inspected records in the same time window, not matching events.",
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
    sleep_until: str | None = None


async def _care_records(context: ToolContext, week_id: str) -> tuple[list[Record], list[Record]]:
    if week_id != context.week_id:
        raise ValueError("week is outside this conversation")
    # Deliberately fetch before filtering: the API's DB-backed store stays unchanged.
    care = select_records(
        await context.store.care_events(week_id),
        since=context.care_since,
        until=context.care_until,
    )
    sleeps = select_records(
        await context.store.sleep_sessions(week_id),
        since=context.sleep_since,
        until=context.sleep_until,
    )
    return care, sleeps


async def get_care_events(
    context: ToolContext,
    week_id: str,
    kinds: list[str] | None = None,
    research_day: int | None = None,
    cue: str | None = None,
    valence: str | None = None,
) -> dict[str, Any]:
    care, sleeps = await _care_records(context, week_id)
    filters = dict(kinds=kinds, research_day=research_day, cue=cue, valence=valence)
    return compact_result(select_records(care, **filters), select_records(sleeps, **filters))


async def count_care_events(
    context: ToolContext,
    week_id: str,
    kinds: list[str] | None = None,
    research_day: int | None = None,
    cue: str | None = None,
    valence: str | None = None,
) -> dict[str, Any]:
    care, sleeps = await _care_records(context, week_id)
    filters = dict(kinds=kinds, research_day=research_day, cue=cue, valence=valence)
    selected = select_records(care + sleeps, **filters)
    inspected = selected or care + sleeps
    return {
        "count": len(selected),
        "ids": [r.id for r in newest_records(inspected)[:4]],
        "filters": {"week_id": week_id, **filters},
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
        "count_care_events": count_care_events,
        "get_association": get_association,
        "run_odor_choice": run_odor_choice,
        "search_papers": search_papers,
    }
    return await functions[name](context, **validated)
