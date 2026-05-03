"""Collector for the Remote OK public API (no authentication required)."""

import urllib.error

from job_search_agent.collectors.base import JobListing, fetch_json
from job_search_agent.filters import is_tech_job
from job_search_agent.logger import get_logger

logger = get_logger(__name__)

_API_URL = "https://remoteok.com/api"


def collect() -> list[JobListing]:
    """Fetch tech job listings from Remote OK and return them as canonical JobListings.

    Remote OK serves a single JSON dump. The first element is a legal-notice object
    (no ``slug`` field) and is filtered out automatically. Non-tech roles are
    discarded after normalization.
    Returns an empty list if the API is unreachable.
    """
    logger.info("remote_ok: fetching job dump")

    try:
        data = fetch_json(_API_URL)
    except urllib.error.URLError as exc:
        logger.error("remote_ok: request failed: %s", exc)
        return []

    jobs = [record for record in data if record.get("slug")]  # type: ignore[union-attr]
    logger.info("remote_ok: received %d jobs", len(jobs))

    listings = [_normalize(job) for job in jobs]
    tech_listings = [j for j in listings if is_tech_job(j)]
    logger.info(
        "remote_ok: %d tech jobs retained (dropped %d non-tech)",
        len(tech_listings),
        len(listings) - len(tech_listings),
    )
    return tech_listings


def _normalize(job: dict) -> JobListing:
    tags = job.get("tags") or []

    salary_min = _to_int(job.get("salary_min"))
    salary_max = _to_int(job.get("salary_max"))

    return JobListing(
        source_id=str(job.get("id", "")),
        source="remote_ok",
        title=job.get("position", ""),
        company=job.get("company", ""),
        location=job.get("location") or None,
        url=job.get("url", ""),
        tags=tags,
        salary_min=salary_min,
        salary_max=salary_max,
        posted_at=job.get("date", ""),
        description=None,
    )


def _to_int(value: object) -> int | None:
    """Convert a value to int, returning None for falsy or non-numeric inputs."""
    if not value:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
