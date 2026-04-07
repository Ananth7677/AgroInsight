# Detailed Architecture & Design Decisions

## 1) System overview

This project is a multi-turn agriculture research agent built for G3 (Deep Research Agent + Memory Constraints).

Core objectives:
- Answer complex crop-planning questions.
- Work under explicit memory/token and cost constraints.
- Keep conversation continuity across follow-up questions.

Primary stack:
- API layer: FastAPI
- Agent orchestration: LangGraph
- LLM synthesis: Gemini (with resilient fallback behavior)
- Persistence: PostgreSQL + pgvector
- Frontend: Angular 21 (standalone components + signals)
- Runtime: Docker Compose or local Conda environment

## 2) Runtime components

- API bootstrap: [app/main.py](../app/main.py)
- Route composition: [app/controllers/router.py](../app/controllers/router.py)
- Main research controller: [app/controllers/research_controller.py](../app/controllers/research_controller.py)
- Workflow singleton: [app/core/workflow.py](../app/core/workflow.py)
- LangGraph workflow: [app/graph.py](../app/graph.py)
- Database init + seed logic: [app/db.py](../app/db.py)
- Config and constraints: [app/config.py](../app/config.py)

## 3) Request flow (end-to-end)

1. Client sends `POST /research` with `query` and optional `session_id`.
2. Controller resolves/create session (`chat_sessions`) and reads recent conversation context (`chat_turns`).
3. Controller normalizes query and resolves:
   - location from query aliases / provided location / prior turn metadata / IP fallback,
   - crop focus for deictic follow-ups (e.g., "this crop"),
   - compare mode for `compare` / `vs` profitability queries.
4. Controller checks in-memory TTL cache key.
5. On miss, LangGraph executes:
   - `plan` node: query decomposition,
   - `context` node: location-season-soil-market + memory retrieval,
   - `synthesize` node: generate recommendation under mode (ranking/comparison/precaution),
   - `memory` node: save episodic events in `memory_events`.
6. Controller writes user + assistant turns into `chat_turns`.
7. Response is cached and returned.

### Sequence diagram

```mermaid
sequenceDiagram
   participant U as User/Client
   participant API as FastAPI Controller
   participant C as TTL Cache
   participant DB as PostgreSQL + pgvector
   participant G as LangGraph
   participant L as Gemini LLM

   U->>API: POST /research (query, optional session_id)
   API->>DB: ensure session + fetch recent turns
   API->>API: parse query (location/crop/compare intent)
   API->>C: lookup cache key
   alt Cache hit
      C-->>API: cached response
      API-->>U: 200 response
   else Cache miss
      API->>G: invoke workflow state
      G->>DB: retrieve vector memory + market/soil context
      G->>L: synthesize recommendation
      L-->>G: generated answer
      G->>DB: save episodic memory events
      G-->>API: structured result
      API->>DB: save user/assistant chat turns
      API->>C: store response (TTL)
      API-->>U: 200 response
   end
```

## 4) LangGraph node design

### `plan`
- File: [app/graph.py](../app/graph.py)
- Uses deterministic decomposition from [app/services/planner.py](../app/services/planner.py).

### `context`
- Resolves geography: [app/services/geo.py](../app/services/geo.py)
- Derives season: [app/services/season.py](../app/services/season.py)
- Resolves soil: [app/services/soil.py](../app/services/soil.py)
- Loads market trend snapshot: [app/services/market.py](../app/services/market.py)
- Retrieves memory under token budget: [app/services/memory.py](../app/services/memory.py)

### `synthesize`
- Builds structured prompt with conversation + retrieved memory context.
- Handles three modes:
  - generic ranking mode,
  - comparison mode for crop-vs-crop profitability,
  - focus-crop precaution mode for follow-up care/risk questions.
- Calls Gemini through [app/services/llm.py](../app/services/llm.py).
- Emits recommendation, follow-up suggestions, constraints flags, and top candidates.

### `memory`
- Saves episodic memory events (`query` + `result`) for semantic retrieval later.

## 5) Memory architecture

### A) Semantic episodic memory (`memory_events`)
- Embedding: deterministic hash embedding for portable demo behavior.
- Storage: pgvector vector column.
- Retrieval: nearest neighbors, then token-budget clipping.

### B) Conversation memory (`chat_sessions`, `chat_turns`)
- Purpose: multi-turn continuity.
- Keeps prior location/crop focus/top candidates and complete turn transcript.
- Enables follow-up questions without re-supplying context.

## 6) Constraints strategy

Configured in [app/config.py](../app/config.py) and `.env`:
- `MAX_CONTEXT_TOKENS` (default 2000)
- `MAX_SESSION_COST_USD` (default 0.05)
- `CACHE_ENABLED` and `CACHE_TTL_SECONDS`

Enforcement:
- Retrieval budget uses a capped token budget segment.
- Prompt/cost estimates are reported in response.
- `constraints_ok` indicates whether constraints were satisfied.

## 7) Caching strategy

- In-memory TTL cache implemented in [app/core/cache.py](../app/core/cache.py).
- Integrated at controller level in [app/controllers/research_controller.py](../app/controllers/research_controller.py).
- Cache key includes session/query/location/crop/IP dimensions for safe reuse.

## 8) API surface

Primary endpoints:
- `POST /research`
- `GET /sessions`
- `GET /sessions/{session_id}/history`
- `GET /health`

## 9) Data model summary

Reference data:
- [data/soil_defaults.json](../data/soil_defaults.json)
- [data/crop_prices.csv](../data/crop_prices.csv)

DB tables:
- `market_prices`
- `soil_defaults`
- `memory_events`
- `chat_sessions`
- `chat_turns`

## 10) Key design decisions

1. LangGraph over visual orchestrators
- Reason: deterministic, testable node-level behavior and explicit state transitions.

2. PostgreSQL + pgvector
- Reason: one DB for both relational state and vector retrieval, operational simplicity.

3. Two-layer memory
- Reason: semantic memory for long-term relevance + session turns for dialogue continuity.

4. Mode-aware synthesis
- Reason: avoid generic responses for specialized intents (comparison, precautions).

5. Graceful LLM fallback
- Reason: avoid hard failures when model identifiers or API behavior changes.

## 11) Known limitations

- Prototype agronomy logic is intentionally simplified.
- Price dataset is seed/mock and limited in geographic granularity.
- Cost estimation is heuristic, not exact provider billing.
- In-memory cache is single-process (not distributed).

## 12) Suggested future improvements

- Redis cache backend for multi-instance deployments.
- Rich agronomic data sources (district-level weather/soil APIs).
- Profitability model including input-cost datasets.
- Automated eval suite for response quality and constraint adherence.

## 13) Frontend architecture (Angular)

Frontend lives in sibling project folder `DeepResearchAgentUI`.

Routing and shell:
- Root shell: `src/app/app.ts`, `src/app/app.html`, `src/app/app.css`
- Routes: `src/app/app.routes.ts`
   - `/` → Home page (`pages/home`)
   - `/research` → Research console (`pages/research`)

State management:
- `ResearchPage` uses Angular `signal()` for UI state:
   - query, location, soil, loading flags, API status,
   - chat messages, selected session, sessions list.

Service layer:
- API client: `src/app/services/research-api.service.ts`
- Calls backend endpoints:
   - `GET /health`
   - `POST /research`
   - `GET /sessions`
   - `GET /sessions/{session_id}/history`

Interface contracts:
- Request/response interfaces are separated under:
   - `src/app/interfaces/health.interfaces.ts`
   - `src/app/interfaces/research.interfaces.ts`
   - `src/app/interfaces/session.interfaces.ts`

UI behavior notes:
- Left panel scroll is constrained to session list only.
- Session cards use meaningful labels derived from history (not raw IDs).
- Assistant output renders markdown-style bold (`**text**`) for readability.
