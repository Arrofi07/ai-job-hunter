# AI Job Hunter — Development Plan

This is a living document. Each slice is small, ships something runnable/testable end to end,
and doesn't depend on later slices existing. We update status as we go. See `CLAUDE.md` (the PRD)
for the full product spec — this file is the *build order* and the *decisions log* for it.

**Owner:** Muhammad Taqiyuddin Ar Rofi
**Stack:** Python 3.12+, FastAPI, SQLModel + PostgreSQL, Qdrant, APScheduler, python-docx, uv

---

## How to read this doc

- `[ ]` not started · `[~]` in progress · `[x]` done
- Each slice has: **Goal**, **Definition of Done**, **Depends on**, **Open questions** (if any)
- "Open questions" get resolved with you before or during the slice — not silently assumed.

---

## Decisions log

Recorded so we don't relitigate these later.

| # | Decision | Date |
|---|----------|------|
| 1 | Build vertically, one slice at a time, tracked in this README | 2026-07-08 |
| 2 | LLM: hybrid **Gemini + Groq** behind a provider-agnostic interface | 2026-07-08 |
| 3 | Job sources: **Greenhouse API + Lever API** as primary, **Adzuna/JSearch** as secondary, targeted Google search as long-tail fallback. No LinkedIn/Indeed scraping (ToS risk). | 2026-07-08 |
| 4 | Cover letter template: **must be `.docx`**, not PDF — pending upload | 2026-07-08 |
| 5 | MCP: **`github/github-mcp-server`** (official, read-only mode) + **Google's official remote Google Drive MCP server** | 2026-07-08 |
| 6 | Dev env: existing `uv`-managed project on your machine; I scaffold files here, you place them in your repo | 2026-07-08 |

---

## Slice 0 — Project scaffolding & LLM provider layer
**Goal:** A project skeleton that runs, with config/env handling and a provider-agnostic LLM client
that can call Gemini or Groq interchangeably.

**Definition of Done**
- [ ] Repo layout in place (`app/`, `tests/`, `pyproject.toml` deps added via `uv add`)
- [ ] `.env.example` documenting every required secret (no real secrets committed)
- [ ] `LLMClient` interface with `Gemini` and `Groq` implementations, selectable via config
- [ ] One smoke test: send a trivial prompt to each configured provider, assert non-empty response
- [ ] `docker-compose.yml` for local Postgres + Qdrant

**Depends on:** nothing

**Open questions**
- Do you want Gemini as primary (cheap/good context) and Groq as a fast fallback, or split by task
  (e.g. Groq for quick matching, Gemini for longer cover-letter generation)? I'd default to:
  **Gemini for anything needing large context or nuance (matching, cover letters), Groq for
  cheap/fast structured tasks (extraction, classification)** — flag if you'd rather split differently.

---

## Slice 1 — Resume Knowledge Base (FR1)
**Goal:** Upload a resume PDF → structured, versioned, embedded, queryable.

**Definition of Done**
- [ ] `POST /resume` accepts a PDF, stores raw file
- [ ] Parse via PyMuPDF → LLM-assisted structuring into Education/Experience/Projects/Skills/Certifications/Languages
- [ ] Structured resume stored in Postgres (versioned — old versions kept, latest flagged)
- [ ] Embeddings generated per section, stored in Qdrant
- [ ] `GET /resume/latest` returns the current structured resume
- [ ] Unit tests with a sample resume fixture (not your real one — synthetic)

**Depends on:** Slice 0

---

## Slice 2 — MCP connectivity (GitHub + Google Drive)
**Goal:** Prove both MCP servers are reachable and usable before building features on top of them.

**Definition of Done**
- [ ] GitHub MCP configured in read-only mode, PAT scoped minimally, smoke-tested (list a repo's languages)
- [ ] Google Drive MCP OAuth flow completed, smoke-tested (list `AI Job Hunter/` folder contents, or create it if absent)
- [ ] `AI Job Hunter/{Resume,Templates,Jobs,Reports}` folder structure created in Drive if missing
- [ ] Thin `MCPClient` wrapper module in `app/mcp/` so features don't call MCP tools directly

**Depends on:** Slice 0
**Open questions:** none yet — will surface config specifics when we do this slice together (you'll need to run the OAuth consent flow locally, I can't do that from here).

---

## Slice 3 — Job Search & Collection (FR2)
**Goal:** Given filters, pull job postings from Greenhouse + Lever into Postgres in a normalized schema.

**Definition of Done**
- [ ] `JobCollector` interface; `GreenhouseCollector` and `LeverCollector` implementations
- [ ] Normalized `JobPosting` schema (title, company, location, description, url, posted_date, source, raw_json)
- [ ] Filter support: location, experience level (required), job type/remote/date/company/salary (optional, best-effort since not all sources expose all fields)
- [ ] Dedup on (source, external_id) before insert
- [ ] CLI or endpoint to trigger a collection run manually, logs count collected

**Depends on:** Slice 0
**Open questions**
- Company list to target on Greenhouse/Lever — do you want to hand-pick a seed list (BMW, Bosch, DLR-adjacent companies, Berlin tech scene) or should I propose one based on your target roles/location?

---

## Slice 4 — Job Matching Engine (FR3)
**Goal:** Score a job against the latest resume.

**Definition of Done**
- [ ] Embedding similarity (Qdrant) as a first-pass signal
- [ ] LLM-based structured comparison producing `{score, strengths[], missing[], summary}`
- [ ] Persisted per (resume_version, job_id) pair — never recompute unnecessarily
- [ ] Unit tests with fixture resume + fixture JD pairs, asserting output shape

**Depends on:** Slice 1, Slice 3

---

## Slice 5 — Ranking Engine (FR4)
**Goal:** Turn many scored jobs into a Top 5.

**Definition of Done**
- [ ] Ranking function: match score (primary) + freshness + preference-filter fit
- [ ] Deterministic, unit-testable (pure function, no LLM call)
- [ ] Excludes jobs already in "discovered/recommended" history (ties into Slice 7)

**Depends on:** Slice 4, Slice 7 (duplicate check)

---

## Slice 6 — Cover Letter Generation (FR6)
**Goal:** Fill your real `.docx` template's body with LLM-generated, personalized content.

**Definition of Done**
- [ ] Template structure inspected and documented (styles, placeholder strategy)
- [ ] `python-docx`-based filler that only touches body paragraphs, preserves header/footer/fonts/margins/signature
- [ ] LLM generates body content from resume + JD + company info
- [ ] Output saved locally, then uploaded to Drive under `Jobs/{year}/{month}/{date}/{Company}_{Role}/`
- [ ] Drive file ID stored in Postgres

**Depends on:** Slice 1, Slice 2, Slice 4
**Blocked on:** your `.docx` template upload

---

## Slice 7 — Stateful Memory (FR7)
**Goal:** Track job lifecycle status, prevent duplicate recommendations.

**Definition of Done**
- [ ] Status enum: discovered → recommended → applied → interview → offer → rejected → archived
- [ ] `PATCH /jobs/{id}/status` to update
- [ ] Ranking/matching queries automatically exclude already-recommended jobs unless `force=true`

**Depends on:** Slice 3

---

## Slice 8 — Scheduler (daily search + Saturday report)
**Goal:** Automate the pipeline instead of manual triggering.

**Definition of Done**
- [ ] APScheduler job: daily run of Slice 3 → 4 → 5 → 6 pipeline
- [ ] APScheduler job: weekly (Saturday) trigger for Slice 9
- [ ] Basic run logging (start/end time, jobs collected, errors) in Postgres

**Depends on:** Slices 3–7

---

## Slice 9 — Weekly Report (FR8) + GitHub Portfolio Analysis (FR9)
**Goal:** Saturday report combining job-search analytics with GitHub-derived skill signals.

**Definition of Done**
- [ ] GitHub MCP-based repo analyzer: languages, frameworks, ML/CI-CD/Docker/testing signals
- [ ] Weekly aggregation: jobs collected, top jobs, avg score, companies, frequent/missing skills
- [ ] Resume improvement suggestions (LLM, grounded in missing-skills + GitHub signals — no auto-edit of resume, per FR1/reliability requirement)
- [ ] Report uploaded to Drive `Reports/`

**Depends on:** Slice 2, Slice 3, Slice 7

---

## Slice 10 — API surface & (optional) Streamlit frontend
**Goal:** Make the system usable without curling endpoints by hand.

**Definition of Done**
- [ ] FastAPI routes consolidated and documented (`/docs` works)
- [ ] Optional: minimal Streamlit view — resume upload, top-5 jobs, status updates, report viewer

**Depends on:** all prior slices

---

## Slice 11 — Hardening
**Goal:** Make it reliable enough to trust running unattended daily.

**Definition of Done**
- [ ] Error handling + retries around external calls (LLM, MCP, job APIs)
- [ ] Structured logging
- [ ] Test coverage on matching/ranking/dedup logic (the parts most likely to silently misbehave)

**Depends on:** all prior slices

---

## Design smells / things to revisit later (not fixing now, just tracking)

*(I'll add entries here as I encounter anything worth flagging per your rule #3 — nothing yet since we haven't written code.)*

---

## Next action

Start **Slice 0**. Confirm the Gemini/Groq task split question above (or say "your call") and I'll scaffold it.