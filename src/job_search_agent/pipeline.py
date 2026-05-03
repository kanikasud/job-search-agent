"""Pipeline entry point: collect jobs from all free sources and persist to SQLite."""

import json
import sys
from pathlib import Path

from job_search_agent.collectors import remote_ok, the_muse
from job_search_agent.collectors.base import JobListing
from job_search_agent.db import get_engine, init_db, make_session_factory
from job_search_agent.ingest import upsert_jobs
from job_search_agent.logger import get_logger

logger = get_logger(__name__)


def run(
    muse_max_pages: int = 10,
    db_path: Path | str | None = None,
) -> list[JobListing]:
    """Collect jobs from The Muse and Remote OK, optionally persisting to *db_path*.

    Returns the combined list of canonical job dicts regardless of whether
    persistence is requested.
    """
    logger.info("pipeline: starting collection")

    muse_jobs = the_muse.collect(max_pages=muse_max_pages)
    remoteok_jobs = remote_ok.collect()

    all_jobs = muse_jobs + remoteok_jobs
    logger.info(
        "pipeline: done — the_muse=%d remote_ok=%d total=%d",
        len(muse_jobs),
        len(remoteok_jobs),
        len(all_jobs),
    )

    if db_path is not None:
        engine = get_engine(db_path)
        init_db(engine)
        factory = make_session_factory(engine)
        with factory() as session:
            inserted, skipped = upsert_jobs(session, all_jobs)
        logger.info("pipeline: db=%s inserted=%d skipped=%d", db_path, inserted, skipped)

    return all_jobs


if __name__ == "__main__":
    args = sys.argv[1:]
    output_path: Path | None = None
    db: Path | None = None

    for arg in args:
        if arg.endswith(".db"):
            db = Path(arg)
        else:
            output_path = Path(arg)

    jobs = run(db_path=db)

    if output_path:
        output_path.write_text(json.dumps(jobs, indent=2))
        print(f"Wrote {len(jobs)} jobs to {output_path}")
    elif db is None:
        print(json.dumps(jobs, indent=2))
