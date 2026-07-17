"""
Normalized job posting shape, independent of which collector found it.
Every collector (AdzunaCollector today, others later) maps its source's
native response into this shape — nothing downstream (matching, ranking,
storage) needs to know which source a job came from.
"""
from datetime import datetime

from pydantic import BaseModel


class NormalizedJob(BaseModel):
    source: str  # "adzuna", later "greenhouse", "lever", etc.
    external_id: str  # the ID from the source's own system — dedup key together with `source`
    title: str
    company: str
    location: str | None = None
    description: str
    url: str
    posted_date: datetime | None = None
    salary_min: float | None = None
    salary_max: float | None = None
    raw: dict  # full original response for this job — kept for fields we don't map yet