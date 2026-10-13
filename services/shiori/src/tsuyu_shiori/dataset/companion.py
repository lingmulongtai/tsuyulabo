"""v3 intent examples use the same trusted observation payloads as runtime phrasing."""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Any

from tsuyu_shiori.agent.prompt import SYSTEM_PROMPT
from tsuyu_shiori.companion import diary_entry, quiet_hint
from tsuyu_shiori.dataset.questions import Question
from tsuyu_shiori.dataset.world import build_world
from tsuyu_shiori.diary_events import notable_events
from tsuyu_shiori.features import JST
from tsuyu_shiori.gateway import MockProvider
from tsuyu_shiori.hint_rules import detect_trouble
from tsuyu_shiori.records import Record

INTENTS = {"diary", "hint", "behaviour-why", "morning"}
TEMPLATES = {
    "diary": ("今日の観察日記を残して", "この子の一日を書いて", "今日の育ちを日記にして"),
    "hint": ("困った様子にひとこと", "この子に今できる手助けは", "そっと世話のヒントを伝えて"),
    "behaviour-why": (
        "今の動きはどうして？",
        "この子が動く理由は？",
        "いま見せた動きを短く説明して",
    ),
    "morning": ("朝のメモをお願い", "前日と前夜を振り返って", "おはようの観察メモを残して"),
}


def companion_questions(variant: int) -> list[Question]:
    return [
        Question(intent, texts[variant], f"{intent}:{variant}", {})
        for intent, texts in TEMPLATES.items()
    ]


def observation(seed: int) -> Record:
    # Synthetic measured state, never a fabricated value for a real individual's cue.
    return Record(
        "#v3-state",
        "habitat_observation",
        {
            "temperature": 32.0 if seed % 2 else 16.0,
            "behaviour": "walk",
            "stage": "larva3",
        },
        "eval-week",
        "eval-fly",
        datetime(2026, 9, 26, 12, tzinfo=JST),
    )


async def companion_trace(seed: int, q: Question) -> dict[str, Any]:
    context = build_world(seed)
    measured = observation(seed)
    context.store.add(measured)
    if q.intent == "morning":
        from tsuyu_shiori.tools import SCHEMAS, execute
        from tsuyu_shiori.verify import verify

        now = datetime(2026, 9, 27, 8, tzinfo=JST)
        today = now.replace(hour=0)
        context.care_since = (today - timedelta(days=1)).isoformat()
        context.care_until = today.isoformat()
        context.sleep_since = (today - timedelta(hours=12)).isoformat()
        context.sleep_until = now.isoformat()
        result = await execute(context, "get_care_events", {"week_id": context.week_id})
        request = {
            "feature": "morning",
            "question": q.text,
            "week_id": context.week_id,
            "fly_id": context.fly_id,
            "now": now.isoformat(),
        }
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(request, ensure_ascii=False)},
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "id": "care",
                        "type": "function",
                        "function": {
                            "name": "get_care_events",
                            "arguments": {"week_id": context.week_id},
                        },
                    }
                ],
            },
            {
                "role": "tool",
                "name": "get_care_events",
                "tool_call_id": "care",
                "content": json.dumps(result, ensure_ascii=False),
            },
        ]
        response = await MockProvider().complete(messages, [], "mock-journal")
        checked = await verify(
            response.text,
            context.store,
            allowed_ids={r["id"] for r in result["records"] + result["sleep_sessions"]},
        )
        if checked.report.dropped or not checked.text:
            raise ValueError("invalid morning oracle")
        messages.append({"role": "assistant", "content": checked.text})
        return {
            "messages": messages,
            "tools": [{"type": "function", "function": s} for s in SCHEMAS],
        }
    if q.intent == "diary":
        start = measured.occurred_at.replace(hour=0)
        moments = notable_events(
            await context.store.care_events(context.week_id), start, start + timedelta(days=1)
        )
        payload = {
            "feature": "diary",
            "moments": [{"description": m.description, "evidence": m.evidence} for m in moments],
        }
        answer = await diary_entry(moments, context.store)
    elif q.intent == "hint":
        trouble = detect_trouble(measured.data, measured.occurred_at)
        payload = {
            "feature": "hint",
            "observation": trouble.observation,
            "help": trouble.help,
            "evidence": [measured.id],
        }
        answer = await quiet_hint(trouble, measured.id, context.store)
    else:
        # A behavior observation is distinct from an unmeasured association or a copy trial.
        payload = {
            "feature": "behaviour-why",
            "question": q.text,
            "observation": {"behaviour": "walk", "id": measured.id, "label": "歩く"},
            "context_text": f"この記録だけでは理由は断定できません {measured.id}。",
            "context_evidence": [measured.id],
        }
        from tsuyu_shiori.agent import Answer
        from tsuyu_shiori.verify import verify

        text = f"いまの脳の出力は歩く動きです {measured.id}。"
        text += f"この記録だけでは理由は断定できません {measured.id}。"
        checked = await verify(text, context.store, allowed_ids={measured.id})
        answer = Answer(checked.text, checked.evidence_ids, checked.report)
    return {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
            {"role": "assistant", "content": answer.text},
        ],
        "tools": [],
    }
