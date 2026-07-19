from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.jobs.models import JobPosting
from app.jobs.schema import NormalizedJob


def save_new_jobs(session: Session, jobs: list[NormalizedJob]) -> tuple[int, int]:
    """Inserts jobs, skipping ones that already exist (same source +
    external_id). Returns (saved_count, skipped_count).

    Relies on the DB's unique constraint rather than a SELECT-then-INSERT
    check for each job — fewer round trips, and correct even if this ever
    runs concurrently."""
    saved = 0
    skipped = 0

    for job in jobs:
        existing = session.exec(
            select(JobPosting).where(
                JobPosting.source == job.source,
                JobPosting.external_id == job.external_id,
            )
        ).first()
        if existing:
            skipped += 1
            continue

        posting = JobPosting(**job.model_dump())
        session.add(posting)
        try:
            session.commit()
            saved += 1
        except IntegrityError:
            # Race condition insurance: something else inserted the same
            # (source, external_id) between our SELECT and this commit.
            session.rollback()
            skipped += 1

    return saved, skipped


def get_recent(session: Session, limit: int = 50) -> list[JobPosting]:
    return session.exec(
        select(JobPosting).order_by(JobPosting.collected_at.desc()).limit(limit)
    ).all()