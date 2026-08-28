"""Freightos public Shipping Calculator → indicative US$/kg by lane."""
from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any

import requests


def chargeable_weight_kg(
    actual_kg: float,
    length_cm: float,
    width_cm: float,
    height_cm: float,
    divisor: float = 6000.0,
) -> float:
    volumetric = (length_cm * width_cm * height_cm) / divisor
    return max(float(actual_kg), float(volumetric))


def fetch_quote(
    session: requests.Session,
    base_url: str,
    origin: str,
    destination: str,
    weight_kg: int,
    length: int,
    width: int,
    height: int,
    timeout: float = 30.0,
    max_retries: int = 3,
    retry_backoff_seconds: float = 30.0,
) -> dict[str, Any]:
    params = {
        "mode": "air",
        "origin": origin,
        "destination": destination,
        "loadtype": "boxes",
        "weight": weight_kg,
        "quantity": 1,
        "length": length,
        "width": width,
        "height": height,
        "format": "json",
    }
    last_exc: Exception | None = None
    for attempt in range(max_retries):
        resp = session.get(base_url, params=params, timeout=timeout)
        if resp.status_code == 429:
            # Soft signal to caller: rate limited. Limited retries only.
            if attempt >= max_retries - 1:
                raise requests.HTTPError("429 Too Many Requests", response=resp)
            wait = retry_backoff_seconds * (attempt + 1)
            retry_after = resp.headers.get("Retry-After")
            if retry_after:
                try:
                    wait = max(wait, float(retry_after))
                except ValueError:
                    pass
            time.sleep(wait)
            last_exc = requests.HTTPError("429 Too Many Requests", response=resp)
            continue
        resp.raise_for_status()
        return resp.json()
    assert last_exc is not None
    raise last_exc


def parse_usd_per_kg(payload: dict[str, Any], chargeable_kg: float) -> dict[str, float | int | None]:
    response = payload.get("response") or {}
    rates = response.get("estimatedFreightRates") or {}
    num = int(rates.get("numQuotes") or 0)
    if num <= 0:
        return {
            "num_quotes": 0,
            "total_min_usd": None,
            "total_max_usd": None,
            "usd_per_kg_min": None,
            "usd_per_kg_max": None,
            "usd_per_kg_mid": None,
            "transit_min_days": None,
            "transit_max_days": None,
        }

    mode = rates.get("mode") or {}
    price = mode.get("price") or {}
    min_amt = ((price.get("min") or {}).get("moneyAmount") or {}).get("amount")
    max_amt = ((price.get("max") or {}).get("moneyAmount") or {}).get("amount")
    transit = mode.get("transitTimes") or {}

    min_usd = float(min_amt) if min_amt is not None else None
    max_usd = float(max_amt) if max_amt is not None else None
    mid_usd = None
    if min_usd is not None and max_usd is not None:
        mid_usd = (min_usd + max_usd) / 2.0

    return {
        "num_quotes": num,
        "total_min_usd": min_usd,
        "total_max_usd": max_usd,
        "usd_per_kg_min": (min_usd / chargeable_kg) if min_usd is not None else None,
        "usd_per_kg_max": (max_usd / chargeable_kg) if max_usd is not None else None,
        "usd_per_kg_mid": (mid_usd / chargeable_kg) if mid_usd is not None else None,
        "transit_min_days": transit.get("min"),
        "transit_max_days": transit.get("max"),
    }


def collect_freightos_lanes(cfg: dict[str, Any]) -> list[dict[str, Any]]:
    freightos = cfg["freightos"]
    delay = float(cfg.get("request_delay_seconds", 8.0))
    ua = cfg.get("user_agent", "AirFreightRateCollector/1.0")
    divisor = float(freightos.get("air_vol_divisor", 6000))
    dims = freightos["dim_cm_by_weight"]
    weights = freightos["weight_breaks_kg"]
    base_url = freightos["base_url"]
    max_retries = int(freightos.get("max_retries", 3))
    retry_backoff = float(freightos.get("retry_backoff_seconds", 30))
    max_requests = int(freightos.get("max_requests_per_run", 12))
    stop_on_rate_limit = bool(freightos.get("stop_on_rate_limit", True))

    session = requests.Session()
    session.headers.update({"User-Agent": ua, "Accept": "application/json"})

    collected_at = datetime.now(timezone.utc).isoformat()
    rows: list[dict[str, Any]] = []
    requests_made = 0
    rate_limited = False

    # Prefer explicitly prioritized lanes first
    lanes = sorted(cfg["lanes"], key=lambda x: (0 if x.get("priority") else 1, x.get("origin", ""), x.get("destination", "")))

    for lane in lanes:
        if rate_limited:
            break
        origin = lane["origin"]
        destination = lane["destination"]
        region = lane.get("region", "")
        for weight in weights:
            if requests_made >= max_requests or rate_limited:
                rate_limited = True
                break
            dim = dims.get(weight) or dims.get(str(weight))
            if not dim:
                continue
            length, width, height = int(dim["length"]), int(dim["width"]), int(dim["height"])
            cw = chargeable_weight_kg(weight, length, width, height, divisor)
            try:
                payload = fetch_quote(
                    session,
                    base_url,
                    origin,
                    destination,
                    int(weight),
                    length,
                    width,
                    height,
                    max_retries=max_retries,
                    retry_backoff_seconds=retry_backoff,
                )
                requests_made += 1
                parsed = parse_usd_per_kg(payload, cw)
                status = "ok" if parsed["num_quotes"] else "no_quote"
                error = None
            except requests.HTTPError as exc:
                requests_made += 1
                code = getattr(exc.response, "status_code", None)
                parsed = {
                    "num_quotes": 0,
                    "total_min_usd": None,
                    "total_max_usd": None,
                    "usd_per_kg_min": None,
                    "usd_per_kg_max": None,
                    "usd_per_kg_mid": None,
                    "transit_min_days": None,
                    "transit_max_days": None,
                }
                if code == 429:
                    status = "rate_limited"
                    error = "429 Too Many Requests"
                    if stop_on_rate_limit:
                        rate_limited = True
                else:
                    status = "error"
                    error = str(exc)
            except Exception as exc:  # noqa: BLE001
                parsed = {
                    "num_quotes": 0,
                    "total_min_usd": None,
                    "total_max_usd": None,
                    "usd_per_kg_min": None,
                    "usd_per_kg_max": None,
                    "usd_per_kg_mid": None,
                    "transit_min_days": None,
                    "transit_max_days": None,
                }
                status = "error"
                error = str(exc)

            rows.append(
                {
                    "collected_at_utc": collected_at,
                    "source": "freightos_shipping_calculator",
                    "source_url": "https://ship.freightos.com/api/shippingCalculator",
                    "attribution": "Data courtesy Freightos — https://www.freightos.com",
                    "rate_type": "marketplace_estimate",
                    "origin": origin,
                    "destination": destination,
                    "lane": f"{origin}-{destination}",
                    "region": region,
                    "weight_break_kg": int(weight),
                    "chargeable_kg": round(cw, 3),
                    "currency": "USD",
                    "usd_per_kg_min": parsed["usd_per_kg_min"],
                    "usd_per_kg_max": parsed["usd_per_kg_max"],
                    "usd_per_kg_mid": parsed["usd_per_kg_mid"],
                    "total_min_usd": parsed["total_min_usd"],
                    "total_max_usd": parsed["total_max_usd"],
                    "transit_min_days": parsed["transit_min_days"],
                    "transit_max_days": parsed["transit_max_days"],
                    "num_quotes": parsed["num_quotes"],
                    "status": status,
                    "error": error,
                }
            )
            time.sleep(delay)

    return rows
