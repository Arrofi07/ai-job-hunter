"""
Chunking strategy for resume embeddings: one chunk per meaningful entry
(each job, each project) rather than one giant resume-wide embedding.
This gives Slice 4 (matching) the ability to point at *which* experience
matched a job requirement, not just an overall similarity score — and it's
a small amount of extra code now vs. re-chunking everything later.
"""
from dataclasses import dataclass

from app.resume.schema import StructuredResume


@dataclass
class ResumeChunk:
    section: str  # "experience" | "project" | "education" | "skills" | "certifications" | "languages"
    index: int    # position within that section's list, for traceability back to the structured data
    text: str


def chunk_resume(resume: StructuredResume) -> list[ResumeChunk]:
    chunks: list[ResumeChunk] = []

    for i, exp in enumerate(resume.experience):
        parts = [f"{exp.title} at {exp.company}"]
        if exp.location:
            parts.append(exp.location)
        parts.extend(exp.highlights)
        chunks.append(ResumeChunk("experience", i, ". ".join(parts)))

    for i, proj in enumerate(resume.projects):
        parts = [proj.name]
        if proj.description:
            parts.append(proj.description)
        if proj.technologies:
            parts.append("Technologies: " + ", ".join(proj.technologies))
        chunks.append(ResumeChunk("project", i, ". ".join(parts)))

    for i, edu in enumerate(resume.education):
        parts = [f"{edu.degree} in {edu.field_of_study or ''}".strip(), edu.institution]
        if edu.description:
            parts.append(edu.description)
        chunks.append(ResumeChunk("education", i, ". ".join(p for p in parts if p)))

    if resume.skills:
        chunks.append(ResumeChunk("skills", 0, ", ".join(s.name for s in resume.skills)))

    for i, cert in enumerate(resume.certifications):
        text = cert.name if not cert.issuer else f"{cert.name} ({cert.issuer})"
        chunks.append(ResumeChunk("certifications", i, text))

    if resume.languages:
        chunks.append(
            ResumeChunk(
                "languages",
                0,
                ", ".join(f"{lang.name} ({lang.proficiency})" if lang.proficiency else lang.name for lang in resume.languages),
            )
        )

    return chunks
