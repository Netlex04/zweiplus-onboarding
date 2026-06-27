# Zweiplus Onboarding-Plattform

Modulare, KI-gestützte Onboarding-Plattform für Datenschutzprozesse. Kunden bearbeiten konfigurierbare **Module** (Steps + Fragen), erhalten kontextbezogene **KI-Hilfe** auf Basis modulbezogener Wissenskonfiguration, Eingaben werden im **Backend verbindlich validiert**, Zweiplus prüft und gibt frei, und validierte Daten werden in ein **kanonisches Zwischenmodell** überführt und über **Zielsystem-Adapter (DPMS)** gemappt.

## Status je Phase

| Phase | Inhalt | Status |
|-------|--------|--------|
| 0/1 Doku & Planung | Architektur, Plan, OpenAPI, Design-System | ✅ |
| 1 Backend-Fundament | Datenmodell, Migrationen, Seeds | ✅ |
| 2 Backend-API & Validierung | REST, Statemachine, Backend-Validierung, Upload | ✅ |
| 3 KI-Service | LangChain (OpenAI-kompatibel/lokal), Chat/Suggest/Validate | ✅ |
| 4 Review & DPMS | Review, Canonical, DPMS-Adapter, Import | ✅ |
| 5 Frontend-Fundament | App-Shell, Auth/Routing, API-Client, Dashboard, Modulkarten, Dashboard-KI | ✅ |
| 6 Frontend Modul-Flow & Review | Bearbeitung, Antworttypen, Vorlagen, Review, Import | ✅ |

## Schnellstart

```bash
# Alles (Postgres + Backend + Frontend) — ein Befehl
docker compose up --build
# Frontend: http://localhost:5173   API: http://localhost:8000   Docs: http://localhost:8000/docs
docker compose down -v   # Stoppen + Volumes (DB, Storage) aufräumen
```

Das Backend führt beim Start automatisch `alembic upgrade head` gegen Postgres aus und lädt die Seeds. **KI:** Standardmäßig läuft der deterministische Stub (`AI_USE_STUB=1`) — kein Schlüssel/Modellserver nötig. Für einen echten, OpenAI-kompatiblen Provider in der Wurzel-`.env` (Vorlage `.env.example`) `AI_USE_STUB=0` setzen und `AI_BASE_URL`/`AI_API_KEY`/`AI_MODEL` füllen.

Lokal ohne Docker:

```bash
# Backend (Port 8000)
cd backend && python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
DATABASE_URL=sqlite:///./dev.db alembic upgrade head
AI_USE_STUB=1 SEED_ON_STARTUP=1 DATABASE_URL=sqlite:///./dev.db uvicorn app.main:app --port 8000

# Frontend (Port 5173) — in einem zweiten Terminal
cd frontend && npm ci
VITE_API_URL=http://localhost:8000 npm run dev
```

Demo-Login: `kunde@demo.test` / `demo1234`. Details: siehe `backend/README.md` bzw. `frontend/README.md`.

## Tests

```bash
cd backend && pytest          # Backend (deterministisch, KI-Stub-LLM, SQLite)
cd frontend && npm test       # Frontend (Vitest + React Testing Library)
```

## Konfiguration

`.env` (Vorlage `.env.example`): `DATABASE_URL` (Postgres-Treiber `postgresql+psycopg2`), `AI_USE_STUB`, `AI_BASE_URL` (OpenAI-kompatibler Endpoint, z. B. `https://api.openai.com/v1` oder lokal `http://localhost:11434/v1`), `AI_API_KEY`, `AI_MODEL`, `STORAGE_DIR`, `MAX_UPLOAD_MB`, `JWT_SECRET`, `CORS_ORIGINS`. Hinweis: `CORS_ORIGINS` per ENV als JSON-Array setzen, z. B. `["http://localhost:5173"]`. Die Wurzel-`.env.example` ist die Single Source der Docker-Compose-Defaults. Tests laufen ohne KI-Variablen (Stub-LLM). Keine Secrets im Repo.

Demo-Zugänge: siehe [docs/annahmen.md](docs/annahmen.md).

## Dokumentation

- [Anforderungsdokument](docs/anfoderungsdokument.md) — Scope, MVP, Use Cases
- [Annahmen](docs/annahmen.md) — geschlossene Lücken
- [Architekturdokument](docs/architekturdokument.md) — Komponenten, Datenmodell, Seams
- [Implementierungsplan](docs/implementierungsplan.md) — Phasen 1–6 + Schnittstellenverträge
- [OpenAPI-Spezifikation](docs/openapi.yaml) — API-Vertrag
- [Betrieb & Datenschutz](docs/betrieb-und-datenschutz.md) — DSGVO, Auth, Backup
- [Design System](docs/design-system/design-system.md) — visuelles Fundament
