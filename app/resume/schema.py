"""
Structured resume schema (FR1).

This is the contract between three things: what we ask the LLM to produce,
what we validate its output against, and what we return from the API. Keeping
one schema for all three means a malformed LLM response fails loudly at
validation time instead of silently corrupting stored data.
"""
from pydantic import BaseModel, Field


class Education(BaseModel):
    institution: str
    degree: str
    field_of_study: str | None = None
    start_date: str | None = None  # free text: LLM output on resumes is rarely clean ISO dates
    end_date: str | None = None
    description: str | None = None


class Experience(BaseModel):
    company: str
    title: str
    location: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    highlights: list[str] = Field(default_factory=list)  # bullet points, kept separate for embedding granularity


class Project(BaseModel):
    name: str
    description: str | None = None
    technologies: list[str] = Field(default_factory=list)
    url: str | None = None


class Skill(BaseModel):
    name: str
    category: str | None = None  # e.g. "language", "framework", "tool" — optional, LLM's best guess


class Certification(BaseModel):
    name: str
    issuer: str | None = None
    date: str | None = None


class Language(BaseModel):
    name: str
    proficiency: str | None = None


class StructuredResume(BaseModel):
    education: list[Education] = Field(default_factory=list)
    experience: list[Experience] = Field(default_factory=list)
    projects: list[Project] = Field(default_factory=list)
    skills: list[Skill] = Field(default_factory=list)
    certifications: list[Certification] = Field(default_factory=list)
    languages: list[Language] = Field(default_factory=list)
