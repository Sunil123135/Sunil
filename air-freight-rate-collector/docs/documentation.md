# Documentation Index

Master index for the air freight rate forecasting system.

## Read in this order

1. [NEXT_STEPS.md](NEXT_STEPS.md) — what to do this week  
2. [ARCHITECTURE.md](ARCHITECTURE.md) — full architecture  
3. Pick orchestration:
   - [POWER_AUTOMATE.md](POWER_AUTOMATE.md) — **complete Power Automate step-by-step**  
   - [N8N.md](N8N.md) — n8n flows  
   - [GITHUB_ACTIONS_CRON.md](GITHUB_ACTIONS_CRON.md) — GitHub cron connected to this codebase  
   - [TEMPORAL_AND_ALTERNATIVES.md](TEMPORAL_AND_ALTERNATIVES.md) — Temporal, Azure Functions, VM cron, Prefect…  
4. [FABRIC.md](FABRIC.md) — **how to get data + forecasting models into Microsoft Fabric**  
5. [RUNBOOK.md](RUNBOOK.md) — operate and troubleshoot  

## Code map

| Path | Role |
|---|---|
| `src/` | Collector + local proxy forecast |
| `fabric/notebooks/` | Fabric-ready ingest + forecast notebooks |
| `fabric/sql/` | Lakehouse DDL |
| `n8n/` | Importable n8n workflows |
| `.github/workflows/weekly-collect.yml` | GitHub Actions cron (repo root) |
| `scripts/upload_to_sharepoint.py` | Graph upload to SharePoint bridge |
| `scripts/cron/sync_to_fabric.sh` | azcopy sync helper |
| `temporal/` | Optional Temporal stub |

## Preferred production path

**GitHub Actions (weekly collect)** → **SharePoint/OneLake incoming** → **Fabric notebooks (ingest + forecast)** → **Power BI** → **Power Automate email alerts**.
