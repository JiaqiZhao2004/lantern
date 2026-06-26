# Lantern

Lantern is a household finance app for bringing clarity and control to shared financial life.

| Directory   | Description                                                  |
| ----------- | ------------------------------------------------------------ |
| `backend/`  | FastAPI backend, Alembic migrations, PostgreSQL, sync worker |
| `frontend/` | React + TypeScript frontend built with Vite                  |
| `docs/adr/` | Architecture Decision Records                                |
| `ops/`      | Deployment and observability configuration                   |

## Development Runbook

### Prerequisites

- Docker and Docker Compose for the full local stack.
- Python 3 for backend-only development.
- Node.js and npm for frontend-only development.
- `ngrok` or another HTTPS tunnel when testing Plaid webhooks locally.
- A Firebase Admin SDK JSON file for backend authentication.

### 1. Configure the backend environment

Create the local backend environment file:

```sh
test -f backend/.env || cp backend/.env.example backend/.env
```

Fill in `backend/.env`. Keep secrets in this file only; do not expose backend secrets in the frontend.

Key values for local development:

- `DATABASE_URL`: use `postgresql+psycopg://postgres:password@localhost:5432/lantern` when running the backend directly on the host. Docker Compose overrides this to use the `db` service.
- `GOOGLE_APPLICATION_CREDENTIALS`: path to your Firebase Admin SDK JSON file when running directly on the host. Docker Compose mounts a local secret file at `/run/secrets/firebase-adminsdk.json`.
- `OPENAI_API_KEY`: required for AI-assisted Named Query generation.
- `OPENAI_MODEL`: optional; defaults can be overridden, for example `gpt-4.1-mini`.
- `PLAID_CLIENT_ID`, `PLAID_SECRET`, `SIGNAL_RULESET_KEY`, and related Plaid values for Plaid flows.
- `PLAID_WEBHOOK_URL`: public webhook URL when testing webhooks.

The root `docker-compose.yml` currently expects the Firebase Admin SDK JSON at:

```text
~/.secrets/lantern-firebase-adminsdk.json
```

Update the compose mount or place the file there before using the full stack.

### 2. Start the full stack

From the repository root:

```sh
docker-compose up --build
```

This starts:

- Postgres on `localhost:5432`
- Backend API on `http://localhost:8000`
- Backend sync worker
- Frontend on `http://localhost:3000`

### 3. Run migrations

After the database is running, apply migrations from the repository root:

```sh
docker-compose run --rm backend alembic upgrade head
```

For host-based backend development, run the same command from `backend/` after activating the virtualenv:

```sh
alembic upgrade head
```

### 4. Test Plaid webhooks locally

Start an HTTPS tunnel to the backend:

```sh
ngrok http 8000
```

Set `PLAID_WEBHOOK_URL` in `backend/.env` to:

```text
https://<your-ngrok-domain>/api/v1/plaid/webhooks
```

Restart the backend after changing the env file. Keep the `backend-worker` service running so webhook-created sync jobs are processed.

## Running Services Without Compose

### Backend API

From `backend/`:

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn src.server:app --reload --host 0.0.0.0 --port 8000
```

### Backend worker

From `backend/` with the virtualenv active:

```sh
python -m src.transactions_sync_runner
```

### Frontend

From `frontend/`:

```sh
npm install
npm start
```

The Vite dev server listens on `http://localhost:3000` and proxies `/api` to `VITE_BACKEND_HOST`, defaulting to `http://127.0.0.1:8000`.

## Verification Commands

Backend:

```sh
cd backend
pytest
```

Frontend:

```sh
cd frontend
npm test
npm run typecheck
npm run build
```

Regenerate frontend API types after changing backend schemas or routes. Start the backend first, then run:

```sh
cd frontend
npm run generate-api-types
```

## Backend Docker Image

To build and run only the backend container from `backend/`:

```sh
docker build . -t lantern-backend
docker run --rm --env-file .env -p 8000:8000 lantern-backend
```
