# Annahmen (MVP)

Lücken aus dem Anforderungsdokument (insb. §17.1 „Offene fachliche Fragen") werden hier mit begründeten Annahmen geschlossen. Änderungen an diesen Annahmen sind hier zu pflegen.

| # | Offene Frage | Annahme für MVP | Begründung |
|---|--------------|-----------------|------------|
| A1 | Pilotmodul | **`software_inventory`** (Software-Erfassung) ist Leitmodul. Zusätzlich geseedet: `tom_erfassung`, `avv_onboarding`. | Beweist Modularität (mehrere Module, eigene Wissenskonfig) statt VVT-Einzelfall. |
| A2 | Modulanzahl im MVP | 3 Module in einem Prozess `datenschutz_basis_onboarding`. | Genug, um Reihenfolge, Sperre, parallele Freischaltung & Zuständigkeit zu zeigen. |
| A3 | Freischaltlogik | `software_inventory` sofort verfügbar; nach dessen Abschluss werden `tom_erfassung` **und** `avv_onboarding` **parallel** freigeschaltet. | Deckt FR-MOD-003/004/005 (linear, gesperrt, parallel) ab. |
| A4 | DPMS-Import | Nur **Mapping + Importvorschau + simulierter Import** (kein echter API-Call). DPMS-Adapter erzeugt DPMS-kompatibles JSON. | §7.2 / §16: kein echter bidirektionaler Sync im MVP. Adapter-Seam bleibt austauschbar. |
| A5 | Rollen | Drei Rollen: `customer`, `reviewer` (Zweiplus-Fachbearbeiter), `admin`. Geseedete Demo-User mit Bearer-Token-Login. | §14.2 verlangt Auth + rollenbasierte Zugriffe; umfangreiche Rechteverwaltung ist explizit out of scope (§7.2). |
| A6 | Dateitypen | `pdf`, `docx`, `xlsx`, `png`, `jpg`, `jpeg`. Max. **10 MB**/Datei. | Deckt §8.3 FR-Q-006 Beispiele ab; deterministische Grenze für Validierung. |
| A7 | KI-Anbindung | KI über **LangChain** gegen eine **OpenAI-kompatible** Chat-Completions-Schnittstelle (`langchain-openai` `ChatOpenAI` mit konfigurierbarem `base_url`). Funktioniert mit OpenAI **und lokalen Modellen** (Ollama/LM Studio/vLLM). Konfiguration per ENV (`AI_BASE_URL`, `AI_API_KEY`, `AI_MODEL`). Für Tests ein **deterministischer Stub-LLM** (offline, kein Server). | §14.2: datenschutzkonforme, self-hostbare, herstellerneutrale KI; reproduzierbare Tests ohne Modellserver; keine Secrets im Repo. |
| A8 | Wissensbasis | Wissens-Snippets als geseedete `KnowledgeEntry`-Einträge (key→Text). Moduldefinition referenziert Keys. | §11: modulbezogenes Wissen ohne Codeänderung pflegbar; einfacher Store statt RAG für MVP. |
| A9 | Pflege der Definitionen | Moduldefinitionen als **versionierte JSON-Seeds** (`backend/seeds/`), beim Start in die DB geladen. Admin-CRUD-UI ist out of scope. | §14.6 Wartbarkeit ohne Codeänderung; Admin-UI nicht MVP-kritisch. |
| A10 | Review-Tiefe | Reviewer kann Antworten sehen/editieren, KI-Vorschläge & Validierungen einsehen, Modul freigeben oder zur Korrektur zurückgeben. | §8.9 Minimalumfang. |
| A11 | Asynchronität | KI-/Import-Operationen laufen synchron als Request, sind aber hinter Service-Interfaces gekapselt (später async). | §14.5: MVP-pragmatisch, Seam erhalten. |
| A12 | Persistenz Dateien | Lokaler Storage-Ordner (`backend/storage/`), Pfad in `FileUpload`. Storage hinter Interface (später S3). | §8.8 FR-DOC-002 sichere, verknüpfte Ablage; austauschbarer Seam. |
| A13 | DB | PostgreSQL (Docker Compose) für Laufzeit; **SQLite** für Tests via `DATABASE_URL`. SQLAlchemy + Alembic. | Reproduzierbare, deterministische Tests; produktionsnahe Laufzeit. |

## Demo-Zugänge (Seed)

| Rolle | E-Mail | Passwort |
|-------|--------|----------|
| Kunde | `kunde@demo.test` | `demo1234` |
| Reviewer (Zweiplus) | `review@zweiplus.test` | `demo1234` |
| Admin | `admin@zweiplus.test` | `demo1234` |

> Demo-Passwörter sind nur für die lokale Entwicklung; sie sind als Seed dokumentiert, keine echten Secrets.
