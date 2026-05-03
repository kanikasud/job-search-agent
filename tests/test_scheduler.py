"""Tests for the nightly scheduler and 0-row health check."""

from pathlib import Path
from unittest.mock import patch

import pytest

from job_search_agent.collectors.base import JobListing as CollectedJob
from job_search_agent.scheduler import run_collection


def _make_job(**overrides) -> CollectedJob:
    defaults: CollectedJob = {
        "source_id": "1",
        "source": "the_muse",
        "title": "Engineer",
        "company": "Acme",
        "location": "Remote",
        "url": "https://example.com/1",
        "tags": [],
        "salary_min": None,
        "salary_max": None,
        "posted_at": "2024-01-01T00:00:00Z",
        "description": None,
    }
    return {**defaults, **overrides}  # type: ignore[return-value]


@pytest.fixture()
def db_path(tmp_path: Path) -> Path:
    return tmp_path / "test_jobs.db"


def test_run_collection_inserts_new_jobs(db_path):
    jobs = [_make_job(source_id="1"), _make_job(source_id="2")]
    with patch("job_search_agent.scheduler.pipeline_run", return_value=jobs):
        inserted, skipped = run_collection(db_path)

    assert inserted == 2
    assert skipped == 0


def test_run_collection_skips_duplicates(db_path):
    jobs = [_make_job(source_id="99")]
    with patch("job_search_agent.scheduler.pipeline_run", return_value=jobs):
        run_collection(db_path)
        inserted, skipped = run_collection(db_path)

    assert inserted == 0
    assert skipped == 1


def test_run_collection_zero_row_alert_when_pipeline_empty(db_path):
    with patch("job_search_agent.scheduler.pipeline_run", return_value=[]):
        with patch("job_search_agent.scheduler.logger") as mock_logger:
            inserted, skipped = run_collection(db_path)

    assert inserted == 0
    assert skipped == 0
    mock_logger.warning.assert_called_once()
    assert "0 jobs" in mock_logger.warning.call_args[0][0]


def test_run_collection_zero_row_alert_when_all_duplicates(db_path):
    jobs = [_make_job(source_id="42")]
    with patch("job_search_agent.scheduler.pipeline_run", return_value=jobs):
        run_collection(db_path)

    with patch("job_search_agent.scheduler.pipeline_run", return_value=jobs):
        with patch("job_search_agent.scheduler.logger") as mock_logger:
            inserted, skipped = run_collection(db_path)

    assert inserted == 0
    assert skipped == 1
    mock_logger.warning.assert_called_once()
    assert "0 new rows" in mock_logger.warning.call_args[0][0]


def test_run_collection_no_warning_when_jobs_inserted(db_path):
    jobs = [_make_job(source_id="7")]
    with patch("job_search_agent.scheduler.pipeline_run", return_value=jobs):
        with patch("job_search_agent.scheduler.logger") as mock_logger:
            run_collection(db_path)

    mock_logger.warning.assert_not_called()


def test_run_collection_returns_counts(db_path):
    jobs = [_make_job(source_id=str(i)) for i in range(5)]
    with patch("job_search_agent.scheduler.pipeline_run", return_value=jobs):
        inserted, skipped = run_collection(db_path)

    assert inserted == 5
    assert skipped == 0
