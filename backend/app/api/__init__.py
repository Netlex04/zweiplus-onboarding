"""API routers registry."""

from app.api import (
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
]

__all__ = ["ROUTERS"]
