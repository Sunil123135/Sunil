# Fabric Notebook 02 — Proxy forecast baseline (v1)
# Attach lakehouse lh_air_freight. Writes to table `forecasts` and Files/models/.

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from pyspark.sql import SparkSession

spark = SparkSession.builder.getOrCreate()

MODELS = Path("/lakehouse/default/Files/models")
MODELS.mkdir(parents=True, exist_ok=True)

proxies = spark.table("proxies_macro").toPandas()
proxies["observation_date"] = pd.to_datetime(proxies["observation_date"], errors="coerce")


def monthly(name: str) -> pd.Series:
    s = proxies[proxies["series_name"] == name].copy()
    s = s.set_index("observation_date")["value"].astype(float).sort_index()
    return s.resample("MS").mean().dropna()


freight = monthly("us_air_freight_ppi")
jet = monthly("us_gulf_jet_fuel_spot_usd_per_gal")
if jet.empty:
    jet = monthly("us_jet_fuel_ppi")
fx = monthly("usd_inr")

df = pd.concat({"freight_ppi": freight, "jet": jet, "usd_inr": fx}, axis=1, sort=True).dropna()
if len(df) < 36:
    raise RuntimeError(f"Need ≥36 monthly points; have {len(df)}")

train = df.iloc[:-6]
test = df.iloc[-6:]
y = np.log(train["freight_ppi"])
X = np.column_stack([np.ones(len(train)), np.log(train["jet"]), np.log(train["usd_inr"])])
beta, *_ = np.linalg.lstsq(X, y, rcond=None)


def predict(frame: pd.DataFrame) -> pd.Series:
    Xp = np.column_stack([np.ones(len(frame)), np.log(frame["jet"]), np.log(frame["usd_inr"])])
    return pd.Series(np.exp(Xp @ beta), index=frame.index)


holdout = predict(test)
mape = float(np.mean(np.abs((test["freight_ppi"] - holdout) / test["freight_ppi"])) * 100)
resid_std = float(np.std(np.log(train["freight_ppi"]) - np.log(predict(train))))

last = df.iloc[[-1]]
future_idx = pd.date_range(df.index[-1] + pd.offsets.MonthBegin(1), periods=6, freq="MS")
future = pd.DataFrame({"jet": last["jet"].values[0], "usd_inr": last["usd_inr"].values[0]}, index=future_idx)
fwd = predict(future)

generated = datetime.now(timezone.utc)
rows = []
for i, (dt, val) in enumerate(fwd.items(), start=1):
    # crude 80% PI in log space
    low = float(np.exp(np.log(val) - 1.28 * resid_std))
    high = float(np.exp(np.log(val) + 1.28 * resid_std))
    horizon = 1 if i <= 1 else 3 if i <= 3 else 6
    rows.append(
        {
            "generated_at_utc": generated,
            "model_name": "proxy_log_ols_v1",
            "lane": "GLOBAL_PROXY",
            "target": "us_air_freight_ppi",
            "horizon_months": horizon,
            "forecast_date": dt.date(),
            "point_forecast": float(val),
            "pi_low_80": low,
            "pi_high_80": high,
            "metrics_json": json.dumps({"holdout_mape_pct": mape}),
        }
    )

out = pd.DataFrame(rows)
spark.createDataFrame(out.astype(object)).write.mode("append").saveAsTable("forecasts")

meta = {
    "model_name": "proxy_log_ols_v1",
    "holdout_mape_pct": mape,
    "coefficients": {"intercept": float(beta[0]), "log_jet": float(beta[1]), "log_usd_inr": float(beta[2])},
    "generated_at_utc": generated.isoformat(),
}
(MODELS / "proxy_ols_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
print(json.dumps(meta, indent=2))
print(out.head())
