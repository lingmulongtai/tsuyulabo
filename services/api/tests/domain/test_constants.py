from __future__ import annotations

from tsuyulabo_api.domain import constants as c


def test_tables_are_complete() -> None:
    assert all(sum(row) == 100 for row in c.ODDS.values())
    assert set(c.SHAPES) == set(c.SHAPE_WEIGHTS)
    assert len(c.SHAPES) == 18
    assert all(len(cells) == len(set(cells)) for cells in c.SHAPES.values())
    assert set(c.CUES) == set(c.SKILL_UNLOCKS)
    assert all(set(table) == set(c.VALENCES) for table in c.SKILL_UNLOCKS.values())
    assert len(c.TRAITS) == 8
    assert len(c.SUBSKILLS) == 7
    assert len(c.REASON_CODES) == 13
    assert not set("0O1I") & set(c.FRIEND_CODE_ALPHABET)
