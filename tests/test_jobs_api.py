from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app.db import get_session
from app.jobs.schema import NormalizedJob
from app.main import app
from app.resume.routes import get_llm_client
from unittest.mock import MagicMock


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)

    def override_session():
        with Session(engine) as s:
            yield s

    app.dependency_overrides[get_session] = override_session
    app.dependency_overrides[get_llm_client] = lambda: MagicMock()

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def test_recent_jobs_empty_before_any_collection(client):
    r = client.get("/jobs/recent")
    assert r.status_code == 200
    assert r.json() == []


def test_collect_endpoint_returns_summary(client):
    fake_job = NormalizedJob(
        source="adzuna", external_id="1", title="Data Scientist", company="Acme",
        location="Berlin", description="desc", url="https://example.com/1", raw={},
    )
    with patch("app.jobs.service.AdzunaCollector") as MockCollector:
        MockCollector.return_value.collect.return_value = [fake_job]

        r = client.post(
            "/jobs/collect",
            json={"location": "Berlin", "experience_level": "entry level"},
        )

    assert r.status_code == 200
    assert r.json() == {"found": 1, "saved": 1, "skipped_duplicates": 0}

    r = client.get("/jobs/recent")
    assert len(r.json()) == 1
    assert r.json()[0]["title"] == "Data Scientist"