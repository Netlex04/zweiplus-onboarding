"""API routers registry."""

from app.api import (
    ai,
    auth,
    definitions,
    modules,
    processes,
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
]

__all__ = ["ROUTERS"]
