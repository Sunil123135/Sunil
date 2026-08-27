# Temporal (optional / advanced)

Temporal is **not required** for weekly air-freight collection. Use it only if you already run Temporal or need durable multi-step workflows.

## Minimal pattern

1. Deploy Temporal server (or Temporal Cloud).
2. Register workflow `AirFreightWeeklyWorkflow`.
3. Activity 1: run collector subprocess.
4. Activity 2: sync files to OneLake.
5. Activity 3: trigger Fabric pipeline HTTP API.
6. Schedule via Temporal Schedule API (cron `30 0 * * 0`).

## Stub

See `worker_stub.py` — educational skeleton showing where to call this repo's Python entrypoints.

## Prefer instead

GitHub Actions / n8n / Fabric Pipeline for MVP (see `TEMPORAL_AND_ALTERNATIVES.md`).
