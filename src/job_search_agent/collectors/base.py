"""Shared types and HTTP helper for all collectors."""

import json
import urllib.error
import urllib.request
from typing import TypedDict

_HEADERS = {"User-Agent": "JSA-Bot/1.0 job-search-agent"}
_TIMEOUT = 15


class JobListing(TypedDict):
    """Canonical job record produced by every collector.

    Field names match the SQLAlchemy model that JSA-26 will define.
    """

    source_id: str        # original ID from the source API
    source: str           # "the_muse" | "remote_ok"
    title: str
    company: str
    location: str | None
    url: str
    tags: list[str]
    salary_min: int | None
    salary_max: int | None
    posted_at: str        # ISO 8601 date string (YYYY-MM-DD or full datetime)
    description: str | None


def fetch_json(url: str, extra_headers: dict[str, str] | None = None) -> object:
    """Fetch *url* and return the parsed JSON body.

    Raises urllib.error.URLError / urllib.error.HTTPError on network or HTTP failure.
    """
    headers = {**_HEADERS, **(extra_headers or {})}
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
        return json.loads(resp.read())
