from datetime import datetime, timezone

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class ResumeVersion(SQLModel, table=True):
    __tablename__ = "resume_versions"

    id: int | None = Field(default=None, primary_key=True)
    version_number: int
    is_latest: bool = Field(default=True, index=True)
    source_filename: str
    uploaded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    raw_text: str
    # Stored as JSON rather than normalized tables: this data is always read/written
    # as a whole StructuredResume, never queried by sub-field, so normalizing it
    # would add join complexity with no real benefit at this scale.
    structured: dict = Field(sa_column=Column(JSON))
