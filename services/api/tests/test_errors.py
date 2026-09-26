from __future__ import annotations

import json

from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
from tsuyulabo_api.errors import APIError, error_response


def test_error_envelopes() -> None:
    cases = [
        (APIError("insufficient_funds", "no funds", 409), 409, "insufficient_funds"),
        (HTTPException(404, "missing"), 404, "not_found"),
        (RuntimeError("private detail"), 500, "internal_error"),
        (
            RequestValidationError(
                [
                    {
                        "loc": ["body"],
                        "msg": "invalid",
                        "type": "value_error",
                        "ctx": {"error": ValueError("bad")},
                    }
                ]
            ),
            422,
            "validation_error",
        ),
    ]
    for exception, status, code in cases:
        response = error_response(exception)
        error = json.loads(response.body)["error"]
        assert response.status_code == status
        assert set(error) == {"code", "message", "details"}
        assert error["code"] == code
        assert b"private detail" not in response.body
