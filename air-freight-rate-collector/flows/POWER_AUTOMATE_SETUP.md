# Power Automate — Complete Step-by-Step Setup

This guide builds a **production-ready Power Automate flow** that:
1. Runs on a weekly schedule
2. Triggers data collection (via Azure Function **or** GitHub Actions **or** a hosted script)
3. Lands files in SharePoint / OneDrive (bridge to Fabric)
4. Optionally refreshes a Fabric/Power BI dataset
5. Emails a lane forecast summary

> Power Automate alone cannot easily run arbitrary Python. Use it as the **orchestrator + notifier**, and run the Python collector in one of the backends below.

---

## Prerequisites

- Microsoft 365 account with **Power Automate** (per-user or premium connectors as needed)
- SharePoint site (e.g. `https://contoso.sharepoint.com/sites/AirFreight`)
- Folder: `Shared Documents/AirFreight/incoming`
- Folder: `Shared Documents/AirFreight/processed`
- (Optional) Fabric workspace + Lakehouse + Power BI dataset
- (Optional) GitHub repo with Actions enabled **or** Azure Function

---

## Architecture choices for the “Run collector” step

| Backend | Power Automate action | When to use |
|---|---|---|
| **GitHub Actions** | HTTP → `workflow_dispatch` | Easiest code-first; already in this repo |
| **Azure Function** (Python timer alternative) | HTTP POST to function URL | Enterprise M365-centric |
| **n8n / self-hosted VM** | HTTP webhook | If n8n already exists |
| **Desktop flow (PAD)** | Run Python on a Windows VM | Last resort / on-prem |

This doc uses **Option 1: GitHub Actions** as primary, with notes for Azure Function.

---

## Part A — One-time SharePoint setup

1. Create SharePoint site **AirFreight** (Team site).
2. In **Documents**, create:
   - `incoming/` — raw collector drops
   - `processed/` — archived runs
   - `manual_quotes/` — human CSV uploads
   - `reports/` — emailed PDF/Excel exports (optional)
3. Create a SharePoint **List** named `AirFreight_Collection_Log` with columns:
   - `RunId` (Single line)
   - `Status` (Choice: Started, Success, Failed)
   - `RowsRates` (Number)
   - `RowsProxies` (Number)
   - `Message` (Multiple lines)
   - `RunTimeUtc` (Date/time)

---

## Part B — GitHub Actions backend (recommended with this repo)

1. Ensure workflow file exists: `.github/workflows/weekly-collect.yml` (in this repo).
2. Create a GitHub **Personal Access Token** (classic) with `repo` + `workflow` scopes **or** use a GitHub App.
3. In Power Automate → **Create** → **Automated cloud flow** is wrong here — use **Scheduled cloud flow**.

### B1. Create the scheduled flow

1. Go to https://make.powerautomate.com  
2. **Create** → **Scheduled cloud flow**  
3. Name: `AirFreight_Weekly_Collect_Forecast`  
4. Recurrence:
   - Frequency: **Week**
   - Interval: **1**
   - On these days: **Sunday**
   - Time: **00:30** (UTC) ≈ 06:00 IST  
5. Click **Create**.

### B2. Add steps (exact sequence)

#### Step 1 — Initialize variables
Add action **Initialize variable** (repeat as needed):

| Name | Type | Value |
|---|---|---|
| `RunId` | String | `concat('run-', utcNow('yyyyMMddTHHmmss'))` |
| `GitHubOwner` | String | `YOUR_GITHUB_USER_OR_ORG` |
| `GitHubRepo` | String | `YOUR_REPO_NAME` |
| `GitHubWorkflowFile` | String | `weekly-collect.yml` |

#### Step 2 — Log “Started” to SharePoint list
Action: **SharePoint – Create item**
- Site: AirFreight site
- List: `AirFreight_Collection_Log`
- RunId: `variables('RunId')`
- Status: `Started`
- RunTimeUtc: `utcNow()`
- Message: `Weekly collection triggered`

#### Step 3 — Trigger GitHub Actions workflow_dispatch
Action: **HTTP** (or **GitHub – Trigger a workflow run** if available in your tenant)

**Method:** `POST`  
**URI:**
```
https://api.github.com/repos/@{variables('GitHubOwner')}/@{variables('GitHubRepo')}/actions/workflows/@{variables('GitHubWorkflowFile')}/dispatches
```
**Headers:**
```
Accept: application/vnd.github+json
Authorization: Bearer @{parameters('GitHubPAT')}
X-GitHub-Api-Version: 2022-11-28
```
**Body:**
```json
{
  "ref": "master",
  "inputs": {
    "run_id": "@{variables('RunId')}"
  }
}
```

> Create a flow **Parameter** or **Azure Key Vault** secret named `GitHubPAT`. Do not hardcode.

#### Step 4 — Wait for artifact / file arrival
Action: **Do until** (timeout 30–45 minutes)

Condition example: SharePoint file exists  
`incoming/rates_observed_@{variables('RunId')}.csv`

Inside loop:
- **Delay** 2 minutes
- **SharePoint – Get file metadata using path** (or List folder)

Alternative simpler approach: skip polling; have GitHub Action write directly to SharePoint via Graph API, then use a **second flow** “When a file is created in SharePoint” to continue (Part C).

#### Step 5 — Copy into Fabric (two options)

**Option 5a — Fabric shortcut / OneLake path**  
If SharePoint is connected to Fabric via shortcut, skip copy.

**Option 5b — Call Fabric pipeline**  
Action: **HTTP** to Fabric Job Scheduler API (requires Fabric SPN):

```
POST https://api.fabric.microsoft.com/v1/workspaces/{workspaceId}/items/{pipelineId}/jobs/instances?jobType=Pipeline
Authorization: Bearer {fabric_token}
```

(See `FABRIC.md` → “Trigger pipeline from Power Automate”.)

#### Step 6 — Refresh Power BI dataset
Action: **Power BI – Refresh a dataset**
- Workspace: `AirFreight-Prod`
- Dataset: `Air Freight Rates & Forecasts`

#### Step 7 — Email summary
Action: **Office 365 Outlook – Send an email (V2)**

**To:** your ops DL  
**Subject:** `Air Freight weekly run @{variables('RunId')} – @{outputs('HTTP_status')}`  
**Body:** HTML table with:
- RunId
- Status
- Link to Power BI report
- Note: “Freightos attribution: https://www.freightos.com”

#### Step 8 — Update SharePoint log
Action: **SharePoint – Update item** → Status `Success` or `Failed` (use **Configure run after** on failures).

---

## Part C — Cleaner pattern: two flows (recommended)

### Flow C1 — `AirFreight_Schedule_Trigger`
- Recurrence weekly
- Dispatch GitHub Actions / call Azure Function
- Write SharePoint log Started

### Flow C2 — `AirFreight_On_File_Arrive`
- Trigger: **When a file is created (properties only)** on `incoming/`
- Filter: file name starts with `rates_observed`
- Actions:
  1. Move/copy file to Fabric Files or trigger Fabric pipeline
  2. Refresh Power BI
  3. Send email
  4. Move file to `processed/`

This avoids brittle “wait until” polling.

---

## Part D — Azure Function backend (alternative to GitHub)

1. Create Azure Function App (Python 3.11), Consumption or Flex.
2. Deploy a function `CollectAirFreight` that clones/runs this package or calls packaged code.
3. Protect with function key.
4. In Power Automate HTTP action:
   - POST `https://<app>.azurewebsites.net/api/CollectAirFreight?code=<key>`
   - Body: `{ "run_id": "..." }`
5. Function writes CSVs to SharePoint (Microsoft Graph) or directly to ADLS/OneLake.

Timer-trigger Azure Function can **replace** Power Automate schedule entirely if you want fewer moving parts.

---

## Part E — Manual quote capture flow (optional)

Name: `AirFreight_Manual_Quote_Upload`

1. Trigger: **When a file is created** in `manual_quotes/`
2. Condition: `.csv`
3. HTTP/Function: run `python -m src.ingest_manual_quotes --file ...`
4. Or: Fabric notebook that reads the CSV from Files and MERGEs into `rates_observed`

Template columns: see `config/manual_quote_template.csv`.

---

## Part F — Failure handling checklist

| Failure | Flow behavior |
|---|---|
| GitHub 401 | Email “PAT expired”; Status=Failed |
| Freightos 429 | Collector exits soft; email “partial collect — rotate lanes next week” |
| Power BI refresh fail | Email with dataset URL; don’t fail whole archive step |
| No new OK quotes | Email warning; still refresh proxies |

Use **Configure run after** → has failed / timed out on critical actions → send failure email.

---

## Part G — Connection references to create

1. SharePoint  
2. Office 365 Outlook  
3. Power BI  
4. HTTP (with Azure AD if calling Fabric API)  
5. (Optional) GitHub  

---

## Part H — Test plan

1. **Test manually**: Flow → Run → confirm GitHub workflow starts.  
2. Confirm artifact/CSV lands in `incoming/`.  
3. Confirm Flow C2 picks up file.  
4. Confirm Power BI refresh completes.  
5. Confirm email received.  
6. Force-fail PAT → confirm failure email.

---

## Minimal “no GitHub” Power Automate path

If you cannot use GitHub Actions:
1. Run collector on a small **always-on VM / Container Apps** job with cron.
2. Power Automate only does: **file arrive → Fabric refresh → email**.

Or use **n8n** for collection (see `N8N.md`) and Power Automate only for M365 email/Power BI refresh.

---

## Related files in this repo

- `.github/workflows/weekly-collect.yml` — collector cron + optional SharePoint upload script  
- `scripts/upload_to_sharepoint.py` — Graph upload helper  
- `docs/FABRIC.md` — Lakehouse load + forecast notebooks  
- `docs/N8N.md` — n8n alternative orchestrator  
