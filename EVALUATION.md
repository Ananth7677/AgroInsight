# Evaluation: G3 Deep Research Agent + Memory Constraints

## 1) Architecture choices
- **Orchestration**: LangGraph state machine for deterministic multi-step reasoning.
- **LLM**: Gemini (via `langchain-google-genai`) with fallback path when key is absent.
- **Memory**: PostgreSQL + pgvector for persisted episodic memory retrieval.
- **Deployment**: Docker Compose for reproducible local evaluation.

## 2) Constraints (self-defined)
- **Context limit**: `MAX_CONTEXT_TOKENS=2000` per query.
- **Session budget**: `MAX_SESSION_COST_USD=0.05` estimated per session.

## 3) Memory strategy
- **Episodic writes**: each run stores query + result records with metadata and vector embedding.
- **Constrained retrieval**: top-k semantic retrieval, then token-budget clipping.
- **Summarization boundary**: retrieved snippets are compacted into minimal context lines for prompt use.

## 4) Trade-offs
- **Pros**:
  - Stable and testable behavior due to explicit graph nodes.
  - Works without paid APIs by deterministic fallback.
  - Persistent memory enables iterative quality improvement.
- **Cons**:
  - Hash embeddings are weaker than model embeddings.
  - Cost estimate is approximate (token-based heuristic).
  - Regional agronomy mappings are intentionally simplified for prototype speed.

## 5) Why no mandatory n8n/Dify
- Assignment says "use tools like n8n/Dify" as workflow suggestion, not hard requirement.
- LangGraph already provides programmatic query routing + memory management.
- n8n can be added later for cron ingestion and alert workflows if desired.

## 6) Business impact reasoning
- Recommends crops with both agronomic suitability and market trend awareness.
- Reduces bad decisions from spot-price noise by emphasizing historical trends.
- Defaults for missing data (location/soil) make system usable in real low-info situations.
