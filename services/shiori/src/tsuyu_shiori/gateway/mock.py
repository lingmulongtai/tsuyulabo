"""A deterministic, deliberately small Japanese template provider for offline use."""

from __future__ import annotations

import json
import re
from typing import Any

from .base import Cost, Response, ToolCall

CUES = {
    "banana": "バナナ",
    "apple_vinegar": "りんご酢",
    "yeast": "酵母",
    "grape": "ぶどう",
    "blue_light": "青い光",
}
KINDS = {
    "training": "しつけ",
    "meal": "ごはん",
    "cleaning": "そうじ",
    "temperature": "温度あわせ",
    "pupation_site": "場所えらび",
}


def cue_in(question: str) -> str | None:
    return next((cue for cue, label in CUES.items() if cue in question or label in question), None)


def citations(records: list[dict[str, Any]]) -> str:
    return " ".join(dict.fromkeys(r["id"] for r in records))


def count_records(question: str, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    selected = records
    day = re.search(r"(?:研究)?(\d+)日目", question)
    if day:
        selected = [r for r in selected if r["data"].get("research_day") == int(day[1])]
    else:
        weekday = next(
            (i for i, name in enumerate("月火水木金土日") if f"{name}曜" in question), None
        )
        if weekday is not None:
            from datetime import datetime, timedelta, timezone

            selected = [
                r
                for r in selected
                if r.get("occurred_at")
                and datetime.fromisoformat(r["occurred_at"])
                .astimezone(timezone(timedelta(hours=9)))
                .weekday()
                == weekday
            ]
    cue = cue_in(question)
    if cue:
        selected = [r for r in selected if r["data"].get("cue") == cue]
    valence = (
        "punish"
        if "罰" in question or "punish" in question
        else ("reward" if "報酬" in question or "reward" in question else None)
    )
    if valence:
        selected = [r for r in selected if r["data"].get("valence") == valence]
    kind = next(
        (kind for kind, label in KINDS.items() if kind in question or label in question), None
    )
    if kind:
        selected = [r for r in selected if r["kind"] == kind]
    return selected


class MockProvider:
    cache_namespace = "mock:v1"

    def model_for(self, purpose: str) -> str:
        return "mock-" + purpose

    async def complete(
        self, messages: list[dict[str, Any]], tools: list[dict[str, Any]], model: str
    ) -> Response:
        request = json.loads(next(m["content"] for m in messages if m["role"] == "user"))
        question = request["question"]
        results = [json.loads(m["content"]) for m in messages if m["role"] == "tool"]
        if not results:
            calls = [ToolCall("care", "get_care_events", {"week_id": request["week_id"]})]
            cue = cue_in(question)
            if cue and any(
                word in question for word in ("なぜ", "なんで", "実験", "好み", "コーチ")
            ):
                calls.extend(
                    [
                        ToolCall(
                            "association",
                            "get_association",
                            {"fly_id": request["fly_id"], "cue": cue},
                        ),
                        ToolCall(
                            "experiment",
                            "run_odor_choice",
                            {"fly_id": request["fly_id"], "cue": cue},
                        ),
                    ]
                )
            if any(
                word in question.lower() for word in ("論文", "文献", "キノコ体", "nobel", "mn9")
            ):
                calls.append(ToolCall("papers", "search_papers", {"query": question, "k": 2}))
            return self.response(messages, tool_calls=calls[:4])

        records = {r["id"]: r for result in results for r in result.get("records", [])}
        care = [r for r in records.values() if r["kind"] not in {"experiment", "association"}]
        sleeps = [r for result in results for r in result.get("sleep_sessions", [])]
        papers = [p for result in results for p in result.get("papers", [])]
        sentences: list[str] = []
        feature = request.get("feature", "answer")
        if any(word in question for word in ("何回", "回数", "件数")) and care:
            selected = count_records(question, care)
            sentences.append(f"該当する記録は{len(selected)}回です {citations(selected or care)}。")
        elif feature == "coach":
            associations = [r for r in records.values() if "value" in r["data"]]
            if associations:
                record = associations[-1]
                sentences.append(
                    f"連合値は{record['data']['value']:.2f}ですので、"
                    f"次のしつけ前後も比較して観察しましょう {record['id']}。"
                )
            elif care:
                sentences.append(
                    f"今週の{len(care)}件のお世話を手がかりに、"
                    f"次のしつけ前後も比べましょう {citations(care)}。"
                )
        else:
            if care:
                sentences.append(f"お世話の記録は{len(care)}件あります {citations(care)}。")
            if sleeps:
                sleep = sleeps[-1]
                if sleep["data"].get("hours") is not None:
                    sentences.append(
                        f"睡眠の記録は{sleep['data']['hours']:.1f}時間です {sleep['id']}。"
                    )
                else:
                    sentences.append(f"睡眠の開始が記録されています {sleep['id']}。")
            if feature == "morning" and care:
                last = care[-1]
                label = KINDS.get(last["kind"], "お世話")
                sentences.append(f"直近のお世話は{label}でした {last['id']}。")
            for record in records.values():
                data = record["data"]
                if record["kind"] == "experiment":
                    sentences.append(
                        f"コピーの実験では接近{data['toward']}回、"
                        f"回避{data['away']}回でした {record['id']}。"
                    )
                elif record["kind"] == "presentation" and "rank" in data:
                    sentences.append(f"研究発表会のランクは{data['rank']}です {record['id']}。")
        if feature not in {"coach", "morning"}:
            for paper in papers:
                summary = paper["summary"].rstrip("。")
                sentences.append(f"文献では、{summary} {paper['id']}。")
        return self.response(
            messages, text="".join(sentences[:3] if feature == "morning" else sentences)
        )

    @staticmethod
    def response(
        messages: list[dict[str, Any]], text: str = "", tool_calls: list[ToolCall] | None = None
    ) -> Response:
        # Mock tokens are a reproducible character-based estimate, not vendor tokenization.
        count = max(1, len(json.dumps(messages, ensure_ascii=False)) // 4)
        output = max(1, len(text) // 4 + len(tool_calls or []) * 12)
        return Response(text, tool_calls or [], Cost(count, output))
