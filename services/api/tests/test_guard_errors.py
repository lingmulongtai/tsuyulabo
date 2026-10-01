from __future__ import annotations

import pytest
from tsuyulabo_api.errors import APIError, error_response


@pytest.mark.parametrize(("code", "status"), [("rate_limited", 429), ("server_busy", 503)])
def test_retry_header(code: str, status: int) -> None:
    response = error_response(APIError(code, "少し待ってね", status, {"retry_after": 10}))
    assert response.status_code == status
    assert response.headers["retry-after"] == "10"
