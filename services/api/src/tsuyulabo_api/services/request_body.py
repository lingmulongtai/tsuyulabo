"""Bound mutation bodies before parsing, hashing or opening a database transaction."""

from __future__ import annotations

import json
import math

from fastapi import Request
from tsuyulabo_api.errors import APIError

MAX_BODY_BYTES = 65_536


def finite_number(value: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError("nonfinite number")
    return number


async def read_body(request: Request) -> bytes:
    body = bytearray()
    async for chunk in request.stream():
        if len(body) + len(chunk) > MAX_BODY_BYTES:
            raise APIError("payload_too_large", "入力が大きすぎます", 413)
        body.extend(chunk)
    # Starlette's body cache lets FastAPI consume the already bounded stream.
    request._body = bytes(body)
    if body:
        try:
            request._json = json.loads(
                body, parse_constant=finite_number, parse_float=finite_number
            )
        except (ValueError, UnicodeError, RecursionError) as exc:
            raise APIError("validation_error", "JSON の入力内容を確認してください", 422) from exc
    return request._body
