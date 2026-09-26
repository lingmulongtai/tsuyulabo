from __future__ import annotations

from random import Random

from tsuyulabo_api.domain.puzzles import pupation_site


def test_hidden_winner_and_seed() -> None:
    params, secret = pupation_site.generate(Random(42), {})
    assert pupation_site.generate(Random(42), {}) == (params, secret)
    assert set(params) == {"options", "hint"}
    assert len({o["label"] for o in params["options"]}) == 3
    assert not pupation_site.verify(params, {"choice": "x"}).valid
    for option in params["options"]:
        submission = {"choice": option["id"]}
        assert pupation_site.verify(params, submission).valid
        result = pupation_site.roll(Random(0), params, secret, submission)
        assert result["hit"] == (option["id"] == secret["winning_id"])


def test_hint_accuracy() -> None:
    rng = Random(102)
    hits = 0
    for _ in range(10000):
        _, secret = pupation_site.generate(rng, {})
        hits += secret["winning_id"] == secret["hinted_id"]
    assert 6800 <= hits <= 7200
