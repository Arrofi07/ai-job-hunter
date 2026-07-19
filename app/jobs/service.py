import logging

from sqlmodel import Session

from app.jobs.adzuna_collector import AdzunaCollector
from app.jobs.collector import SearchFilters
from app.jobs.repository import save_new_jobs

logger = logging.getLogger(__name__)


def run_collection(session: Session, filters: SearchFilters) -> dict:
    """FR2 + FR7: collect postings matching filters, persist only the new
    ones. Returns a summary dict rather than raw objects — this is what
    both the manual-trigger endpoint and (later) the daily scheduler job
    will report."""
    collector = AdzunaCollector()
    jobs = collector.collect(filters)
    saved, skipped = save_new_jobs(session, jobs)

    logger.info(
        "Job collection run: %d found, %d new, %d duplicates skipped",
        len(jobs), saved, skipped,
    )
    return {"found": len(jobs), "saved": saved, "skipped_duplicates": skipped}