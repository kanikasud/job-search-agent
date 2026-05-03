"""Unit tests for the Remote OK collector."""

import json
from unittest.mock import MagicMock, patch

from job_search_agent.collectors import remote_ok


def _make_response(payload: object, status: int = 200):
    body = json.dumps(payload).encode()
    mock_resp = MagicMock()
    mock_resp.read.return_value = body
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    return mock_resp


_LEGAL_NOTICE = {"legal": "This API is provided by Remote OK..."}

_SAMPLE_JOB = {
    "id": 123,
    "slug": "remote-senior-engineer-acme",
    "position": "Senior Engineer",
    "company": "Acme Corp",
    "location": "Worldwide",
    "tags": ["python", "backend"],
    "salary_min": 80000,
    "salary_max": 120000,
    "date": "2024-05-01T00:00:00Z",
    "url": "https://remoteok.com/remote-jobs/123-remote-senior-engineer-acme",
}


@patch("urllib.request.urlopen")
def test_collect_normalizes_fields(mock_urlopen):
    mock_urlopen.return_value = _make_response([_LEGAL_NOTICE, _SAMPLE_JOB])

    jobs = remote_ok.collect()

    assert len(jobs) == 1
    job = jobs[0]
    assert job["source"] == "remote_ok"
    assert job["source_id"] == "123"
    assert job["title"] == "Senior Engineer"
    assert job["company"] == "Acme Corp"
    assert job["location"] == "Worldwide"
    assert job["url"] == "https://remoteok.com/remote-jobs/123-remote-senior-engineer-acme"
    assert job["tags"] == ["python", "backend"]
    assert job["salary_min"] == 80000
    assert job["salary_max"] == 120000
    assert job["posted_at"] == "2024-05-01T00:00:00Z"
    assert job["description"] is None


@patch("urllib.request.urlopen")
def test_collect_filters_legal_notice(mock_urlopen):
    mock_urlopen.return_value = _make_response([_LEGAL_NOTICE, _SAMPLE_JOB, _SAMPLE_JOB])

    jobs = remote_ok.collect()
    assert len(jobs) == 2


@patch("urllib.request.urlopen")
def test_collect_returns_empty_on_http_error(mock_urlopen):
    import urllib.error

    mock_urlopen.side_effect = urllib.error.URLError("timeout")

    jobs = remote_ok.collect()
    assert jobs == []


@patch("urllib.request.urlopen")
def test_normalize_null_salary_becomes_none(mock_urlopen):
    job = {**_SAMPLE_JOB, "salary_min": None, "salary_max": ""}
    mock_urlopen.return_value = _make_response([_LEGAL_NOTICE, job])

    jobs = remote_ok.collect()

    assert jobs[0]["salary_min"] is None
    assert jobs[0]["salary_max"] is None


@patch("urllib.request.urlopen")
def test_normalize_null_location_becomes_none(mock_urlopen):
    job = {**_SAMPLE_JOB, "location": ""}
    mock_urlopen.return_value = _make_response([_LEGAL_NOTICE, job])

    jobs = remote_ok.collect()
    assert jobs[0]["location"] is None


@patch("urllib.request.urlopen")
def test_collect_empty_api_response(mock_urlopen):
    mock_urlopen.return_value = _make_response([_LEGAL_NOTICE])

    jobs = remote_ok.collect()
    assert jobs == []


@patch("urllib.request.urlopen")
def test_collect_drops_non_tech_jobs(mock_urlopen):
    non_tech = {**_SAMPLE_JOB, "id": 999, "slug": "marketing-manager", "position": "Marketing Manager", "tags": ["marketing", "brand"]}
    mock_urlopen.return_value = _make_response([_LEGAL_NOTICE, _SAMPLE_JOB, non_tech])

    jobs = remote_ok.collect()
    assert len(jobs) == 1
    assert jobs[0]["title"] == "Senior Engineer"
