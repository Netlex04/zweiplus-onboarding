"""SQLAlchemy 2.x engine and session management.

Works with both PostgreSQL (runtime) and SQLite (tests). The SQLite-specific
``check_same_thread`` connect arg is only applied for sqlite URLs.
"""

from __future__ import annotations

from collections.abc import Generator, Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings


def _create_engine() -> Engine:
    settings = get_settings()
    connect_args: dict[str, object] = {}
    if settings.is_sqlite:
        # SQLite needs this when the connection is shared across threads
        # (FastAPI/uvicorn) and for in-memory test databases.
        connect_args["check_same_thread"] = False
    return create_engine(
        settings.database_url,
        connect_args=connect_args,
        future=True,
        pool_pre_ping=not settings.is_sqlite,
    )


engine: Engine = _create_engine()

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    class_=Session,
)


def get_session() -> Generator[Session, None, None]:
    """FastAPI dependency: yield a session and always close it."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@contextmanager
def session_scope() -> Iterator[Session]:
    """Transactional context manager for scripts/seed-loaders.

    Commits on success, rolls back on exception, always closes.
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
