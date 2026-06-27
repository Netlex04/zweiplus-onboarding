"""API routers registry."""

from app.api import (
    ai,
    auth,
    definitions,
    imports,
    modules,
    processes,
    review,
    steps,
    templates,
    uploads,
)

ROUTERS = [
    auth.router,
    definitions.router,
    processes.router,
    modules.router,
    steps.router,
    uploads.router,
    templates.router,
    ai.router,
    review.router,
    imports.router,
]

__all__ = ["ROUTERS"]
