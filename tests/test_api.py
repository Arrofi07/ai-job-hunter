"""
TestClient tests for the parts of the API that don't need live Postgres/Qdrant.

Note on the SQLite fixture: FastAPI runs sync endpoints in a thread pool, and
default in-memory SQLite gives each new connection its own separate database
— so without `poolclass=StaticPool`, table-not-found errors appear randomly
depending on which worker thread handles the request. StaticPool pins every
session to one shared connection, which is the standard fix for this in
SQLModel/FastAPI test setups (and irrelevant in production, where the real
Postgres URL handles connection pooling normally).

The full upload flow (POST /resume) additionally needs a live Qdrant
instance and isn't covered here — see SETUP.md for running it manually
against `docker compose up`.
"""
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy.pool import StaticPool

from app.db import get_session
from app.main import app
from app.resume.routes import get_llm_client


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


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_latest_resume_404_before_any_upload(client):
    r = client.get("/resume/latest")
    assert r.status_code == 404


def test_upload_rejects_non_pdf(client):
    r = client.post(
        "/resume", files={"file": ("resume.txt", b"not a pdf", "text/plain")}
    )
    assert r.status_code == 400
