# Lantern Backend

FastAPI backend for Lantern, including Alembic migrations, PostgreSQL integration, Plaid webhook handling, Firebase authentication, Named Query generation, and the transaction sync worker.

Use the root [README.md](../README.md) for the full development runbook, including environment setup, Docker Compose bring-up, migrations, webhook tunneling, and frontend coordination.

## Backend-Only Commands

Set up a local virtualenv from this directory:

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run the API:

```sh
uvicorn src.server:app --reload --host 0.0.0.0 --port 8000
```

Run the sync worker:

```sh
python -m src.transactions_sync_runner
```

Apply migrations:

```sh
alembic upgrade head
```

Run tests:

```sh
pytest
```

## Notes

- Keep backend secrets in `backend/.env`.
- Set `OPENAI_API_KEY` in `backend/.env` for AI-assisted Named Query generation.
- Set `PLAID_WEBHOOK_URL` to `https://<public-domain>/api/v1/plaid/webhooks` when testing webhooks through a tunnel.
- Keep the sync worker running when testing webhook-created sync jobs.
