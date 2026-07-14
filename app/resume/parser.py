"""Raw text extraction from a resume PDF. Deliberately dumb — no layout
inference, no LLM here. Structuring happens in extractor.py, one step later,
so this stays trivially testable and swappable if we ever need OCR for
scanned resumes."""
import fitz  # PyMuPDF


class EmptyResumeError(Exception):
    """Raised when a PDF has no extractable text (e.g. it's a scanned image)."""


def extract_text(pdf_bytes: bytes) -> str:
    with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
        pages = [page.get_text() for page in doc]

    text = "\n".join(pages).strip()
    if not text:
        raise EmptyResumeError(
            "No extractable text found in the PDF. If this is a scanned "
            "resume (image-only), it needs OCR first — not supported yet."
        )
    return text
