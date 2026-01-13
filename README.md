## development

```bash
uvicorn server:app --reload --host 0.0.0.0 --port 8000
```


## docker

```bash
docker build . -t family-finance-backend
docker run --rm --env-file .env -p 8000:8000 family-finance-backend
```
