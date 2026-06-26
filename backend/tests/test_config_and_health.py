"""Settings defaults and the /api/health endpoint."""

import importlib

from fastapi.testclient import TestClient

from app.config import Settings


def test_settings_defaults(monkeypatch):
    # Clear env so defaults are exercised deterministically.
    for var in (
        "DATABASE_URL",
        "AI_PROVIDER",
        "ANTHROPIC_MODEL",
        "MAX_UPLOAD_MB",
        "CORS_ORIGINS",
    ):
        monkeypatch.delenv(var, raising=False)
    settings = Settings(_env_file=None)
    assert settings.database_url.startswith("sqlite")
    assert settings.ai_provider == "fake"
    assert settings.anthropic_model == "claude-opus-4-8"
    assert settings.max_upload_mb == 10
    assert settings.cors_origins == ["http://localhost:5173"]
    assert settings.is_sqlite is True


def test_cors_origins_comma_separated():
    settings = Settings(_env_file=None, cors_origins="http://a.test, http://b.test")
    assert settings.cors_origins == ["http://a.test", "http://b.test"]


def test_health_endpoint(monkeypatch):
    monkeypatch.setenv("SEED_ON_STARTUP", "0")
    main = importlib.import_module("app.main")
    with TestClient(main.app) as client:
        resp = client.get("/api/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}
