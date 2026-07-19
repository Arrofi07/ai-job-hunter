from unittest.mock import patch

import pytest
from sqlmodel import Session, SQLModel, create_engine

from app.jobs.collector import SearchFilters
from app.jobs.models import JobPosting  # noqa: F401
from app.jobs.schema import NormalizedJob
from app.jobs.service import run_collection


@pytest.fixture
def session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    with Session(engine) as s:
        yield s


def _fake_jobs(n: int) -> list[NormalizedJob]:
    return [
        NormalizedJob(
            source="adzuna",
            external_id=str(i),
            title="Data Scientist",
            company="Acme",
            location="Berlin",
            description="desc",
            url=f"https://example.com/{i}",
            raw={},
        )
        for i in range(n)
    ]


def test_run_collection_reports_correct_summary(session):
    with patch("app.jobs.service.AdzunaCollector") as MockCollector:
        MockCollector.return_value.collect.return_value = _fake_jobs(3)

        result = run_collection(
            session, SearchFilters(location="Berlin", experience_level="entry")
        )

    assert result == {"found": 3, "saved": 3, "skipped_duplicates": 0}


def test_run_collection_reports_duplicates_on_second_run(session):
    with patch("app.jobs.service.AdzunaCollector") as MockCollector:
        MockCollector.return_value.collect.return_value = _fake_jobs(3)
        run_collection(session, SearchFilters(location="Berlin", experience_level="entry"))

        MockCollector.return_value.collect.return_value = _fake_jobs(3)
        result = run_collection(session, SearchFilters(location="Berlin", experience_level="entry"))

    assert result == {"found": 3, "saved": 0, "skipped_duplicates": 3}