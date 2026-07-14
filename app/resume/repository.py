from sqlmodel import Session, select

from app.resume.models import ResumeVersion
from app.resume.schema import StructuredResume


def save_new_version(
    session: Session,
    source_filename: str,
    raw_text: str,
    structured: StructuredResume,
) -> ResumeVersion:
    """Persist a new resume version and demote any previous version's
    is_latest flag. FR1: 'always use the latest resume version' — this is
    the single place that invariant is enforced."""
    previous_latest = session.exec(
        select(ResumeVersion).where(ResumeVersion.is_latest == True)  # noqa: E712
    ).all()
    for version in previous_latest:
        version.is_latest = False
        session.add(version)

    next_version_number = (
        session.exec(select(ResumeVersion).order_by(ResumeVersion.version_number.desc())).first()
    )
    next_version_number = (next_version_number.version_number + 1) if next_version_number else 1

    new_version = ResumeVersion(
        version_number=next_version_number,
        is_latest=True,
        source_filename=source_filename,
        raw_text=raw_text,
        structured=structured.model_dump(),
    )
    session.add(new_version)
    session.commit()
    session.refresh(new_version)
    return new_version


def get_latest(session: Session) -> ResumeVersion | None:
    return session.exec(
        select(ResumeVersion).where(ResumeVersion.is_latest == True)  # noqa: E712
    ).first()
