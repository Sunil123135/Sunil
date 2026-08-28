# AGENTS.md

## Cursor Cloud specific instructions

### What this repo is
A **standalone Python project** for collecting free-source air cargo freight rates (BOM-focused lanes),
building historical observations, and running proxy-based forecasts. Integrates with Fabric, Power BI,
n8n, Power Automate, and GitHub Actions.

### Quick start
```bash
pip install -r requirements.txt
PYTHONPATH=. python3 -m src.run_collect --all
PYTHONPATH=. python3 -m src.forecast_proxy_baseline
PYTHONPATH=. python3 -m pytest tests/ -q
```

### Weekly automation
- GitHub Actions: `.github/workflows/weekly-collect.yml` (Sunday 00:30 UTC)
- n8n flows: `n8n/` and `flows/`
- Fabric notebooks: `fabric/notebooks/`

### Gotchas
- Freightos public calculator is rate-limited — collect **weekly**, not daily.
- Quotes are marketplace **estimates**, not audited TAC indices.
- For Convex/cloud agent isolation when developing other backends: set `CONVEX_AGENT_MODE=anonymous`.

### Docs
Start at `docs/NEXT_STEPS.md` and `docs/ARCHITECTURE.md`.
