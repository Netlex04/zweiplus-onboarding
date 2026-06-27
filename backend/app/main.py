"""FastAPI application entry point.

Wires CORS, the health endpoint, all domain routers (Phase 2) and a unified
``{error, detail}`` error schema (Architektur §11). Seeds load on startup when
``SEED_ON_STARTUP`` is not ``0``.
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api import ROUTERS
from app.config import get_settings
from app.seeds.loader import load_seeds
from app.services.statemachine import IllegalTransition

logger = logging.getLogger("app")

# Map HTTP status codes to short machine-readable error labels.
_ERROR_LABELS = {
    400: "bad_request",
    401: "unauthorized",
    403: "forbidden",
    404: "not_found",
    409: "conflict",
    413: "payload_too_large",
    415: "unsupported_media_type",
    422: "validation_error",
}


def _error_body(status_code: int, detail: object) -> dict:
    return {
        "error": _ERROR_LABELS.get(status_code, "error"),
        "detail": detail if isinstance(detail, str) else str(detail),
    }


@asynccontextmanager
async def lifespan(app: FastAPI):
    if os.getenv("SEED_ON_STARTUP", "1") != "0":
        try:
            counts = load_seeds()
            logger.info("Seeds loaded: %s", counts)
        except Exception:  # pragma: no cover - startup robustness
            logger.exception("Seed loading failed during startup")
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Zweiplus Onboarding API", version="0.1.0", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_body(exc.status_code, exc.detail),
            headers=getattr(exc, "headers", None),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        return JSONResponse(
            status_code=422,
            content={"error": "validation_error", "detail": exc.errors()},
        )

    @app.exception_handler(IllegalTransition)
    async def illegal_transition_handler(request: Request, exc: IllegalTransition):
        return JSONResponse(
            status_code=409, content=_error_body(409, str(exc))
        )

    @app.get("/api/health", tags=["health"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    for router in ROUTERS:
        app.include_router(router)

    return app


app = create_app()
