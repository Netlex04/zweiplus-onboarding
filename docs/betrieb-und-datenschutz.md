# Betrieb & Datenschutz

Die Plattform verarbeitet sensible Unternehmens- und Datenschutzinformationen. Dieses Dokument hält die organisatorischen und technischen Leitplanken fest (Anforderungen §14.2/§14.3).

## 1. Authentifizierung & Autorisierung

- Login per E-Mail/Passwort → Bearer-Token (JWT). Passwörter gehasht (bcrypt/argon2).
- Rollen: `customer`, `reviewer`, `admin`. Endpunkte prüfen Rolle serverseitig.
- Kein Zugriff über Rollen-/Instanzgrenzen hinweg (Kunde sieht nur eigenen Prozess).

## 2. KI & Datenminimierung

- KI-Provider hinter `AiProvider`-Seam; **Default `fake`** (keine Datenweitergabe an Dritte).
- Bei `anthropic`: nur kontextrelevante Felder werden übermittelt (keine vollständigen Kundendatensätze), API-Key nur aus ENV.
- KI schreibt nie final in Zielsysteme; jeder Vorschlag ist `requires_review` und durchläuft Backend-Validierung + Review (§4.3/§8.5).
- Strukturierte KI-Outputs werden vor Persistenz Backend-validiert.

## 3. Dateien & Storage

- Upload-Whitelist: `pdf, docx, xlsx, png, jpg, jpeg`; max. 10 MB (siehe [annahmen.md](annahmen.md) A6).
- `FileStorage`-Seam (lokal im MVP, S3-fähig später); Dateien mit Modul-/Step-/Frage-Instanz verknüpft.
- Storage-Verzeichnis nicht im Repo (`.gitignore`).

## 4. Transport & Secrets

- TLS-Terminierung über Reverse-Proxy (z. B. Caddy/Traefik/Nginx) vor dem Backend; lokal HTTP.
- Keine Secrets im Repo; Konfiguration via ENV/`.env` (Vorlage `.env.example`). `JWT_SECRET`, `ANTHROPIC_API_KEY` nur aus Umgebung.

## 5. Nachvollziehbarkeit (Audit)

Jede `Answer` trägt `source` (`user|ai|document|manual`), `ai_suggested`, `created_by`, Zeitstempel. Review-Aktionen und Importjobs werden mit Status/Zeit/Reviewer gespeichert. Logs strukturiert, **ohne PII/Secrets**.

## 6. Backup & Betrieb

- PostgreSQL-Backups (z. B. `pg_dump` periodisch); Storage-Verzeichnis mitsichern.
- Migrationen versioniert (Alembic), idempotente Seeds.
- Externe Telemetrie deaktiviert; lokale Verarbeitung bevorzugt.

## 7. DSGVO-Bezug

- Trennung von Kundendaten je Prozessinstanz.
- Datensparsamkeit gegenüber KI-Diensten; Option auf datenschutzkonforme/self-hosted Modelle (Seam vorbereitet).
- Löschkonzept: Prozessinstanz-Löschung entfernt zugehörige Instanzen, Antworten, Uploads (post-MVP zu automatisieren).

## 8. Build/Start (Docker Compose)

Ein-Befehl-Start des Gesamtstacks (Postgres + Backend + Frontend):

```bash
docker compose up --build        # Frontend :5173, API :8000, Docs :8000/docs
docker compose down -v           # Stoppen und Volumes (DB, Storage) entfernen
```

- **Services:** `db` (postgres:16-alpine, Healthcheck `pg_isready`, Named Volume `db_data`), `backend` (FastAPI, `depends_on: db healthy`; Entrypoint führt `alembic upgrade head` aus, dann `uvicorn`; Seeds via Startup-Hook), `frontend` (Multi-Stage Build → nginx:alpine, SPA-Fallback auf `index.html`).
- **Konfiguration:** Single Source der Compose-Defaults ist die Wurzel-`.env.example` (nach `.env` kopieren zum Überschreiben) — nur Demo-Werte, keine echten Secrets. `DATABASE_URL` nutzt den Treiber `postgresql+psycopg2`; `CORS_ORIGINS` ist als JSON-Array zu setzen (pydantic-settings parst Listenfelder als JSON), z. B. `["http://localhost:5173"]`.
- **KI/DSGVO:** Default `AI_USE_STUB=1` (deterministischer Offline-Stub, kein Schlüssel/Server nötig). Für einen echten, OpenAI-kompatiblen Provider `AI_USE_STUB=0` setzen und `AI_BASE_URL`/`AI_API_KEY`/`AI_MODEL` füllen.
- **Persistenz:** DB im Volume `db_data`, Uploads im Volume `backend_storage` (`STORAGE_DIR=/app/storage`).
