# Runbook

## Weekly happy path
1. Orchestrator triggers collector.
2. `rates_observed.csv` + `proxies_macro.csv` land in Fabric `Files/incoming/`.
3. Notebook 01 ingests → tables.
4. Notebook 02 writes proxy forecasts.
5. Power BI refreshes / Direct Lake updates.
6. Email/Slack sent.

## Freightos HTTP 429
- Symptom: `status=rate_limited` or many errors in `rates_observed`.
- Action: do nothing aggressive. Wait until next week.
- Reduce `freightos.max_requests_per_run` in `config/lanes.yaml`.
- Keep priority lanes first (BOM–LHR/FRA/DXB).

## No quotes (`numQuotes=0`)
- Lane may lack marketplace coverage.
- Fill `config/manual_quote_template.csv` from eCargoRates / forwarder and run `python -m src.ingest_manual_quotes`.

## Stale data
- Alert if `collection_runs.finished_at_utc` older than 8 days.

## Attribution
Include Freightos credit in any external dashboard: https://www.freightos.com
