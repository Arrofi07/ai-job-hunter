import json
from unittest.mock import MagicMock

import pytest

from app.resume.extractor import ExtractionError, extract_structured_resume

VALID_LLM_JSON = json.dumps(
    {
        "education": [
            {"institution": "TU Berlin", "degree": "M.Sc. Computer Science", "start_date": "2022", "end_date": "2024"}
        ],
        "experience": [
            {
                "company": "Acme Corp",
                "title": "Data Scientist",
                "location": "Berlin",
                "start_date": "2021",
                "end_date": "2023",
                "highlights": ["Built ML pipelines for churn prediction"],
            }
        ],
        "projects": [{"name": "Churn Predictor", "technologies": ["XGBoost", "pandas"]}],
        "skills": [{"name": "Python"}, {"name": "SQL"}],
        "certifications": [{"name": "AWS Certified Cloud Practitioner", "issuer": "Amazon"}],
        "languages": [{"name": "English", "proficiency": "Fluent"}],
    }
)


def test_extracts_valid_json_into_structured_resume():
    llm_client = MagicMock()
    llm_client.generate.return_value = VALID_LLM_JSON

    result = extract_structured_resume("raw resume text", llm_client)

    assert result.education[0].institution == "TU Berlin"
    assert result.experience[0].company == "Acme Corp"
    assert result.skills[0].name == "Python"


def test_strips_markdown_code_fences():
    llm_client = MagicMock()
    llm_client.generate.return_value = f"```json\n{VALID_LLM_JSON}\n```"

    result = extract_structured_resume("raw resume text", llm_client)

    assert result.experience[0].company == "Acme Corp"


def test_raises_extraction_error_on_invalid_json():
    llm_client = MagicMock()
    llm_client.generate.return_value = "not json at all"

    with pytest.raises(ExtractionError, match="did not return valid JSON"):
        extract_structured_resume("raw resume text", llm_client)


def test_raises_extraction_error_on_schema_mismatch():
    llm_client = MagicMock()
    # Missing required fields (institution/degree) inside education entries
    llm_client.generate.return_value = json.dumps({"education": [{"foo": "bar"}]})

    with pytest.raises(ExtractionError, match="did not match StructuredResume schema"):
        extract_structured_resume("raw resume text", llm_client)


def test_empty_sections_produce_empty_lists():
    llm_client = MagicMock()
    llm_client.generate.return_value = "{}"

    result = extract_structured_resume("raw resume text", llm_client)

    assert result.education == []
    assert result.experience == []
