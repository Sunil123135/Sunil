#!/usr/bin/env bash
# Create the dedicated GitHub repo and push this project.
# Requires: gh CLI authenticated as Sunil123135 with repo create permission.
set -euo pipefail

REPO_NAME="${REPO_NAME:-air-freight-rate-collector}"
OWNER="${GITHUB_OWNER:-Sunil123135}"

if ! command -v gh >/dev/null 2>&1; then
  echo "Install GitHub CLI: https://cli.github.com/" >&2
  exit 1
fi

if ! gh auth status >/dev/null 2>&1; then
  echo "Run: gh auth login" >&2
  exit 1
fi

if gh repo view "${OWNER}/${REPO_NAME}" >/dev/null 2>&1; then
  echo "Repository ${OWNER}/${REPO_NAME} already exists."
  git remote set-url origin "https://github.com/${OWNER}/${REPO_NAME}.git"
  git push -u origin main
else
  gh repo create "${OWNER}/${REPO_NAME}" \
    --public \
    --description "Free-source air cargo freight rate collector and forecast pipeline (BOM-focused lanes)" \
    --source=. \
    --remote=origin \
    --push
fi

echo "Done: https://github.com/${OWNER}/${REPO_NAME}"
