"""Unit tests for the tech-job filter."""

import pytest

from job_search_agent.filters import is_tech_job


def _job(title: str, tags: list[str] | None = None) -> dict:
    return {
        "source_id": "1",
        "source": "test",
        "title": title,
        "company": "Co",
        "location": None,
        "url": "",
        "tags": tags or [],
        "salary_min": None,
        "salary_max": None,
        "posted_at": "",
        "description": None,
    }


# ---------------------------------------------------------------------------
# Title-based matches
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("title", [
    "Senior Software Engineer",
    "Backend Developer",
    "Frontend Developer",
    "Full-Stack Engineer",
    "DevOps Engineer",
    "Site Reliability Engineer",
    "Machine Learning Engineer",
    "Data Scientist",
    "Data Engineer",
    "Data Analyst",
    "Cloud Architect",
    "Infrastructure Engineer",
    "iOS Developer",
    "Android Developer",
    "Cybersecurity Engineer",
    "QA Engineer",
    "Technical Lead",
])
def test_tech_titles_pass(title):
    assert is_tech_job(_job(title)) is True


# ---------------------------------------------------------------------------
# Tag-based matches (non-tech title, tech tags)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("tags", [
    ["python"],
    ["javascript", "react"],
    ["aws", "terraform"],
    ["docker", "kubernetes"],
    ["machine learning", "pytorch"],
    ["engineering"],
    ["llm", "ai"],
])
def test_tech_tags_pass(tags):
    assert is_tech_job(_job("Specialist", tags=tags)) is True


# ---------------------------------------------------------------------------
# Non-tech jobs should be rejected
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("title,tags", [
    ("Marketing Manager", ["campaigns", "brand"]),
    ("Sales Representative", ["b2b", "crm"]),
    ("HR Business Partner", ["recruiting", "hr"]),
    ("Accountant", ["finance", "excel"]),
    ("Graphic Designer", ["photoshop", "illustrator"]),
    ("Customer Support Agent", ["zendesk", "support"]),
    ("Operations Manager", ["logistics", "supply chain"]),
])
def test_non_tech_jobs_rejected(title, tags):
    assert is_tech_job(_job(title, tags=tags)) is False


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

def test_empty_title_and_tags_rejected():
    assert is_tech_job(_job("", tags=[])) is False


def test_title_match_is_case_insensitive():
    assert is_tech_job(_job("SENIOR SOFTWARE ENGINEER")) is True


def test_tag_match_is_case_insensitive():
    assert is_tech_job(_job("Specialist", tags=["Python", "AWS"])) is True
