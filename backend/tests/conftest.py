"""Pytest fixtures: isolated SQLite database per test.

Each test gets a fresh SQLite file-backed database (created via the ORM
metadata), keeping tests deterministic and independent of the developer's
configured DATABASE_URL.
"""

from __future__ import annotations

import os
from collections.abc import Iterator

import pytest

# Ensure the app never tries to load seeds on FastAPI startup during tests
# unless a test explicitly opts in.
os.environ.setdefault("SEED_ON_STARTUP", "0")

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
import app.models  # noqa: F401  -- register all tables on Base.metadata


@pytest.fixture
def db_session(tmp_path) -> Iterator[Session]:
    db_file = tmp_path / "test.db"
    engine = create_engine(
        f"sqlite:///{db_file}",
        connect_args={"check_same_thread": False},
        future=True,
    )
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine, expire_on_commit=False, class_=Session)
    session = TestSession()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()
