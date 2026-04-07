# G3 Deep Research Agent (Agriculture)

Concise guide for setup and usage.

For deep technical details, see:
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- [evaluation.md](evaluation.md)

## What this project does

- Answers crop-planning questions with season + soil + market trend logic.
- Supports multi-turn sessions using `session_id`.
- Stores conversation history and semantic memory in PostgreSQL + pgvector.
- Enforces memory/cost constraints and reports them in responses.

## Tech stack

- FastAPI + LangGraph + LangChain
- Gemini (with fallback behavior)
- PostgreSQL + pgvector
- Docker Compose

## Quick start (Docker)

1. Copy env:
   - `cp .env.example .env`
2. Start services:
   - `docker compose up --build`
3. Open docs:
   - `http://127.0.0.1:8000/docs`

## Quick start (Local)

1. Create env + install deps:
   - `conda create -y -n deepresearch_g3 python=3.11`
   - `conda activate deepresearch_g3`
   - `pip install -r requirements.txt`
2. Ensure PostgreSQL + pgvector is available (this repo maps Docker DB to `5433`).
3. Copy env:
   - `cp .env.example .env`
4. Run API:
   - `uvicorn main:app --reload --port 8001`

## Main endpoints

- `GET /health`
- `POST /research`
- `GET /sessions`
- `GET /sessions/{session_id}/history`

## Example usage

1) First query (new session)

```json
{
  "query": "which is the ideal crop to be put now hassan"
}
```

2) Follow-up using returned `session_id`

```json
{
  "query": "compare profitability of maize vs soybean for next 3 months",
  "session_id": "<session-id-from-previous-response>"
}
```

## Notes

- If `location` is omitted, the system infers from query text (e.g., "hassan") or IP fallback.
- If `soil_type` is omitted, regional default soil is used.
- Constraints are configurable in `.env`.

## Secrets and config policy

- Keep real secrets (for example `GEMINI_API_KEY`) only in local `.env`.
- Commit only `.env.example` with empty placeholders.
- Teammates create their own `.env` from `.env.example` and add personal keys locally.

## Unit tests

- Tests are under [tests/unit](tests/unit).
- Install test dependency:
   - `pip install -r requirements-dev.txt`
- Run tests:
   - `pytest tests/unit -q`