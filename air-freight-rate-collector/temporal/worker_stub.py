"""Educational Temporal stub — not wired to a live Temporal cluster.

Shows how activities would call this repo's collector. Prefer GitHub Actions / n8n / Fabric for MVP.
"""
from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


@dataclass
class CollectResult:
    returncode: int
    ok: bool


def activity_run_collect(mode: str = "all") -> CollectResult:
    cmd = [sys.executable, "-m", "src.run_collect"]
    if mode == "freightos":
        cmd.append("--freightos")
    elif mode == "proxies":
        cmd.append("--proxies")
    else:
        cmd.append("--all")
    proc = subprocess.run(cmd, cwd=str(REPO), env={**dict(**__import__("os").environ), "PYTHONPATH": str(REPO)})
    return CollectResult(returncode=proc.returncode, ok=proc.returncode == 0)


def activity_run_proxy_forecast() -> CollectResult:
    proc = subprocess.run(
        [sys.executable, "-m", "src.forecast_proxy_baseline"],
        cwd=str(REPO),
        env={**dict(**__import__("os").environ), "PYTHONPATH": str(REPO)},
    )
    return CollectResult(returncode=proc.returncode, ok=proc.returncode == 0)


def workflow_air_freight_weekly() -> dict:
    """Stand-in for @workflow.defn — run activities sequentially."""
    c = activity_run_collect("all")
    f = activity_run_proxy_forecast()
    return {"collect_ok": c.ok, "forecast_ok": f.ok}


if __name__ == "__main__":
    print(workflow_air_freight_weekly())
