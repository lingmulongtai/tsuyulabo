from __future__ import annotations

import pytest
from pydantic import ValidationError
from tsuyu_worker.config import WorkerConfig
from tsuyu_worker.main import WorkerSettings


def test_worker_default_and_timeout() -> None:
    assert WorkerConfig(_env_file=None).max_jobs == 2
    assert WorkerSettings.max_jobs == 2
    assert WorkerSettings.job_timeout == 180


def test_worker_concurrency_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WORKER_MAX_JOBS", "3")
    assert WorkerConfig(_env_file=None).max_jobs == 3
    monkeypatch.setenv("WORKER_MAX_JOBS", "0")
    with pytest.raises(ValidationError):
        WorkerConfig(_env_file=None)
