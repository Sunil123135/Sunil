# Temporal and Other Orchestrators — Options Comparison

You asked for **all easily implementable options**. Below is a practical comparison and when to bother with Temporal.

## Option matrix

| Tool | Ease | Best for | Fabric fit | Notes |
|---|---|---|---|---|
| **Fabric Pipeline schedule** | ★★★★☆ | Your stated Microsoft stack | Native | Preferred serving + model home |
| **Power Automate** | ★★★★★ | Email, SharePoint, M365 approvals | Excellent | Weak at running Python directly |
| **n8n** | ★★★★☆ | Visual flows, webhooks, self-host | Via file/HTTP | Great collector orchestrator |
| **GitHub Actions cron** | ★★★★★ | Code in GitHub, zero servers | Via upload/API | Best MVP cron for this repo |
| **Azure Functions timer** | ★★★★☆ | Azure-centric enterprise | ADLS/OneLake | Solid alternative to Actions |
| **Azure Container Apps Jobs** | ★★★☆☆ | Containerized weekly job | Good | Slightly more ops |
| **Temporal** | ★★☆☆☆ | Durable workflows, complex retries/saga | Via activities | Overkill for weekly CSV collect |
| **Prefect / Dagster / Airflow** | ★★★☆☆ | Data platform teams | Via I/O | Good if you already run them |
| **cron on a VM** | ★★★★★ | Absolute simplest Linux | scp/azcopy | Don't forget monitoring |

---

## Recommended combinations (easy → powerful)

### 1) Easiest Microsoft-aligned (recommended for you)
**GitHub Actions (collect) + Fabric notebooks (forecast) + Power BI + Power Automate (email)**

### 2) No GitHub
**n8n self-host (collect) + Fabric (forecast) + Power Automate (email)**  
or **Azure Function timer (collect) + Fabric**

### 3) All-in Fabric
**Fabric notebook collect+forecast scheduled pipeline**  
(only if outbound HTTP allowed)

### 4) Temporal (only if needed later)
Use Temporal when you have:
- multi-step human approvals  
- long-running scrapes with continue-as-new  
- many downstream systems needing exactly-once orchestration  

For a weekly 19-lane quote pull, Temporal adds infra cost without much benefit.

Stub worker: `temporal/worker_stub.py` + `temporal/README.md`.

---

## Azure Functions timer (sketch)

```python
import azure.functions as func
# run subprocess or import src.run_collect.main
```

Schedule: `0 30 0 * * 0`  
Then `azcopy` CSVs to OneLake.

---

## Plain Linux cron

```cron
30 0 * * 0  cd /opt/air-freight-rate-collector && PYTHONPATH=. /opt/venv/bin/python -m src.run_collect --all && PYTHONPATH=. /opt/venv/bin/python -m src.forecast_proxy_baseline && /opt/air-freight-rate-collector/scripts/cron/sync_to_fabric.sh
```

See `scripts/cron/sync_to_fabric.sh`.

---

## Decision rule

- If you live in **M365/Fabric** → Options **1 or 2**  
- If you want **zero Microsoft orchestration** → GitHub Actions + download to Fabric  
- If you need **workflow durability at scale** later → Temporal/Prefect, keep collector code unchanged (call `python -m src.run_collect`)  
