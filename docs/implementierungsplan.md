# Implementierungsplan

Sechs Phasen, die nahtlos ineinandergreifen. Jede Phase wird von einem eigenen Subagent mit frischem Kontext umgesetzt (siehe [.claude/CLAUDE.md](../.claude/CLAUDE.md)). Test-Driven; nach jeder Phase reale Verifikation.

## Wie die Phasen ineinandergreifen — Schnittstellen-Verträge

| Phase | Definiert (Output-Vertrag) | Konsumiert (von vorher) |
|-------|----------------------------|--------------------------|
| 1 Backend-Fundament | SQLAlchemy-Modelle (alle Definition+Instance-Entitäten), Alembic-Migrationen, Seed-Loader + 3 Seed-Module, `Settings`, DB-Session-Dependency, Enums | — |
| 2 Backend-API & Validierung | REST-Endpunkte Prozess/Modul/Step/Answer/Upload/Template, Modul-Engine (Freischaltung/Progress/Statemachine), Backend-Validierungs-Service, Auth, `openapi.yaml` aktuell | Modelle, Enums, Seeds, Settings (P1) |
| 3 KI-Service | `AiProvider`-Seam (LangChain gegen OpenAI-kompatible API + Test-Stub), `/api/ai/*`-Endpunkte, Prompt-Komposition aus `ai_knowledge_config`+`KnowledgeEntry`, strukturierter Output, `AiSuggestion`/`AiValidationResult`-Persistenz | Modelle+Knowledge (P1), Step/Answer-API (P2) |
| 4 Review & DPMS-Adapter | `/api/review/*`, Canonical-Output-Service, `TargetAdapter`-Seam + `DpmsAdapter`, Importvorschau/-status, `/api/import-jobs/*` | Statemachine+Validierung (P2), AiSuggestion (P3) |
| 5 Frontend-Fundament | Vite/React/TS-App, Tokens, API-Client+Auth, Routing, Dashboard (Modulkarten, Status, Zuständigkeit, Sperre, Progress), Dashboard-KI-Chat | Alle Backend-APIs (P2–P4) |
| 6 Frontend Modul-Flow & Review | Modul-Start, Modul-Bearbeitung (4 Antworttypen, Upload, KI-Hilfe, Vorlagen, Validierung), Review-Screen (Freigabe, Importvorschau) | API-Client+Routing (P5), Backend-APIs |

**Seam-First-Regel:** Schemas & öffentliche Signaturen (Modelle, Enums, OpenAPI-Pfade, Provider-ABCs) werden in der definierenden Phase **vollständig** angelegt, bevor Folgephasen sie konsumieren.

---

## Phase 1 — Backend-Fundament

**Ziel:** Datenmodell, Persistenz, Konfiguration, Seeds stehen.
**Voraussetzungen:** keine.

**Arbeitspakete:**
- [ ] Projektgerüst `backend/` (FastAPI, SQLAlchemy, Alembic, Pydantic-Settings, pytest), Deps gepinnt.
- [ ] `Settings` (ENV) + `.env.example`; `DATABASE_URL` (Postgres prod / SQLite test).
- [ ] Alle Entitäten aus Architektur §5 als SQLAlchemy-Modelle + Enums (§5.3).
- [ ] Alembic-Initialmigration; DB-Session-Dependency.
- [ ] Seed-Loader (idempotent) + Seeds: Prozess `datenschutz_basis_onboarding` mit `software_inventory`, `tom_erfassung`, `avv_onboarding` (Intro, Steps, Fragen aller 4 Typen, Templates, ai_knowledge_config, unlock_rules gem. annahmen A3), `KnowledgeEntry`-Set, Demo-User (A5).
- [ ] Tests: Modelle anlegbar, Seed-Loader idempotent, Enums vollständig.

**Schnittstellenvertrag → Phase 2:** Importierbare Modelle/Enums/Settings/`get_session`; geseedete DB mit lauffähigem Demo-Prozess.
**DoD:** `pytest` grün; `alembic upgrade head` + Seed laufen gegen Postgres und SQLite. Deckt Datenmodell §12, FR-MOD-001/002, A1–A3, A5, A8, A9.

---

## Phase 2 — Backend-API & Validierung

**Ziel:** Vollständige REST-API für Bearbeitung + verbindliche Backend-Validierung + Statemachine.
**Voraussetzungen:** P1.

**Arbeitspakete:**
- [ ] Auth: `POST /api/auth/login` (Bearer/JWT), Rollen-Dependency.
- [ ] `POST /api/processes`, `GET /api/processes`, `GET /api/processes/{id}` (Dashboard-DTO: Module mit Status/Progress/Zuständigkeit/Sperre/nächste Aktion).
- [ ] Modul-Engine: Freischaltung aus `unlock_rule`, Progress, Status-Statemachine (Architektur §5.3) — erlaubte Übergänge erzwingen.
- [ ] `GET /api/modules/{id}`, `GET /api/steps/{id}` (Fragen + Antworten + Sichtbarkeitslogik FR-Q-007), `PUT /api/steps/{id}/answers`, `POST /api/steps/{id}/complete`.
- [ ] Backend-Validierungs-Service (FR-VAL-001/002): Schema/Typ/Pflicht/erlaubte Werte/Statusübergang/Berechtigung + fachliche Regeln; Ergebnis als `BackendValidationResult`.
- [ ] Upload: `POST /api/uploads` (Typ/Größen-Whitelist A6, `FileStorage`-Seam local), `GET /api/uploads/{id}/download`.
- [ ] Vorlagen: `GET /api/templates/{key}` (E-Mail mit Platzhalter-Rendering FR-TPL-002), `GET /api/templates/{key}/file`.
- [ ] `openapi.yaml` mit Implementierung konsistent halten.
- [ ] Tests: Statemachine-Übergänge, Validierung (positiv/negativ), Sichtbarkeitslogik, Progress, Upload-Whitelist, Auth/Rollen.

**Schnittstellenvertrag → Phase 3/4:** Stabile Step/Answer/Module-Endpunkte + DTOs; `BackendValidationResult`; Statemachine als Service nutzbar; `FileStorage`-Seam.
**DoD:** `pytest` grün; API real hochgefahren, E2E-Smoke: Login→Prozess→Modul→Step→Antworten→Validierung→Step complete→Progress steigt. Deckt FR-STEP, FR-Q, FR-DASH-001/002/003, FR-VAL, FR-DOC-001/002, FR-TPL.

---

## Phase 3 — KI-Service

**Ziel:** Kontextbezogene KI-Assistenz, strukturierter Output, semantische Prüfung — provider-agnostisch.
**Voraussetzungen:** P1, P2.

**Arbeitspakete:**
- [ ] `AiProvider`-ABC + `LangChainAiProvider` (LangChain `langchain-openai` `ChatOpenAI` gegen OpenAI-kompatible API, `base_url` per ENV → OpenAI oder lokales Modell) + deterministischer `StubChatModel` für Tests. **KI-Wissen aktuell halten:** aktuelle LangChain-Syntax (`with_structured_output`, `ChatOpenAI`) vor Implementierung per Websuche verifizieren.
- [ ] Prompt-Komposition: Auflösung `ai_knowledge_config` (Modul→Step→Frage) gegen `KnowledgeEntry`; Kontext aus bisherigen Antworten/Dokumenten; minimale Datenweitergabe.
- [ ] `POST /api/ai/chat` (Kontexte dashboard/module/step/question), `POST /api/ai/suggest` (strukturierter Vorschlag → `AiSuggestion`), `POST /api/ai/validate` (semantisch → `AiValidationResult`), `POST /api/ai/analyze-document` (Upload→Vorschläge, Herkunft FR-DOC-004).
- [ ] Strukturierter Output Backend-validiert vor Persistenz; `requires_review` gesetzt; KI schreibt nie final (FR-AI-007).
- [ ] Tests: deterministisch gegen `StubChatModel` — Kontextauflösung, Schema-Konformität des Outputs, Validierungsergebnis-Persistenz, Knowledge-Kaskade.

**Schnittstellenvertrag → Phase 4/6:** `/api/ai/*`-Endpunkte + Response-Schemas; `AiSuggestion`/`AiValidationResult` lesbar für Review/Frontend.
**DoD:** `pytest` grün (Stub-LLM); reale Smoke der Endpunkte. Deckt FR-AI-001…007, FR-DOC-003/004, §10, §11.

---

## Phase 4 — Review, Canonical & DPMS-Adapter

**Ziel:** Zweiplus-Review, kanonischer Output, Zielsystem-Mapping + Importvorschau/-status.
**Voraussetzungen:** P2 (Statemachine/Validierung), P3 (AiSuggestion).

**Status:** ✅ abgeschlossen (`feat/phase-4-review-import`, in den Phase-6-Branch integriert).

**Arbeitspakete:**
- [x] `GET /api/review/tasks`, `GET /api/review/modules/{id}` (Antworten+KI-Vorschläge+KI-/Backend-Validierungen+Herkunft), `PATCH /api/review/answers/{id}` (Reviewer-Edit), `POST …/approve`, `POST …/request-changes`.
- [x] Canonical-Output-Service: `ModuleInstance` → `CanonicalOutput` nach `output_schema_key` (FR-INT-001).
- [x] `TargetAdapter`-ABC + `DpmsAdapter`: Mapping canonical→DPMS-JSON (FR-INT-003), `preview()` (gemappt/ungemappt/Warnungen/Fehler FR-INT-004), `run_import()` simuliert.
- [x] `POST /api/modules/{id}/canonical`, `POST /api/modules/{id}/import-preview`, `POST /api/import-jobs`, `POST /api/import-jobs/{id}/run`; `ImportJob`-Statemachine (Architektur §5.3, FR-INT-005/006).
- [x] Freigabe-Gate: Import erst nach Review-`approved` (FR-REV-003).
- [x] Tests: Review-Übergänge, Gate, Canonical-Schema, DPMS-Mapping + Preview (gemappt/ungemappt), Importstatus-Maschine.

**Schnittstellenvertrag → Phase 6:** Review- & Import-Endpunkte + DTOs für Review-Screen.
**DoD:** `pytest` grün; Smoke: Modul complete→Review approve→Canonical→Importvorschau→ImportJob run→`imported`. Deckt FR-REV, FR-INT, §8.9/§8.10.

---

## Phase 5 — Frontend-Fundament & Dashboard

**Ziel:** Lauffähige React-App, Auth, Dashboard mit Modulkarten + Dashboard-KI-Chat.
**Voraussetzungen:** P2–P4 (APIs).

**Status:** ✅ abgeschlossen (`feat/phase-5-frontend-dashboard`).

**Arbeitspakete:**
- [x] Vite + React + TS Gerüst, `tokens.css` aus Design-System übernommen, globale Styles, Fonts (`@fontsource`).
- [x] API-Client (typisiert, inkl. Phase-6-Endpunkte) + Auth (Login, Token in memory + localStorage, Rollen-Routing), Lade-/Fehler-/Leerzustände.
- [x] Routing: `/login`, `/` (Dashboard/Prozesswahl), `/processes/:id`, Platzhalter `/modules/:id`, `/steps/:id`, `/review`(+`:id`); `ProtectedRoute`.
- [x] Dashboard (FR-DASH, §9.1/9.2): Begrüßung, Gesamtfortschritt, Modulkarten (Name, Explainer, Status-Pill, Progressbalken, Zuständigkeit, Aufwand, Schloss + Freischalthinweis, CTA), gesperrt ausgegraut/deaktiviert.
- [x] Dashboard-KI-Chat (FR-DASH-004) gegen `/api/ai/chat` (context=dashboard).
- [x] Design-System verbindlich: nur Tokens, keine Hex/px-Literale, AA-Kontrast, dunkle Tinte auf Grün.
- [x] Im Browser verifiziert (agent-browser): Login (Kunde/Reviewer), Bootstrap, Dashboard mit 1 freiem + 2 gesperrten Modulen, Chat-Antwort.
- [x] Tests (Vitest + RTL): StatusPill-Mapping, ProgressBar, Dashboard-Render/Locked/CTA-Nav, Auth/ProtectedRoute, API-Error-Mapping (27 Tests grün).

**Schnittstellenvertrag → Phase 6:** API-Client (`src/api/`, alle Endpunkte typisiert), Auth-Context (`useAuth`), `ProtectedRoute`, UI-Grundkomponenten (`Button`, `Card`, `StatusPill`, `ProgressBar`, `Spinner`, `EmptyState`, `ErrorBanner`, `ChatPanel`, `AppShell`) wiederverwendbar.
**DoD:** ✅ App startet, Login funktioniert, Dashboard zeigt Seed-Module korrekt; Browser-Smoke grün. Deckt §9.1/9.2, FR-DASH.

---

## Phase 6 — Frontend Modul-Flow & Review

**Ziel:** Vollständige Bearbeitung + Review im Browser.
**Voraussetzungen:** P5.

**Status:** ✅ abgeschlossen (`feat/phase-6-frontend-module-review`).

**Arbeitspakete:**
- [x] Modul-Start (§9.3): Intro (Ziel/Warum/Wer/Aufwand/Explainer), Status-Pill, Progressbalken, Step-Liste (abgehakt), Vorlagen, Start/Fortsetzen, Modul-KI (`ModulePage`).
- [x] Modul-Bearbeitung (§9.4): Step-Navigation (abgehakt), Progressbalken, dynamische Felder für **single_select/multi_select/text/file_upload** (`QuestionField`), Sichtbarkeitslogik (Re-Fetch nach Speichern), Validierungshinweise inline, Speichern/Abschließen (409-Hinweis), `StepPage`.
- [x] KI-Hilfe je Frage (`/ai/suggest`, `/ai/chat` context=question) + Step-/Modul-Hilfe; Vorschläge übernehmbar (Herkunfts-Badge); Prüf-KI (`/ai/validate`).
- [x] Vorlagen im Step/Modul (§9.5): E-Mail anzeigen/kopieren, Fragebogen-Download (authentifiziert via Blob), Begleittext (`TemplateList`).
- [x] Upload-Komponente (Dropzone, Typ/Größe clientseitig, 415/413) gegen `/api/uploads`.
- [x] Review-Screen (§9.6, reviewer/admin): Antworten + Herkunft, KI-Vorschläge, KI-/Backend-Validierungen, Editieren (`PATCH`), Freigabe/Rückgabe, DPMS-Importvorschau + Import (`ReviewListPage`, `ReviewDetailPage`, `ImportPanel`).
- [x] Browser-Verifikation (agent-browser): kompletter Kundenfluss (4 Antworttypen, Upload, Sichtbarkeit, KI-Vorschlag, Vorlagen, Modulabschluss → Folge-Module freigeschaltet) + Reviewer-Fluss (Antwort editieren → Freigabe → Importvorschau → Import `imported`).
- [x] Tests (Vitest + RTL): Fragefeld-Rendering je Typ, multi/single-Werte, Inline-Validierung, complete-409, KI-Vorschlag-Übernahme + Badge, Vorlage Kopieren/Download, Review-Render/Patch/Approve/Request-Changes, Importvorschau + Import-Flow (47 Tests grün, P5 inklusive).

**Schnittstellenvertrag → Abschluss:** vollständige UI gegen alle Akzeptanzkriterien.
**DoD:** ✅ End-to-End im Browser grün; alle 4 Antworttypen, KI-Hilfe, Vorlagen, Upload, Review, Importvorschau funktionieren. Deckt §9.3–9.6, FR-Q-002…006, FR-TPL-004, FR-REV, FR-INT-004.

---

## Anhang — Kriterien-Abdeckung je Phase

| Anforderung | Phase |
|-------------|-------|
| FR-MOD-001…006 (Module, Reihenfolge, Sperre, parallel, Zuständigkeit) | P1 (Modell/Seed) · P2 (Engine) · P5 (UI) |
| FR-STEP-001…004 (Steps, Status, Abhaken, Progress) | P1 · P2 · P6 |
| FR-Q-001…007 (Fragen, 4 Antworttypen, Sichtbarkeit) | P1 · P2 · P6 |
| FR-DASH-001…004 (Dashboard, Status, Zuständigkeit, KI-Chat) | P2 · P5 |
| FR-AI-001…007 (KI-Kontexte, Wissenskonfig, struktur. Output, sem. Prüfung) | P3 · P6 |
| FR-VAL-001…003 (Backend-Validierung) | P2 |
| FR-TPL-001…005 (Vorlagen) | P1/P2 · P6 |
| FR-DOC-001…004 (Upload, Speicherung, Dok-Analyse, Herkunft) | P2 · P3 · P6 |
| FR-REV-001…003 (Review, Verlauf, Importfreigabe) | P4 · P6 |
| FR-INT-001…006 (Canonical, Adapter, DPMS-Mapping, Importvorschau/-status) | P4 · P6 |
| NFR Erweiterbarkeit/Sicherheit/Nachvollziehbarkeit/Usability | alle (Seeds, Auth, Audit-Felder, Design-System) |
