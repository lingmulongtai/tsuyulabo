"""A deterministic, deliberately small Japanese template provider for offline use."""

from __future__ import annotations

import json
import re
from typing import Any

from .base import Cost, Response, ToolCall
from .topics import CUES, KINDS, citations, compact, cue_in, newest, observations, topic_in


def count_records(question: str, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    selected = records
    day = re.search(r"(?:研究)?(\d+)日目", question)
    if day:
        selected = [
            r
            for r in selected
            if r.get("research_day", r["data"].get("research_day")) == int(day[1])
        ]
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
        else ("reward" if any(w in question for w in ("報酬", "reward", "ごほうび")) else None)
    )
    if valence:
        selected = [r for r in selected if r["data"].get("valence") == valence]
    kind = topic_in(question)
    if cue and kind is None:
        kind = "training"
    if kind:
        selected = [r for r in selected if r["kind"] == kind]
    if "大成功" in question:
        selected = [r for r in selected if r["data"].get("great_success") is True]
    return selected


class MockProvider:
    cache_namespace = "mock:v2"

    def model_for(self, purpose: str) -> str:
        return "mock-" + purpose

    async def complete(
        self, messages: list[dict[str, Any]], tools: list[dict[str, Any]], model: str
    ) -> Response:
        request = json.loads(next(m["content"] for m in messages if m["role"] == "user"))
        question = request["question"]
        counting = any(word in question for word in ("何回", "回数", "件数"))
        results = [json.loads(m["content"]) for m in messages if m["role"] == "tool"]
        weekday = any(f"{day}曜" in question for day in "月火水木金土日")
        if not results:
            topic = topic_in(question)
            arguments: dict[str, Any] = {"week_id": request["week_id"]}
            if topic and request.get("feature", "answer") == "answer":
                arguments["kinds"] = [topic]
            if counting:
                day = re.search(r"(?:研究)?(\d+)日目", question)
                if day:
                    arguments["research_day"] = int(day[1])
                cue = cue_in(question)
                if cue:
                    arguments["cue"] = cue
                if "罰" in question or "punish" in question:
                    arguments["valence"] = "punish"
                elif any(w in question for w in ("報酬", "reward", "ごほうび")):
                    arguments["valence"] = "reward"
                if not topic:
                    arguments["kinds"] = [
                        "training",
                        "meal",
                        "cleaning",
                        "temperature",
                        "pupation_site",
                        "eclosion",
                        "presentation",
                    ]
            if "いちばん多" in question:
                return self.response(
                    messages,
                    tool_calls=[
                        ToolCall(
                            cue,
                            "count_care_events",
                            {"week_id": request["week_id"], "kinds": ["training"], "cue": cue},
                        )
                        for cue in CUES
                    ][:4],
                )
            calls = [
                ToolCall(
                    "care",
                    "count_care_events" if counting and not weekday else "get_care_events",
                    arguments,
                )
            ]
            cue = cue_in(question)
            if cue and topic_in(question) == "training" and not counting:
                calls.extend(self.measure(request["fly_id"], cue))
            if any(
                word in question.lower() for word in ("論文", "文献", "キノコ体", "nobel", "mn9")
            ):
                calls.append(ToolCall("papers", "search_papers", {"query": question, "k": 2}))
            return self.response(messages, tool_calls=calls[:4])

        counts = [result for result in results if "count" in result]
        if counts and counting:
            result = counts[0]
            refs = " ".join(result["ids"][:2])
            return self.response(
                messages,
                text=compact(
                    [
                        f"該当する記録は{result['count']}回です {refs}。",
                        f"この回数は確認できた記録の範囲です {refs}。",
                    ]
                ),
            )
        if counts and "いちばん多" in question:
            missing = [cue for cue in CUES if cue not in {r["filters"]["cue"] for r in counts}]
            if missing and tools:
                return self.response(
                    messages,
                    tool_calls=[
                        ToolCall(
                            cue,
                            "count_care_events",
                            {"week_id": request["week_id"], "kinds": ["training"], "cue": cue},
                        )
                        for cue in missing
                    ],
                )
            result = max(counts, key=lambda r: r["count"])
            cue = result["filters"]["cue"]
            refs = " ".join(result["ids"][:2])
            return self.response(
                messages,
                text=compact(
                    [f"比較したしつけでは{CUES[cue]}が最多で{result['count']}回です {refs}。"]
                ),
            )
        # Association results may reuse a training ID; preserve both views of the record.
        records = [r for result in results for r in result.get("records", [])]
        care = list(
            {r["id"]: r for r in records if r["kind"] not in {"experiment", "association"}}.values()
        )
        sleeps = [r for result in results for r in result.get("sleep_sessions", [])]
        papers = [p for result in results for p in result.get("papers", [])]
        if not care and not sleeps and not records and tools and not counts:
            return self.response(
                messages,
                tool_calls=[
                    ToolCall(
                        "inspected",
                        "count_care_events",
                        {"week_id": request["week_id"], "kinds": [topic_in(question)]},
                    )
                ],
            )
        if not records and not sleeps and counts:
            refs = " ".join(counts[0]["ids"][:1])
            label = KINDS.get(topic_in(question), "お世話")
            return self.response(
                messages,
                text=compact(
                    [
                        f"確認した今週の記録には、{label}の該当記録がありません {refs}。",
                        f"次は{label}の記録を残してから、一緒に確かめましょう {refs}。",
                    ]
                ),
            )
        sentences: list[str] = []
        feature = request.get("feature", "answer")
        if feature == "answer" and topic_in(question) == "training" and not counting:
            measured = any(m.get("name") == "get_association" for m in messages)
            cue = cue_in(question) or next(
                (
                    r["data"]["cue"]
                    for r in newest(care)
                    if r["kind"] == "training" and r["data"].get("cue") in CUES
                ),
                None,
            )
            if cue and not measured and tools:
                return self.response(messages, tool_calls=self.measure(request["fly_id"], cue))
        if counting and weekday and any(r.get("truncated") for r in results):
            return self.response(
                messages,
                text=compact(
                    [
                        "取得した一覧は一部のため、曜日別の全件数はこの結果だけでは確認できません "
                        f"{citations(care + sleeps, 1)}。"
                    ]
                ),
            )
        if counting and (care or sleeps):
            selected = count_records(question, sleeps if topic_in(question) == "sleep" else care)
            evidence = selected or care + sleeps
            refs = citations(evidence, 1 if any(r["kind"] == "sleep" for r in evidence) else 2)
            sentences.append(f"該当する記録は{len(selected)}回です {refs}。")
            if selected:
                sentences.append(f"この回数は確認できた記録の範囲です {citations(selected, 1)}。")
            else:
                sentences.append(
                    "該当するお世話の記録を残して、また確かめましょう "
                    f"{citations(care + sleeps, 1)}。"
                )
        elif feature == "coach":
            associations = [r for r in records if "value" in r["data"]]
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
        elif feature == "answer":
            observed = observations(question, care, sleeps, records)
            if any(r.get("truncated") for r in results):
                # A capped view supports measurements, not a week's exact frequency.
                observed = [s for s in observed if "回の記録" not in s and "回記録" not in s]
            sentences.extend(observed)
        else:
            if care:
                sentences.append(f"確認したお世話の記録は{len(care)}件あります {citations(care)}。")
            if sleeps:
                sleep = newest(sleeps)[0]
                if sleep["data"].get("hours") is not None:
                    sentences.append(
                        f"睡眠の記録は{sleep['data']['hours']:.1f}時間です {sleep['id']}。"
                    )
                else:
                    sentences.append(f"睡眠の開始が記録されています {sleep['id']}。")
            if feature == "morning" and care:
                last = newest(care)[0]
                label = KINDS.get(last["kind"], "お世話")
                sentences.append(f"直近のお世話は{label}でした {last['id']}。")
            for record in records:
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
                sentences.insert(0, f"文献では、{summary} {paper['id']}。")
        return self.response(messages, text=compact(sentences))

    @staticmethod
    def measure(fly_id: str, cue: str) -> list[ToolCall]:
        return [
            ToolCall("association", "get_association", {"fly_id": fly_id, "cue": cue}),
            ToolCall("experiment", "run_odor_choice", {"fly_id": fly_id, "cue": cue, "trials": 20}),
        ]

    @staticmethod
    def response(
        messages: list[dict[str, Any]], text: str = "", tool_calls: list[ToolCall] | None = None
    ) -> Response:
        # Mock tokens are a reproducible character-based estimate, not vendor tokenization.
        count = max(1, len(json.dumps(messages, ensure_ascii=False)) // 4)
        output = max(1, len(text) // 4 + len(tool_calls or []) * 12)
        return Response(text, tool_calls or [], Cost(count, output))
