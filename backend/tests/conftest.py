"""Pytest fixtures: isolated SQLite database per test + seeded API TestClient.

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


@pytest.fixture
def api(tmp_path, monkeypatch):
    """A TestClient backed by a fresh, seeded SQLite DB and isolated storage.

    Yields ``(client, TestSession)`` so tests can both call the HTTP API and
    inspect the database directly.
    """
    from fastapi.testclient import TestClient

    from app.config import Settings, get_settings
    from app.db.session import get_session
    from app.main import create_app
    from app.seeds.loader import load_seeds

    db_file = tmp_path / "api.db"
    storage_dir = tmp_path / "storage"
    storage_dir.mkdir()

    test_settings = Settings(
        database_url=f"sqlite:///{db_file}",
        storage_dir=str(storage_dir),
        jwt_secret="test-secret",
        max_upload_mb=10,
    )

    engine = create_engine(
        f"sqlite:///{db_file}",
        connect_args={"check_same_thread": False},
        future=True,
    )
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine, expire_on_commit=False, class_=Session)

    # Seed the test DB.
    seed_session = TestSession()
    try:
        load_seeds(seed_session)
        seed_session.commit()
    finally:
        seed_session.close()

    monkeypatch.setenv("SEED_ON_STARTUP", "0")
    app = create_app()

    def _override_session() -> Iterator[Session]:
        s = TestSession()
        try:
            yield s
        finally:
            s.close()

    app.dependency_overrides[get_session] = _override_session
    app.dependency_overrides[get_settings] = lambda: test_settings

    client = TestClient(app)
    try:
        yield client, TestSession
    finally:
        client.close()
        engine.dispose()


def login(client, email: str, password: str = "demo1234") -> dict:
    """Helper: log in and return ``{"headers": {...}, "body": {...}}``."""
    resp = client.post(
        "/api/auth/login", json={"email": email, "password": password}
    )
    resp.raise_for_status()
    body = resp.json()
    return {"headers": {"Authorization": f"Bearer {body['token']}"}, "body": body}
