"""Declarative base and shared column helpers.

A single ``Base`` carries the metadata that both the ORM models and Alembic's
autogenerate use. Keeping it in its own module avoids import cycles between
models and the session/engine.
"""

from __future__ import annotations

import uuid

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


def new_uuid() -> str:
    """Generate a new UUID4 as a string (used for all primary keys)."""
    return str(uuid.uuid4())
