# Next Steps — Air Freight Rate Forecasting System

This is the implementation playbook after the free-source collector is in place.

## Decide your orchestration path (pick one primary)

| Option | Best if you… | Difficulty | Cost | Fabric-native? |
|---|---|---|---|---|
| **A. Microsoft Fabric + Pipelines/Notebook schedule** | Already on M365 / Fabric / Power BI | Medium | Fabric capacity | **Yes — preferred for your stack** |
| **B. Power Automate** | Want no-code scheduling + SharePoint + email | Low–Medium | Power Automate license | Via SharePoint/OneLake connectors |
| **C. n8n** | Want visual flows, self-host or cloud n8n | Low–Medium | Free self-host / n8n cloud | Export CSV → Fabric |
| **D. GitHub Actions cron** | Want code in GitHub, zero infra servers | Low | Free minutes | Upload artifacts / push to Lakehouse API |
| **E. Temporal / Prefect / Dagster** | Need durable workflows, retries, scale later | Higher | Infra + ops | Call collector then load Fabric |

**Recommendation for your stated stack (Fabric + Power BI):**  
**Primary = A (Fabric notebooks + pipeline schedule)**  
**Secondary = B (Power Automate for email/alerts) or D (GitHub Actions) for collection if Fabric spark jobs are awkward for outbound HTTP.**

Many teams use a **hybrid**: GitHub Actions or n8n collects quotes → writes to OneLake/Lakehouse → Fabric notebook trains/forecasts → Power BI reports → Power Automate emails.

---

## Week-by-week plan

### Week 0 (today)
1. Clone this repo / open PR branch `cursor/air-freight-rate-collector-124a`.
2. Run locally once: `PYTHONPATH=. python3 -m src.run_collect --all`.
3. Confirm BOM rates appear in `data/processed/rates_observed.csv`.
4. Choose orchestration option A–E (or hybrid).

### Week 1 — Data landing
1. Create Fabric **Workspace** + **Lakehouse** (`lh_air_freight`).
2. Create tables (see `fabric/sql/01_create_tables.sql`).
3. Wire collector output → Lakehouse (`rates_observed`, `proxies_macro`).
4. Schedule collection **weekly** (Sunday 06:00 IST recommended).

### Week 2 — Forecast v1 (proxies)
1. Import `fabric/notebooks/02_forecast_proxy_baseline.ipynb` (or `.py`).
2. Schedule notebook after collection.
3. Build Power BI semantic model on `proxy_forecast_baseline`.

### Week 3 — Ops
1. Add Power Automate email when forecast MAPE regresses or collection fails.
2. Start **manual quote log** for BOM lanes (eCargoRates) into `manual_quotes`.
3. Document runbook (`docs/RUNBOOK.md`).

### Month 2–6 — Forecast v2 (real rates)
1. After ≥12–24 weekly lane observations, enable `03_forecast_lane_sarimax.py`.
2. Publish lane-level 1/3/6-month fan charts in Power BI.
3. Optionally buy TAC/FAX for 1–2 critical lanes if business value justifies it.

---

## Doc map

| Doc | Purpose |
|---|---|
| [`ARCHITECTURE.md`](ARCHITECTURE.md) | End-to-end architecture (all options) |
| [`POWER_AUTOMATE.md`](POWER_AUTOMATE.md) | Complete Power Automate step-by-step |
| [`FABRIC.md`](FABRIC.md) | Lakehouse, notebooks, pipelines, Power BI |
| [`N8N.md`](N8N.md) | Full n8n flow import + setup |
| [`GITHUB_ACTIONS_CRON.md`](GITHUB_ACTIONS_CRON.md) | GitHub-connected cron collector |
| [`TEMPORAL_AND_ALTERNATIVES.md`](TEMPORAL_AND_ALTERNATIVES.md) | Temporal, Prefect, Dagster, Azure Functions |
| [`RUNBOOK.md`](RUNBOOK.md) | Operate, debug 429s, rotate lanes |

---

## Immediate commands

```bash
cd air-freight-rate-collector
pip install -r requirements.txt
PYTHONPATH=. python3 -m src.run_collect --all
PYTHONPATH=. python3 -m src.forecast_proxy_baseline
```

Then follow **Option A** in `FABRIC.md` or **Option B** in `POWER_AUTOMATE.md`.
