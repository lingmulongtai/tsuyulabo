"""Expose arq startup readiness on Cloud Run's PORT; keep arq in the main thread."""

from __future__ import annotations

import logging
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Event, Thread
from typing import Any

from arq.worker import run_worker
from tsuyu_worker.main import WorkerSettings

ready = Event()


async def startup(ctx: dict[str, Any]) -> None:
    await WorkerSettings.on_startup(ctx)
    ready.set()


async def shutdown(ctx: dict[str, Any]) -> None:
    ready.clear()
    await WorkerSettings.on_shutdown(ctx)


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        status = 404 if self.path != "/healthz" else (200 if ready.is_set() else 503)
        body = b"ok\n" if status == 200 else b"not ready\n"
        self.send_response(status)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: Any) -> None:
        # Cloud Run already records probe failures; avoid per-probe application logs.
        pass


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    server = ThreadingHTTPServer(("0.0.0.0", int(os.environ.get("PORT", "8080"))), HealthHandler)
    Thread(target=server.serve_forever, daemon=True).start()
    try:
        # Cloud Run grants 10 seconds after SIGTERM. Leave time for connection cleanup.
        # Limit concurrency and polling to reduce memory and metered Redis commands.
        run_worker(
            WorkerSettings,
            on_startup=startup,
            on_shutdown=shutdown,
            job_completion_wait=8,
            max_jobs=2,
            poll_delay=1,
        )
    finally:
        ready.clear()
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    main()
