# Microsoft Fabric — Setup, Code, Forecasting

This guide configures **Microsoft Fabric** as the system of record for rates + forecasts, and Power BI for serving.

## What you will create

1. Fabric **Workspace** `AirFreight-Prod`  
2. **Lakehouse** `lh_air_freight`  
3. Tables: `rates_observed`, `proxies_macro`, `forecasts`, `collection_runs`  
4. Notebooks: ingest, proxy forecast, lane SARIMAX (later)  
5. **Data pipeline** schedule (or trigger from Power Automate / GitHub)  
6. **Power BI** report/dataset on Lakehouse SQL endpoint  

---

## Step 1 — Create workspace & lakehouse

1. Open https://app.fabric.microsoft.com  
2. **Workspaces** → **New workspace** → `AirFreight-Prod`  
3. **New** → **Lakehouse** → name `lh_air_freight`  
4. Note:
   - Workspace ID  
   - Lakehouse ID  
   - SQL analytics endpoint  

Create folders under **Files**:
```
Files/
  incoming/
  archive/
  manuals/
```

---

## Step 2 — Create tables

Open Lakehouse → **New warehouse SQL query** / notebook spark SQL, run:

See `fabric/sql/01_create_tables.sql` (also pasted below conceptually):

- `rates_observed`
- `proxies_macro`
- `forecasts`
- `collection_runs`

Or let the ingest notebook `spark.createDataFrame(...).write.saveAsTable` create them on first run.

---

## Step 3 — How data gets into Fabric

### Path A — Recommended hybrid (GitHub Actions / n8n → Files → Tables)

1. Collector writes CSVs.  
2. Upload to `Files/incoming/rates_observed.csv` and `proxies_macro.csv`  
   - Via GitHub Action + OneLake DFS API / Azure ML style upload  
   - Or SharePoint shortcut into OneLake  
   - Or `az storage` / Fabric UI manual upload for smoke test  
3. Pipeline/notebook **Ingest** reads Files and MERGEs into Tables.

### Path B — Fabric notebook runs collector directly

Possible but often harder:
- Manage Python packages (`requests`, `pandas`, `statsmodels`) on Fabric runtime  
- Outbound network allowlists for `ship.freightos.com`, `fred.stlouisfed.org`, `eia.gov`  
- Handle Freightos 429s inside Spark driver (single-machine logic is fine)

Use Path B only if your Fabric capacity allows unrestricted egress. Code: `fabric/notebooks/01_collect_and_ingest.py`.

### Path C — Power Automate drops to SharePoint → OneLake shortcut

1. Create OneLake **shortcut** from SharePoint `AirFreight/incoming`.  
2. Ingest notebook reads shortcut path.

---

## Step 4 — Notebooks to import

Upload these as Fabric notebooks (`.py` source included; paste into notebook cells or import):

| File | Purpose | Schedule |
|---|---|---|
| `fabric/notebooks/01_collect_and_ingest.py` | Optional in-Fabric collect + always ingest CSVs | After files land |
| `fabric/notebooks/02_forecast_proxy_baseline.py` | Proxy forecast v1 | After ingest |
| `fabric/notebooks/03_forecast_lane_sarimax.py` | Lane SARIMAX v2 (needs history) | Monthly / weekly after month 6+ |

### Attach lakehouse
In each notebook: **Add lakehouse** → `lh_air_freight` → set as default.

### Default lakehouse paths
```python
FILES_INCOMING = "/lakehouse/default/Files/incoming"
```

---

## Step 5 — Create a Fabric Data Pipeline

1. Workspace → **New** → **Data pipeline** → `pl_air_freight_weekly`  
2. Activities:
   1. **Notebook** `01_collect_and_ingest` (or **Copy data** Files→Tables)  
   2. **Notebook** `02_forecast_proxy_baseline`  
   3. (Optional later) **Notebook** `03_forecast_lane_sarimax`  
3. **Schedule**: Sunday 01:00 UTC weekly  
   — **or** leave unscheduled and trigger from Power Automate/GitHub after upload.

### Trigger pipeline from Power Automate / HTTP

1. Create Entra ID App Registration (Service Principal).  
2. Grant SPN access to Fabric workspace (Contributor).  
3. Get token (client credentials).  
4. POST:
```
https://api.fabric.microsoft.com/v1/workspaces/{workspaceId}/items/{pipelineId}/jobs/instances?jobType=Pipeline
```

---

## Step 6 — Forecasting model into Fabric (exactly how)

### What “put the model in Fabric” means
Fabric does **not** need a separate MLflow registry for MVP. You:
1. Store **feature tables** in the Lakehouse  
2. Run training code in a **Notebook job**  
3. Write **forecast rows** back to table `forecasts`  
4. Optionally save model coefficients/pickle to `Files/models/`

### v1 — Proxy model (available now)
Notebook `02_forecast_proxy_baseline.py`:
- Reads `proxies_macro`
- Fits log-OLS: `freight_ppi ~ jet + usd_inr`
- Writes 1/3/6 month-ahead rows into `forecasts` with `lane='GLOBAL_PROXY'`
- Saves metrics JSON to `Files/models/proxy_ols_meta.json`

### v2 — Lane SARIMAX (after history accumulates)
Notebook `03_forecast_lane_sarimax.py`:
- Reads `rates_observed` where `status='ok'` and `source` in marketplace/manual  
- For each lane with ≥ 40 weekly points, fit SARIMAX with exogenous fuel  
- Write forecasts per lane  
- Save per-lane model metadata under `Files/models/lanes/{lane}.json`

### Optional: Fabric ML / MLflow
If your tenant has Fabric ML experiments enabled, log params/metrics there. Not required for Power BI.

---

## Step 7 — Power BI on Fabric

1. In Lakehouse, click **New Power BI dataset / semantic model** (or Power BI Desktop → OneLake).  
2. Include tables: `rates_observed`, `proxies_macro`, `forecasts`.  
3. Create measures:
   - Latest mid rate by lane  
   - WoW change  
   - Forecast vs last actual  
4. Build pages:
   - BOM lanes trend  
   - Proxy drivers (fuel, FX, PPI)  
   - 1/3/6 month forecast fan  
5. Publish to workspace `AirFreight-Prod`.  
6. Enable scheduled refresh **or** rely on Direct Lake (if using Direct Lake mode on Lakehouse deltas).

---

## Step 8 — End-to-end smoke test

1. Manually upload sample CSVs from this repo:
   - `data/processed/rates_observed.csv`
   - `data/processed/proxies_macro.csv`
   into `Files/incoming/`.  
2. Run notebook 01 → confirm tables have rows.  
3. Run notebook 02 → confirm `forecasts` has rows.  
4. Open Power BI report.  
5. Then wire schedule/orchestration.

---

## Code locations

```
fabric/
  sql/01_create_tables.sql
  notebooks/01_collect_and_ingest.py
  notebooks/02_forecast_proxy_baseline.py
  notebooks/03_forecast_lane_sarimax.py
  pipelines/pl_air_freight_weekly.json   # descriptive stub
```

---

## Troubleshooting

| Issue | Fix |
|---|---|
| Cannot reach Freightos from Fabric | Use hybrid Path A (collect outside Fabric) |
| Package missing | `%pip install statsmodels pandas pyyaml requests` in notebook first cell |
| Direct Lake not updating | Wait for table commit; refresh semantic model |
| Duplicate rates | Ingest uses append + `collection_runs` watermark; dedupe in views |
