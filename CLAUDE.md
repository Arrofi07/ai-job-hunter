# Product Requirements Document (PRD)

## AI Job Hunter: An AI-powered Career Assistant

**Version:** 1.0 (MVP)
**Author:** Muhammad Taqiyuddin Ar Rofi
**Status:** Draft
**Last Updated:** July 2026

---

# 1. Product Overview

## Problem

Searching for jobs every day is repetitive and time-consuming. Applicants often need to search across multiple job platforms, manually compare job descriptions against their resume, determine whether a position is worth applying for, and write customized cover letters.

This process can take hours each day.

## Solution

AI Job Hunter is an AI-powered career assistant that automates the most repetitive parts of the job hunting process.

Given a resume and user-defined preferences, the system:

* Searches multiple job platforms daily
* Finds relevant job postings
* Ranks jobs based on resume compatibility
* Saves job descriptions and metadata
* Generates personalized cover letters using a predefined template
* Stores generated documents in Google Drive
* Maintains application history to avoid duplicate recommendations
* Provides weekly analytics and resume improvement suggestions
* Uses GitHub repositories as additional evidence of technical skills

The goal is **not** to automatically apply for jobs, but to significantly reduce the time required to discover, evaluate, and prepare high-quality applications.

---

# 2. Goals

### Primary Goals

* Reduce daily job search time from hours to minutes
* Recommend only highly relevant job opportunities
* Generate personalized cover letters
* Maintain a history of discovered jobs
* Improve the user's resume over time through trend analysis

### Non Goals (MVP)

* Automatic job application submission
* Resume rewriting
* Interview preparation
* Salary negotiation assistance

---

# 3. Target User

Primary User

* Job seekers
* Students
* New graduates
* Professionals looking for new opportunities

Current target user:

Muhammad Taqiyuddin Ar Rofi

Looking for:

* Data Scientist
* Machine Learning Engineer
* AI Engineer
* Data Engineer
* Data Analyst

---

# 4. User Flow

```text
Upload Resume
        │
        ▼
Store Resume Knowledge Base
        │
        ▼
Search Jobs
        │
        ▼
Collect Job Descriptions
        │
        ▼
Match Resume ↔ Job
        │
        ▼
Rank Jobs
        │
        ▼
Top 5 Jobs
        │
 ┌──────┴─────────┐
 ▼                ▼
Save JD      Generate Cover Letter
        │
        ▼
Store Results
        │
        ▼
Daily Memory
        │
        ▼
Weekly Report
```

---

# 5. Functional Requirements

## FR1 Resume Knowledge Base

The user uploads a master resume (PDF).

The system shall:

* Parse and extract resume content.
* Store structured resume information.
* Generate embeddings for semantic retrieval.
* Allow the resume to be updated at any time.
* Always use the latest resume version during matching and cover letter generation.

Structured resume sections include:

* Education
* Experience
* Projects
* Skills
* Certifications
* Languages

---

## FR2 Job Search

The user specifies filters:

Required

* Location
* Experience Level

Optional

* Job Type
* Remote / Hybrid / Onsite
* Date Posted
* Company
* Salary

The system searches supported job platforms and collects matching job postings.

---

## FR3 Job Matching

For every collected job:

The system compares

Resume

↓

Job Description

Output

* Match Score
* Strengths
* Missing Skills
* Summary

Example

Overall Score

92%

Strengths

* Python
* SQL
* Docker
* Machine Learning

Missing

* AWS
* Spark

---

## FR4 Ranking

Jobs are ranked by

* Match Score
* Job Freshness
* Preference Filters

Output

Top 5 Jobs

---

## FR5 Storage Service

The system shall separate **application data** from **user documents**.

### PostgreSQL (Application Database)

Stores structured application data including:

* Job postings
* Company information
* Match scores
* Search history
* User preferences
* Weekly reports metadata
* Google Drive file IDs
* Application status
* Duplicate detection history

### Google Drive (Document Storage)

Stores generated user documents including:

```text
AI Job Hunter/

Resume/

Templates/

Jobs/

Reports/
```

Each recommended job shall have its own folder:

```text
Jobs/

2026/

07/

2026-07-08/

BMW_Data_Scientist/

metadata.json

job_description.md

cover_letter.docx
```

The database shall maintain the Google Drive File IDs for synchronization and future updates.

---

## FR6 Cover Letter Generation

Input

* Resume Knowledge Base
* Job Description
* Company Information

Output

* Personalized cover letter

Requirements

* Preserve the user's DOCX template.
* Preserve fonts, margins, spacing, signature, and formatting.
* Generate only the body content using the LLM.
* Save the generated cover letter to Google Drive.
* Store the corresponding Google Drive File ID in PostgreSQL.

---

## FR7 Stateful Memory

The system shall maintain a persistent history of job recommendations.

Track:

* Already discovered
* Already recommended
* Applied
* Interview
* Offer
* Rejected
* Archived

Duplicate jobs shall never be recommended again unless explicitly requested by the user.

---

## FR8 Weekly Report

Every Saturday, the system shall generate a weekly report including:

* Jobs collected
* Top recommended jobs
* Average match score
* Companies discovered
* Frequently requested skills
* Missing skills
* Resume improvement suggestions
* GitHub portfolio insights

The report shall be uploaded to Google Drive.

---

## FR9 GitHub Portfolio Analysis

The system shall enrich the user's professional profile by analyzing selected GitHub repositories.

The GitHub analysis should identify:

* Programming languages
* Frameworks
* Libraries
* Machine learning projects
* Deployment experience
* CI/CD implementations
* Docker usage
* Testing practices
* Project complexity

This information shall be used as additional context during:

* Job matching
* Cover letter generation
* Resume improvement recommendations

The GitHub analysis supplements the resume but never replaces it.

---

# 6. Non Functional Requirements

Performance

* Complete search within 5 minutes
* Generate cover letter within 30 seconds

Scalability

Support

* Thousands of stored jobs

Reliability

* Resume should never be modified automatically
* Duplicate jobs should not be recommended

Maintainability

* Modular architecture
* Independent components

---

# 7. Inputs

Resume

PDF

Search Filters

Example

```text
Location

Berlin

Experience

Entry Level

Remote

Hybrid

Date Posted

Past 7 Days
```

---

# 8. Outputs

Top 5 Jobs

Example

```text
1.

Data Scientist

Company

BMW

Score

94%

Link

...

Files

job_description.md

cover_letter.docx

-----------------

2.

ML Engineer

Bosch

92%
```

---

# 9. Storage Architecture

The application follows a hybrid storage architecture.

| Storage      | Purpose                     |
| ------------ | --------------------------- |
| PostgreSQL   | Structured application data |
| Google Drive | User-generated documents    |
| Qdrant       | Resume and job embeddings   |

This separation ensures that application state and user documents are managed independently.

---

# 10. MCP Integration

The application uses the **Model Context Protocol (MCP)** to integrate external services in a standardized manner.

### GitHub MCP

Purpose:

* Read selected GitHub repositories
* Analyze projects
* Extract demonstrated technical skills
* Improve resume matching
* Enhance cover letter personalization
* Support weekly portfolio analysis

The GitHub MCP server provides contextual information but never modifies repositories.

---

### Google Drive MCP

Purpose:

* Read the latest resume
* Access the cover letter template
* Create folders
* Upload generated cover letters
* Upload job descriptions
* Upload weekly reports
* Retrieve existing application documents

Google Drive serves as the user's document repository, while PostgreSQL stores metadata and references.

---

# 11. Tech Stack

| Component            | Technology                                        |
| -------------------- | ------------------------------------------------- |
| Programming Language | Python 3.12+                                      |
| Backend API          | FastAPI                                           |
| Workflow Scheduler   | APScheduler                                       |
| Database             | PostgreSQL                                        |
| ORM                  | SQLModel                                          |
| Vector Database      | Qdrant                                            |
| LLM Provider         | Provider-agnostic (OpenAI, Gemini, Kimi, etc.)    |
| Embedding Model      | Provider-agnostic                                 |
| Resume Parser        | PyMuPDF                                           |
| Job Collector        | JobSpy (MVP), extensible to additional collectors |
| Document Generation  | python-docx                                       |
| Cloud Storage        | Google Drive                                      |
| MCP Client           | Model Context Protocol Client                     |
| MCP Servers          | GitHub MCP, Google Drive MCP                      |
| Containerization     | Docker                                            |
| Frontend (Optional)  | Streamlit                                         |

---

# 12. Success Criteria

The MVP is considered successful when it can:

* ✅ Upload and store a resume
* ✅ Search jobs using user-defined filters
* ✅ Match jobs against the resume
* ✅ Rank and recommend the Top 5 jobs
* ✅ Save each job description locally
* ✅ Generate a customized cover letter using the user's DOCX template
* ✅ Avoid recommending duplicate jobs
* ✅ Produce a weekly report with resume improvement suggestions

---

## System Architecture

```text
                            User
                              │
                              ▼
                         FastAPI API
                              │
                     Workflow Scheduler
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
 Resume Knowledge      Job Collection        Weekly Scheduler
        │                     │                     │
        └──────────────┬──────┴─────────────────────┘
                       ▼
                Matching Engine
                       │
                       ▼
                Ranking Engine
                       │
          ┌────────────┴────────────┐
          ▼                         ▼
  Cover Letter Generator      Storage Service
                                        │
                     ┌──────────────────┴──────────────────┐
                     ▼                                     ▼
               PostgreSQL                           Google Drive
                     │                                     ▲
                     └──────────────┬──────────────────────┘
                                    │
                               MCP Client
                             ┌──────┴──────┐
                             ▼             ▼
                      GitHub MCP     Google Drive MCP
```
