## Workflow (verbindlich)

**Rollentrennung:** Der **Orchestrator** plant und delegiert, implementiert aber nicht selbst. Jede abgegrenzte Implementierungsaufgabe (z. B. eine Phase des Implementierungsplans) geht an einen eigenen **Subagent** mit frischem Kontext.

### Orchestrator

- Zerlegt Arbeit in abgegrenzte Aufgaben, spawnt pro Aufgabe einen Subagent mit klarem Auftrag und Schnittstellenvertrag.
- **Serielle Abarbeitung bei Abhängigkeiten:** Phasen mit festgelegter Reihenfolge strikt nacheinander; der nächste Subagent startet erst, wenn der vorherige fertig (Rückgabe geprüft, ggf. MR gemerged) ist. Unabhängige Aufgaben dürfen parallel laufen.
- **Kontext destillieren statt weiterreichen:** Jeder Subagent startet mit frischem Kontext. Der Orchestrator gibt ihm nur das Nötige aus den vorherigen Rückgaben mit (Schnittstellen, getroffene Entscheidungen, Branch/MR, betroffene Files) — nicht den Gesamtverlauf.
- **Phase zu groß → Sub-Plan, aber nur im Notfall:** Ist der Aufwand einer Phase zu groß, darf daraus ein Sub-Implementierungsplan abgeleitet werden — nur wenn wirklich nötig. Das deutet meist auf einen Planungsfehler hin; diesen für die Zukunft im Implementierungsplan korrigieren.
- Schreibt keinen Implementierungscode selbst.

### Subagent (pro Aufgabe)

- **Branch + MR:** Vor dem Branch IMMER erst pullen (aktueller Stand). Neuen Branch (`feat/`, `fix/`, `chore/`, …) anlegen, nie direkt auf `main`. Nach der Änderung remote pushen und als MR stellen. Danach prüfen, ob die CI-Actions durchlaufen, und Fehler beheben.
- **Test-Driven:** Testbare Anforderungen zuerst als Test mit erwartetem Verhalten schreiben, dann den Code dazu. Nicht-testbares (z. B. reines Styling) direkt umsetzen.
- **Doku pflegen:** Prüfen, ob Doku angepasst werden muss (Implementierungsplan, README, OpenAPI, Architektur, …). Plan­abweichungen sind verbindlich nachzuziehen.
- **Frontend im Browser testen:** Bei frontend-relevanten Änderungen das Ergebnis im Browser verifizieren.
- **Code-Prinzipien:** DRY, KISS, YAGNI; kleine, klar benannte Einheiten; bestehende Patterns wiederverwenden statt neu erfinden.
- **Wissenslücken per Websuche schließen:** Bei fehlenden Infos (passende Library, aktueller Library-Syntax, …) nicht raten, sondern recherchieren.
- Gibt eine kompakte Zusammenfassung an den Orchestrator zurück.

## Dokumentation (verbindlich)

**Die gesamte Doku ist verbindlich** — vor jeder Arbeit die relevanten Dokumente konsultieren und einhalten (nicht nur das Design System).

- [README](../README.md) — Einstieg: Status, Schnellstart, Tests, Konfiguration, Doku-Index
- [Anforderungsdokument](../docs/anfoderungsdokument.md) — Scope, MVP, Use Cases
- [Annahmen](../docs/annahmen.md) — geschlossene Lücken / MVP-Entscheidungen
- [Architekturdokument](../docs/architekturdokument.md) — Komponenten, Datenmodell, Datenflüsse
- [OpenAPI-Spezifikation](../docs/openapi.yaml) — API-Vertrag
- [Implementierungsplan](../docs/implementierungsplan.md) — Phasen 1–6 mit Schnittstellenverträgen
- [Betrieb & Datenschutz](../docs/betrieb-und-datenschutz.md) — DSGVO, TLS/Reverse-Proxy, Backup, Tests
- [Design System](../docs/design-system/design-system.md) — visuelles Fundament (siehe unten)

## Stack & Konventionen

- **Backend:** Python 3.11+, FastAPI, SQLAlchemy 2.x, Alembic, Pydantic v2 (`pydantic-settings`), pytest. Verbindliche Backend-Validierung über Pydantic + fachliche Regeln.
- **DB:** PostgreSQL (Laufzeit, Docker Compose); SQLite via `DATABASE_URL` für deterministische Tests.
- **KI:** hinter `AiProvider`-Seam, umgesetzt mit **LangChain** (`langchain-openai` `ChatOpenAI`) gegen eine **OpenAI-kompatible** API. `AI_BASE_URL` konfigurierbar → OpenAI **oder** lokales Modell (Ollama/LM Studio/vLLM). Tests gegen deterministischen Stub-LLM. Aktuelle LangChain-Syntax per Websuche prüfen, nicht raten.
- **Seams:** `AiProvider`, `FileStorage`, `TargetAdapter` als ABCs + Fakes; Auswahl per `Settings`.
- **Frontend:** React + Vite + TypeScript. Design **ausschließlich** über `frontend/src/styles/tokens.css` (Kopie aus `docs/design-system/tokens.css`) — keine Hex-/px-Literale in Components, AA-Kontrast, dunkle Tinte auf Grün.
- **Start:** `docker compose up --build`. **Tests:** `cd backend && pytest`, `cd frontend && npm test`.
- **Git (projektangepasst):** lokale Feature-Branches pro Phase (`feat/…`), lokale Commits — **kein** Push/PR auf den Remote (Entscheidung des Owners). Co-Author-Trailer in Commits beibehalten.
- **Keine Secrets im Repo;** `.env` via `.env.example`, `.gitignore` für `storage/`, `.env`, `node_modules`, venv.
