# Air Freight Rate Collector (Free-Source Workaround)

> **Standalone project** — lives on branch [`air-freight-rate-collector`](https://github.com/Sunil123135/Sunil/tree/air-freight-rate-collector) until you run [`MIGRATION.md`](MIGRATION.md) to create `Sunil123135/air-freight-rate-collector`.

**Yes — you can get actual $/kg observations without a paid TAC/WorldACD subscription**, but only by **building your own history from free live quotes + free proxies**. You cannot unlock someone else’s 10-year audited lane archive for free.

## Start here (next steps + all orchestration options)

| Doc | What it covers |
|---|---|
| [`docs/NEXT_STEPS.md`](docs/NEXT_STEPS.md) | Week-by-week plan + which option to pick |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | End-to-end architecture diagram |
| [`docs/POWER_AUTOMATE.md`](docs/POWER_AUTOMATE.md) | **Complete Power Automate step-by-step** |
| [`docs/FABRIC.md`](docs/FABRIC.md) | **Fabric Lakehouse, notebooks, how to load model** |
| [`docs/N8N.md`](docs/N8N.md) | n8n flows (self-host + Cloud) |
| [`docs/GITHUB_ACTIONS_CRON.md`](docs/GITHUB_ACTIONS_CRON.md) | GitHub-connected weekly cron |
| [`docs/TEMPORAL_AND_ALTERNATIVES.md`](docs/TEMPORAL_AND_ALTERNATIVES.md) | Temporal, Azure Functions, cron, Prefect… |
| [`docs/RUNBOOK.md`](docs/RUNBOOK.md) | Operate / debug 429s |

**Recommended hybrid for your stack:**  
**GitHub Actions or n8n (collect)** → **Fabric Lakehouse + notebooks (store + forecast)** → **Power BI** → **Power Automate (email)**.

## What the Python collector does

1. Freightos public Shipping Calculator → **US$/kg**  
2. FRED / EIA proxies (10+ years free)  
3. Optional SHAQ / Drewry snapshots  
4. Manual quote CSV ingest  

## Live sample (this environment)

| Lane | Weight | Mid US$/kg |
|---|---|---|
| BOM–LHR | 300 kg | ~9.26 |
| BOM–FRA | 300 kg | ~8.10 |
| BOM–DXB | 300 kg | ~6.65 |

Data courtesy [Freightos](https://www.freightos.com). See `LEGAL.md`.

## Quick start (local)

```bash
pip install -r requirements.txt
PYTHONPATH=. python3 -m src.run_collect --all
PYTHONPATH=. python3 -m src.forecast_proxy_baseline
```

## Fabric code (download / copy into Fabric)

```
fabric/sql/01_create_tables.sql
fabric/notebooks/01_collect_and_ingest.py
fabric/notebooks/02_forecast_proxy_baseline.py
fabric/notebooks/03_forecast_lane_sarimax.py
fabric/pipelines/pl_air_freight_weekly.json
```

## Schedulers in this repo

- GitHub Actions: `.github/workflows/weekly-collect.yml`
- n8n: `n8n/air_freight_weekly.json`, `n8n/air_freight_trigger_github.json`
- VM cron helper: `scripts/cron/sync_to_fabric.sh`
- Temporal stub: `temporal/` (optional / advanced)
