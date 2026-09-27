"""Build/push images or migrate/deploy Cloud Run. Dry-run unless --execute is given."""

from __future__ import annotations

import argparse
import json
import re
import shlex
import shutil
import subprocess
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[2]


def identifier(value: str) -> str:
    if not re.fullmatch(r"[a-z][a-z0-9-]*", value):
        raise argparse.ArgumentTypeError("use lower-case letters, digits and hyphens")
    return value


def image_tag(value: str) -> str:
    if not re.fullmatch(r"[a-zA-Z0-9_][a-zA-Z0-9_.-]{0,127}", value):
        raise argparse.ArgumentTypeError("invalid Docker tag")
    return value


def origin(value: str) -> str:
    parsed = urlsplit(value)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.path
        or parsed.query
        or parsed.fragment
        or any(char in value for char in "@,\n\r ")
    ):
        raise argparse.ArgumentTypeError("use an HTTPS origin without a path or trailing slash")
    return value


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("action", choices=["build", "deploy"])
    result.add_argument("--project", required=True, type=identifier)
    result.add_argument("--region", default="asia-northeast1", type=identifier)
    result.add_argument("--repository", default="tsuyulabo", type=identifier)
    result.add_argument("--tag", required=True, type=image_tag)
    result.add_argument("--cors-origin", action="append", type=origin, default=[])
    result.add_argument("--secret-version", default="1", type=lambda value: str(int(value)))
    result.add_argument(
        "--shiori-provider", choices=["mock", "openai", "anthropic"], default="mock"
    )
    result.add_argument("--execute", action="store_true")
    return result


def commands(args: argparse.Namespace) -> list[list[str]]:
    registry = f"{args.region}-docker.pkg.dev/{args.project}/{args.repository}"
    api = f"{registry}/api:{args.tag}"
    worker = f"{registry}/worker:{args.tag}"
    if args.action == "build":
        base = f"tsuyulabo-worker-base:{args.tag}"
        return [
            ["gcloud", "auth", "configure-docker", f"{args.region}-docker.pkg.dev", "--quiet"],
            [
                "docker",
                "build",
                "--platform=linux/amd64",
                "-f",
                "services/api/Dockerfile",
                "-t",
                api,
                ".",
            ],
            [
                "docker",
                "build",
                "--platform=linux/amd64",
                "-f",
                "services/worker/Dockerfile",
                "-t",
                base,
                ".",
            ],
            [
                "docker",
                "build",
                "--platform=linux/amd64",
                "-f",
                "infra/cloudrun/worker.Dockerfile",
                "--build-arg",
                f"WORKER_BASE={base}",
                "-t",
                worker,
                ".",
            ],
            ["docker", "push", api],
            ["docker", "push", worker],
        ]

    if not args.cors_origin:
        raise ValueError("deploy requires at least one --cors-origin")
    if int(args.secret_version) < 1:
        raise ValueError("--secret-version must be a positive, enabled Secret Manager version")
    scope = [f"--project={args.project}", f"--region={args.region}", "--quiet"]
    runtime = f"--service-account=tsuyulabo-runtime@{args.project}.iam.gserviceaccount.com"
    database = f"DATABASE_URL=tsuyulabo-database-url:{args.secret_version}"
    secrets = ",".join(
        [
            database,
            f"REDIS_URL=tsuyulabo-redis-url:{args.secret_version}",
            f"JWT_SECRET=tsuyulabo-jwt-secret:{args.secret_version}",
        ]
    )
    if args.shiori_provider != "mock":
        secrets += (
            f",{args.shiori_provider.upper()}_API_KEY="
            f"tsuyulabo-{args.shiori_provider}-api-key:{args.secret_version}"
        )
    cors = json.dumps(args.cors_origin, separators=(",", ":"))
    env = (
        "--set-env-vars=^@^TSUYU_DEV_TOOLS=0@BRAIN_MODE=queue"
        f"@SHIORI_PROVIDER={args.shiori_provider}@CORS_ORIGINS={cors}"
        "@OMP_NUM_THREADS=1@MKL_NUM_THREADS=1"
    )
    common = [*scope, runtime, "--cpu=1", "--memory=1Gi"]
    probe = "httpGet.path=/healthz,timeoutSeconds=5,periodSeconds=10,failureThreshold=24"
    return [
        [
            "gcloud",
            "run",
            "jobs",
            "deploy",
            "tsuyulabo-migrate",
            *common,
            f"--image={api}",
            "--tasks=1",
            "--parallelism=1",
            "--max-retries=0",
            "--task-timeout=600s",
            "--command=alembic",
            "--args=-c,services/api/alembic.ini,upgrade,head",
            f"--set-secrets={database}",
            "--set-env-vars=TSUYU_DEV_TOOLS=0",
        ],
        ["gcloud", "run", "jobs", "execute", "tsuyulabo-migrate", *scope, "--wait"],
        [
            "gcloud",
            "run",
            "deploy",
            "tsuyulabo-worker",
            *common,
            f"--image={worker}",
            "--port=8080",
            "--min=1",
            "--max=1",
            "--no-cpu-throttling",
            "--no-allow-unauthenticated",
            "--ingress=internal",
            "--concurrency=1",
            f"--startup-probe={probe},httpGet.port=8080",
            f"--set-secrets={secrets}",
            env,
        ],
        [
            "gcloud",
            "run",
            "deploy",
            "tsuyulabo-api",
            *common,
            f"--image={api}",
            "--port=8000",
            "--min=0",
            "--max=2",
            "--cpu-throttling",
            "--allow-unauthenticated",
            "--ingress=all",
            "--concurrency=8",
            "--timeout=300s",
            f"--startup-probe={probe},httpGet.port=8000",
            f"--set-secrets={secrets}",
            env,
        ],
    ]


def run(plan: list[list[str]], *, execute: bool) -> None:
    for command in plan:
        print(shlex.join(command), flush=True)
        if execute:
            # Resolve gcloud.cmd on Windows; never interpolate arguments into shell text.
            executable = shutil.which(command[0])
            if executable is None:
                raise FileNotFoundError(f"Install {command[0]} and add it to PATH first")
            subprocess.run([executable, *command[1:]], cwd=ROOT, check=True)


def main() -> None:
    cli = parser()
    args = cli.parse_args()
    try:
        plan = commands(args)
    except ValueError as error:
        cli.error(str(error))
    if not args.execute:
        print("DRY RUN: no commands will be executed. Add --execute to apply.")
    run(plan, execute=args.execute)


if __name__ == "__main__":
    main()
