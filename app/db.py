"""
Single place that creates the SQLModel engine. Everything else imports
`get_session` rather than constructing its own engine, so tests can override
the URL (e.g. sqlite in-memory) without touching business logic code.
"""
from collections.abc import Generator

from sqlmodel import Session, SQLModel, create_engine

from app.config import settings

_engine = None


def get_engine():
    global _engine
    if _engine is None:
        _engine = create_engine(settings.database_url)
    return _engine


def init_db() -> None:
    """Create all tables. Fine for MVP; replace with Alembic migrations once
    the schema needs to evolve without dropping data.

    Importing model modules here (not at the top of this file) is
    deliberate: SQLModel.metadata only knows about a table class once that
    class has been imported somewhere. Centralizing the imports in this one
    function means every new model module added in future slices gets
    picked up automatically just by adding one import line here — nobody
    has to remember to import it from the calling script too, which is
    exactly the gap that caused create_all() to silently create zero
    tables the first time this ran against a real database.
    """
    import app.jobs.models  # noqa: F401
    import app.resume.models  # noqa: F401

    SQLModel.metadata.create_all(get_engine())


def get_session() -> Generator[Session, None, None]:
    with Session(get_engine()) as session:
        yield session