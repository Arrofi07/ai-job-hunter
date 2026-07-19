from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session

from app.db import get_session
from app.jobs import repository
from app.jobs.adzuna_collector import AdzunaConfigError
from app.jobs.collector import SearchFilters
from app.jobs.service import run_collection

router = APIRouter(prefix="/jobs", tags=["jobs"])


class CollectRequest(BaseModel):
    location: str
    experience_level: str
    job_type: str | None = None
    remote: str | None = None
    date_posted_days: int | None = None
    company: str | None = None
    salary_min: int | None = None
    keywords: list[str] | None = None


@router.post("/collect")
def collect_jobs(body: CollectRequest, session: Session = Depends(get_session)):
    filters = SearchFilters(**body.model_dump())
    try:
        return run_collection(session, filters)
    except AdzunaConfigError as e:
        raise HTTPException(500, str(e)) from e


@router.get("/recent")
def recent_jobs(limit: int = 50, session: Session = Depends(get_session)):
    jobs = repository.get_recent(session, limit=limit)
    return [
        {
            "id": j.id,
            "source": j.source,
            "title": j.title,
            "company": j.company,
            "location": j.location,
            "url": j.url,
            "status": j.status,
            "collected_at": j.collected_at,
        }
        for j in jobs
    ]