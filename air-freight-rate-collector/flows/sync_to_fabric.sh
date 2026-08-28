#!/usr/bin/env bash
# Example sync from a VM cron job into Fabric/OneLake using azcopy.
# Configure: ONELAKE_URL='https://onelake.dfs.fabric.microsoft.com/<workspace>/<lakehouse>/Files/incoming'
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
PROCESSED="$ROOT/data/processed"
: "${ONELAKE_URL:?Set ONELAKE_URL to Fabric OneLake incoming folder}"

azcopy copy "$PROCESSED/rates_observed.csv" "$ONELAKE_URL/" --overwrite=true
azcopy copy "$PROCESSED/proxies_macro.csv" "$ONELAKE_URL/" --overwrite=true
azcopy copy "$PROCESSED/proxy_forecast_baseline.csv" "$ONELAKE_URL/" --overwrite=true
echo "Synced to $ONELAKE_URL"
