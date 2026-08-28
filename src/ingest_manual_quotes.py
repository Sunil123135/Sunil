"""Append human-entered forwarder quotes into rates_observed.csv."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from src import CONFIG_PATH, PROCESSED_DIR, ensure_dirs


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--file",
        type=Path,
        default=CONFIG_PATH.parent / "manual_quote_template.csv",
        help="CSV with usd_per_kg_mid filled in",
    )
    args = parser.parse_args()
    ensure_dirs()

    df = pd.read_csv(args.file)
    if "usd_per_kg_mid" not in df.columns:
        raise SystemExit("CSV must include usd_per_kg_mid")

    filled = df[df["usd_per_kg_mid"].notna() & (df["usd_per_kg_mid"].astype(str).str.strip() != "")].copy()
    if filled.empty:
        raise SystemExit("No filled usd_per_kg_mid values found")

    now = datetime.now(timezone.utc).isoformat()
    filled["collected_at_utc"] = filled.get("collected_at_utc", now)
    filled["source"] = filled.get("source", "manual_forwarder_quote")
    filled["rate_type"] = filled.get("rate_type", "indicative_list_rate")
    filled["status"] = "ok"
    filled["usd_per_kg_min"] = filled["usd_per_kg_mid"]
    filled["usd_per_kg_max"] = filled["usd_per_kg_mid"]
    filled["num_quotes"] = 1
    filled["attribution"] = filled.get("attribution", "Manual quote entry by operator")

    out = PROCESSED_DIR / "rates_observed.csv"
    if out.exists() and out.stat().st_size > 0:
        old = pd.read_csv(out)
        combined = pd.concat([old, filled], ignore_index=True)
    else:
        combined = filled
    combined.to_csv(out, index=False)
    print(f"Appended {len(filled)} manual quotes → {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
