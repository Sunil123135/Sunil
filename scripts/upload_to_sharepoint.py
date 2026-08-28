"""Upload processed CSVs to SharePoint via Microsoft Graph (app-only).

Required env:
  SHAREPOINT_TENANT_ID, SHAREPOINT_CLIENT_ID, SHAREPOINT_CLIENT_SECRET,
  SHAREPOINT_SITE_ID, SHAREPOINT_DRIVE_ID
Optional:
  SHAREPOINT_FOLDER=incoming
  RUN_ID
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import requests

from src import PROCESSED_DIR


def token() -> str:
    tid = os.environ["SHAREPOINT_TENANT_ID"]
    cid = os.environ["SHAREPOINT_CLIENT_ID"]
    secret = os.environ["SHAREPOINT_CLIENT_SECRET"]
    url = f"https://login.microsoftonline.com/{tid}/oauth2/v2.0/token"
    data = {
        "client_id": cid,
        "client_secret": secret,
        "scope": "https://graph.microsoft.com/.default",
        "grant_type": "client_credentials",
    }
    resp = requests.post(url, data=data, timeout=60)
    resp.raise_for_status()
    return resp.json()["access_token"]


def upload(file_path: Path, access_token: str) -> None:
    site_id = os.environ["SHAREPOINT_SITE_ID"]
    drive_id = os.environ["SHAREPOINT_DRIVE_ID"]
    folder = os.environ.get("SHAREPOINT_FOLDER", "incoming")
    run_id = os.environ.get("RUN_ID", "manual")
    remote_name = f"{file_path.stem}_{run_id}{file_path.suffix}"
    # simple upload (<4MB). For larger files use upload session.
    url = (
        f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives/{drive_id}/root:"
        f"/{folder}/{remote_name}:/content"
    )
    headers = {"Authorization": f"Bearer {access_token}"}
    with file_path.open("rb") as f:
        resp = requests.put(url, headers=headers, data=f, timeout=120)
    resp.raise_for_status()
    print(f"uploaded {remote_name}")


def main() -> int:
    required = [
        "SHAREPOINT_TENANT_ID",
        "SHAREPOINT_CLIENT_ID",
        "SHAREPOINT_CLIENT_SECRET",
        "SHAREPOINT_SITE_ID",
        "SHAREPOINT_DRIVE_ID",
    ]
    missing = [k for k in required if not os.environ.get(k)]
    if missing:
        print(f"Missing secrets: {missing}", file=sys.stderr)
        return 1

    access = token()
    for name in ["rates_observed.csv", "proxies_macro.csv", "proxy_forecast_baseline.csv", "collection_run_meta.json"]:
        path = PROCESSED_DIR / name
        if path.exists():
            upload(path, access)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
