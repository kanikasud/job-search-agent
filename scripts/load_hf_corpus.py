"""One-time script to pull the HuggingFace job corpus and load it into the DB.

Usage
-----
    python scripts/load_hf_corpus.py [--db PATH] [--dataset NAME] [--split SPLIT]

Defaults
--------
    --db       jobs.db
    --dataset  jacob-hugging-face/job-descriptions
    --split    train

The script is idempotent: rows already present (matched by source + source_id)
are silently skipped via the SQLite ON CONFLICT DO NOTHING clause.

JSA-107
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

# Ensure the src tree is on sys.path when run directly.
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from job_search_agent.collectors import huggingface
from job_search_agent.db import get_engine, init_db, make_session_factory
from job_search_agent.ingest import upsert_jobs
from job_search_agent.logger import get_logger

logger = get_logger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Load HuggingFace job corpus into SQLite.")
    parser.add_argument("--db", default="jobs.db", help="Path to the SQLite database file.")
    parser.add_argument(
        "--dataset",
        default="jacob-hugging-face/job-descriptions",
        help="HuggingFace dataset identifier.",
    )
    parser.add_argument("--split", default="train", help="Dataset split to load.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    db_path = Path(args.db)
    logger.info("load_hf_corpus: using DB at %s", db_path)

    engine = get_engine(db_path)
    init_db(engine)

    t0 = time.perf_counter()
    listings = huggingface.collect(dataset_name=args.dataset, split=args.split)
    elapsed_fetch = time.perf_counter() - t0

    if not listings:
        logger.warning("load_hf_corpus: no records fetched — aborting")
        sys.exit(1)

    logger.info(
        "load_hf_corpus: fetched %d records in %.1fs", len(listings), elapsed_fetch
    )

    factory = make_session_factory(engine)
    t1 = time.perf_counter()
    with factory() as session:
        inserted, skipped = upsert_jobs(session, listings)
    elapsed_ingest = time.perf_counter() - t1

    logger.info(
        "load_hf_corpus: done — inserted=%d skipped=%d in %.1fs",
        inserted,
        skipped,
        elapsed_ingest,
    )
    print(
        f"Loaded {inserted} new jobs ({skipped} already existed) "
        f"from '{args.dataset}' into '{db_path}' in {elapsed_fetch + elapsed_ingest:.1f}s."
    )


if __name__ == "__main__":
    main()
