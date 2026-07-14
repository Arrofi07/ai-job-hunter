# Setup — merging into your existing `uv` project

You already ran `uv init` and have a venv. This covers Slice 0 (LLM layer) and
Slice 1 (Resume Knowledge Base) together, since you're merging both at once.

## 1. Copy files into your project

Copy these into your project root, preserving structure:

```
app/                  (config.py, db.py, main.py, vector_store.py, llm/, resume/)
scripts/               (init_db.py)
tests/                 (all test files + fixtures/)
.env.example
docker-compose.yml
```

## 2. Add dependencies

```bash
uv add fastapi uvicorn python-multipart sqlmodel psycopg2-binary qdrant-client apscheduler \
       python-docx pymupdf pydantic-settings python-dotenv \
       google-genai groq httpx sentence-transformers

uv add --dev pytest
```

Note: `sentence-transformers` pulls in `torch` — it's a genuinely heavy
install (multiple GB). That's expected; we chose it deliberately over an API
embedding provider specifically to avoid rate limits (see decisions log).

## 3. Create your real `.env`

```bash
cp .env.example .env
```

Fill in `GEMINI_API_KEY` and `GROQ_API_KEY`. Leave `LLM_FORCE_PROVIDER` blank for now.

## 4. Install Ollama (optional but recommended, given your rate-limit concern)

```bash
# https://ollama.com/download — pick your OS
ollama pull llama3.1
ollama serve   # keep running in a separate terminal, or as a background service
```

Two-command escape hatch for later: if Gemini throttles you mid-pipeline, set
`LLM_FORCE_PROVIDER=ollama` in `.env` and every task routes to your local
model instead — no code changes, no redeploy.

## 5. Start Postgres + Qdrant

```bash
docker compose up -d
```

## 6. Create the database tables

Table creation is a deliberate, explicit step — not something that happens
automatically when the app starts (see "design smells" note in README.md
about why). Run it once, and again any time you add a new model:

```bash
uv run python -m scripts.init_db
```

## 7. Run the tests

```bash
uv run pytest tests/ -v
```

You should see **32 passed, 2 skipped**. The 2 skipped are live smoke tests
against real Gemini/Groq (see step 8). Everything else — including the full
resume ingestion pipeline against a real PDF and a real database — runs for
real in this step; only the LLM provider calls and Qdrant/Postgres
connections are mocked in the test suite itself.

## 8. (Once your .env has real keys) Run the live smoke tests

Temporarily remove the `@pytest.mark.skip` line above
`test_live_smoke_gemini` and `test_live_smoke_groq` in
`tests/test_llm_client.py`, run once, then put the skip markers back (so CI
or future test runs don't depend on live network/keys by default):

```bash
uv run pytest tests/test_llm_client.py -v -k live_smoke
```

## 9. Try the real API

```bash
uv run uvicorn app.main:app --reload
```

Then in another terminal:

```bash
curl -X POST http://localhost:8000/resume \
  -F "file=@/Users/apple/Documents/Projects/ai-job-hunter/tests/fixtures/CV_Rofi_Airbus_Data-Science.pdf"

curl http://localhost:8000/resume/latest
```

First upload will be slow-ish (sentence-transformers downloads the embedding
model on first use, ~90MB, one time only).

## What "done" looks like

- [x] Slice 0: LLM provider layer — routing, fallback, tested with your real keys
- [x] Slice 1: Resume Knowledge Base — parse, structure, version, chunk, embed, store
- [x] 32 tests passing in this sandbox (real PDF parsing, real SQLite DB, real
      chunking/routing logic; only Gemini/Groq/Qdrant/Postgres network calls mocked)
- [x] One real bug found and fixed: app startup no longer silently requires a live DB
- [ ] **You**: run steps 1–9 above, confirm the live smoke tests pass, confirm
      a real upload of your actual resume works end-to-end

Once you confirm that, we move to **Slice 2: MCP connectivity** (GitHub + Google Drive).

