# Migrate to a dedicated GitHub repository

This project was developed inside `Sunil123135/Sunil` but is meant to live in its **own repository**.

## Option A — One command (recommended)

Requires [GitHub CLI](https://cli.github.com/) logged in as **Sunil123135** with permission to create repositories.

```bash
git clone -b air-freight-rate-collector https://github.com/Sunil123135/Sunil.git air-freight-rate-collector
cd air-freight-rate-collector
gh repo create Sunil123135/air-freight-rate-collector \
  --public \
  --description "Free-source air cargo freight rate collector and forecast pipeline (BOM-focused lanes)" \
  --source=. \
  --remote=origin \
  --push
```

This creates `https://github.com/Sunil123135/air-freight-rate-collector` and pushes `main`.

## Option B — GitHub website

1. Open https://github.com/new
2. Repository name: `air-freight-rate-collector`
3. Public, **no** README / .gitignore / license
4. Create repository
5. In your terminal:

```bash
git clone -b air-freight-rate-collector https://github.com/Sunil123135/Sunil.git air-freight-rate-collector
cd air-freight-rate-collector
git remote set-url origin https://github.com/Sunil123135/air-freight-rate-collector.git
git push -u origin main
```

## After migration

1. Enable **GitHub Actions** in the new repo (Settings → Actions).
2. Close or ignore PR #2 on `Sunil/Sunil` (do not merge — that mixes notebooks + this project).
3. Optional: delete branch `air-freight-rate-collector` from `Sunil/Sunil` once the new repo is verified.
4. Reconnect schedulers (n8n / Power Automate) to the new repo URL for `workflow_dispatch`.

## What is in this standalone repo

- Python collector + forecast (`src/`)
- Fabric notebooks (`fabric/`)
- n8n + Power Automate flows (`n8n/`, `flows/`)
- GitHub Actions weekly cron (`.github/workflows/weekly-collect.yml`)
- Full documentation (`docs/`)

**Not included:** ML notebooks, Cloudflare `moneycontrol-gemini-proxy` worker, or other unrelated files from `Sunil/Sunil`.
