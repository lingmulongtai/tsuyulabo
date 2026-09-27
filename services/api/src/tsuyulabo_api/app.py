from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Mapping
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from redis.asyncio import Redis
from sqlalchemy import text
from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse

from tsuyulabo_api.auth.provider import AuthProvider, GuestAuthProvider
from tsuyulabo_api.brain_adapter import BrainAdapter
from tsuyulabo_api.db.session import create_engine, session_factory
from tsuyulabo_api.errors import APIError, exception_handler
from tsuyulabo_api.routers import (
    adults,
    brain,
    clock,
    daily_circuit,
    dev,
    friends,
    home,
    inventory,
    jobs,
    odds,
    push,
    puzzles,
    races,
    shiori,
    sleep,
    team,
    users,
    weeks,
    zukan,
)
from tsuyulabo_api.services.clock import Clock, SystemClock
from tsuyulabo_api.services.experiments import handler as experiment_handler
from tsuyulabo_api.services.idempotency import IdempotentRoute
from tsuyulabo_api.services.jobs import (
    ArqJobQueue,
    BrainClient,
    InlineJobQueue,
    JobFunction,
    JobQueue,
)
from tsuyulabo_api.services.maze_race import handler as maze_handler
from tsuyulabo_api.services.shiori import handler as shiori_handler
from tsuyulabo_api.settings import Settings


def create_app(
    settings: Settings | None = None,
    *,
    clock_source: Clock | None = None,
    auth_provider: AuthProvider | None = None,
    brain_handlers: Mapping[str, JobFunction] | None = None,
    brain_adapter: BrainAdapter | None = None,
) -> FastAPI:
    settings = settings or Settings()
    if settings.brain_mode == "queue" and not settings.redis_url:
        raise ValueError("REDIS_URL is required when BRAIN_MODE=queue")
    engine = create_engine(settings.database_url)
    sessions = session_factory(engine)
    adapter = brain_adapter or BrainAdapter()
    handlers = {
        "brain.experiment": experiment_handler(sessions, adapter),
        "brain.maze_run": maze_handler(),
        "shiori.answer": shiori_handler(sessions),
    } | dict(brain_handlers or {})
    redis = (
        Redis.from_url(settings.redis_url, socket_connect_timeout=1, socket_timeout=1)
        if settings.redis_url
        else None
    )
    queue: JobQueue = (
        ArqJobQueue(settings.redis_url)
        if settings.brain_mode == "queue"
        else InlineJobQueue(sessions, handlers)
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        try:
            yield
        finally:
            pending = tuple(getattr(app.state, "pending_calculations", ()))
            for task in pending:
                task.cancel()
            if pending:
                await asyncio.gather(*pending, return_exceptions=True)
            await queue.close()
            if redis is not None:
                await redis.aclose()
            await engine.dispose()

    app = FastAPI(title="Tsuyu Labo API", version="0.1.0", lifespan=lifespan)
    app.router.route_class = IdempotentRoute
    app.state.settings = settings
    app.state.engine = engine
    app.state.session_factory = sessions
    app.state.clock = clock_source or SystemClock()
    app.state.auth_provider = auth_provider or GuestAuthProvider(
        settings.jwt_secret.get_secret_value()
    )
    app.state.redis = redis
    app.state.job_queue = queue
    app.state.brain_client = BrainClient(sessions, queue)
    app.state.brain_adapter = adapter
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "Idempotency-Key"],
    )
    for exception in (APIError, RequestValidationError, HTTPException, Exception):
        app.add_exception_handler(exception, exception_handler)

    @app.get("/healthz")
    async def health() -> JSONResponse:
        async def database_status() -> str:
            try:
                async with engine.connect() as connection:
                    await connection.execute(text("SELECT 1"))
                return "ok"
            except Exception:
                return "error"

        async def redis_status() -> str:
            if app.state.redis is None:
                return "disabled"
            try:
                await app.state.redis.ping()
                return "ok"
            except Exception:
                return "error"

        database, cache = await asyncio.gather(database_status(), redis_status())
        healthy = "error" not in (database, cache)
        return JSONResponse(
            {"status": "ok" if healthy else "error", "database": database, "redis": cache},
            status_code=200 if healthy else 503,
        )

    for router in (
        users.router,
        clock.router,
        dev.router,
        jobs.router,
        weeks.router,
        puzzles.router,
        daily_circuit.router,
        races.router,
        adults.router,
        team.router,
        inventory.router,
        sleep.router,
        home.router,
        friends.router,
        zukan.router,
        odds.router,
        push.router,
        brain.router,
        shiori.router,
    ):
        app.include_router(router)
    return app
