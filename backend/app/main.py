"""FastAPI application entry point (Phase 1 minimal surface).

Provides CORS, a health endpoint and an optional startup hook that loads seeds.
Routers for the onboarding domains are added in later phases.
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.seeds.loader import load_seeds

logger = logging.getLogger("app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load seeds on startup unless explicitly disabled (e.g. in some tests).
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

    @app.get("/api/health", tags=["health"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
