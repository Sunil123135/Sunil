# n8n — Complete Weekly Air Freight Flow

n8n is a strong **orchestration** option when you want a visual workflow without living entirely inside Power Automate.

## When to use n8n

- You can self-host n8n (Docker) or use n8n Cloud  
- You want retries, branching, Slack/Teams webhooks easily  
- You still land data in Fabric/SharePoint for Power BI  

## Architecture with n8n

```
n8n Schedule (Sun 00:30 UTC)
  → Execute Command / SSH / Webhook to runner
      → python -m src.run_collect --all
      → python -m src.forecast_proxy_baseline
  → Upload CSVs to SharePoint OR OneLake
  → HTTP trigger Fabric pipeline (optional)
  → HTTP refresh Power BI dataset (optional)
  → Email / Slack notification
```

---

## Option N1 — Self-hosted n8n + Execute Command (simplest)

### Prerequisites
- VM/container with:
  - n8n
  - this git repo cloned at `/opt/air-freight-rate-collector`
  - Python venv with `requirements.txt`

### Import workflow
1. n8n → **Workflows** → **Import from File**  
2. Import `n8n/air_freight_weekly.json`  
3. Set env vars in n8n:
   - `AIR_FREIGHT_DIR=/opt/air-freight-rate-collector`
   - `SHAREPOINT_SITE=...` (if using upload)
   - `FABRIC_PIPELINE_URL=...` (optional)

### Nodes (what the JSON contains)
1. **Schedule Trigger** — weekly  
2. **Execute Command** — collect  
3. **Execute Command** — proxy forecast  
4. **Read Binary Files** — `data/processed/*.csv`  
5. **HTTP Request** — upload to SharePoint Graph **or** save to disk for Fabric shortcut  
6. **HTTP Request** — trigger Fabric pipeline (optional)  
7. **HTTP Request** — Power BI refresh (optional)  
8. **Send Email** / **Slack** — status  

### Execute Command examples
```bash
cd "$AIR_FREIGHT_DIR" && PYTHONPATH=. python3 -m src.run_collect --all
```
```bash
cd "$AIR_FREIGHT_DIR" && PYTHONPATH=. python3 -m src.forecast_proxy_baseline
```

---

## Option N2 — n8n Cloud (no local Execute Command)

n8n Cloud cannot run local Python. Pattern:
1. Schedule in n8n Cloud  
2. **HTTP Request** → GitHub `workflow_dispatch` (same as Power Automate)  
3. Wait / webhook callback from GitHub Action  
4. Notify  

Use `n8n/air_freight_trigger_github.json` for this variant.

---

## Option N3 — n8n only notifies; Fabric does work

1. Fabric Pipeline already scheduled  
2. n8n weekly checks Lakehouse/SQL for fresh `collection_runs`  
3. Alerts if stale (>8 days)

Good as a monitoring layer.

---

## Rate-limit tip

Put a **Wait** node of 1–2 minutes between heavy steps is unnecessary for weekly cadence; the collector already sleeps between Freightos calls. Do **not** run the collect node more than once per day.

---

## Mapping to Fabric

After n8n produces CSVs:
- Upload to `Files/incoming/` in Lakehouse, **or**
- Upload to SharePoint folder that is a OneLake shortcut, **or**
- Commit/push artifacts and let GitHub Action sync  

Then Fabric notebooks 01→02 run on schedule or via HTTP trigger.
