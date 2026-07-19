from unittest.mock import MagicMock, patch

import pytest

from app.config import settings
from app.jobs.adzuna_collector import AdzunaCollector, AdzunaConfigError
from app.jobs.collector import SearchFilters

# Shaped exactly like Adzuna's own documented example response —
# see developer.adzuna.com/docs/search
SAMPLE_RESPONSE = {
    "results": [
        {
            "id": "129698749",
            "title": "Data Scientist",
            "description": "Great data science role...",
            "created": "2026-07-01T18:07:39Z",
            "redirect_url": "https://adzuna.de/jobs/land/ad/129698749",
            "location": {
                "area": ["Germany", "Berlin"],
                "display_name": "Berlin, Germany",
            },
            "company": {"display_name": "Acme Corp"},
            "category": {"label": "IT Jobs", "tag": "it-jobs"},
            "salary_min": 55000,
            "salary_max": 70000,
            "contract_type": "permanent",
        }
    ]
}


@pytest.fixture(autouse=True)
def fake_adzuna_creds():
    original_id, original_key = settings.adzuna_app_id, settings.adzuna_app_key
    settings.adzuna_app_id = "fake-id"
    settings.adzuna_app_key = "fake-key"
    yield
    settings.adzuna_app_id, settings.adzuna_app_key = original_id, original_key


def test_raises_config_error_when_credentials_missing():
    settings.adzuna_app_id = None
    with pytest.raises(AdzunaConfigError):
        AdzunaCollector()


def test_collect_normalizes_response_into_normalized_job():
    mock_response = MagicMock()
    mock_response.json.return_value = SAMPLE_RESPONSE
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.get", return_value=mock_response) as mock_get:
        collector = AdzunaCollector()
        jobs = collector.collect(
            SearchFilters(location="Berlin", experience_level="entry level", keywords=["data scientist"])
        )

    assert len(jobs) == 1
    job = jobs[0]
    assert job.source == "adzuna"
    assert job.external_id == "129698749"
    assert job.title == "Data Scientist"
    assert job.company == "Acme Corp"
    assert job.location == "Berlin, Germany"
    assert job.salary_min == 55000
    assert job.url == "https://adzuna.de/jobs/land/ad/129698749"

    # Confirm request shape matches the documented API
    call_args = mock_get.call_args
    assert call_args.args[0] == "https://api.adzuna.com/v1/api/jobs/de/search/1"
    params = call_args.kwargs["params"]
    assert params["app_id"] == "fake-id"
    assert params["app_key"] == "fake-key"
    assert "entry level" in params["what"]
    assert "data scientist" in params["what"]
    assert params["where"] == "Berlin"


def test_missing_company_defaults_to_unknown():
    response_missing_company = {
        "results": [
            {
                "id": "1",
                "title": "Some Job",
                "redirect_url": "https://example.com/1",
                "location": {"display_name": "Berlin"},
                "company": {},
            }
        ]
    }
    mock_response = MagicMock()
    mock_response.json.return_value = response_missing_company
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.get", return_value=mock_response):
        collector = AdzunaCollector()
        jobs = collector.collect(SearchFilters(location="Berlin", experience_level=""))

    assert jobs[0].company == "Unknown"


def test_empty_results_returns_empty_list():
    mock_response = MagicMock()
    mock_response.json.return_value = {"results": []}
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.get", return_value=mock_response):
        collector = AdzunaCollector()
        jobs = collector.collect(SearchFilters(location="Berlin", experience_level=""))

    assert jobs == []