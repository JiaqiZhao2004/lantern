FROM python:3.12-alpine

WORKDIR /app
COPY requirements.txt .

RUN pip3 install -r requirements.txt

COPY . .

ENV FASTAPI_APP=/app/src/server.py
EXPOSE 8000
ENTRYPOINT ["uvicorn"]
CMD ["src.server:app", "--host=0.0.0.0", "--port=8000", "--reload"]
