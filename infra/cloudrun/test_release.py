from __future__ import annotations

import subprocess
from unittest.mock import Mock

import pytest

from infra.cloudrun import release


def test_migration_finishes_before_worker_and_api_are_deployed() -> None:
    args = release.parser().parse_args(
        [
            "deploy",
            "--project=test-project",
            "--tag=abc123",
            "--cors-origin=https://tsuyu.vercel.app",
            "--cors-origin=https://demo.example.com",
        ]
    )
    plan = release.commands(args)
    assert plan[0][1:5] == ["run", "jobs", "deploy", "tsuyulabo-migrate"]
    assert "--args=-c,services/api/alembic.ini,upgrade,head" in plan[0]
    assert "--wait" in plan[1]
    assert plan[2][3] == "tsuyulabo-worker"
    assert {"--no-cpu-throttling", "--min=1", "--max=1"} <= set(plan[2])
    assert plan[3][3] == "tsuyulabo-api"
    env = next(arg for arg in plan[3] if arg.startswith("--set-env-vars="))
    assert '@CORS_ORIGINS=["https://tsuyu.vercel.app","https://demo.example.com"]' in env
    assert "TSUYU_DEV_TOOLS=0" in env
    assert not any("API_KEY=" in arg for command in plan for arg in command)


def test_failure_stops_release_and_dry_run_has_no_side_effects(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    execute = Mock(side_effect=subprocess.CalledProcessError(1, "gcloud"))
    monkeypatch.setattr(release.shutil, "which", lambda name: name)
    monkeypatch.setattr(release.subprocess, "run", execute)
    plan = [["gcloud", "migrate"], ["gcloud", "deploy"]]
    release.run(plan, execute=False)
    execute.assert_not_called()
    with pytest.raises(subprocess.CalledProcessError):
        release.run(plan, execute=True)
    assert execute.call_count == 1


def test_build_pushes_only_final_api_and_worker_images() -> None:
    args = release.parser().parse_args(["build", "--project=test-project", "--tag=abc123"])
    plan = release.commands(args)
    pushes = [cmd[-1] for cmd in plan if cmd[:2] == ["docker", "push"]]
    assert pushes == [
        "asia-northeast1-docker.pkg.dev/test-project/tsuyulabo/api:abc123",
        "asia-northeast1-docker.pkg.dev/test-project/tsuyulabo/worker:abc123",
    ]
    assert all("--platform=linux/amd64" in cmd for cmd in plan if cmd[:2] == ["docker", "build"])


def test_deploy_requires_cors_and_maps_optional_provider_secret() -> None:
    args = release.parser().parse_args(["deploy", "--project=test-project", "--tag=abc123"])
    with pytest.raises(ValueError, match="cors-origin"):
        release.commands(args)
    args.cors_origin = ["https://tsuyu.vercel.app"]
    args.shiori_provider = "anthropic"
    plan = release.commands(args)
    assert any("ANTHROPIC_API_KEY=tsuyulabo-anthropic-api-key:1" in arg for arg in plan[-1])


@pytest.mark.parametrize(
    "value", ["http://localhost:3000", "https://a/", "https://a@b", "https://a,b"]
)
def test_rejects_ambiguous_cors_origins(value: str) -> None:
    with pytest.raises(SystemExit):
        release.parser().parse_args(
            [
                "deploy",
                "--project=test-project",
                "--tag=abc123",
                f"--cors-origin={value}",
            ]
        )
