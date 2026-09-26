from __future__ import annotations

from fastapi import APIRouter, FastAPI
from fastapi.exceptions import RequestValidationError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from starlette.exceptions import HTTPException
from tsuyulabo_api.auth.provider import GuestAuthProvider
from tsuyulabo_api.errors import APIError, exception_handler
from tsuyulabo_api.services.clock import SystemClock
from tsuyulabo_api.settings import Settings


def router_app(sessions: async_sessionmaker[AsyncSession], *routers: APIRouter) -> FastAPI:
    app = FastAPI()
    app.state.settings = Settings(dev_tools=True, _env_file=None)
    app.state.session_factory = sessions
    app.state.clock = SystemClock()
    app.state.auth_provider = GuestAuthProvider("test-secret-with-at-least-32-characters")
    for exception in (APIError, RequestValidationError, HTTPException):
        app.add_exception_handler(exception, exception_handler)
    for router in routers:
        app.include_router(router)
    return app
