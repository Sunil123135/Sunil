# GitHub Actions Cron — Codebase Connected to GitHub

This is the **easiest code-first cron**: no VM to babysit. GitHub schedules the collector; you sync outputs into Fabric.

## What you get

- Weekly cron in `.github/workflows/weekly-collect.yml`  
- Also `workflow_dispatch` so Power Automate / n8n can trigger on demand  
- Artifacts uploaded in Actions  
- Optional SharePoint / OneLake upload step  

---

## Step-by-step

### 1. Push this repo to GitHub
Already on branch `cursor/air-freight-rate-collector-124a`. Merge PR or push to `master`.

### 2. Enable Actions
Repo → **Settings** → **Actions** → allow workflows.

### 3. (Optional) Add secrets
Repo → **Settings** → **Secrets and variables** → **Actions**:

| Secret | Purpose |
|---|---|
| `SHAREPOINT_TENANT_ID` | Graph upload |
| `SHAREPOINT_CLIENT_ID` | App registration |
| `SHAREPOINT_CLIENT_SECRET` | App secret |
| `SHAREPOINT_SITE_ID` | Target site |
| `SHAREPOINT_DRIVE_ID` | Documents drive |
| `FABRIC_TRIGGER_URL` | Pipeline job URL (optional) |
| `FABRIC_SPN_TOKEN` | Or use OIDC later |

If you skip SharePoint secrets, the workflow still runs and stores **Actions artifacts** you can download / sync manually.

### 4. Verify workflow file
`.github/workflows/weekly-collect.yml` schedules:
```yaml
on:
  schedule:
    - cron: "30 0 * * 0"   # Sunday 00:30 UTC
  workflow_dispatch:
```

### 5. Run once manually
Actions → **Weekly Air Freight Collect** → **Run workflow**.

### 6. Connect to Fabric
Pick one:
- **A.** Download artifact → upload to Lakehouse `Files/incoming/` (manual smoke test)  
- **B.** Enable SharePoint upload job → OneLake shortcut → Fabric ingest notebook  
- **C.** Add a final workflow step calling Fabric pipeline HTTP API  

---

## Hybrid with Power Automate

Power Automate scheduled flow → GitHub `workflow_dispatch` → (Action uploads to SharePoint) → Power Automate file-created flow → Fabric refresh + email.

See `POWER_AUTOMATE.md`.

---

## Cron expression cheatsheet

| Schedule | Cron (UTC) |
|---|---|
| Weekly Sunday 00:30 | `30 0 * * 0` |
| Daily 01:00 (proxies only — not recommended for Freightos) | `0 1 * * *` |

Keep Freightos collection **weekly**.

---

## Self-hosted runner alternative

If GitHub.com egress is blocked/rate-limited differently:
1. Install a **self-hosted runner** on an Azure VM  
2. Pin the workflow: `runs-on: self-hosted`  
3. Same Python commands  

This is still “GitHub-connected cron,” just compute is yours.
