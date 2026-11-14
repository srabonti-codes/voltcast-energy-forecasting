from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import router
from app.config import ALLOWED_ORIGINS, APP_ENV, APP_NAME, APP_VERSION

logger = logging.getLogger(__name__)

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description="VoltCast ML-powered electricity consumption prediction platform.",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.exception_handler(Exception)
async def unexpected_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled request error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected server error occurred."},
    )


@app.get("/")
async def root() -> dict:
    return {
        "application": APP_NAME,
        "version": APP_VERSION,
        "environment": APP_ENV,
        "documentation": "/api/docs",
        "status": "running",
    }


@app.get("/health")
async def health() -> dict:
    return {
        "status": "healthy",
        "application": APP_NAME,
        "version": APP_VERSION,
    }
