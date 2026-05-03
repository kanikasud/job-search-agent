"""Unit tests for the ingest module (upsert_jobs)."""

import pytest

from job_search_agent.collectors.base import JobListing as CollectedJob
from job_search_agent.db import get_engine, init_db, make_session_factory
from job_search_agent.ingest import upsert_jobs
from job_search_agent.models import JobListing


def _make_job(**overrides) -> CollectedJob:
    defaults: CollectedJob = {
        "source_id": "1",
        "source": "the_muse",
        "title": "Software Engineer",
        "company": "Acme Corp",
        "location": "Remote",
        "url": "https://example.com/job/1",
        "tags": ["Python", "Backend"],
        "salary_min": None,
        "salary_max": None,
        "posted_at": "2024-05-01T00:00:00Z",
        "description": None,
    }
    return {**defaults, **overrides}  # type: ignore[return-value]


@pytest.fixture()
def session():
    engine = get_engine(":memory:")
    init_db(engine)
    factory = make_session_factory(engine)
    with factory() as s:
        yield s


def test_upsert_inserts_new_jobs(session):
    jobs = [_make_job(source_id="1"), _make_job(source_id="2")]
    inserted, skipped = upsert_jobs(session, jobs)

    assert inserted == 2
    assert skipped == 0
    assert session.query(JobListing).count() == 2


def test_upsert_returns_zero_zero_for_empty_list(session):
    inserted, skipped = upsert_jobs(session, [])
    assert inserted == 0
    assert skipped == 0
    assert session.query(JobListing).count() == 0


def test_upsert_skips_duplicates(session):
    job = _make_job(source_id="42", source="remote_ok")
    upsert_jobs(session, [job])

    inserted, skipped = upsert_jobs(session, [job])

    assert inserted == 0
    assert skipped == 1
    assert session.query(JobListing).count() == 1


def test_upsert_same_source_id_different_sources_both_inserted(session):
    muse_job = _make_job(source_id="99", source="the_muse")
    remoteok_job = _make_job(source_id="99", source="remote_ok")

    inserted, skipped = upsert_jobs(session, [muse_job, remoteok_job])

    assert inserted == 2
    assert skipped == 0
    assert session.query(JobListing).count() == 2


def test_upsert_partial_duplicates(session):
    existing = _make_job(source_id="10", source="the_muse")
    upsert_jobs(session, [existing])

    new_job = _make_job(source_id="11", source="the_muse")
    inserted, skipped = upsert_jobs(session, [existing, new_job])

    assert inserted == 1
    assert skipped == 1
    assert session.query(JobListing).count() == 2


def test_upsert_persists_all_fields(session):
    job = _make_job(
        source_id="55",
        source="remote_ok",
        title="Staff Engineer",
        company="BigCo",
        location="Worldwide",
        url="https://remoteok.com/jobs/55",
        tags=["Go", "Distributed Systems"],
        salary_min=150000,
        salary_max=200000,
        posted_at="2024-06-15T12:00:00Z",
        description="An exciting role.",
    )
    upsert_jobs(session, [job])

    record = session.query(JobListing).filter_by(source_id="55", source="remote_ok").one()
    assert record.title == "Staff Engineer"
    assert record.company == "BigCo"
    assert record.location == "Worldwide"
    assert record.url == "https://remoteok.com/jobs/55"
    assert record.tags == ["Go", "Distributed Systems"]
    assert record.salary_min == 150000
    assert record.salary_max == 200000
    assert record.posted_at == "2024-06-15T12:00:00Z"
    assert record.description == "An exciting role."


def test_upsert_nullable_fields(session):
    job = _make_job(source_id="77", location=None, salary_min=None, salary_max=None, description=None)
    upsert_jobs(session, [job])

    record = session.query(JobListing).filter_by(source_id="77").one()
    assert record.location is None
    assert record.salary_min is None
    assert record.salary_max is None
    assert record.description is None


def test_upsert_multiple_calls_accumulate(session):
    batch1 = [_make_job(source_id=str(i)) for i in range(3)]
    batch2 = [_make_job(source_id=str(i)) for i in range(3, 6)]

    upsert_jobs(session, batch1)
    upsert_jobs(session, batch2)

    assert session.query(JobListing).count() == 6
