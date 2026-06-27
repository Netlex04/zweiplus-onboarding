# Zweiplus Onboarding-Plattform

Modulare, KI-gestützte Onboarding-Plattform für Datenschutzprozesse. Kunden bearbeiten konfigurierbare **Module** (Steps + Fragen), erhalten kontextbezogene **KI-Hilfe** auf Basis modulbezogener Wissenskonfiguration, Eingaben werden im **Backend verbindlich validiert**, Zweiplus prüft und gibt frei, und validierte Daten werden in ein **kanonisches Zwischenmodell** überführt und über **Zielsystem-Adapter (DPMS)** gemappt.

## Status je Phase

| Phase | Inhalt | Status |
|-------|--------|--------|
| 0/1 Doku & Planung | Architektur, Plan, OpenAPI, Design-System | ✅ |
| 1 Backend-Fundament | Datenmodell, Migrationen, Seeds | ✅ |
| 2 Backend-API & Validierung | REST, Statemachine, Backend-Validierung, Upload | ✅ |
| 3 KI-Service | Provider-Seam (fake/Anthropic), Chat/Suggest/Validate | ⏳ geplant |
| 4 Review & DPMS | Review, Canonical, DPMS-Adapter, Import | ⏳ geplant |
| 5 Frontend-Fundament | Dashboard, Modulkarten, Dashboard-KI | ⏳ geplant |
| 6 Frontend Modul-Flow & Review | Bearbeitung, Antworttypen, Vorlagen, Review | ⏳ geplant |

## Schnellstart

```bash
# Alles (Postgres + Backend + Frontend)
docker compose up --build
# Frontend: http://localhost:5173   API: http://localhost:8000   Docs: http://localhost:8000/docs
```

Lokal ohne Docker: siehe `backend/README` bzw. `frontend/README` (ab Phase 1/5).

## Tests

```bash
cd backend && pytest          # Backend (deterministisch, KI-Fake-Provider, SQLite)
cd frontend && npm test       # Frontend (ab Phase 5)
```

## Konfiguration

`.env` (Vorlage `.env.example`): `DATABASE_URL`, `AI_PROVIDER` (`fake`|`anthropic`, Default `fake`), `ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL` (`claude-opus-4-8`), `STORAGE_DIR`, `MAX_UPLOAD_MB`, `JWT_SECRET`, `CORS_ORIGINS`. Keine Secrets im Repo.

Demo-Zugänge: siehe [docs/annahmen.md](docs/annahmen.md).

## Dokumentation

- [Anforderungsdokument](docs/anfoderungsdokument.md) — Scope, MVP, Use Cases
- [Annahmen](docs/annahmen.md) — geschlossene Lücken
- [Architekturdokument](docs/architekturdokument.md) — Komponenten, Datenmodell, Seams
- [Implementierungsplan](docs/implementierungsplan.md) — Phasen 1–6 + Schnittstellenverträge
- [OpenAPI-Spezifikation](docs/openapi.yaml) — API-Vertrag
- [Betrieb & Datenschutz](docs/betrieb-und-datenschutz.md) — DSGVO, Auth, Backup
- [Design System](docs/design-system/design-system.md) — visuelles Fundament
