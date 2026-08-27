"""Run all free-source collectors and append to processed CSVs."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yaml

from src import ARTIFACTS_DIR, CONFIG_PATH, PROCESSED_DIR, ensure_dirs
from src.collectors.drewry_public import collect_drewry_public
from src.collectors.freightos_quotes import collect_freightos_lanes
from src.collectors.proxies import collect_all_proxies
from src.collectors.shaq_index import collect_shaq_air


def load_config(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def append_rates(rows: list[dict], path: Path) -> pd.DataFrame:
    new_df = pd.DataFrame(rows)
    if path.exists() and path.stat().st_size > 0:
        old = pd.read_csv(path)
        combined = pd.concat([old, new_df], ignore_index=True)
    else:
        combined = new_df
    combined.to_csv(path, index=False)
    return combined


def write_snapshot_table(rates: pd.DataFrame, path: Path) -> None:
    """Latest successful mid $/kg per lane + weight break for dashboards."""
    if rates.empty:
        path.write_text("", encoding="utf-8")
        return
    ok = rates[rates["status"] == "ok"].copy()
    if ok.empty:
        path.write_text("", encoding="utf-8")
        return
    ok["collected_at_utc"] = pd.to_datetime(ok["collected_at_utc"], utc=True, errors="coerce")
    ok = ok.sort_values("collected_at_utc")
    latest = ok.groupby(["source", "lane", "weight_break_kg"], dropna=False).tail(1)
    cols = [
        "collected_at_utc",
        "source",
        "rate_type",
        "lane",
        "origin",
        "destination",
        "weight_break_kg",
        "usd_per_kg_min",
        "usd_per_kg_mid",
        "usd_per_kg_max",
        "attribution",
    ]
    latest[cols].to_csv(path, index=False)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Collect free air-freight rate observations")
    parser.add_argument("--config", type=Path, default=CONFIG_PATH)
    parser.add_argument("--all", action="store_true", help="Freightos + proxies + SHAQ + Drewry")
    parser.add_argument("--freightos", action="store_true")
    parser.add_argument("--proxies", action="store_true")
    parser.add_argument("--shaq", action="store_true")
    parser.add_argument("--drewry", action="store_true")
    args = parser.parse_args(argv)

    if not (args.all or args.freightos or args.proxies or args.shaq or args.drewry):
        args.all = True

    ensure_dirs()
    cfg = load_config(args.config)
    meta: dict = {
        "started_at_utc": datetime.now(timezone.utc).isoformat(),
        "sources": {},
    }

    rates_path = PROCESSED_DIR / "rates_observed.csv"
    proxies_path = PROCESSED_DIR / "proxies_macro.csv"
    latest_path = PROCESSED_DIR / "rates_latest_snapshot.csv"
    meta_path = PROCESSED_DIR / "collection_run_meta.json"

    rate_rows: list[dict] = []

    if args.all or args.freightos:
        print("Collecting Freightos marketplace air quotes...", flush=True)
        try:
            fr = collect_freightos_lanes(cfg)
            rate_rows.extend(fr)
            ok = sum(1 for r in fr if r["status"] == "ok")
            meta["sources"]["freightos"] = {"rows": len(fr), "ok": ok}
            print(f"  Freightos: {ok}/{len(fr)} quotes OK", flush=True)
        except Exception as exc:  # noqa: BLE001
            meta["sources"]["freightos"] = {"error": str(exc)}
            print(f"  Freightos FAILED: {exc}", flush=True)

    if args.all or args.shaq:
        print("Collecting SHAQ free air $/kg...", flush=True)
        try:
            sh = collect_shaq_air(cfg)
            rate_rows.extend(sh)
            meta["sources"]["shaq"] = {"rows": len(sh)}
            print(f"  SHAQ air lanes: {len(sh)}", flush=True)
        except Exception as exc:  # noqa: BLE001
            meta["sources"]["shaq"] = {"error": str(exc)}
            print(f"  SHAQ FAILED: {exc}", flush=True)

    if args.all or args.drewry:
        print("Collecting Drewry public composite snapshot...", flush=True)
        try:
            dr = collect_drewry_public(cfg)
            rate_rows.extend(dr)
            meta["sources"]["drewry_public"] = {"rows": len(dr), "value": dr[0]["usd_per_kg_mid"] if dr else None}
            print(f"  Drewry public: {dr[0]['usd_per_kg_mid'] if dr else 'none'}", flush=True)
        except Exception as exc:  # noqa: BLE001
            meta["sources"]["drewry_public"] = {"error": str(exc)}
            print(f"  Drewry FAILED: {exc}", flush=True)

    if rate_rows:
        rates_df = append_rates(rate_rows, rates_path)
        write_snapshot_table(rates_df, latest_path)
        # Human-readable artifact for walkthrough
        snap = rates_df[rates_df["status"] == "ok"].copy()
        if not snap.empty:
            bom = snap[snap["origin"] == "BOM"][
                ["lane", "weight_break_kg", "usd_per_kg_mid", "usd_per_kg_min", "usd_per_kg_max", "source"]
            ]
            artifact = ARTIFACTS_DIR / "latest_bom_rates.md"
            lines = [
                "# Latest BOM-origin marketplace rates (US$/kg mid)",
                "",
                "Source: Freightos public Shipping Calculator (indicative marketplace estimates).",
                "Attribution: https://www.freightos.com",
                "",
                bom.tail(50).to_string(index=False),
                "",
            ]
            artifact.write_text("\n".join(lines), encoding="utf-8")

    if args.all or args.proxies:
        print("Collecting FRED + EIA proxies...", flush=True)
        try:
            proxies = collect_all_proxies(cfg)
            proxies.to_csv(proxies_path, index=False)
            meta["sources"]["proxies"] = {
                "rows": int(len(proxies)),
                "series": sorted(proxies["series_name"].dropna().unique().tolist()) if not proxies.empty else [],
            }
            print(f"  Proxies: {len(proxies)} rows", flush=True)
        except Exception as exc:  # noqa: BLE001
            meta["sources"]["proxies"] = {"error": str(exc)}
            print(f"  Proxies FAILED: {exc}", flush=True)

    meta["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"Wrote meta → {meta_path}", flush=True)
    print(f"Rates history → {rates_path}", flush=True)
    print(f"Proxies → {proxies_path}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
