"""Nightly cron runner using APScheduler with a 0-row collection health check."""

from __future__ import annotations

import os
from pathlib import Path

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from job_search_agent.logger import get_logger
from job_search_agent.pipeline import run as pipeline_run

logger = get_logger(__name__)

_DEFAULT_DB_PATH = Path(os.getenv("JOBS_DB_PATH", "jobs.db"))
_DEFAULT_HOUR = int(os.getenv("CRON_HOUR", "0"))
_DEFAULT_MINUTE = int(os.getenv("CRON_MINUTE", "0"))


def run_collection(db_path: Path | str = _DEFAULT_DB_PATH) -> tuple[int, int]:
    """Run the collection pipeline once and return *(inserted, skipped)*.

    Logs a WARNING when no new jobs are collected (0-row alert).
    """
    from job_search_agent.db import get_engine, init_db, make_session_factory
    from job_search_agent.ingest import upsert_jobs

    logger.info("scheduler: starting nightly collection run")
    jobs = pipeline_run(db_path=None)

    if not jobs:
        logger.warning("scheduler: health-check FAILED — pipeline returned 0 jobs (source down?)")
        return 0, 0

    engine = get_engine(db_path)
    init_db(engine)
    factory = make_session_factory(engine)
    with factory() as session:
        inserted, skipped = upsert_jobs(session, jobs)

    if inserted == 0:
        logger.warning(
            "scheduler: health-check FAILED — 0 new rows inserted "
            "(all %d jobs already seen or sources returned no new data)",
            skipped,
        )
    else:
        logger.info("scheduler: health-check OK — inserted=%d skipped=%d", inserted, skipped)

    return inserted, skipped


def start(
    db_path: Path | str = _DEFAULT_DB_PATH,
    hour: int = _DEFAULT_HOUR,
    minute: int = _DEFAULT_MINUTE,
) -> None:
    """Start the blocking nightly scheduler.

    Runs *run_collection* every day at *hour*:*minute* (local time).
    """
    scheduler = BlockingScheduler()
    trigger = CronTrigger(hour=hour, minute=minute)
    scheduler.add_job(run_collection, trigger=trigger, kwargs={"db_path": db_path})
    logger.info("scheduler: nightly job scheduled at %02d:%02d — press Ctrl+C to stop", hour, minute)
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("scheduler: shutting down")


if __name__ == "__main__":
    start()
