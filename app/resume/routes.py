from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlmodel import Session

from app.db import get_session
from app.llm import LLMClient
from app.resume import repository
from app.resume.extractor import ExtractionError
from app.resume.parser import EmptyResumeError
from app.resume.schema import StructuredResume
from app.resume.service import ingest_resume

router = APIRouter(prefix="/resume", tags=["resume"])


def get_llm_client() -> LLMClient:
    # A dependency, not a module-level singleton, so tests can override it
    # via FastAPI's dependency_overrides without touching real config.
    return LLMClient()


@router.post("")
async def upload_resume(
    file: UploadFile,
    session: Session = Depends(get_session),
    llm_client: LLMClient = Depends(get_llm_client),
):
    if file.content_type != "application/pdf":
        raise HTTPException(400, "Resume must be a PDF")

    pdf_bytes = await file.read()
    try:
        version = ingest_resume(session, pdf_bytes, file.filename, llm_client)
    except EmptyResumeError as e:
        raise HTTPException(422, str(e)) from e
    except ExtractionError as e:
        raise HTTPException(502, f"Failed to structure resume: {e}") from e

    return {
        "id": version.id,
        "version_number": version.version_number,
        "uploaded_at": version.uploaded_at,
        "structured": version.structured,
    }


@router.get("/latest")
def get_latest_resume(session: Session = Depends(get_session)):
    version = repository.get_latest(session)
    if version is None:
        raise HTTPException(404, "No resume has been uploaded yet")

    return {
        "id": version.id,
        "version_number": version.version_number,
        "uploaded_at": version.uploaded_at,
        "structured": StructuredResume.model_validate(version.structured),
    }
