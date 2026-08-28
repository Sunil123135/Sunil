# Air Freight — All Flows (Download Index)

One folder with every **importable orchestration flow** in this project.

## Quick download

From the repo root:

```bash
zip -r air-freight-flows.zip flows/
```

Or download individual files from the table below.

---

## Files in this folder

| File | Platform | Purpose | How to import |
|------|----------|---------|---------------|
| `n8n_air_freight_weekly.json` | **n8n** (self-hosted) | Weekly collect → forecast → OneLake sync → Fabric trigger | n8n → Workflows → Import from File |
| `n8n_air_freight_trigger_github.json` | **n8n Cloud** | Schedule → GitHub `workflow_dispatch` | Same |
| `github_weekly-collect.yml` | **GitHub Actions** | Weekly cron + manual dispatch; collect + forecast + optional SharePoint/Fabric | Copy to `.github/workflows/` in your repo |
| `fabric_pl_air_freight_weekly.json` | **Microsoft Fabric** | Pipeline spec: Notebook 01 → 02 → (03) | Recreate in Fabric UI (stub reference) |
| `sync_to_fabric.sh` | **VM / n8n Execute Command** | azcopy CSVs to OneLake `Files/incoming/` | Run from cron or n8n node |
| `POWER_AUTOMATE_SETUP.md` | **Power Automate** | Step-by-step (no JSON export — build in make.powerautomate.com) | Follow manual steps |

---

## Recommended stack

```
n8n OR GitHub Actions  →  OneLake/SharePoint  →  Fabric pipeline  →  Power BI  →  Power Automate email
```

---

## Schedule alignment (UTC)

| Flow | Cron | Time |
|------|------|------|
| n8n / GitHub collect | `30 0 * * 0` | Sunday 00:30 |
| Fabric pipeline | `0 1 * * 0` | Sunday 01:00 (after upload) |

---

## Environment variables

### n8n self-hosted (`n8n_air_freight_weekly.json`)

| Variable | Required |
|----------|----------|
| `AIR_FREIGHT_DIR` | Yes — path to cloned repo |
| `ONELAKE_URL` | For azcopy sync |
| `FABRIC_PIPELINE_URL` | Optional HTTP trigger |
| `FABRIC_TOKEN` | Optional Bearer token |

### n8n Cloud (`n8n_air_freight_trigger_github.json`)

| Variable | Required |
|----------|----------|
| `GITHUB_OWNER` | Yes |
| `GITHUB_REPO` | Yes |
| `GITHUB_PAT` | Yes — `workflow` scope |

### GitHub Actions (`github_weekly-collect.yml`)

Optional secrets: `SHAREPOINT_*`, `FABRIC_TRIGGER_URL`, `FABRIC_SPN_TOKEN`

---

## Docs (full guides)

- `../docs/N8N.md` — n8n architecture + sequences
- `../docs/POWER_AUTOMATE.md` — Power Automate flows
- `../docs/GITHUB_ACTIONS_CRON.md` — GitHub Actions setup
- `../docs/FABRIC.md` — Fabric lakehouse + notebooks
- `../docs/ARCHITECTURE.md` — end-to-end diagram
