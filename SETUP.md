# Slice 0 setup — merging into your existing `uv` project

You already ran `uv init` and have a venv. Here's how to fold this in.

## 1. Copy files into your project

Copy these into your project root, preserving structure:

```
app/                  (config.py, llm/)
tests/test_llm_client.py
.env.example
docker-compose.yml
```

## 2. Add dependencies

```bash
uv add fastapi uvicorn sqlmodel psycopg2-binary qdrant-client apscheduler \
       python-docx pymupdf pydantic-settings python-dotenv \
       google-genai groq httpx

uv add --dev pytest
```

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

You don't need this today, but it's a two-command escape hatch for later:
if Gemini throttles you mid-pipeline, set `LLM_FORCE_PROVIDER=ollama` in `.env`
and every task routes to your local model instead — no code changes, no redeploy.

## 5. Start Postgres + Qdrant

```bash
docker compose up -d
```

## 6. Run the tests

```bash
uv run pytest tests/ -v
```

You should see 5 passed, 2 skipped (the 2 skipped ones are live smoke tests
against real Gemini/Groq — see step 7).

## 7. (Once your .env has real keys) Run the live smoke tests

```bash
uv run pytest tests/test_llm_client.py -v -m "" -k live_smoke --no-skip
```

Or simpler, just unskip them temporarily by removing the `@pytest.mark.skip`
line, run once, put it back. This confirms your actual API keys work before
we build anything on top of them.

## What "done" looks like for Slice 0

- [x] `app/config.py` — typed settings, task-based LLM routing
- [x] `app/llm/` — provider-agnostic client with Gemini/Groq/Ollama + rate-limit fallback
- [x] `tests/test_llm_client.py` — routing/fallback logic covered (5 passing, verified in sandbox)
- [x] `docker-compose.yml` — Postgres + Qdrant (valid YAML, verified in sandbox)
- [x] `.env.example` — every config var documented
- [ ] **You**: run steps 1–7 above on your machine and confirm the live smoke tests pass with your real keys

Once you confirm that, we move to **Slice 1: Resume Knowledge Base**.
