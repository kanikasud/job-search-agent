"""Collector for The Muse public jobs API (no authentication required)."""

import time
import urllib.error

from job_search_agent.collectors.base import JobListing, fetch_json
from job_search_agent.logger import get_logger

logger = get_logger(__name__)

_BASE_URL = "https://www.themuse.com/api/public/jobs"
_PER_PAGE = 100
# The Muse allows ~500 requests/day; a 0.5 s pause keeps well within limits.
_PAGE_DELAY_SECONDS = 0.5


def collect(max_pages: int = 10) -> list[JobListing]:
    """Fetch job listings from The Muse and return them as canonical JobListings.

    Paginates until all results are fetched or *max_pages* is reached.
    Returns an empty list if the API is unreachable.
    """
    listings: list[JobListing] = []

    for page in range(max_pages):
        url = f"{_BASE_URL}?page={page}&per_page={_PER_PAGE}"
        logger.info("the_muse: fetching page %d", page)

        try:
            data = fetch_json(url)
        except urllib.error.URLError as exc:
            logger.error("the_muse: request failed (page %d): %s", page, exc)
            break

        results = data.get("results", [])  # type: ignore[union-attr]
        if not results:
            logger.info("the_muse: no more results at page %d", page)
            break

        for job in results:
            listings.append(_normalize(job))

        logger.info("the_muse: page %d — %d jobs (total so far: %d)", page, len(results), len(listings))

        if page < max_pages - 1:
            time.sleep(_PAGE_DELAY_SECONDS)

    return listings


def _normalize(job: dict) -> JobListing:
    locations = job.get("locations") or []
    location = locations[0].get("name") if locations else None

    categories = job.get("categories") or []
    tags = [c["name"] for c in categories if c.get("name")]

    return JobListing(
        source_id=str(job["id"]),
        source="the_muse",
        title=job.get("name", ""),
        company=(job.get("company") or {}).get("name", ""),
        location=location,
        url=(job.get("refs") or {}).get("landing_page", ""),
        tags=tags,
        salary_min=None,
        salary_max=None,
        posted_at=job.get("publication_date", ""),
        description=None,
    )
