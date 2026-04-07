# DeepResearchAgentUI (Angular Frontend)

This is the Angular UI for the Deep Research Agent backend.

## Stack

- Angular 21 (standalone + routing + SSR scaffold)
- Signals-based state in the research page
- HTTP integration with FastAPI backend
- Served via Node.js http-server (v20.20.2)

## Prerequisites

- Node.js 20+
- npm
- Backend running at `http://127.0.0.1:8000`

## Quick start (Docker - Recommended)

From project root:

```bash
docker compose up --build
```

Frontend automatically starts on `http://localhost:4200`

**Running services output:**
```
✔ Container deepresearch-ui   Created
deepresearch-ui  | Starting up http-server, serving dist
deepresearch-ui  | http-server version: 14.1.1
deepresearch-ui  | Available on:
deepresearch-ui  |   http://127.0.0.1:4200
deepresearch-ui  |   http://172.20.0.4:4200
```

The http-server directly serves Angular browser bundles from `dist/browser/`, so routes like `/research` work correctly without path prefixes.

## Run locally

1. Install dependencies

```bash
npm install
```

2. Start frontend

```bash
npm start
```

3. Open

`http://localhost:4200`

## Build

```bash
npm run build
```

Production build output:

`dist/DeepResearchAgentUI`

## Routes

- `/` → Home page
- `/research` → Research chat console

Route config is in:

- `src/app/app.routes.ts`

## Project structure

- `src/app/pages/home` → Landing page
- `src/app/pages/research` → Main research chat UI
- `src/app/services/research-api.service.ts` → API calls
- `src/app/interfaces` → Request/response interfaces

## API integration

Frontend calls:

- `GET /health`
- `POST /research`
- `GET /sessions`
- `GET /sessions/{session_id}/history`

Base URL is currently set in:

- `src/app/services/research-api.service.ts`

## Notes

- Research page uses Angular `signal()` state.
- Left panel scroll is limited to the sessions list area.
- Markdown-style `**bold**` in assistant output is rendered as bold in UI.
- Backend secrets policy: keep real keys only in backend `.env` and commit only backend `.env.example`.
- Full system architecture (backend + frontend integration): `../DeepResearchAgent/docs/ARCHITECTURE.md`.
