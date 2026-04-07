# Agri Research Agent Platform (Full Stack)

This workspace contains:

- `DeepResearchAgent` → FastAPI + LangGraph backend
- `DeepResearchAgentUI` → Angular frontend

## What this project solves

This is a **Deep Research Agent** that answers complex agricultural questions while operating under strict **memory and cost constraints**. It:
- Breaks down multi-part crop-planning queries
- Retrieves relevant context without exceeding token/cost limits
- Maintains conversation continuity across follow-ups
- Provides crop recommendations considering season, soil, market trends, and historical data

## Core architecture & design decisions

### Why LangGraph (not n8n/Dify)
- **LangGraph**: Programmatic, deterministic, fully testable node-by-node
- **n8n/Dify**: Visual, great for schedules, but less control over state transitions
- **Decision**: Chose LangGraph because we need explicit constraint enforcement at each node (token counting, cost tracking, memory clipping). Programmatic control is essential.

### Why PostgreSQL + pgvector (not just vector DB)
- **Two-layer memory**:
  - **Episodic memory** (`memory_events` + pgvector): semantic retrieval of past research insights
  - **Session memory** (`chat_turns`): conversation continuity and deictic follow-ups (e.g., "compare this crop")
- **Why both**: Semantic memory alone loses dialogue context; conversation memory alone loses cross-session knowledge
- **Why PostgreSQL**: One operational database, no additional infrastructure, pgvector is production-ready

### Why mode-aware synthesis (ranking vs. comparison vs. precaution)
- Different query intents need different LLM prompts:
  - "Which crop to plant now?" → **Ranking mode** (scored list of options)
  - "Maize vs soybean profitability?" → **Comparison mode** (head-to-head analysis)
  - "How to care for this crop?" → **Precaution mode** (risk + guidance)
- **Decision**: Hard-code intent detection + mode-specific prompts to avoid generic, unhelpful responses

### Why TTL in-memory cache
- Prevents redundant LLM calls for identical queries within same session
- Simple, single-process solution sufficient for prototype
- Cache key includes session/query/location/crop dimensions for safe reuse

### Why deterministic hash embeddings (not model embeddings)
- Model embeddings require API calls; hash embeddings are portable
- Seed data consistency across Docker containers and local runs
- Trade-off: slightly weaker semantic matching, but stable eval behavior

### Why Gemini with fallback behavior
- Gemini 2.0 Flash: fast, cheap, excellent for function calling
- Fallback logic: if API key absent or model unavailable, system returns mock recommendation (not hard error)
- Trade-off: Graceful degradation over hard failure during assessment

---

## Documentation & evaluation

- **Architecture deep-dive**: [DeepResearchAgent/docs/ARCHITECTURE.md](DeepResearchAgent/docs/ARCHITECTURE.md)
- **Evaluation & trade-offs**: [DeepResearchAgent/evaluation.md](DeepResearchAgent/evaluation.md) ← **Read this for constraint strategy and business reasoning**
- **Backend README**: [DeepResearchAgent/README.md](DeepResearchAgent/README.md)
- **Frontend README**: [DeepResearchAgentUI/README.md](DeepResearchAgentUI/README.md)

## End-to-end start guide

### 1) Start backend

From `DeepResearchAgent`:

- Copy config template:
  - `cp .env.example .env`
- Add your real key in `.env`:
  - `GEMINI_API_KEY=...`
- Start backend (choose one):
  - Docker: `docker compose up --build`
  - Local: `uvicorn main:app --reload --port 8001`

Backend health URL:
- `http://127.0.0.1:8001/health`

### 2) Start frontend

From `DeepResearchAgentUI`:

- `npm install`
- `npm start`

Frontend URL:
- `http://localhost:4200`

## Integration contract

Frontend calls backend endpoints:

- `GET /health`
- `POST /research`
- `GET /sessions`
- `GET /sessions/{session_id}/history`

Backend base URL expected by UI:
- `http://127.0.0.1:8001`

## Secrets policy

- Keep real secrets only in local `.env` files.
- Commit only `.env.example` placeholders.
- Do not commit API keys to git.
