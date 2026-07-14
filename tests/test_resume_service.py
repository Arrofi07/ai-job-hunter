from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from sqlmodel import Session, SQLModel, create_engine

from app.resume import repository
from app.resume.models import ResumeVersion  # noqa: F401
from app.resume.service import ingest_resume

FIXTURES = Path(__file__).parent / "fixtures"

FAKE_LLM_JSON = """
{
  "experience": [{"company": "Acme Corp", "title": "Data Scientist", "highlights": ["Built ML pipelines"]}],
  "skills": [{"name": "Python"}]
}
"""


@pytest.fixture
def session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    with Session(engine) as s:
        yield s


def test_full_ingestion_pipeline(session):
    pdf_bytes = (FIXTURES / "sample_resume.pdf").read_bytes()

    fake_llm = MagicMock()
    fake_llm.generate.return_value = FAKE_LLM_JSON

    with patch("app.resume.service.embed_texts", return_value=[[0.1] * 384]) as mock_embed, \
         patch("app.resume.service.ensure_collection") as mock_ensure, \
         patch("app.resume.service.upsert_vectors") as mock_upsert, \
         patch("app.resume.service.delete_by_payload") as mock_delete:

        version = ingest_resume(session, pdf_bytes, "sample_resume.pdf", fake_llm)

    # Postgres side: structured resume was parsed, validated, and stored
    assert version.id is not None
    assert version.version_number == 1
    assert version.structured["experience"][0]["company"] == "Acme Corp"
    assert repository.get_latest(session).id == version.id

    # Embedding side: pipeline reached out to embed + store, with the right collection
    mock_ensure.assert_called_once()
    assert mock_ensure.call_args.args[0] == "resume_chunks"
    mock_embed.assert_called_once()
    mock_delete.assert_called_once_with("resume_chunks", "resume_version_id", version.id)
    mock_upsert.assert_called_once()


def test_second_ingestion_creates_new_version_not_overwrite(session):
    pdf_bytes = (FIXTURES / "sample_resume.pdf").read_bytes()
    fake_llm = MagicMock()
    fake_llm.generate.return_value = FAKE_LLM_JSON

    with patch("app.resume.service.embed_texts", return_value=[[0.1] * 384]), \
         patch("app.resume.service.ensure_collection"), \
         patch("app.resume.service.upsert_vectors"), \
         patch("app.resume.service.delete_by_payload"):
        v1 = ingest_resume(session, pdf_bytes, "sample_resume.pdf", fake_llm)
        v2 = ingest_resume(session, pdf_bytes, "sample_resume.pdf", fake_llm)

    assert v1.id != v2.id
    assert v2.version_number == 2
    assert repository.get_latest(session).id == v2.id
