from app.resume.chunking import chunk_resume
from app.resume.schema import Experience, Language, Skill, StructuredResume


def test_chunks_each_experience_entry_separately():
    resume = StructuredResume(
        experience=[
            Experience(company="Acme", title="Data Scientist", highlights=["Did X"]),
            Experience(company="Globex", title="ML Engineer", highlights=["Did Y"]),
        ]
    )

    chunks = chunk_resume(resume)
    exp_chunks = [c for c in chunks if c.section == "experience"]

    assert len(exp_chunks) == 2
    assert "Acme" in exp_chunks[0].text
    assert "Did X" in exp_chunks[0].text
    assert exp_chunks[0].index == 0
    assert exp_chunks[1].index == 1


def test_skills_combined_into_one_chunk():
    resume = StructuredResume(skills=[Skill(name="Python"), Skill(name="SQL")])

    chunks = chunk_resume(resume)
    skill_chunks = [c for c in chunks if c.section == "skills"]

    assert len(skill_chunks) == 1
    assert "Python" in skill_chunks[0].text
    assert "SQL" in skill_chunks[0].text


def test_empty_resume_produces_no_chunks():
    resume = StructuredResume()
    assert chunk_resume(resume) == []


def test_languages_include_proficiency_when_present():
    resume = StructuredResume(languages=[Language(name="German", proficiency="B2")])

    chunks = chunk_resume(resume)
    lang_chunk = [c for c in chunks if c.section == "languages"][0]

    assert "German" in lang_chunk.text
    assert "B2" in lang_chunk.text
