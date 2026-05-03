"""Persist collected job listings into the SQLite canonical store."""

from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from job_search_agent.collectors.base import JobListing as CollectedJob
from job_search_agent.logger import get_logger
from job_search_agent.models import JobListing

logger = get_logger(__name__)


def upsert_jobs(session: Session, listings: list[CollectedJob]) -> tuple[int, int]:
    """Insert *listings* into the DB, skipping records that already exist.

    Uniqueness is determined by the ``(source, source_id)`` constraint.
    Returns ``(inserted, skipped)`` counts.
    """
    if not listings:
        return 0, 0

    stmt = sqlite_insert(JobListing.__table__).values(listings)
    stmt = stmt.on_conflict_do_nothing(index_elements=["source", "source_id"])
    result = session.execute(stmt)
    session.commit()

    inserted = result.rowcount
    skipped = len(listings) - inserted
    logger.info("ingest: inserted=%d skipped=%d", inserted, skipped)
    return inserted, skipped
