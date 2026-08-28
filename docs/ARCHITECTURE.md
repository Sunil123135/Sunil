# Architecture — Air Freight Rate Forecasting

## Goal

Weekly (or daily-proxy) pipeline that:
1. Collects free air-freight **price observations** (BOM-focused lanes)
2. Stores history in **Fabric Lakehouse** (or SharePoint as bridge)
3. Trains/refreshes a **forecast model** in a Fabric notebook
4. Publishes **Power BI** lane dashboards + optional email

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         ORCHESTRATION LAYER                              │
│  Fabric Pipeline  |  Power Automate  |  n8n  |  GitHub Actions  | Temporal│
└───────────────┬──────────────┬─────────────┬─────────────┬───────────────┘
                │              │             │             │
                ▼              ▼             ▼             ▼
        ┌───────────────────────────────────────────────────────┐
        │              COLLECTOR (this repo, Python)            │
        │  Freightos quotes → $/kg                              │
        │  FRED / EIA proxies                                   │
        │  SHAQ / Drewry snapshots                              │
        │  Manual CSV ingest                                    │
        └──────────────────────────┬────────────────────────────┘
                                   │ CSV / Parquet / API
                                   ▼
        ┌───────────────────────────────────────────────────────┐
        │         STORAGE (Microsoft Fabric Lakehouse)          │
        │  tables: rates_observed, proxies_macro,               │
        │          forecasts, collection_runs                   │
        │  (optional bridge: SharePoint / ADLS Gen2)            │
        └──────────────────────────┬────────────────────────────┘
                                   │
                                   ▼
        ┌───────────────────────────────────────────────────────┐
        │         MODEL (Fabric Notebook / Spark Job)           │
        │  v1: proxy OLS/SARIMAX on fuel+FX+PPI                 │
        │  v2: per-lane SARIMAX once ≥12–24 months quotes       │
        └──────────────────────────┬────────────────────────────┘
                                   │
                                   ▼
        ┌───────────────────────────────────────────────────────┐
        │         SERVE                                         │
        │  Power BI / Fabric report  +  Power Automate email    │
        └───────────────────────────────────────────────────────┘
```

## Data contracts

### `rates_observed`
One row per collection attempt per lane/weight.

| Column | Type | Notes |
|---|---|---|
| collected_at_utc | timestamp | Collection time |
| source | string | freightos_shipping_calculator, shaq_sfx, manual, … |
| rate_type | string | marketplace_estimate, proxy_index, … |
| origin / destination / lane | string | IATA codes |
| weight_break_kg | double | e.g. 300 |
| usd_per_kg_mid | double | Primary modeling target |
| usd_per_kg_min / max | double | Marketplace range |
| status | string | ok, no_quote, rate_limited, error |

### `proxies_macro`
Long free history (fuel, PPI, FX).

### `forecasts`
| Column | Type |
|---|---|
| generated_at_utc | timestamp |
| model_name | string |
| lane | string (or GLOBAL_PROXY) |
| horizon_months | int (1,3,6) |
| point_forecast | double |
| pi_low_80 / pi_high_80 | double |

## Hybrid pattern (easiest for HTTP + Fabric)

Outbound HTTPS to Freightos from Fabric Spark can be painful (egress, libraries, rate limits). Preferred hybrid:

1. **GitHub Actions or n8n or Azure Function** runs `src.run_collect` weekly  
2. Uploads CSVs to **OneLake / Lakehouse Files** (`Files/incoming/`)  
3. **Fabric pipeline** copies Files → Tables  
4. **Fabric notebook** forecasts  
5. **Power BI** + **Power Automate** notify  

This hybrid is documented in both `GITHUB_ACTIONS_CRON.md` and `FABRIC.md`.

## Security

- No paid API keys required for MVP.
- If you later add Freightos Terminal / TAC keys, store in **Azure Key Vault** or Fabric **variable library** — never commit secrets.
- Respect Freightos attribution + rate limits (`LEGAL.md`).

## Environments

| Env | Purpose |
|---|---|
| Dev | Manual runs, small lane set |
| Prod | Weekly schedule, full priority lanes, Power BI |

Use separate Fabric workspaces: `AirFreight-Dev`, `AirFreight-Prod`.
