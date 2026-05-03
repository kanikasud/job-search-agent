"""Collector that pulls a job-description corpus from a HuggingFace dataset.

Default dataset: jacob-hugging-face/job-descriptions (~19 k records, train split).

Fields in that dataset
-----------------------
position      str   – job title
company       str   – employer name
description   str   – full job-description text
job_skills    str   – comma-separated skill tags, e.g. "Python, SQL, Machine Learning"
work_type     str   – "Full-time" / "Part-time" / …  (kept in tags)
experience    str   – experience band (kept in tags)
location      str   – free-text city / country (may be absent or empty)

All fields are mapped into the canonical JobListing TypedDict that every
collector must produce.  Missing or falsy fields are normalised to safe
defaults so the transformer never raises on an incomplete record.

JSA-106 inspection notes
------------------------
Run  ``python -c "from datasets import load_dataset; ds = load_dataset(
  'jacob-hugging-face/job-descriptions', split='train');
  print(ds.features); print(ds[0])"``
to reproduce the field inspection step before modifying the transformer.
"""

from __future__ import annotations

from job_search_agent.collectors.base import JobListing
from job_search_agent.logger import get_logger

logger = get_logger(__name__)

_DEFAULT_DATASET = "jacob-hugging-face/job-descriptions"
_DEFAULT_SPLIT = "train"


def collect(
    dataset_name: str = _DEFAULT_DATASET,
    split: str = _DEFAULT_SPLIT,
) -> list[JobListing]:
    """Load *dataset_name* from HuggingFace and return canonical JobListings.

    Each row is assigned a stable ``source_id`` of ``"<dataset_name>/<row_index>"``
    so that repeated runs are idempotent when upserted via the SQLite
    ``(source, source_id)`` unique constraint.

    Returns an empty list if the dataset cannot be loaded.
    """
    try:
        from datasets import load_dataset  # heavy import — kept local
    except ImportError:
        logger.error("huggingface: 'datasets' package is not installed")
        return []

    logger.info("huggingface: loading dataset %r split=%r", dataset_name, split)
    try:
        ds = load_dataset(dataset_name, split=split)
    except Exception as exc:  # noqa: BLE001
        logger.error("huggingface: failed to load dataset: %s", exc)
        return []

    logger.info("huggingface: loaded %d records", len(ds))

    results: list[JobListing] = []
    for idx, row in enumerate(ds):
        results.append(_normalize(row, dataset_name, idx))

    logger.info("huggingface: transformed %d records", len(results))
    return results


def _normalize(row: dict, dataset_name: str, idx: int) -> JobListing:
    """Map a single HuggingFace dataset row to the canonical JobListing shape."""
    source_id = f"{dataset_name}/{idx}"

    title = str(row.get("position") or "").strip()
    company = str(row.get("company") or "").strip()
    description = str(row.get("description") or "").strip() or None

    location_raw = str(row.get("location") or "").strip()
    location = location_raw or None

    tags = _parse_tags(row)

    return JobListing(
        source_id=source_id,
        source="huggingface",
        title=title,
        company=company,
        location=location,
        url="",
        tags=tags,
        salary_min=None,
        salary_max=None,
        posted_at="",
        description=description,
    )


def _parse_tags(row: dict) -> list[str]:
    """Build a deduplicated tag list from job_skills, work_type, and experience."""
    tags: list[str] = []

    skills_raw = str(row.get("job_skills") or "")
    for skill in skills_raw.split(","):
        skill = skill.strip()
        if skill:
            tags.append(skill)

    for extra_field in ("work_type", "experience"):
        value = str(row.get(extra_field) or "").strip()
        if value and value not in tags:
            tags.append(value)

    return tags
