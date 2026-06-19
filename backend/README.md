## development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

fill in .env
copy over postgres-data
copy over google app secret

For AI-assisted Named Query generation, set:

```bash
OPENAI_API_KEY=...
OPENAI_MODEL=gpt-4.1-mini
```

Keep the OpenAI key in the backend `.env` only. The frontend already calls the
backend generation endpoint, so the browser never needs direct access to the key.

```bash
uvicorn src.server:app --reload --host 0.0.0.0 --port 8000
```

### setup ngrok webhook server for local dev

```bash
ngrok http 8001
```

set `PLAID_WEBHOOK_URL` to your public webhook endpoint, e.g.
`https://<your-domain>/api/v1/plaid/webhooks`

```bash
uvicorn src.dev_webhook_server:app --reload --host 0.0.0.0 --port 8001
```

## docker

```bash
docker build . -t family-finance-backend
docker run --rm --env-file .env -p 8000:8000 family-finance-backend
```

## postgres

```bash
docker run --rm -d \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=postgres \
  -v $(pwd)/postgres-data:/var/lib/postgresql \
  -p 5432:5432 \
  postgres:18
```
