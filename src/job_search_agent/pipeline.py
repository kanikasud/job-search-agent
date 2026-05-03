"""Pipeline entry point: collect jobs from all free sources and return aggregated results."""

import json
import sys
from pathlib import Path

from job_search_agent.collectors import remote_ok, the_muse
from job_search_agent.collectors.base import JobListing
from job_search_agent.logger import get_logger

logger = get_logger(__name__)


def run(muse_max_pages: int = 10) -> list[JobListing]:
    """Collect jobs from The Muse and Remote OK, returning the combined list."""
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
    return all_jobs


if __name__ == "__main__":
    output_path = Path(sys.argv[1]) if len(sys.argv) > 1 else None

    jobs = run()

    if output_path:
        output_path.write_text(json.dumps(jobs, indent=2))
        print(f"Wrote {len(jobs)} jobs to {output_path}")
    else:
        print(json.dumps(jobs, indent=2))
