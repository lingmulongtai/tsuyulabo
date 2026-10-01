from __future__ import annotations

import json
from dataclasses import dataclass, field, replace
from typing import Any

from tsuyu_shiori.gateway import Cost, MockProvider, Provider, default_provider
from tsuyu_shiori.tools import SCHEMAS, ToolContext, execute
from tsuyu_shiori.verify import VerificationReport, verify

from .prompt import SYSTEM_PROMPT


@dataclass(frozen=True)
class Answer:
    text: str
    evidence_ids: list[str]
    verification: VerificationReport
    calls: list[Cost] = field(default_factory=list)
    experiments: list[str] = field(default_factory=list)
    steps: int = 0
    stopped_reason: str = "final"
    fallback_used: bool = False
    empty_state: bool = False
    provider_text: str = ""
    provider_verification: VerificationReport | None = None
    ai_label: str = "AI"
    disclaimer: str = "ゲーム内のモデルで測った結果です"

    @property
    def cost(self) -> dict[str, Any]:
        return {
            "usd": sum(call.usd for call in self.calls),
            "input_tokens": sum(call.input_tokens for call in self.calls),
            "output_tokens": sum(call.output_tokens for call in self.calls),
            "cache_hits": sum(call.cached for call in self.calls),
            "calls": [call.to_dict() for call in self.calls],
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "answer": self.text,
            "evidence": self.evidence_ids,
            "verification": self.verification.to_dict(),
            "cost": self.cost,
            "experiments": self.experiments,
            "steps": self.steps,
            "stopped_reason": self.stopped_reason,
            "fallback_used": self.fallback_used,
            "empty_state": self.empty_state,
            "provider_text": self.provider_text,
            "provider_verification": (self.provider_verification or self.verification).to_dict(),
            "ai_label": self.ai_label,
            "disclaimer": self.disclaimer,
        }


async def run_agent(
    question: str,
    context: ToolContext,
    *,
    provider: Provider | None = None,
    feature: str = "answer",
    purpose: str = "qa",
    max_steps: int = 4,
    max_sentences: int | None = None,
    _allow_fallback: bool = True,
    _tool_results: dict[str, dict[str, Any]] | None = None,
) -> Answer:
    if not 1 <= max_steps <= 4:
        raise ValueError("max_steps must be between 1 and 4")
    if not question.strip() or len(question) > 4000:
        raise ValueError("question must contain between 1 and 4000 characters")
    provider = provider if provider is not None else default_provider()
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": json.dumps(
                {
                    "question": question,
                    "feature": feature,
                    "week_id": context.week_id,
                    "fly_id": context.fly_id,
                },
                ensure_ascii=False,
            ),
        },
    ]
    costs: list[Cost] = []
    allowed_ids: set[str] = set()
    paper_ids: set[str] = set()
    experiments: list[str] = []
    # Repeated identical tool calls reuse results, especially persisted experiments.
    tool_results = _tool_results if _tool_results is not None else {}
    retrieved = False
    text, stopped = "", "step_limit"
    for step in range(1, max_steps + 1):
        final_step = step == max_steps
        if final_step:
            messages.append(
                {"role": "system", "content": "ここで終了です。既存の根拠だけで答えてください。"}
            )
        response = await provider.complete(
            messages, [] if final_step else SCHEMAS, provider.model_for(purpose)
        )
        costs.append(response.cost)
        if not response.tool_calls and not retrieved and not final_step:
            messages.append(
                {
                    "role": "assistant",
                    "content": response.text,
                    "continuation": response.continuation,
                }
            )
            messages.append(
                {
                    "role": "system",
                    "content": "記録未取得です。質問に必要な記録ツールを呼んでください。"
                    "回数にはcount_care_events、観察にはget_care_events、"
                    "好みにはget_associationやrun_odor_choiceを使います。",
                }
            )
            continue
        if not response.tool_calls:
            text, stopped = response.text, "final"
            break
        if final_step:
            # Never execute a tool after exhausting the step budget.
            break
        messages.append(
            {"role": "assistant", "content": response.text, "continuation": response.continuation}
        )
        # Bound fan-out as well as round trips, and return a result for every call ID.
        for index, call in enumerate(response.tool_calls):
            key = json.dumps([call.name, call.arguments], sort_keys=True)
            result: dict[str, Any]
            if index >= 4:
                result = {"error": "tool_call_limit"}
            elif key in tool_results:
                result = tool_results[key]
            else:
                try:
                    result = await execute(context, call.name, call.arguments)
                except (ValueError, KeyError):
                    result = {"error": "invalid_tool_arguments_or_missing_record"}
                tool_results[key] = result
            retrieved = retrieved or (
                "error" not in result
                and call.name
                in {"get_care_events", "count_care_events", "get_association", "run_odor_choice"}
            )
            allowed_ids.update(result.get("ids", []))
            for record in result.get("records", []) + result.get("sleep_sessions", []):
                allowed_ids.add(record["id"])
                if record["kind"] == "experiment" and record["id"] not in experiments:
                    experiments.append(record["id"])
            for paper in result.get("papers", []):
                allowed_ids.add(paper["id"])
                paper_ids.add(paper["id"])
            messages.append(
                {
                    "role": "tool",
                    "call_id": call.id,
                    "name": call.name,
                    "content": json.dumps(result, ensure_ascii=False),
                }
            )
    verified = await verify(text, context.store, allowed_ids=allowed_ids, paper_ids=paper_ids)
    if max_sentences is not None:
        from tsuyu_shiori.verify import extract_ids, split_sentences

        text = "".join(split_sentences(verified.text)[:max_sentences])
        evidence = extract_ids(text)
    else:
        text, evidence = verified.text, verified.evidence_ids
    if not text and _allow_fallback:
        if tool_results and all("error" in result for result in tool_results.values()):
            # Keep failed boundary checks authoritative. Recovery must not broaden a
            # rejected request into a fresh retrieval or a copy experiment.
            response = await MockProvider().complete(messages, [], "mock-" + purpose)
            recovery = await verify(response.text, context.store, allowed_ids=allowed_ids)
            fallback = Answer(
                recovery.text or "参照できる記録がありません。今週の記録について質問してください。",
                recovery.evidence_ids,
                recovery.report,
                empty_state=not recovery.text,
            )
        else:
            fallback = await run_agent(
                question,
                context,
                provider=MockProvider(),
                feature=feature,
                purpose=purpose,
                max_sentences=max_sentences,
                _allow_fallback=False,
                _tool_results=tool_results,
            )
        return replace(
            fallback,
            calls=costs,
            experiments=list(dict.fromkeys(experiments + fallback.experiments)),
            steps=step,
            stopped_reason="fallback",
            fallback_used=True,
            provider_text=verified.text,
            provider_verification=verified.report,
        )
    empty_state = not text
    if empty_state:
        # UI status, not an explanation about the fly: never invent an evidence ID.
        text = "確認できる記録がありません。お世話の記録を残してから、もう一度質問してください。"
    return Answer(
        text,
        evidence,
        verified.report,
        costs,
        experiments,
        step,
        stopped,
        empty_state=empty_state,
        provider_text=verified.text,
        provider_verification=verified.report,
    )
