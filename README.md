## development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

```bash
uvicorn server:app --reload --host 0.0.0.0 --port 8000
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
