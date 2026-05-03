"""Tests for the SQLAlchemy JobListing model and db helpers."""

import pytest
from sqlalchemy import inspect, text

from job_search_agent.db import get_engine, init_db, make_session_factory
from job_search_agent.models import JobListing


@pytest.fixture()
def session():
    engine = get_engine(":memory:")
    init_db(engine)
    factory = make_session_factory(engine)
    with factory() as s:
        yield s


def test_table_created(session):
    engine = session.get_bind()
    assert "job_listings" in inspect(engine).get_table_names()


def test_all_columns_present(session):
    engine = session.get_bind()
    col_names = {c["name"] for c in inspect(engine).get_columns("job_listings")}
    expected = {
        "id", "source_id", "source", "title", "company",
        "location", "url", "tags", "salary_min", "salary_max",
        "posted_at", "description",
    }
    assert expected.issubset(col_names)


def test_insert_and_retrieve(session):
    job = JobListing(
        source_id="123",
        source="the_muse",
        title="Senior Engineer",
        company="Acme Corp",
        location="New York, NY",
        url="https://example.com/job/123",
        tags=["Engineering", "Python"],
        salary_min=None,
        salary_max=None,
        posted_at="2024-05-01T00:00:00Z",
        description=None,
    )
    session.add(job)
    session.commit()

    retrieved = session.get(JobListing, job.id)
    assert retrieved.source == "the_muse"
    assert retrieved.title == "Senior Engineer"
    assert retrieved.tags == ["Engineering", "Python"]
    assert retrieved.location == "New York, NY"
    assert retrieved.salary_min is None


def test_unique_constraint_source_source_id(session):
    from sqlalchemy.exc import IntegrityError

    job1 = JobListing(
        source_id="42", source="remote_ok", title="Dev", company="Co",
        location=None, url="https://example.com", tags=[],
        salary_min=None, salary_max=None, posted_at="2024-01-01", description=None,
    )
    job2 = JobListing(
        source_id="42", source="remote_ok", title="Dev Duplicate", company="Co",
        location=None, url="https://example.com", tags=[],
        salary_min=None, salary_max=None, posted_at="2024-01-01", description=None,
    )
    session.add(job1)
    session.commit()

    session.add(job2)
    with pytest.raises(IntegrityError):
        session.commit()


def test_same_source_id_different_sources_allowed(session):
    job1 = JobListing(
        source_id="99", source="the_muse", title="Role A", company="Co",
        location=None, url="https://a.com", tags=[],
        salary_min=None, salary_max=None, posted_at="2024-01-01", description=None,
    )
    job2 = JobListing(
        source_id="99", source="remote_ok", title="Role B", company="Co",
        location=None, url="https://b.com", tags=[],
        salary_min=None, salary_max=None, posted_at="2024-01-01", description=None,
    )
    session.add_all([job1, job2])
    session.commit()

    count = session.query(JobListing).filter_by(source_id="99").count()
    assert count == 2


def test_nullable_fields(session):
    job = JobListing(
        source_id="1", source="remote_ok", title="Role", company="Co",
        location=None, url="https://example.com", tags=[],
        salary_min=None, salary_max=None, posted_at="2024-01-01", description=None,
    )
    session.add(job)
    session.commit()

    retrieved = session.get(JobListing, job.id)
    assert retrieved.location is None
    assert retrieved.salary_min is None
    assert retrieved.salary_max is None
    assert retrieved.description is None


def test_salary_fields(session):
    job = JobListing(
        source_id="2", source="remote_ok", title="Staff Eng", company="BigCo",
        location="Remote", url="https://example.com/2", tags=["Go"],
        salary_min=120000, salary_max=180000, posted_at="2024-03-15", description="Great role.",
    )
    session.add(job)
    session.commit()

    retrieved = session.get(JobListing, job.id)
    assert retrieved.salary_min == 120000
    assert retrieved.salary_max == 180000
