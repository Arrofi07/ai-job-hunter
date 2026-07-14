"""Turns raw resume text into StructuredResume via the LLM (FR1: structured
resume sections). Uses LLMTask.STRUCTURED — this is exactly the kind of
cheap, deterministic-ish extraction task Groq should handle, per our routing."""
import json
import re

from app.llm import LLMClient
from app.config import LLMTask
from app.resume.schema import StructuredResume

_SYSTEM_PROMPT = """\
You extract structured data from resumes. You will be given raw resume text
(extracted from a PDF, so spacing/line breaks may be imperfect). Output ONLY
a single JSON object matching this shape — no prose, no markdown fences:

{
  "education": [{"institution": "", "degree": "", "field_of_study": "", "start_date": "", "end_date": "", "description": ""}],
  "experience": [{"company": "", "title": "", "location": "", "start_date": "", "end_date": "", "highlights": [""]}],
  "projects": [{"name": "", "description": "", "technologies": [""], "url": ""}],
  "skills": [{"name": "", "category": ""}],
  "certifications": [{"name": "", "issuer": "", "date": ""}],
  "languages": [{"name": "", "proficiency": ""}]
}

Rules:
- Every field is optional except: education.institution, education.degree,
  experience.company, experience.title, projects.name, skills.name,
  certifications.name, languages.name. Omit a field entirely rather than
  guessing a value that isn't in the text.
- "highlights" should be the resume's own bullet points for that role,
  lightly cleaned up (fix obvious OCR/spacing artifacts only) — do not
  rewrite, summarize, or embellish the person's actual wording.
- If a section is absent from the resume, return an empty list for it.
- Do not invent institutions, companies, dates, or skills not present in the text.
"""


class ExtractionError(Exception):
    """Raised when the LLM's output can't be parsed/validated as a StructuredResume."""


def _strip_code_fences(text: str) -> str:
    # Models sometimes wrap JSON in ```json ... ``` despite instructions not to.
    match = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    return match.group(1).strip() if match else text.strip()


def extract_structured_resume(raw_text: str, llm_client: LLMClient) -> StructuredResume:
    response = llm_client.generate(
        LLMTask.STRUCTURED,
        prompt=raw_text,
        system=_SYSTEM_PROMPT,
    )

    cleaned = _strip_code_fences(response)
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ExtractionError(f"LLM did not return valid JSON: {e}\nRaw response: {response[:500]}") from e

    try:
        return StructuredResume.model_validate(data)
    except Exception as e:  # pydantic.ValidationError, but catch broadly for a clear wrapped error
        raise ExtractionError(f"LLM JSON did not match StructuredResume schema: {e}") from e
