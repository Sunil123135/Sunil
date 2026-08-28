"""Proxy-based baseline forecast until own rate history accumulates.

Fits a simple OLS / SARIMAX-style relationship of US air freight PPI on jet fuel
and FX, then writes a forward path for dashboard wiring. This is intentionally
honest: it forecasts a *proxy index*, not BOM lane $/kg, until rates_observed.csv
has enough weekly points.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from src import ARTIFACTS_DIR, PROCESSED_DIR, ensure_dirs


def _monthly_series(proxies: pd.DataFrame, name: str) -> pd.Series:
    s = proxies[proxies["series_name"] == name].copy()
    s["observation_date"] = pd.to_datetime(s["observation_date"])
    s = s.set_index("observation_date")["value"].astype(float).sort_index()
    # Month-end resample for mixed daily/monthly inputs
    return s.resample("MS").mean().dropna()


def main() -> int:
    ensure_dirs()
    path = PROCESSED_DIR / "proxies_macro.csv"
    if not path.exists():
        raise SystemExit("Run collectors first: python -m src.run_collect --proxies")

    proxies = pd.read_csv(path)
    freight = _monthly_series(proxies, "us_air_freight_ppi")
    jet = _monthly_series(proxies, "us_gulf_jet_fuel_spot_usd_per_gal")
    if jet.empty:
        jet = _monthly_series(proxies, "us_jet_fuel_ppi")
    fx = _monthly_series(proxies, "usd_inr")

    df = pd.concat(
        {"freight_ppi": freight, "jet": jet, "usd_inr": fx},
        axis=1,
        sort=True,
    ).dropna()

    if len(df) < 36:
        raise SystemExit(f"Need ≥36 monthly overlapping points; have {len(df)}")

    # Train on all but last 6 months for a quick holdout check
    train = df.iloc[:-6]
    test = df.iloc[-6:]

    # Log-linear: freight ~ jet + fx
    y = np.log(train["freight_ppi"])
    X = np.column_stack([np.ones(len(train)), np.log(train["jet"]), np.log(train["usd_inr"])])
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)

    def predict(frame: pd.DataFrame) -> pd.Series:
        Xp = np.column_stack([np.ones(len(frame)), np.log(frame["jet"]), np.log(frame["usd_inr"])])
        return pd.Series(np.exp(Xp @ beta), index=frame.index, name="forecast")

    fitted = predict(train)
    holdout = predict(test)
    mape = float(np.mean(np.abs((test["freight_ppi"] - holdout) / test["freight_ppi"])) * 100)

    # Naive 6-month ahead: freeze latest jet/fx (scenario: flat costs)
    last = df.iloc[[-1]]
    future_idx = pd.date_range(df.index[-1] + pd.offsets.MonthBegin(1), periods=6, freq="MS")
    future = pd.DataFrame(
        {
            "jet": last["jet"].values[0],
            "usd_inr": last["usd_inr"].values[0],
        },
        index=future_idx,
    )
    fwd = predict(future)

    out = pd.DataFrame(
        {
            "date": list(df.index) + list(fwd.index),
            "actual_freight_ppi": list(df["freight_ppi"]) + [np.nan] * len(fwd),
            "model_fitted_or_forecast": list(predict(df)) + list(fwd),
            "kind": ["history"] * len(df) + ["forecast_1_to_6m"] * len(fwd),
        }
    )
    out_path = PROCESSED_DIR / "proxy_forecast_baseline.csv"
    out.to_csv(out_path, index=False)

    meta = {
        "model": "log_ols_freight_ppi ~ jet + usd_inr",
        "holdout_mape_pct": round(mape, 2),
        "n_train_months": int(len(train)),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "note": "Proxy forecast only — not lane-level BOM $/kg.",
        "coefficients": {
            "intercept": float(beta[0]),
            "log_jet": float(beta[1]),
            "log_usd_inr": float(beta[2]),
        },
    }
    (PROCESSED_DIR / "proxy_forecast_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    (ARTIFACTS_DIR / "proxy_forecast_summary.md").write_text(
        "\n".join(
            [
                "# Proxy forecast baseline",
                "",
                f"- Holdout MAPE (last 6 months): **{mape:.1f}%**",
                f"- Train months: {len(train)}",
                f"- Output: `{out_path.name}`",
                "",
                "This forecasts US air freight PPI from jet fuel + USDINR, as a bridge until",
                "your Freightos-logged lane history is long enough for SARIMAX.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(json.dumps(meta, indent=2))
    print(f"Wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
