# Fabric Notebook 01 — Collect (optional) + Ingest CSVs into Lakehouse tables
# Paste into a Fabric notebook attached to lakehouse `lh_air_freight`.
# Cell 1: packages (uncomment if needed)
# %pip install requests pyyaml pandas statsmodels openpyxl xlrd -q

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from pyspark.sql import SparkSession

spark = SparkSession.builder.getOrCreate()

FILES_INCOMING = Path("/lakehouse/default/Files/incoming")
FILES_ARCHIVE = Path("/lakehouse/default/Files/archive")
FILES_INCOMING.mkdir(parents=True, exist_ok=True)
FILES_ARCHIVE.mkdir(parents=True, exist_ok=True)

RUN_COLLECT_IN_FABRIC = False  # set True only if egress to Freightos/FRED/EIA is allowed


def archive(path: Path) -> None:
    if not path.exists():
        return
    dest = FILES_ARCHIVE / f"{path.stem}_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}{path.suffix}"
    dest.write_bytes(path.read_bytes())


def read_csv_if_exists(name: str) -> pd.DataFrame | None:
    path = FILES_INCOMING / name
    if not path.exists():
        print(f"Missing {path}")
        return None
    return pd.read_csv(path)


def append_pandas_to_table(df: pd.DataFrame, table: str) -> int:
    if df is None or df.empty:
        return 0
    sdf = spark.createDataFrame(df.astype(object).where(pd.notnull(df), None))
    sdf.write.mode("append").saveAsTable(table)
    return len(df)


run_id = f"run-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
started = datetime.now(timezone.utc)
meta = {"run_id": run_id, "status": "started"}

# Optional: run collector inside Fabric (hybrid preferred)
if RUN_COLLECT_IN_FABRIC:
    import subprocess
    import sys

    # Expect repo files uploaded under Files/repo/air-freight-rate-collector
    repo = Path("/lakehouse/default/Files/repo/air-freight-rate-collector")
    subprocess.check_call(
        [sys.executable, "-m", "src.run_collect", "--all"],
        cwd=str(repo),
        env={**dict(**{k: v for k, v in __import__("os").environ.items()}), "PYTHONPATH": str(repo)},
    )
    # Copy outputs into incoming
    processed = repo / "data" / "processed"
    for fname in ["rates_observed.csv", "proxies_macro.csv", "collection_run_meta.json"]:
        src = processed / fname
        if src.exists():
            (FILES_INCOMING / fname).write_bytes(src.read_bytes())

rates = read_csv_if_exists("rates_observed.csv")
proxies = read_csv_if_exists("proxies_macro.csv")

n_rates = append_pandas_to_table(rates, "rates_observed") if rates is not None else 0
n_proxies = append_pandas_to_table(proxies, "proxies_macro") if proxies is not None else 0

ok = 0
if rates is not None and "status" in rates.columns:
    ok = int((rates["status"] == "ok").sum())

finished = datetime.now(timezone.utc)
run_row = pd.DataFrame(
    [
        {
            "run_id": run_id,
            "started_at_utc": started,
            "finished_at_utc": finished,
            "status": "success" if (n_rates or n_proxies) else "empty",
            "rates_rows": n_rates,
            "rates_ok": ok,
            "proxies_rows": n_proxies,
            "message": "ingest complete",
        }
    ]
)
append_pandas_to_table(run_row, "collection_runs")

for fname in ["rates_observed.csv", "proxies_macro.csv", "collection_run_meta.json"]:
    archive(FILES_INCOMING / fname)

print(json.dumps({"run_id": run_id, "rates_rows": n_rates, "rates_ok": ok, "proxies_rows": n_proxies}, indent=2))
