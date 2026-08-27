# Fabric Notebook 03 — Per-lane SARIMAX (v2)
# Enable after you have ~40+ weekly OK observations per lane.
# %pip install statsmodels -q

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from pyspark.sql import SparkSession

spark = SparkSession.builder.getOrCreate()

try:
    import statsmodels.api as sm
except ImportError as exc:
    raise SystemExit("Install statsmodels in the notebook: %pip install statsmodels") from exc

MODELS = Path("/lakehouse/default/Files/models/lanes")
MODELS.mkdir(parents=True, exist_ok=True)

MIN_POINTS = 40
HORIZONS_WEEKS = {1: 4, 3: 13, 6: 26}  # approx month horizons in weeks

rates = spark.table("rates_observed").toPandas()
rates = rates[(rates["status"] == "ok") & (rates["usd_per_kg_mid"].notna())].copy()
rates["collected_at_utc"] = pd.to_datetime(rates["collected_at_utc"], utc=True, errors="coerce")
rates = rates.dropna(subset=["collected_at_utc", "lane"])

# Prefer marketplace + manual
rates = rates[rates["source"].isin(["freightos_shipping_calculator", "manual_forwarder_quote"])]

# Weekly median mid-rate per lane
rates["week"] = rates["collected_at_utc"].dt.to_period("W-SUN").dt.start_time
weekly = (
    rates.groupby(["lane", "week"], as_index=False)["usd_per_kg_mid"].median().sort_values(["lane", "week"])
)

# Optional exogenous: monthly jet → forward-fill to weeks
proxies = spark.table("proxies_macro").toPandas()
proxies["observation_date"] = pd.to_datetime(proxies["observation_date"], errors="coerce")
jet = proxies[proxies["series_name"] == "us_gulf_jet_fuel_spot_usd_per_gal"].copy()
if jet.empty:
    jet = proxies[proxies["series_name"] == "us_jet_fuel_ppi"].copy()
jet = jet.set_index("observation_date")["value"].astype(float).sort_index().resample("W-SUN").mean().ffill()

generated = datetime.now(timezone.utc)
forecast_rows: list[dict] = []

for lane, g in weekly.groupby("lane"):
    g = g.set_index("week").asfreq("W-SUN")
    y = g["usd_per_kg_mid"].astype(float)
    if y.dropna().shape[0] < MIN_POINTS:
        print(f"skip {lane}: only {y.dropna().shape[0]} points")
        continue

    exog = jet.reindex(y.index).ffill().bfill()
    y = y.interpolate(limit_direction="both")

    try:
        model = sm.tsa.SARIMAX(
            y,
            exog=exog,
            order=(1, 1, 1),
            seasonal_order=(0, 1, 1, 52) if len(y) >= 104 else (0, 0, 0, 0),
            enforce_stationarity=False,
            enforce_invertibility=False,
        )
        res = model.fit(disp=False)
    except Exception as exc:  # noqa: BLE001
        print(f"fit failed {lane}: {exc}")
        continue

    max_h = max(HORIZONS_WEEKS.values())
    future_exog = pd.DataFrame({"exog": [float(exog.iloc[-1])] * max_h})
    # statsmodels expects same exog structure
    fut = pd.Series([float(exog.iloc[-1])] * max_h)
    pred = res.get_forecast(steps=max_h, exog=fut)
    mean = pred.predicted_mean
    ci = pred.conf_int(alpha=0.2)

    meta = {
        "lane": lane,
        "n_obs": int(y.dropna().shape[0]),
        "aic": float(res.aic) if res.aic is not None else None,
        "generated_at_utc": generated.isoformat(),
    }
    (MODELS / f"{lane}.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    for horizon_months, weeks in HORIZONS_WEEKS.items():
        idx = weeks - 1
        forecast_rows.append(
            {
                "generated_at_utc": generated,
                "model_name": "lane_sarimax_v2",
                "lane": lane,
                "target": "usd_per_kg_mid",
                "horizon_months": horizon_months,
                "forecast_date": (y.index[-1] + pd.Timedelta(weeks=weeks)).date(),
                "point_forecast": float(mean.iloc[idx]),
                "pi_low_80": float(ci.iloc[idx, 0]),
                "pi_high_80": float(ci.iloc[idx, 1]),
                "metrics_json": json.dumps(meta),
            }
        )

if not forecast_rows:
    print("No lanes ready for SARIMAX yet — keep collecting weekly.")
else:
    out = pd.DataFrame(forecast_rows)
    spark.createDataFrame(out.astype(object)).write.mode("append").saveAsTable("forecasts")
    print(out)
