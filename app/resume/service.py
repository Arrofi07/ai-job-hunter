from sqlmodel import Session

from app.llm import LLMClient
from app.resume import parser, repository
from app.resume.chunking import chunk_resume
from app.resume.embeddings import EMBEDDING_DIM, embed_texts
from app.resume.extractor import extract_structured_resume
from app.resume.models import ResumeVersion
from app.resume.schema import StructuredResume
from app.vector_store import delete_by_payload, ensure_collection, upsert_vectors

RESUME_COLLECTION = "resume_chunks"


def ingest_resume(
    session: Session,
    pdf_bytes: bytes,
    source_filename: str,
    llm_client: LLMClient,
) -> ResumeVersion:
    """The full FR1 pipeline: PDF -> raw text -> structured JSON -> stored
    version -> chunked -> embedded -> stored in Qdrant.

    Order matters: we save the Postgres row *before* embedding, so if
    embedding fails (e.g. Qdrant unreachable) we still have the structured
    resume durably stored — matching/cover-letter generation degrade to "no
    semantic search yet" rather than losing the upload entirely. Re-running
    ingestion is idempotent-ish: it creates a new version, doesn't lose data.
    """
    raw_text = parser.extract_text(pdf_bytes)
    structured = extract_structured_resume(raw_text, llm_client)

    version = repository.save_new_version(
        session=session,
        source_filename=source_filename,
        raw_text=raw_text,
        structured=structured,
    )

    _embed_and_store(version, structured)
    return version


def _embed_and_store(version: ResumeVersion, structured: StructuredResume) -> None:
    chunks = chunk_resume(structured)
    if not chunks:
        return

    ensure_collection(RESUME_COLLECTION, vector_size=EMBEDDING_DIM)
    vectors = embed_texts([c.text for c in chunks])
    payloads = [
        {
            "resume_version_id": version.id,
            "section": c.section,
            "index": c.index,
            "text": c.text,
        }
        for c in chunks
    ]

    # Clear this version's old vectors first (relevant on re-ingestion of the
    # same version_id, which shouldn't normally happen, but cheap insurance
    # against duplicate points if it ever does).
    delete_by_payload(RESUME_COLLECTION, "resume_version_id", version.id)
    upsert_vectors(RESUME_COLLECTION, vectors, payloads)
