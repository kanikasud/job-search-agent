"""Unit tests for the HuggingFace collector (JSA-108)."""

from unittest.mock import MagicMock, patch

from job_search_agent.collectors import huggingface


def _make_dataset(rows: list[dict]):
    """Return a minimal mock that behaves like a HuggingFace Dataset."""
    ds = MagicMock()
    ds.__len__ = MagicMock(return_value=len(rows))
    ds.__iter__ = MagicMock(return_value=iter(rows))
    return ds


_SAMPLE_ROW = {
    "position_title": "Machine Learning Engineer",
    "company_name": "Acme AI",
    "job_description": "Build ML pipelines at scale.",
    "job_skills": "Python, TensorFlow, Docker",
    "work_type": "Full-time",
    "experience": "Mid-Senior level",
    "location": "San Francisco, CA",
}


# ---------------------------------------------------------------------------
# collect()
# ---------------------------------------------------------------------------


@patch("job_search_agent.collectors.huggingface.load_dataset", create=True)
def test_collect_returns_canonical_listings(mock_load):
    mock_load.return_value = _make_dataset([_SAMPLE_ROW])

    with patch.dict("sys.modules", {"datasets": MagicMock(load_dataset=mock_load)}):
        jobs = huggingface.collect("test/dataset", split="train")

    assert len(jobs) == 1
    job = jobs[0]
    assert job["source"] == "huggingface"
    assert job["title"] == "Machine Learning Engineer"
    assert job["company"] == "Acme AI"
    assert job["description"] == "Build ML pipelines at scale."
    assert job["location"] == "San Francisco, CA"
    assert job["salary_min"] is None
    assert job["salary_max"] is None
    assert job["url"] == ""
    assert job["posted_at"] == ""


@patch("job_search_agent.collectors.huggingface.load_dataset", create=True)
def test_collect_source_id_is_stable(mock_load):
    rows = [_SAMPLE_ROW, {**_SAMPLE_ROW, "position": "Data Scientist"}]
    mock_load.return_value = _make_dataset(rows)

    with patch.dict("sys.modules", {"datasets": MagicMock(load_dataset=mock_load)}):
        jobs = huggingface.collect("myorg/myjobs", split="train")

    assert jobs[0]["source_id"] == "myorg/myjobs/0"
    assert jobs[1]["source_id"] == "myorg/myjobs/1"


@patch("job_search_agent.collectors.huggingface.load_dataset", create=True)
def test_collect_empty_dataset(mock_load):
    mock_load.return_value = _make_dataset([])

    with patch.dict("sys.modules", {"datasets": MagicMock(load_dataset=mock_load)}):
        jobs = huggingface.collect()

    assert jobs == []


@patch("job_search_agent.collectors.huggingface.load_dataset", create=True)
def test_collect_returns_empty_on_load_error(mock_load):
    mock_load.side_effect = Exception("network error")

    with patch.dict("sys.modules", {"datasets": MagicMock(load_dataset=mock_load)}):
        jobs = huggingface.collect()

    assert jobs == []


def test_collect_returns_empty_when_datasets_not_installed():
    # Setting sys.modules[name] = None tells Python the module is absent;
    # a plain pop() lets Python reimport from disk (package is installed).
    with patch.dict("sys.modules", {"datasets": None}):
        jobs = huggingface.collect()
    assert jobs == []


# ---------------------------------------------------------------------------
# _normalize()
# ---------------------------------------------------------------------------


def test_normalize_full_row():
    job = huggingface._normalize(_SAMPLE_ROW, "test/ds", 0)

    assert job["source"] == "huggingface"
    assert job["source_id"] == "test/ds/0"
    assert job["title"] == "Machine Learning Engineer"
    assert job["company"] == "Acme AI"
    assert job["description"] == "Build ML pipelines at scale."
    assert job["location"] == "San Francisco, CA"
    assert "Python" in job["tags"]
    assert "TensorFlow" in job["tags"]
    assert "Docker" in job["tags"]
    assert "Full-time" in job["tags"]
    assert "Mid-Senior level" in job["tags"]


def test_normalize_missing_optional_fields():
    row = {"position_title": "Engineer", "company_name": "Widgets Inc"}
    job = huggingface._normalize(row, "ds", 1)

    assert job["title"] == "Engineer"
    assert job["company"] == "Widgets Inc"
    assert job["location"] is None
    assert job["description"] is None
    assert job["tags"] == []


def test_normalize_fallback_to_legacy_field_names():
    # Collectors using old field names ("position", "company", "description") still work.
    row = {**_SAMPLE_ROW,
           "position_title": None, "position": "Fallback Title",
           "company_name": None, "company": "Fallback Corp",
           "job_description": None, "description": "Fallback desc"}
    job = huggingface._normalize(row, "ds", 99)
    assert job["title"] == "Fallback Title"
    assert job["company"] == "Fallback Corp"
    assert job["description"] == "Fallback desc"


def test_normalize_empty_strings_become_none():
    row = {**_SAMPLE_ROW, "location": "", "job_description": ""}
    job = huggingface._normalize(row, "ds", 2)

    assert job["location"] is None
    assert job["description"] is None


def test_normalize_none_values_become_none():
    row = {**_SAMPLE_ROW, "location": None, "job_description": None}
    job = huggingface._normalize(row, "ds", 3)

    assert job["location"] is None
    assert job["description"] is None


# ---------------------------------------------------------------------------
# _parse_tags()
# ---------------------------------------------------------------------------


def test_parse_tags_splits_skills_on_comma():
    tags = huggingface._parse_tags({"job_skills": "Python, SQL, dbt"})
    assert tags == ["Python", "SQL", "dbt"]


def test_parse_tags_includes_work_type_and_experience():
    row = {
        "job_skills": "Go",
        "work_type": "Contract",
        "experience": "Entry level",
    }
    tags = huggingface._parse_tags(row)
    assert "Go" in tags
    assert "Contract" in tags
    assert "Entry level" in tags


def test_parse_tags_deduplicates_extra_fields():
    # If work_type already appears in job_skills, it should not be added twice.
    row = {"job_skills": "Full-time, Python", "work_type": "Full-time"}
    tags = huggingface._parse_tags(row)
    assert tags.count("Full-time") == 1


def test_parse_tags_empty_skills():
    tags = huggingface._parse_tags({"job_skills": ""})
    assert tags == []


def test_parse_tags_missing_skills_key():
    tags = huggingface._parse_tags({})
    assert tags == []


def test_parse_tags_whitespace_only_skill_ignored():
    tags = huggingface._parse_tags({"job_skills": "Python,  , SQL"})
    assert "" not in tags
    assert "  " not in tags
    assert "Python" in tags
    assert "SQL" in tags


# ---------------------------------------------------------------------------
# Tech-job filtering in collect()
# ---------------------------------------------------------------------------

@patch("job_search_agent.collectors.huggingface.load_dataset", create=True)
def test_collect_drops_non_tech_rows(mock_load):
    non_tech_row = {
        "position_title": "Marketing Manager",
        "company_name": "Brand Co",
        "job_description": "Lead marketing campaigns.",
        "job_skills": "brand strategy, campaigns",
        "work_type": "Full-time",
        "experience": "Senior level",
        "location": "New York, NY",
    }
    mock_load.return_value = _make_dataset([_SAMPLE_ROW, non_tech_row])

    with patch.dict("sys.modules", {"datasets": MagicMock(load_dataset=mock_load)}):
        jobs = huggingface.collect("test/dataset", split="train")

    assert len(jobs) == 1
    assert jobs[0]["title"] == "Machine Learning Engineer"
