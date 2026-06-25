import logging

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

load_dotenv(verbose=True)  # Load environment variables before importing other modules

from src.modules import AppError
from .api.routes.plaid_webhooks import router as webhooks_router


app = FastAPI()
logger = logging.getLogger(__name__)


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
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router=webhooks_router)
