"""
Probe each data source, print status code, record count, and sample keys.
Run locally: python scripts/probe_sources.py
Requires: ADZUNA_APP_ID and ADZUNA_APP_KEY in .env (or environment).
"""

import json
import os
import sys
import urllib.request
import urllib.error
from dotenv import load_dotenv

load_dotenv()

HEADERS = {"User-Agent": "JSA-Bot/1.0 job-search-agent"}


# Sends a GET request and returns (status_code, response_body).
# HTTPError is caught and returned as a non-200 status so callers don't need try/except.
def get(url: str, headers: dict = HEADERS) -> tuple[int, bytes]:
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as e:
        return e.code, b""


# Probes The Muse public jobs API (no auth required).
# Fetches one page of 5 results and prints total count and field names from the first record.
def probe_muse():
    url = "https://www.themuse.com/api/public/jobs?page=0&per_page=5"
    status, body = get(url)
    print(f"\n[The Muse] status={status}")
    if status == 200:
        data = json.loads(body)
        results = data.get("results", [])
        print(f"  records in page: {len(results)} (total: {data.get('total', '?')})")
        if results:
            print(f"  sample keys: {list(results[0].keys())}")
    else:
        print(f"  error body: {body[:200]}")


# Probes the Remote OK open API dump (no auth, User-Agent header required).
# The first element of the array is a legal-notice object, not a job; filtered out via slug presence.
def probe_remoteok():
    url = "https://remoteok.com/api"
    status, body = get(url)
    print(f"\n[Remote OK] status={status}")
    if status == 200:
        data = json.loads(body)
        jobs = [r for r in data if r.get("slug")]
        print(f"  record count: {len(jobs)}")
        if jobs:
            print(f"  sample keys: {list(jobs[0].keys())}")
    else:
        print(f"  error body: {body[:200]}")


# Probes the Adzuna jobs API (requires ADZUNA_APP_ID and ADZUNA_APP_KEY in .env).
# Uses country=in for India; falls back to country=gb if credentials are absent.
# def probe_adzuna():
#     app_id = os.getenv("ADZUNA_APP_ID", "")
#     app_key = os.getenv("ADZUNA_APP_KEY", "")
#     country = "in"
#     if not app_id or not app_key:
#         print("\n[Adzuna] SKIPPED — ADZUNA_APP_ID / ADZUNA_APP_KEY not set in .env")
#         print("  Falling back to country=gb with placeholder credentials for key shape check.")
#         country = "gb"
#         app_id = app_id or "YOUR_APP_ID"
#         app_key = app_key or "YOUR_APP_KEY"
#
#     url = (
#         f"https://api.adzuna.com/v1/api/jobs/{country}/search/1"
#         f"?app_id={app_id}&app_key={app_key}&results_per_page=5"
#         f"&what=data+scientist&content-type=application/json"
#     )
#     status, body = get(url)
#     print(f"\n[Adzuna country={country}] status={status}")
#     if status == 200:
#         data = json.loads(body)
#         results = data.get("results", [])
#         print(f"  records in page: {len(results)} (total: {data.get('count', '?')})")
#         if results:
#             print(f"  sample keys: {list(results[0].keys())}")
#     else:
#         print(f"  error body: {body[:300]}")


if __name__ == "__main__":
    probe_muse()
    probe_remoteok()
    # probe_adzuna()
    print()
