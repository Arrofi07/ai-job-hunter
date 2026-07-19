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
| 7 | LLM routing: Gemini for nuanced tasks (matching, cover letters), Groq for structured/cheap tasks, with automatic fallback to **Ollama** (local) on rate limits, plus a manual `LLM_FORCE_PROVIDER` override for extended outages | 2026-07-08 |
| 8 | Cover letter template confirmed as: static sender block + static closing, template-substituted recipient/date/subject, LLM-generated body (paragraphs 11–16 only). Google Docs export quirk: non-round margins, 0 bottom margin — tolerate, don't "fix" | 2026-07-08 |
| 9 | Embeddings: **local `sentence-transformers` (all-MiniLM-L6-v2)**, not an API — avoids rate limits entirely for a step that runs on every resume/job/match, works offline | 2026-07-09 |
| 10 | DB table creation is an **explicit manual step** (`scripts/init_db.py`), not an implicit app-startup side effect — found this the hard way when it broke testability (see Slice 1 notes) | 2026-07-09 |
| 11 | Bug found running against real Gemini traffic: a `503 UNAVAILABLE` ("high demand") ServerError wasn't caught by our fallback logic — only `429 ClientError` was. Fixed in both Gemini and Groq providers: 5xx errors and connection/timeout failures now trigger the same fallback path as literal rate limits. 7 regression tests added, reconstructing the real SDK exception types. | 2026-07-09 |
| 12 | Local port conflict: `docker-compose.yml` Postgres port changed from `5432:5432` to `5433:5432` on your machine. Remember `DATABASE_URL` in `.env` must use the **host** port (5433), not the container's internal port (5432) | 2026-07-09 |
| 13 | Bug found running `scripts/init_db.py` against real Postgres: it printed "Tables created" but created **zero tables**. Cause: `SQLModel.metadata` only knows about a table once its class has been imported somewhere, and `init_db()` never imported `app.resume.models`. Fixed by importing all model modules inside `init_db()` itself. Regression test added using a real subprocess (the only way to reproduce a genuinely fresh-process import state) — confirmed it fails against the old code and passes against the fix. | 2026-07-09 |
| 14 | Discovered Gemini free tier is **20 requests/day** for `gemini-2.5-flash` — exhausted almost immediately in real use. Swapped defaults: **nuanced tasks now default to Ollama** (free, unlimited, lower quality) instead of Gemini; **fallback target swapped to Gemini** (so if Ollama itself fails, there's still a real fallback instead of a no-op, since fallback-equals-primary is skipped). Revisit once Gemini billing is set up — cover letter quality may be worth paying for even if resume/JD structuring isn't. | 2026-07-09 |
| 15 | Google OAuth consent screen stays in **Testing** mode (no need for Google's full verification process for a personal single-user tool) — but this means refresh tokens expire every **7 days**, requiring a manual re-run of `scripts/gdrive_oauth_setup.py` weekly. Accepted as a known operational cost for now rather than pursuing production verification. | 2026-07-16 |
| 16 | Confirmed via live `list_tools()` call: the GitHub MCP `repos` toolset has **no dedicated repo-metadata tool** (no `get_repository`, no direct "list languages" call) — it's `get_commit`, `get_file_contents`, `list_branches`, `list_commits`, `search_code`, `search_repositories`, etc. This actually fits FR9 well: portfolio analysis (languages, frameworks, CI/CD, Docker, tests) will be built on `get_file_contents` (reading `requirements.txt`/`package.json`/`Dockerfile`/`.github/workflows/*`) and `search_code`, not a single coarse metadata call — better signal anyway. | 2026-07-16 |
| 17 | Root-caused a 401 from Google's Drive MCP endpoint via Google's official docs (not guessing): a **separate API** — "Google Drive MCP API" (`drivemcp.googleapis.com`) — must be enabled in Cloud Console, distinct from the base "Google Drive API." Also corrected the OAuth scope: Google's docs specify exactly `drive.readonly` + `drive.file` for this server, not the broader `drive` scope I'd originally used — that combo actually covers FR6 correctly (read existing files + manage app-created files) with less privilege than what was there before. | 2026-07-16 |
| 18 | Root-caused the subsequent "caller does not have permission" error on `search_files`: confirmed via a live token-scope check that OAuth scopes were correct all along, which ruled out the scope theory. Actual cause, per Google's own docs on every Workspace-MCP page: the Google account itself must be signed up for and **accepted into the Google Workspace Developer Preview Program** (developers.google.com/workspace/preview) — a separate enrollment step from API enablement or OAuth, unique to this being a Developer Preview product rather than GA. Signed up, pending Google's approval. | 2026-07-17 |
| 19 | Decision: don't block on Drive MCP approval. Moving to **Slice 3 (Job Search & Collection)**, which has no dependency on MCP, while waiting. Circle back to Drive once the account is accepted. | 2026-07-17 |
| 20 | Verified against Greenhouse's own docs: their public Job Board API is strictly per-company (`/v1/boards/{board_token}/jobs`), explicitly states "filtering or searching is not possible," and Greenhouse doesn't publish a customer list — so "broad search, no company pre-filtering" is not achievable through Greenhouse/Lever's free APIs directly. **Flipped the plan**: Adzuna becomes the primary broad-search source (verified real request/response schema against developer.adzuna.com docs); Greenhouse/Lever become optional future enrichment, not built in this slice. | 2026-07-17 |
| 18 | Google Drive MCP is a **Developer Preview** product — confirmed via Google's own docs that it requires separate enrollment in the "Google Workspace Developer Preview Program" (developers.google.com/workspace/preview), independent of API enablement or OAuth scopes. Verified token has correct scopes (`drive.readonly` + `drive.file`, confirmed via tokeninfo endpoint) and correct API enabled — remaining "no permission" error is almost certainly pending program approval, not a code issue. **Decision: move on to Slice 3, circle back to Drive once approved.** | 2026-07-17 |
| 15 | GitHub MCP: **PAT auth** (not OAuth) against the official remote server `https://api.githubcopilot.com/mcp/`. Read-only is hardcoded in code, not a settings toggle, per FR9 — verified real behavior via GitHub's server-configuration docs (`X-MCP-Readonly`, `X-MCP-Toolsets` headers). | 2026-07-15 |
| 16 | Google Drive MCP: **official Google-hosted server** at `https://drivemcp.googleapis.com/mcp/v1`, OAuth 2.0, full `drive` scope (not `drive.file`) since FR6 needs to read files the person already has, not just app-created ones. Tool names (`search_files`, `create_file`, etc.) verified against Google's official MCP reference; exact response *shapes* were not verifiable from this sandbox (no live authenticated call possible here) — code degrades gracefully instead of crashing if the shape assumption is wrong, and needs live confirmation on your machine. | 2026-07-15 |

---

## Slice 0 — Project scaffolding & LLM provider layer
**Goal:** A project skeleton that runs, with config/env handling and a provider-agnostic LLM client
that can call Gemini, Groq, or Ollama interchangeably.

**Status: DONE.** All 7 tests pass on your machine (5 unit + 2 live smoke against real Gemini/Groq keys).

One bug found and fixed along the way: pydantic-settings doesn't treat a blank
`LLM_FORCE_PROVIDER=` line in `.env` as "unset" for an `Optional[LLMProvider]`
field — it validates the empty string against the enum and crashes at import
time. Fixed with a `field_validator` that maps blank/whitespace to `None`.
Re-verified against the exact failing `.env` — 5/5 unit tests now pass where
they previously failed collection entirely.

**Definition of Done**
- [x] `app/config.py`, `app/llm/` scaffolded — task-based routing (nuanced→Gemini, structured→Groq)
      with automatic Ollama fallback on rate limits, and a manual force-override for extended outages
- [x] `.env.example` documenting every required secret (no real secrets committed)
- [x] `LLMClient` interface with `Gemini`, `Groq`, `Ollama` implementations, selectable via config
- [x] Routing/fallback logic unit-tested (5 passing, mocked providers)
- [x] Live smoke tests against real Gemini + Groq keys — **passed on your machine**
- [x] `docker-compose.yml` for local Postgres + Qdrant
- [x] Blank-`.env`-value bug found and fixed

**Depends on:** nothing

---

## Slice 1 — Resume Knowledge Base (FR1)
**Goal:** Upload a resume PDF → structured, versioned, embedded, queryable.

**Status: DONE — validated against real production traffic AND your actual
resume end-to-end (PDF → structured JSON → Postgres → embedded → Qdrant, all
via the real API, no mocks).** 42 tests passing.

**Definition of Done**
- [x] `POST /resume` accepts a PDF, stores raw file (rejects non-PDF with 400)
- [x] Parse via PyMuPDF → LLM-assisted structuring into Education/Experience/Projects/Skills/Certifications/Languages
- [x] Structured resume stored in Postgres (versioned — old versions kept, latest flagged)
- [x] Embeddings generated per section (one chunk per experience/project entry, not one blob), stored in Qdrant
- [x] `GET /resume/latest` returns the current structured resume (404 if none uploaded yet)
- [x] Unit tests with a synthetic sample resume fixture (not your real one)
- [x] **Verified against a real upload on your machine, real Postgres, real Gemini/Groq**

**Depends on:** Slice 0

**Real bug #1 found via your live test (decision #11):** Gemini 503
"high demand" wasn't caught by the fallback logic — see Slice 0 for detail.

**Real bug #2 found via your live test (decision #13):** `scripts/init_db.py`
silently created zero tables against real Postgres, because
`SQLModel.metadata.create_all()` only creates tables for model classes that
have been *imported* somewhere first, and `init_db()` never imported
`app.resume.models`. Fixed by moving the model import inside `init_db()`
itself, so every future model gets picked up the same way without anyone
needing to remember to import it elsewhere. Added a subprocess-based
regression test — proved it fails against the old code and passes against
the fix, since an in-process test alone can't reliably reproduce "nothing
has imported this model yet" (other test files' imports leak into the same
process).

**Design smell still flagged, not fixed (per rule 3 — separate issue):**
`create_all()` only adds missing tables, never alters existing ones. Fine
for MVP with no data yet — becomes Alembic migrations once schema changes
need to preserve real data.

**Known limitation, not a bug (noticed in your real resume test):**
PyMuPDF's plain-text extraction drops hyperlinks — text that was a link in
the PDF (e.g. "Access the bachelor thesis here") comes through as plain
text with no URL. Doesn't break anything now, but means any resume content
that relies on a hyperlink (portfolio links, thesis links) loses that link
by the time it reaches the LLM for matching/cover letters. Not fixing
preemptively — flagging so it's a known tradeoff if it matters later.

**Bug found and fixed along the way:** the FastAPI app's startup lifespan
originally called `init_db()` unconditionally against the real configured
Postgres URL — meaning even health-check tests silently required a live DB
with no way to override it. Fixed by making table creation an explicit
script (`scripts/init_db.py`) instead of an app-startup side effect. This is
a genuine design improvement, not just a test workaround: production
deployments shouldn't auto-create tables on every restart either.

**Design smell flagged, not fixed (per rule 3 — separate issue):**
`scripts/init_db.py` uses `SQLModel.metadata.create_all()`, which only adds
missing tables — it never alters existing ones. Fine for MVP with no data
yet. Once the schema needs to change without losing data (e.g. adding a
column to a table with real rows in it), this needs to become Alembic
migrations. Not doing that preemptively — flagging it so it doesn't surprise
us later.

---

## Slice 2 — MCP connectivity (GitHub + Google Drive)
**Goal:** Prove both MCP servers are reachable and usable before building features on top of them.

**Status: PARTIALLY DONE.** GitHub MCP fully working end-to-end against real
data. Google Drive MCP is code-correct and verified up to the last possible
step, but blocked by something outside the code entirely — see below. Moving
on to other slices in the meantime; will circle back once unblocked.

**Definition of Done**
- [x] GitHub MCP configured in read-only mode (hardcoded, not a settings
      toggle — see decision #15), PAT-based, scoped minimally
      (`context,repos` toolsets only) — **smoke-tested successfully against
      real data**: `get_file_contents` on `octocat/Spoon-Knife/README.md` succeeded
- [ ] Google Drive MCP OAuth flow completed and confirmed working end-to-end
      — code is correct (OAuth flow, scopes, query syntax, response parsing
      all individually verified against real calls and Google's official
      docs), but **blocked** on Google's own **Workspace Developer Preview
      Program** approval — a manual account-enrollment step at
      https://developers.google.com/workspace/preview, entirely separate
      from Cloud Console config or code. Signed up with
      `muh.ar.rofi19@gmail.com`, awaiting acceptance.
- [x] `AI Job Hunter/{Resume,Templates,Jobs,Reports}` folder structure
      logic written — idempotent, creates only what's missing (unit-tested;
      real API calls untested pending the above)
- [x] Thin `MCPClient` wrapper module in `app/mcp/client.py` — GitHub and
      Drive clients both build on this instead of talking to the MCP SDK directly

**Depends on:** Slice 0

**What was actually verified live, not just coded, for Drive:** the OAuth
flow completes and correctly saves a refresh token; the token genuinely
carries both `drive.readonly` and `drive.file` scopes (confirmed via
Google's tokeninfo endpoint, not assumed); the required `drivemcp.
googleapis.com` API is enabled; the `search_files` query syntax and
response-shape assumptions in the code both matched Google's official
reference docs on direct inspection. The single remaining unknown is
whether calls succeed once the account is preview-program-approved —
everything upstream of that specific gate is confirmed correct.

**Files added:** `app/mcp/client.py`, `app/mcp/github_client.py`,
`app/mcp/gdrive_auth.py`, `app/mcp/gdrive_client.py`,
`scripts/gdrive_oauth_setup.py`, `scripts/mcp_smoke_test.py`, plus
`tests/test_mcp_client.py`, `tests/test_github_client.py`,
`tests/test_gdrive_client.py`.

---

## Slice 3 — Job Search & Collection (FR2)
**Goal:** Given filters, pull job postings into Postgres in a normalized schema.

**Status: DONE (with a source pivot from the original plan — see decision #20).**
Greenhouse/Lever turned out to be per-company-only APIs with no way to
search broadly (verified against their own docs) — the opposite of what
"no company pre-filtering" needs. Built on **Adzuna** instead, whose
request/response shapes were verified against developer.adzuna.com's
documented examples before writing any parsing code. 12 new tests, 67
total passing (real SQLite dedup logic, real API-shape parsing with mocked
HTTP, real FastAPI TestClient integration).

**Definition of Done**
- [x] `JobCollector` interface; `AdzunaCollector` implementation
      (Greenhouse/Lever deferred — see decision #20; could become
      opportunistic enrichment later, not primary discovery)
- [x] Normalized `NormalizedJob` schema (title, company, location,
      description, url, posted_date, salary, source, raw)
- [x] Filter support: location, experience level (required — folded into
      free-text search since Adzuna has no structured level filter, a real
      precision tradeoff flagged in `adzuna_collector.py`), job type,
      company, salary_min (optional)
- [x] Dedup on (source, external_id) enforced at the **DB level**
      (UniqueConstraint), not just application logic — holds even under
      concurrent runs
- [x] `POST /jobs/collect` triggers a run, returns `{found, saved,
      skipped_duplicates}`; `GET /jobs/recent` lists results
- [x] `JobPosting.status` field added now (FR7 lifecycle values) even
      though the duplicate-*recommendation* logic itself is Slice 7 — cheaper
      to add the column now than migrate it in later

**Depends on:** Slice 0

**You need to do:** sign up free at https://developer.adzuna.com/signup,
put `ADZUNA_APP_ID`/`ADZUNA_APP_KEY` in `.env`, then verify with a real call
(see SETUP.md) — same "I can't reach this API from my sandbox" gap as every
other external service so far.

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

**Template analysis (done 2026-07-08, from `Template_Cover_Letter.docx`):**
Paragraph-level breakdown of the template, everything uses the `Normal` style
(no custom heading styles), font inherited from theme (Calibri):

| Paragraphs | Content | Handling |
|---|---|---|
| 0–3 | Sender name/address/phone/email | Static, never touched |
| 4–6 | Recipient company/dept/location | Template substitution (job metadata) |
| 7 | Date | Auto-generated (today's date) |
| 8–9 | Subject line (role title + Req ID), bold | Template substitution |
| 10 | Salutation ("Dear Hiring Team,") | Static default |
| 11–16 | Body (6 paragraphs in the example) | **LLM-generated — the only part FR6 asks the model to write** |
| 17–18 | Closing + signature name | Static, never touched |

Open implementation question for when we build this: the LLM won't always produce
exactly 6 body paragraphs. Plan is to treat paragraph 11's formatting as the
"body paragraph template" — clone its run/paragraph formatting for however many
paragraphs the LLM produces, rather than assuming a fixed count.

Quirk to tolerate, not fix: this file is a Google Docs export, so margins are
non-round twip values and bottom margin is 0. `python-docx` needs to read/write
around this without choking — flagged now so it doesn't surprise us later.

**Definition of Done**
- [x] Template structure inspected and documented (styles, placeholder strategy) — see table above
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

- **`create_all()` vs. real migrations** (flagged in Slice 1): table creation
  only ever adds missing tables, never alters existing ones. Fine while
  there's no real data yet. Becomes Alembic migrations once a schema change
  needs to happen without losing data.
- **PDF text extraction drops hyperlinks** (flagged in Slice 1, noticed on
  your real resume): PyMuPDF's plain-text extraction strips hrefs — a resume
  bullet that was a hyperlink becomes plain text with no URL by the time it
  reaches the LLM. Not breaking anything now; worth remembering if portfolio
  links ever need to survive into matching/cover letters.
- **Gemini free-tier cost ceiling** (decision #14): 20 req/day means Gemini
  can't be the default workhorse yet. Currently mitigated by routing nuanced
  tasks to Ollama, with Gemini as a rarely-used fallback. Revisit once
  billing is set up, if quality on cover letters specifically justifies it.
- **Google Drive MCP is a Developer Preview product** (decision #18): could
  change endpoints/scopes/requirements with little notice, unlike GitHub's
  MCP server which is stable. Worth remembering this specific dependency is
  less solid ground than the rest of the stack.

---

## Next action

Start **Slice 3: Job Search & Collection** (Greenhouse + Lever APIs) — no
dependency on Slice 2, so no reason to wait on Google's Drive MCP approval.
Open question from the original plan still needs an answer: which companies
to seed the search with (hand-picked list vs. Claude proposing one based on
your target roles/location — Data Scientist/ML Engineer/AI Engineer/Data
Engineer/Data Analyst, Berlin-area).