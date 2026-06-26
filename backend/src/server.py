# server_fastapi.py
import logging

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

load_dotenv(verbose=True)  # Load environment variables before importing other modules

from src.api.routes.households import router as households_router
from src.api.routes.named_queries import router as named_queries_router
from src.api.routes.plaid import router as plaid_router
from src.api.routes.plaid_webhooks import router as webhooks_router
from src.api.routes.transactions import router as transactions_router
from src.api.routes.users import router as users_router
from src.infrastructure.db.database import SessionLocal
from src.infrastructure.metrics import install_http_metrics, metrics_response
from src.modules import AppError


app = FastAPI()
install_http_metrics(app)
logger = logging.getLogger(__name__)


def database_ready() -> bool:
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


@app.get("/health/live")
async def health_live():
    return {"status": "ok"}


@app.get("/health/ready")
async def health_ready():
    if not database_ready():
        return JSONResponse(
            status_code=503,
            content={"status": "degraded", "detail": "Database unavailable"},
        )

    return {"status": "ok"}


@app.get("/metrics", include_in_schema=False)
async def metrics():
    return metrics_response(app)


@app.exception_handler(AppError)
async def handle_app_error(_, exc: AppError):
    if exc.status_code >= 500:
        logger.error(
            "Application error response status_code=%s detail=%s",
            exc.status_code,
            exc.detail,
            exc_info=exc,
        )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


@app.exception_handler(Exception)
async def handle_unexpected_error(_, exc: Exception):
    logger.error("Unhandled request error", exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router=plaid_router)
app.include_router(router=webhooks_router)
app.include_router(router=users_router)
app.include_router(router=households_router)
app.include_router(router=named_queries_router)
app.include_router(router=transactions_router)
