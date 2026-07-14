from pathlib import Path

import pytest

from app.resume.parser import EmptyResumeError, extract_text

FIXTURES = Path(__file__).parent / "fixtures"


def test_extracts_text_from_pdf():
    pdf_bytes = (FIXTURES / "sample_resume.pdf").read_bytes()
    text = extract_text(pdf_bytes)

    assert "Jane Doe" in text
    assert "Acme Corp" in text
    assert "Python" in text


def test_raises_on_empty_pdf():
    import fitz

    doc = fitz.open()
    doc.new_page()  # blank page, no text
    empty_pdf_bytes = doc.tobytes()
    doc.close()

    with pytest.raises(EmptyResumeError):
        extract_text(empty_pdf_bytes)
