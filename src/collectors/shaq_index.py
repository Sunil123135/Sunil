"""Optional free SHAQ air $/kg snapshots (China-origin indicative)."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import requests


def collect_shaq_air(cfg: dict[str, Any]) -> list[dict[str, Any]]:
    shaq = cfg.get("shaq") or {}
    if not shaq.get("enabled", False):
        return []

    ua = cfg.get("user_agent", "AirFreightRateCollector/1.0")
    session = requests.Session()
    session.headers.update({"User-Agent": ua, "Accept": "application/json"})
    resp = session.get(shaq["url"], timeout=45)
    resp.raise_for_status()
    payload = resp.json()

    collected_at = datetime.now(timezone.utc).isoformat()
    updated = payload.get("updated")
    rows: list[dict[str, Any]] = []

    for route in payload.get("routes") or []:
        rates = route.get("rates") or {}
        air = rates.get("air_per_kg")
        if not air:
            continue
        rate = air.get("rate_usd")
        if rate is None:
            continue
        origin = route.get("origin_port") or ""
        destination = route.get("destination_port") or ""
        rows.append(
            {
                "collected_at_utc": collected_at,
                "source": "shaq_sfx",
                "source_url": shaq["url"],
                "attribution": "SHAQ Freight Rate Index (SFX), SHAQ Logistics",
                "rate_type": "forwarder_index",
                "origin": origin,
                "destination": destination,
                "lane": f"{origin}-{destination}",
                "region": f"{route.get('origin_country','')}-{route.get('destination_country','')}",
                "weight_break_kg": None,
                "chargeable_kg": None,
                "currency": air.get("currency", "USD"),
                "usd_per_kg_min": float(rate),
                "usd_per_kg_max": float(rate),
                "usd_per_kg_mid": float(rate),
                "total_min_usd": None,
                "total_max_usd": None,
                "transit_min_days": route.get("transit_days"),
                "transit_max_days": route.get("transit_days"),
                "num_quotes": 1,
                "status": "ok",
                "error": None,
                "source_as_of": updated,
            }
        )
    return rows
