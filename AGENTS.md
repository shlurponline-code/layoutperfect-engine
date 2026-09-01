# Base44 Dev Environment

## What this app is
A Python/FastAPI typesetting engine ("Layout Perfect"). Backend-only — no frontend.
Entry point: `api_server.py` (uvicorn). Core engine: `typeset_engine.py`. ePub builder: `epub_builder.py`.

## Running it
```
docker compose -f docker-compose.base44.yml up -d
```
- Service `api` runs on host port **3000** (mapped to container 3000).
- Base image `python:3.12-slim`; source bind-mounted at `/app`; uvicorn `--reload` watches for edits.
- Startup installs `fonts-freefont-ttf` (required by the engine's FreeSerif fonts) and pip deps from `requirements.txt` on first boot.

## Endpoints
- `GET /health` — health check
- `POST /typeset` — typeset manuscript → PDF (auth: `api_key` field, dev key `lp-dev-key-change-me`)
- `POST /epub` — build ePub
- `GET /docs` — FastAPI interactive docs (good for manual testing in the preview)

## Secrets
None required. `LP_API_KEY` defaults to a dev value; no external services are called.

## Notes
- No frontend exists, so the preview shows the FastAPI JSON/JSON-docs pages, not a UI.
- CORS is open (`allow_origins=["*"]`).
