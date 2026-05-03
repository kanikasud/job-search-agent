"""Unit tests for the The Muse collector."""

import json
from unittest.mock import MagicMock, patch

import pytest

from job_search_agent.collectors import the_muse


def _make_response(payload: object, status: int = 200):
    body = json.dumps(payload).encode()
    mock_resp = MagicMock()
    mock_resp.read.return_value = body
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    return mock_resp


_SAMPLE_JOB = {
    "id": 42,
    "name": "Senior Engineer",
    "company": {"name": "Acme Corp"},
    "locations": [{"name": "New York, NY"}],
    "categories": [{"name": "Engineering"}, {"name": "Software"}],
    "levels": [{"name": "Senior"}],
    "publication_date": "2024-05-01T00:00:00Z",
    "refs": {"landing_page": "https://www.themuse.com/jobs/acme/senior-engineer"},
}


@patch("urllib.request.urlopen")
def test_collect_normalizes_fields(mock_urlopen):
    page0 = {"results": [_SAMPLE_JOB], "total": 1}
    page1 = {"results": [], "total": 1}
    mock_urlopen.side_effect = [_make_response(page0), _make_response(page1)]

    jobs = the_muse.collect(max_pages=5)

    assert len(jobs) == 1
    job = jobs[0]
    assert job["source"] == "the_muse"
    assert job["source_id"] == "42"
    assert job["title"] == "Senior Engineer"
    assert job["company"] == "Acme Corp"
    assert job["location"] == "New York, NY"
    assert job["url"] == "https://www.themuse.com/jobs/acme/senior-engineer"
    assert job["tags"] == ["Engineering", "Software"]
    assert job["salary_min"] is None
    assert job["salary_max"] is None
    assert job["posted_at"] == "2024-05-01T00:00:00Z"
    assert job["description"] is None


@patch("urllib.request.urlopen")
def test_collect_paginates_until_empty(mock_urlopen):
    jobs_page = {"results": [_SAMPLE_JOB] * 3, "total": 6}
    empty_page = {"results": [], "total": 6}
    mock_urlopen.side_effect = [
        _make_response(jobs_page),
        _make_response(jobs_page),
        _make_response(empty_page),
    ]

    jobs = the_muse.collect(max_pages=10)
    assert len(jobs) == 6


@patch("urllib.request.urlopen")
def test_collect_respects_max_pages(mock_urlopen):
    jobs_page = {"results": [_SAMPLE_JOB], "total": 999}
    mock_urlopen.return_value = _make_response(jobs_page)

    jobs = the_muse.collect(max_pages=2)
    assert len(jobs) == 2
    assert mock_urlopen.call_count == 2


@patch("urllib.request.urlopen")
def test_collect_returns_empty_on_http_error(mock_urlopen):
    import urllib.error

    mock_urlopen.side_effect = urllib.error.URLError("connection refused")

    jobs = the_muse.collect(max_pages=5)
    assert jobs == []


@patch("urllib.request.urlopen")
def test_normalize_handles_missing_optional_fields(mock_urlopen):
    sparse_job = {"id": 7, "name": "Dev", "publication_date": "2024-01-01T00:00:00Z"}
    page0 = {"results": [sparse_job], "total": 1}
    page1 = {"results": [], "total": 1}
    mock_urlopen.side_effect = [_make_response(page0), _make_response(page1)]

    jobs = the_muse.collect(max_pages=5)

    assert len(jobs) == 1
    job = jobs[0]
    assert job["company"] == ""
    assert job["location"] is None
    assert job["tags"] == []
    assert job["url"] == ""
