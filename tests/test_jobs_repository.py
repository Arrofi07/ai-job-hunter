import pytest
from sqlmodel import Session, SQLModel, create_engine

from app.jobs import repository
from app.jobs.models import JobPosting  # noqa: F401 -- registers table
from app.jobs.schema import NormalizedJob


@pytest.fixture
def session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    with Session(engine) as s:
        yield s


def _job(external_id="1", **overrides) -> NormalizedJob:
    defaults = dict(
        source="adzuna",
        external_id=external_id,
        title="Data Scientist",
        company="Acme Corp",
        location="Berlin",
        description="desc",
        url="https://example.com/1",
        raw={},
    )
    defaults.update(overrides)
    return NormalizedJob(**defaults)


def test_saves_new_jobs(session):
    saved, skipped = repository.save_new_jobs(session, [_job("1"), _job("2")])
    assert saved == 2
    assert skipped == 0
    assert len(repository.get_recent(session)) == 2


def test_skips_duplicate_source_and_external_id(session):
    repository.save_new_jobs(session, [_job("1")])
    saved, skipped = repository.save_new_jobs(session, [_job("1")])

    assert saved == 0
    assert skipped == 1
    assert len(repository.get_recent(session)) == 1


def test_same_external_id_different_source_is_not_a_duplicate(session):
    repository.save_new_jobs(session, [_job("1", source="adzuna")])
    saved, skipped = repository.save_new_jobs(session, [_job("1", source="jsearch")])

    assert saved == 1
    assert skipped == 0


def test_mixed_batch_saves_new_and_skips_existing(session):
    repository.save_new_jobs(session, [_job("1")])
    saved, skipped = repository.save_new_jobs(session, [_job("1"), _job("2"), _job("3")])

    assert saved == 2
    assert skipped == 1
    assert len(repository.get_recent(session)) == 3