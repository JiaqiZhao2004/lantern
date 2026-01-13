FROM python:3.12-alpine

WORKDIR /app
COPY . .

RUN pip3 install -r requirements.txt

ENV FASTAPI_APP=/app/server.py
EXPOSE 8000
ENTRYPOINT ["uvicorn"]
CMD ["server:app", "--host=0.0.0.0", "--port=8000", "--reload"]
