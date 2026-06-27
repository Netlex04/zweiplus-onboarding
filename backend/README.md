# Backend — Zweiplus Onboarding

FastAPI + SQLAlchemy 2.x + Alembic backend for the modular privacy onboarding
platform. **Phase 1:** data model, persistence, configuration, idempotent seeds.
**Phase 2:** REST API (auth, processes/dashboard, modules, steps, uploads,
templates), the module engine (unlock/progress/state machine) and the binding
backend validation service. **Phase 3:** AI service (`/api/ai/*`) — contextual
chat, structured suggestions, semantic validation and document analysis via
LangChain against any OpenAI-compatible endpoint. Review follows in later phases.

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
| `AI_BASE_URL` | `http://localhost:11434/v1` | OpenAI-compatible chat endpoint (OpenAI or local Ollama/LM Studio/vLLM) |
| `AI_API_KEY` | `not-needed` | API key; any non-empty value for keyless local endpoints |
| `AI_MODEL` | `gpt-4o-mini` | model id (or a local model name) |
| `AI_USE_STUB` | `0` | `1` forces the deterministic offline stub LLM (local smoke, no key/server) |
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
    auth.py            # JWT issue/decode + current_user / require_role deps
    main.py            # FastAPI app, routers, unified {error,detail} handlers
    db/                # Base, engine, get_session(), session_scope()
    models/            # enums + Definition/Instance ORM models
    schemas/           # Pydantic v2 request/response models (camelCase aliases)
    api/               # routers: auth, definitions, processes, modules, steps,
                       #          uploads, templates  (+ deps.py access checks)
    services/          # statemachine, module_engine, validation, step_service,
                       #          templates, dto
    providers/         # storage.py  (FileStorage ABC + LocalFileStorage seam)
    seeds/loader.py    # idempotent seed loader
  seeds/               # JSON seed data (process, modules, knowledge, users)
  alembic/             # migration environment + versions
  tests/               # pytest suite
```

## API & Auth (Phase 2)

Bearer-token auth (HS256 JWT signed with `JWT_SECRET`). Log in, then send
`Authorization: Bearer <token>` on every protected endpoint. Roles: `customer`,
`reviewer`, `admin`. A customer may only access their own process (matched on
`customerName == user.name`).

| Method & path | Role | Purpose |
|---------------|------|---------|
| `POST /api/auth/login` | public | Email/password → `{token, role, name}` |
| `GET  /api/process-definitions` | any auth | Seeded process definitions |
| `POST /api/processes` | any auth | Create process + module/step instances → Dashboard |
| `GET  /api/processes` | reviewer/admin | List process instances |
| `GET  /api/processes/{id}` | owner/staff | Dashboard DTO (ModuleCards + overallProgress) |
| `GET  /api/modules/{moduleInstanceId}` | owner/staff | Module detail (intro, steps, templates) |
| `GET  /api/steps/{stepInstanceId}` | owner/staff | Questions + answers + per-question visibility |
| `PUT  /api/steps/{stepInstanceId}/answers` | owner/staff | Save answers, validate → `{stepStatus, validation}` |
| `POST /api/steps/{stepInstanceId}/complete` | owner/staff | Complete step (200) or 409 if invalid |
| `POST /api/uploads` | owner/staff | Multipart upload (type/size whitelist, 415 on bad type) |
| `GET  /api/uploads/{id}/download` | owner/staff | Download a stored file |
| `GET  /api/templates/{key}` | any auth | Rendered email/text template (placeholders) |
| `GET  /api/templates/{key}/file` | any auth | Template file (generated placeholder) |

Upload whitelist (Annahme A6): `pdf, docx, xlsx, png, jpg, jpeg`, max `MAX_UPLOAD_MB`.

### AI endpoints (Phase 3)

All require auth. Backed by the `AiProvider` seam (LangChain `ChatOpenAI` against
`AI_BASE_URL`). Structured output is validated against a Pydantic schema before
persistence; suggestions always carry `requiresReview=true` (KI writes nothing
final — FR-AI-007).

| Method & path | Request (camelCase) | Response |
|---------------|---------------------|----------|
| `POST /api/ai/chat` | `{context, contextRef?, message, history[]}` | `{reply}` |
| `POST /api/ai/suggest` | `{stepInstanceId?, questionKey?}` | `AiSuggestion` (persisted) |
| `POST /api/ai/validate` | `{stepInstanceId}` | `AiValidationResult` (persisted) |
| `POST /api/ai/analyze-document` | `{uploadId}` | `AiSuggestion` with `sourceUploadId` (persisted) |

`context` ∈ `dashboard|module|step|question`. The system prompt cascades the
module → step → question knowledge config (`ai_knowledge_config` /
`knowledge_scope`) into the matching `KnowledgeEntry` contents. For a local,
key-free smoke run set `AI_USE_STUB=1` (deterministic offline stub LLM).

### Quick start (fresh SQLite)

```bash
DATABASE_URL="sqlite:///./dev.db" alembic upgrade head   # create schema
DATABASE_URL="sqlite:///./dev.db" uvicorn app.main:app   # seeds load on startup
```

## For later phases (consumable seams)

```python
from app.models import (              # all ORM entities + enums (Phase 1)
    ProcessDefinition, ModuleDefinition, StepDefinition, QuestionDefinition,
    TemplateDefinition, KnowledgeEntry, User,
    ProcessInstance, ModuleInstance, StepInstance, Answer, FileUpload,
    AiSuggestion, AiValidationResult, BackendValidationResult,
    ReviewTask, CanonicalOutput, ImportJob,
    ModuleStatus, StepStatus, ImportStatus, QuestionType, Role,
    AnswerSource, ReviewStatus,
)
from app.db import get_session, session_scope
from app.config import get_settings, Settings
from app.security import hash_password, verify_password

# Phase 2 services (reusable by Phase 3/4):
from app.auth import current_user, require_role, create_access_token
from app.services import module_engine          # create_process_instance,
                                                 # evaluate_unlocks, module_progress,
                                                 # is_question_visible, ...
from app.services import validation              # validate_step, run_step_validation
from app.services import step_service            # save_answers, complete_step
from app.services.statemachine import (          # legal-transition enforcement
    assert_step_transition, assert_module_transition, IllegalTransition)
from app.providers.storage import FileStorage, LocalFileStorage, get_storage

# Phase 3 AI seam + services (reusable by Phase 4/6):
from app.providers.ai import (                   # AI provider seam
    AiProvider, LangChainAiProvider, get_ai_provider)
from app.providers.ai_stub import StubChatModel  # deterministic offline LLM for tests
from app.services import ai_context              # build_system_prompt, gather_answer_context
from app.services import ai_service              # run_chat/suggest/validate/analyze_document
```
