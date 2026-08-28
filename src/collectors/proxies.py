"""Free long-history macro proxies (FRED CSV + EIA jet fuel XLS)."""
from __future__ import annotations

from datetime import datetime, timezone
from io import BytesIO, StringIO
from typing import Any

import pandas as pd
import requests


def _get(session: requests.Session, url: str) -> bytes:
    resp = session.get(url, timeout=60)
    resp.raise_for_status()
    return resp.content


def collect_fred_series(cfg: dict[str, Any]) -> pd.DataFrame:
    ua = cfg.get("user_agent", "AirFreightRateCollector/1.0")
    session = requests.Session()
    session.headers.update({"User-Agent": ua})

    frames: list[pd.DataFrame] = []
    collected_at = datetime.now(timezone.utc).isoformat()

    for item in cfg["proxies"]["fred_csv"]:
        content = _get(session, item["url"]).decode("utf-8", errors="replace")
        df = pd.read_csv(StringIO(content))
        # Columns: observation_date, SERIES_ID
        value_col = [c for c in df.columns if c != "observation_date"][0]
        out = pd.DataFrame(
            {
                "observation_date": pd.to_datetime(df["observation_date"], errors="coerce"),
                "series_id": item["id"],
                "series_name": item["name"],
                "value": pd.to_numeric(df[value_col], errors="coerce"),
                "source": "fred",
                "source_url": item["url"],
                "rate_type": "proxy_index",
                "collected_at_utc": collected_at,
            }
        )
        frames.append(out.dropna(subset=["observation_date"]))

    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def collect_eia_jet_monthly(cfg: dict[str, Any]) -> pd.DataFrame:
    """Parse EIA monthly jet fuel XLS into long form."""
    ua = cfg.get("user_agent", "AirFreightRateCollector/1.0")
    url = cfg["proxies"]["eia_jet_monthly_xls"]
    series_id = cfg["proxies"]["eia_series_id"]
    session = requests.Session()
    session.headers.update({"User-Agent": ua})
    raw = _get(session, url)

    # EIA hist_xls is often Excel 97; try xlrd then openpyxl
    try:
        xl = pd.ExcelFile(BytesIO(raw), engine="xlrd")
    except Exception:
        xl = pd.ExcelFile(BytesIO(raw), engine="openpyxl")

    # Typical layout: first sheet with Year + Jan..Dec
    sheet = xl.sheet_names[0]
    df = xl.parse(sheet, header=None)
    # Find header row containing 'Year' and month names
    header_idx = None
    for i in range(min(40, len(df))):
        row = [str(x).strip().lower() for x in df.iloc[i].tolist()]
        if "year" in row and "jan" in row:
            header_idx = i
            break
    if header_idx is None:
        # Fallback: treat first row as header-ish
        header_idx = 0

    header = [str(x).strip() for x in df.iloc[header_idx].tolist()]
    body = df.iloc[header_idx + 1 :].copy()
    body.columns = header
    # Normalize columns
    cols = {c: c for c in body.columns}
    year_col = next((c for c in body.columns if str(c).lower() == "year"), body.columns[0])
    month_map = {
        "jan": 1,
        "feb": 2,
        "mar": 3,
        "apr": 4,
        "may": 5,
        "jun": 6,
        "jul": 7,
        "aug": 8,
        "sep": 9,
        "oct": 10,
        "nov": 11,
        "dec": 12,
    }

    records: list[dict[str, Any]] = []
    collected_at = datetime.now(timezone.utc).isoformat()
    for _, row in body.iterrows():
        try:
            year = int(float(row[year_col]))
        except Exception:
            continue
        for name, month in month_map.items():
            col = next((c for c in body.columns if str(c).strip().lower()[:3] == name), None)
            if col is None:
                continue
            val = row[col]
            try:
                if pd.isna(val) or str(val).strip() in {"", "-", "--", "NA"}:
                    continue
                value = float(val)
            except Exception:
                continue
            records.append(
                {
                    "observation_date": datetime(year, month, 1),
                    "series_id": series_id,
                    "series_name": "us_gulf_jet_fuel_spot_usd_per_gal",
                    "value": value,
                    "source": "eia",
                    "source_url": url,
                    "rate_type": "proxy_index",
                    "collected_at_utc": collected_at,
                }
            )

    return pd.DataFrame.from_records(records)


def collect_all_proxies(cfg: dict[str, Any]) -> pd.DataFrame:
    frames = [collect_fred_series(cfg), collect_eia_jet_monthly(cfg)]
    frames = [f for f in frames if f is not None and not f.empty]
    if not frames:
        return pd.DataFrame()
    out = pd.concat(frames, ignore_index=True)
    out = out.sort_values(["series_name", "observation_date"]).drop_duplicates(
        subset=["series_name", "observation_date"], keep="last"
    )
    return out.reset_index(drop=True)
