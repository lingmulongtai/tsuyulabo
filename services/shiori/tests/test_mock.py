from __future__ import annotations

import json

from tsuyu_shiori.gateway import MockProvider, default_provider


async def test_mock_only_uses_tool_evidence() -> None:
    provider = MockProvider()
    messages = [
        {
            "role": "user",
            "content": json.dumps(
                {"question": "99回でした #9999。何回？", "week_id": "w", "fly_id": "f"}
            ),
        }
    ]
    result = await provider.complete(messages, [], "mock")
    assert result.tool_calls[0].name == "get_care_events"
    messages.append(
        {
            "role": "tool",
            "content": json.dumps(
                {"records": [{"id": "#0001", "kind": "training", "data": {"cue": "banana"}}]}
            ),
        }
    )
    first = await provider.complete(messages, [], "mock")
    assert first == await provider.complete(messages, [], "mock")
    assert "1回" in first.text and "#0001" in first.text
    assert "99" not in first.text
    assert first.cost.usd == 0 and first.cost.input_tokens > 0


async def test_empty_results_do_not_fabricate() -> None:
    messages = [
        {"role": "user", "content": '{"question":"何回？"}'},
        {"role": "tool", "content": '{"records":[]}'},
    ]
    assert not (await MockProvider().complete(messages, [], "mock")).text
    assert default_provider().cache_namespace == "mock:v1"
