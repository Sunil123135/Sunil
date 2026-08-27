# Air Freight Rate Collector (Free-Source Workaround)

**Yes — you can get actual $/kg observations without a paid TAC/WorldACD subscription**, but only by **building your own history from free live quotes + free proxies**. You cannot unlock someone else’s 10-year audited lane archive for free.

## What this repo does

1. Calls the **Freightos public Shipping Calculator** (no API key) for priority airport pairs, converts total USD quotes → **US$/kg** using IATA chargeable weight.
2. Downloads **10+ years of free proxies** (EIA jet fuel, FRED air-freight PPI, USDINR).
3. Optionally pulls **SHAQ** free air $/kg (China-origin indicative) and a **Drewry public composite** snapshot.
4. Accepts **manual forwarder quotes** (eCargoRates / GSA) via CSV ingest.
5. Writes CSVs ready for n8n → SharePoint/Fabric → Power BI, plus a proxy OLS baseline forecast.

## Live sample captured in this environment

| Lane | Weight | Mid US$/kg | Source |
|---|---|---|---|
| BOM–LHR | 300 kg | ~9.26 | Freightos marketplace estimate |
| BOM–FRA | 300 kg | ~8.10 | Freightos marketplace estimate |
| BOM–DXB | 300 kg | ~6.65 | Freightos marketplace estimate |

See `data/processed/bom_focus_freightos_sample.csv` and `LEGAL.md`.

## Honest limits

- Freightos returns **marketplace estimate ranges**, not audited TAC transactional indices.
- Coverage is uneven (some pairs return `numQuotes=0`).
- The endpoint **rate-limits** (HTTP 429) — weekly runs with delays are required.
- Proxies forecast **US freight PPI pressure**, not BOM lane $/kg, until you accumulate ~12–24 months of weekly quotes.

## Quick start

```bash
cd air-freight-rate-collector
pip install -r requirements.txt
PYTHONPATH=. python3 -m src.run_collect --all
PYTHONPATH=. python3 -m src.forecast_proxy_baseline
# Optional: fill config/manual_quote_template.csv then
PYTHONPATH=. python3 -m src.ingest_manual_quotes
```

Outputs: `data/processed/rates_observed.csv`, `proxies_macro.csv`, `proxy_forecast_baseline.csv`.

## Automation

Import `scripts/n8n_weekly_collect_stub.json` into n8n (or mirror in Power Automate). Schedule **weekly**, not high-frequency, to respect Freightos limits. Rotate non-priority lanes across weeks via `config/lanes.yaml`.

## Attribution

Freightos public calculator data requires clear credit and a link to https://www.freightos.com.
