"""Public Drewry Airfreight composite snapshot from marketing page (not lane-level)."""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

import requests


_DOLLAR_RE = re.compile(r"(?:US)?\$\s*([0-9]+(?:\.[0-9]+)?)")


def collect_drewry_public(cfg: dict[str, Any]) -> list[dict[str, Any]]:
    drewry = cfg.get("drewry_public") or {}
    if not drewry.get("enabled", False):
        return []

    ua = cfg.get("user_agent", "AirFreightRateCollector/1.0")
    url = drewry["url"]
    session = requests.Session()
    session.headers.update({"User-Agent": ua})
    resp = session.get(url, timeout=45)
    resp.raise_for_status()
    text = resp.text

    # Prefer numbers near "global average" / "composite" wording when possible
    candidates = _DOLLAR_RE.findall(text)
    if not candidates:
        return []

    # Heuristic: first plausible airfreight $/kg in page body (typically 1–15)
    value = None
    for c in candidates:
        v = float(c)
        if 1.0 <= v <= 20.0:
            value = v
            break
    if value is None:
        value = float(candidates[0])

    collected_at = datetime.now(timezone.utc).isoformat()
    return [
        {
            "collected_at_utc": collected_at,
            "source": "drewry_public_page",
            "source_url": url,
            "attribution": "Drewry public Airfreight Price Index page (marketing snapshot)",
            "rate_type": "public_composite",
            "origin": "GLOBAL",
            "destination": "GLOBAL",
            "lane": "GLOBAL-COMPOSITE",
            "region": "global",
            "weight_break_kg": 1000,
            "chargeable_kg": 1000,
            "currency": "USD",
            "usd_per_kg_min": value,
            "usd_per_kg_max": value,
            "usd_per_kg_mid": value,
            "total_min_usd": None,
            "total_max_usd": None,
            "transit_min_days": None,
            "transit_max_days": None,
            "num_quotes": 1,
            "status": "ok",
            "error": None,
        }
    ]
