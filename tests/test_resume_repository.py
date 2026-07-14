import pytest
from sqlmodel import Session, SQLModel, create_engine

from app.resume import repository
from app.resume.models import ResumeVersion  # noqa: F401 -- registers the table with SQLModel metadata
from app.resume.schema import StructuredResume


@pytest.fixture
def session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    with Session(engine) as s:
        yield s


def test_first_upload_becomes_latest(session):
    version = repository.save_new_version(session, "resume.pdf", "raw text", StructuredResume())

    assert version.version_number == 1
    assert version.is_latest is True
    assert repository.get_latest(session).id == version.id


def test_second_upload_demotes_first(session):
    v1 = repository.save_new_version(session, "resume_v1.pdf", "raw text v1", StructuredResume())
    v2 = repository.save_new_version(session, "resume_v2.pdf", "raw text v2", StructuredResume())

    session.refresh(v1)
    assert v1.is_latest is False
    assert v2.is_latest is True
    assert v2.version_number == 2
    assert repository.get_latest(session).id == v2.id


def test_get_latest_returns_none_when_no_resume_uploaded(session):
    assert repository.get_latest(session) is None


def test_structured_resume_round_trips_through_storage(session):
    structured = StructuredResume.model_validate(
        {"skills": [{"name": "Python"}], "languages": [{"name": "German", "proficiency": "B2"}]}
    )
    version = repository.save_new_version(session, "resume.pdf", "raw text", structured)

    reloaded = repository.get_latest(session)
    reparsed = StructuredResume.model_validate(reloaded.structured)

    assert reparsed.skills[0].name == "Python"
    assert reparsed.languages[0].proficiency == "B2"
