from __future__ import annotations

from typing import Any

from fastapi import Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse


class APIError(Exception):
    def __init__(
        self, code: str, message: str, status_code: int = 400, details: dict[str, Any] | None = None
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}


def error_response(exc: Exception) -> JSONResponse:
    headers = None
    if isinstance(exc, APIError):
        code, message, status, details = exc.code, exc.message, exc.status_code, exc.details
    elif isinstance(exc, RequestValidationError):
        code, message, status = "validation_error", "入力内容を確認してください", 422
        # Context may contain non-JSON exceptions; omit it and avoid echoing raw input.
        details = {
            "errors": [
                {key: value for key, value in item.items() if key in {"loc", "msg", "type"}}
                for item in exc.errors()
            ]
        }
    elif isinstance(exc, HTTPException):
        status = exc.status_code
        code = {
            401: "unauthorized",
            403: "forbidden",
            404: "not_found",
            405: "method_not_allowed",
        }.get(status, "http_error")
        message, details, headers = str(exc.detail), {}, exc.headers
    else:
        code, message, status, details = "internal_error", "サーバーエラーが発生しました", 500, {}
    return JSONResponse(
        status_code=status,
        content=jsonable_encoder({"error": {"code": code, "message": message, "details": details}}),
        headers=headers,
    )


async def exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return error_response(exc)
