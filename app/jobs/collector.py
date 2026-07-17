from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.jobs.schema import NormalizedJob


@dataclass
class SearchFilters:
    """FR2 filters. Required fields have no default; optional ones do.
    Not every collector will support every optional field — collectors
    silently ignore filters they can't apply rather than erroring, since
    the alternative (every collector needing to support every filter)
    doesn't scale as more sources get added."""
    location: str
    experience_level: str  # free text for now — see AdzunaCollector docstring for why
    job_type: str | None = None
    remote: str | None = None  # "remote" | "hybrid" | "onsite"
    date_posted_days: int | None = None
    company: str | None = None
    salary_min: int | None = None
    keywords: list[str] | None = None


class JobCollector(ABC):
    @abstractmethod
    def collect(self, filters: SearchFilters) -> list[NormalizedJob]:
        raise NotImplementedError