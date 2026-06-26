# Backend — Zweiplus Onboarding

FastAPI + SQLAlchemy 2.x + Alembic backend for the modular privacy onboarding
platform. **Phase 1 (Backend-Fundament):** data model, persistence,
configuration and idempotent seeds. REST endpoints, validation, AI and review
follow in later phases.

## Stack

Python 3.11+, FastAPI, SQLAlchemy 2.x, Alembic, Pydantic v2 + pydantic-settings,
pytest. PostgreSQL at runtime, SQLite for tests (selected via `DATABASE_URL`).

## Setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # adjust as needed (defaults: SQLite + fake AI provider)
```

## Configuration

All settings come from the environment (see `.env.example`, Architektur §9):

| Variable | Default | Purpose |
|----------|---------|---------|
| `DATABASE_URL` | `sqlite:///./zweiplus.db` | Postgres at runtime, SQLite for tests |
| `AI_PROVIDER` | `fake` | `fake` (no secret) or `anthropic` |
| `ANTHROPIC_API_KEY` | – | only for `AI_PROVIDER=anthropic` |
| `ANTHROPIC_MODEL` | `claude-opus-4-8` | model id |
| `STORAGE_DIR` | `./storage` | local file storage |
| `MAX_UPLOAD_MB` | `10` | upload size limit |
| `JWT_SECRET` | dev placeholder | auth (used from Phase 2) |
| `CORS_ORIGINS` | `http://localhost:5173` | comma-separated origins |
| `SEED_ON_STARTUP` | `1` | load seeds on app startup; `0` to skip |

## Database migrations (Alembic)

```bash
# Apply all migrations (creates the schema)
alembic upgrade head

# Generate a new migration after model changes
alembic revision --autogenerate -m "describe change"
```

The Alembic env reads `DATABASE_URL` from `Settings`, so the same command works
for SQLite and Postgres. SQLite uses batch mode for ALTERs.

## Seeds

Idempotent loader — running it repeatedly never creates duplicates:

```bash
python -m app.seeds.loader
```

Seeds also load automatically on app startup unless `SEED_ON_STARTUP=0`.

Seed content (`seeds/`):
- **Process:** `datenschutz_basis_onboarding`
- **Modules:** `software_inventory` (`unlock: always`), `tom_erfassung`,
  `avv_onboarding` (both `unlock: after software_inventory` → parallel, Annahme A3)
- **Knowledge:** 27 `KnowledgeEntry` entries covering all referenced config keys
- **Demo users** (password `demo1234`): `kunde@demo.test` (customer),
  `review@zweiplus.test` (reviewer), `admin@zweiplus.test` (admin)

## Run

```bash
uvicorn app.main:app --reload
# Health check: GET http://127.0.0.1:8000/api/health  ->  {"status": "ok"}
# OpenAPI docs: http://127.0.0.1:8000/docs
```

## Tests

```bash
pytest
```

Tests use an isolated SQLite database per test (no external services, AI uses
the deterministic fake provider in later phases).

## Layout

```
backend/
  app/
    config.py          # Settings (pydantic-settings)
    security.py        # bcrypt password hashing
    main.py            # FastAPI app, /api/health, startup seed hook
    db/                # Base, engine, get_session(), session_scope()
    models/            # enums + Definition/Instance ORM models
    seeds/loader.py    # idempotent seed loader
  seeds/               # JSON seed data (process, modules, knowledge, users)
  alembic/             # migration environment + versions
  tests/               # pytest suite
```

## For Phase 2

```python
from app.models import (              # all ORM entities + enums
    ProcessDefinition, ModuleDefinition, StepDefinition, QuestionDefinition,
    TemplateDefinition, KnowledgeEntry, User,
    ProcessInstance, ModuleInstance, StepInstance, Answer, FileUpload,
    AiSuggestion, AiValidationResult, BackendValidationResult,
    ReviewTask, CanonicalOutput, ImportJob,
    ModuleStatus, StepStatus, ImportStatus, QuestionType, Role,
    AnswerSource, ReviewStatus,
)
from app.db import get_session, session_scope   # FastAPI dependency / script scope
from app.config import get_settings, Settings
from app.security import hash_password, verify_password
```
