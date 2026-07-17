from datetime import datetime, timezone

from sqlalchemy import JSON, Column, UniqueConstraint
from sqlmodel import Field, SQLModel


class JobPosting(SQLModel, table=True):
    __tablename__ = "job_postings"
    __table_args__ = (
        # FR7: duplicate jobs are never recommended again — enforced at the
        # DB level, not just in application logic, so it holds even if a
        # future code path forgets to check first.
        UniqueConstraint("source", "external_id", name="uq_job_source_external_id"),
    )

    id: int | None = Field(default=None, primary_key=True)
    source: str
    external_id: str
    title: str
    company: str
    location: str | None = None
    description: str
    url: str
    posted_date: datetime | None = None
    salary_min: float | None = None
    salary_max: float | None = None
    raw: dict = Field(sa_column=Column(JSON))

    collected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # FR7 status lifecycle. Plain string, not an enum column, so adding a
    # new status later doesn't need a migration — validated at the
    # application layer instead (see JobStatus in this module).
    status: str = Field(default="discovered", index=True)


class JobStatus:
    """Not a DB enum on purpose (see JobPosting.status) — just the set of
    valid values the application layer checks against."""
    DISCOVERED = "discovered"
    RECOMMENDED = "recommended"
    APPLIED = "applied"
    INTERVIEW = "interview"
    OFFER = "offer"
    REJECTED = "rejected"
    ARCHIVED = "archived"

    ALL = {DISCOVERED, RECOMMENDED, APPLIED, INTERVIEW, OFFER, REJECTED, ARCHIVED}