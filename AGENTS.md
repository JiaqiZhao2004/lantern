# Repository Guidelines

## Project Structure & Module Organization
`backend/` contains the FastAPI app, Alembic migrations, and pytest suite. Core code lives in `backend/src/`, with HTTP routes under `backend/src/api/routes/`, shared infrastructure under `backend/src/infrastructure/`, and domain modules under `backend/src/modules/`. Tests are split into `backend/tests/unit/`, `backend/tests/integration/`, `backend/tests/api/`, and `backend/tests/e2e/`.

`frontend/` contains the Vite React app. App shell and routing live in `frontend/src/app/`, feature code is organized by domain in `frontend/src/features/`, reusable API helpers are in `frontend/src/shared/api/`, and shared UI components are in `frontend/src/shared/ui/`. Architecture decisions are documented in `docs/adr/`.

## Build, Test, and Development Commands
From `backend/`:
- `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt` sets up the API environment.
- `uvicorn src.server:app --reload --host 0.0.0.0 --port 8000` runs the backend locally.
- `pytest` runs the backend test suite.

From `frontend/`:
- `npm install` installs frontend dependencies.
- `npm start` starts the Vite dev server.
- `npm run build` creates a production build.
- `npm test` runs Vitest.
- `npm run typecheck` checks TypeScript without emitting files.

From the repo root:
- `docker-compose up --build` starts Postgres, backend, and frontend together.

## Security & Configuration Tips
Keep secrets in `backend/.env` only. Do not expose backend keys in the frontend. When working with generated API types, run the backend first, then use `npm run generate-api-types` from `frontend/` against `http://localhost:8000/openapi.json`.
