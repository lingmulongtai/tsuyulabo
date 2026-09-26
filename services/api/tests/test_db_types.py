from __future__ import annotations

from datetime import UTC, datetime

import pytest
from sqlalchemy.dialects import postgresql, sqlite
from tsuyulabo_api.db.base import Embedding, UTCDateTime


def test_utc_datetime_and_vector_portability() -> None:
    timestamp = UTCDateTime()
    naive = datetime(2026, 1, 1)
    assert timestamp.process_result_value(naive, sqlite.dialect()) == naive.replace(tzinfo=UTC)
    with pytest.raises(ValueError, match="timezone-aware"):
        timestamp.process_bind_param(naive, sqlite.dialect())
    assert str(Embedding().compile(dialect=sqlite.dialect())) == "JSON"
    assert str(Embedding().compile(dialect=postgresql.dialect())) == "VECTOR(384)"
