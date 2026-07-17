"""
Adzuna job collector. Request/response shapes below are copied from
developer.adzuna.com's own documented examples, not inferred — see
decisions log #20.

Known gap, not silently papered over: Adzuna has no "experience level"
parameter (no entry/mid/senior filter in their API). FR2 lists experience
level as a *required* filter, so this collector folds it into the free-text
`what` search term instead (e.g. "entry level data scientist") rather than
pretending there's a structured filter that doesn't exist. This is a
real precision tradeoff — free-text keyword matching on experience level is
much noisier than a real filter would be — worth knowing going in.
"""
import httpx

from app.config import settings
from app.jobs.collector import JobCollector, SearchFilters
from app.jobs.schema import NormalizedJob

BASE_URL = "https://api.adzuna.com/v1/api/jobs"


class AdzunaConfigError(Exception):
    pass


class AdzunaCollector(JobCollector):
    def __init__(self, results_per_page: int = 50):
        if not settings.adzuna_app_id or not settings.adzuna_app_key:
            raise AdzunaConfigError(
                "ADZUNA_APP_ID and ADZUNA_APP_KEY must be set in .env. "
                "Register for free at https://developer.adzuna.com/signup"
            )
        self.results_per_page = results_per_page

    def collect(self, filters: SearchFilters) -> list[NormalizedJob]:
        what = " ".join(filters.keywords) if filters.keywords else ""
        if filters.experience_level:
            what = f"{filters.experience_level} {what}".strip()

        params = {
            "app_id": settings.adzuna_app_id,
            "app_key": settings.adzuna_app_key,
            "results_per_page": self.results_per_page,
            "what": what,
            "where": filters.location,
            "content-type": "application/json",
        }
        if filters.salary_min:
            params["salary_min"] = filters.salary_min
        if filters.job_type == "full_time":
            params["full_time"] = 1
        elif filters.job_type == "part_time":
            params["part_time"] = 1
        if filters.company:
            params["company"] = filters.company

        url = f"{BASE_URL}/{settings.adzuna_country}/search/1"
        response = httpx.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        return [self._normalize(job) for job in data.get("results", [])]

    def _normalize(self, job: dict) -> NormalizedJob:
        location = job.get("location", {}).get("display_name")
        company = job.get("company", {}).get("display_name", "Unknown")

        return NormalizedJob(
            source="adzuna",
            external_id=str(job["id"]),
            title=job["title"],
            company=company,
            location=location,
            description=job.get("description", ""),
            url=job["redirect_url"],
            posted_date=job.get("created"),
            salary_min=job.get("salary_min"),
            salary_max=job.get("salary_max"),
            raw=job,
        )