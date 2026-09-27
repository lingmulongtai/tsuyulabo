from __future__ import annotations

from threading import Thread
from unittest.mock import AsyncMock
from urllib.error import HTTPError
from urllib.request import urlopen

import pytest

from infra.cloudrun import worker_service


@pytest.mark.asyncio
async def test_readiness_tracks_successful_startup_and_shutdown(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    worker_service.ready.clear()
    start = AsyncMock(side_effect=RuntimeError("database unavailable"))
    stop = AsyncMock()
    monkeypatch.setattr(worker_service.WorkerSettings, "on_startup", start)
    monkeypatch.setattr(worker_service.WorkerSettings, "on_shutdown", stop)
    with pytest.raises(RuntimeError):
        await worker_service.startup({})
    assert not worker_service.ready.is_set()
    start.side_effect = None
    await worker_service.startup({})
    assert worker_service.ready.is_set()
    await worker_service.shutdown({})
    assert not worker_service.ready.is_set()
    stop.assert_awaited_once()


def test_http_probe_returns_unavailable_until_worker_starts() -> None:
    worker_service.ready.clear()
    server = worker_service.ThreadingHTTPServer(("127.0.0.1", 0), worker_service.HealthHandler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    url = f"http://127.0.0.1:{server.server_port}"
    try:
        with pytest.raises(HTTPError) as error:
            urlopen(url + "/healthz", timeout=2)
        assert error.value.code == 503
        worker_service.ready.set()
        with urlopen(url + "/healthz", timeout=2) as response:
            assert response.status == 200
            assert response.read() == b"ok\n"
        with pytest.raises(HTTPError) as error:
            urlopen(url + "/", timeout=2)
        assert error.value.code == 404
    finally:
        worker_service.ready.clear()
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()
