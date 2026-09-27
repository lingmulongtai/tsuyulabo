"""Smoke test against a running stack (docker compose up).

    uv run python scripts/smoke_api.py [--base http://localhost:8000]

Creates a guest, starts a week, plays a few puzzles through the real endpoints, advances the dev clock,
trains once, asks Shiori through the worker queue, and prints what happened. Needs TSUYU_DEV_TOOLS=1.
"""

from __future__ import annotations

import argparse
import sys
import time
import uuid

import httpx


def solve_zip(n: int, checkpoints: list[dict]) -> list[int]:
    """Depth-first search for a Hamiltonian path that visits the numbers in order."""
    cp = {c["cell"]: c["k"] for c in checkpoints}
    last_k = max(cp.values())
    start = next(cell for cell, k in cp.items() if k == 1)
    path, seen = [start], {start}

    def neighbours(cell: int) -> list[int]:
        r, c = divmod(cell, n)
        out = []
        for dr, dc in ((0, 1), (1, 0), (0, -1), (-1, 0)):
            rr, cc = r + dr, c + dc
            if 0 <= rr < n and 0 <= cc < n:
                out.append(rr * n + cc)
        return out

    def dfs(k: int) -> bool:
        if len(path) == n * n:
            return cp.get(path[-1]) == last_k
        for nxt in neighbours(path[-1]):
            if nxt in seen:
                continue
            nk = cp.get(nxt)
            if nk is not None and nk != k + 1:
                continue
            seen.add(nxt)
            path.append(nxt)
            if dfs(nk or k):
                return True
            path.pop()
            seen.discard(nxt)
        return False

    if not dfs(1):
        raise RuntimeError("no solution found")
    return path


class Client:
    def __init__(self, base: str) -> None:
        self.http = httpx.Client(base_url=base, timeout=30)
        self.token = ""

    def call(self, method: str, path: str, **kwargs) -> dict:
        headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        if method in ("POST", "PUT", "PATCH", "DELETE"):
            headers["Idempotency-Key"] = str(uuid.uuid4())
        res = self.http.request(method, path, headers=headers, **kwargs)
        if res.status_code >= 400:
            print(f"  ! {method} {path} -> {res.status_code} {res.text[:300]}")
            res.raise_for_status()
        return res.json()


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")  # Japanese error messages on Windows consoles
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://localhost:8000")
    args = parser.parse_args()
    api = Client(args.base)

    print("health:", api.call("GET", "/healthz"))
    guest = api.call("POST", "/v1/auth/guest", json={"display_name": "スモーク"})
    api.token = guest["token"]
    print("guest:", guest["user"]["friend_code"])

    week = api.call("POST", "/v1/weeks")
    print("week started, day", week.get("research_day"), "stage", week.get("stage"))

    temp = api.call("POST", "/v1/puzzles", json={"kind": "temperature"})
    time.sleep(0.3)
    res = api.call("POST", f"/v1/puzzles/{temp['puzzle_id']}/submit", json={"stop_ms": 200, "elapsed_ms": 200})
    print("temperature:", res.get("result", res))

    meal = api.call("POST", "/v1/puzzles", json={"kind": "meal"})
    res = api.call("POST", f"/v1/puzzles/{meal['puzzle_id']}/submit", json={"moves": [], "elapsed_ms": 0})
    print("meal (no moves):", res.get("result", res))

    api.call("POST", "/v1/dev/time/advance", json={"to": "next_day"})
    home = api.call("GET", "/v1/home")
    print("after next_day:", home["week"]["research_day"], home["week"]["stage"], "care_miss", home["week"]["care_miss"])

    train = api.call("POST", "/v1/puzzles", json={"kind": "training", "cue": "banana", "valence": "reward"})
    params = train["params"]
    path = solve_zip(params["n"], params["checkpoints"])
    time.sleep(2.0)
    res = api.call("POST", f"/v1/puzzles/{train['puzzle_id']}/submit", json={"path": path, "elapsed_ms": 1800})
    print("training:", res.get("result", res))

    job = api.call("POST", "/v1/shiori/ask", json={"question": "バナナのしつけはうまくいった？"})
    job_id = job.get("job_id") or job.get("id")
    for _ in range(30):
        status = api.call("GET", f"/v1/jobs/{job_id}")
        if status.get("status") in ("succeeded", "done", "completed", "failed", "error"):
            break
        time.sleep(1)
    print("shiori job:", status.get("status"), str(status.get("result"))[:300])
    return 0


if __name__ == "__main__":
    sys.exit(main())
