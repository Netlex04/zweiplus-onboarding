# Zweiplus Onboarding — Frontend

React + Vite + TypeScript Frontend der Onboarding-Plattform. Phase 5 liefert das
Fundament (App-Shell, Auth/Routing, typisierter API-Client, Kunden-Dashboard mit
Modulkarten und Dashboard-KI-Chat). Phase 6 ergänzt den vollständigen
Modul-Flow: Modul-Start, Step-Bearbeitung mit dynamischen Antworttypen
(single/multi-select, Text, Datei-Upload), Sichtbarkeitslogik, Inline-Validierung,
KI-Hilfe je Frage (Erklären/Vorschlag/Prüf-KI), Vorlagen (E-Mail kopieren,
Datei-Download) sowie den Reviewer-Screen mit Freigabe/Korrektur und
DPMS-Importvorschau + Import.

## Voraussetzungen

- Node 20+ (entwickelt mit Node 22)
- Laufendes Backend auf `http://localhost:8000` (siehe `../backend/README.md`).
  CORS erlaubt `http://localhost:5173` standardmäßig.

## Schnellstart

```bash
npm install
cp .env.example .env        # optional; Default reicht für lokal
VITE_API_URL=http://localhost:8000 npm run dev
# App: http://localhost:5173
```

Login mit den Demo-Zugängen (Passwort `demo1234`):
`kunde@demo.test` (Kunde), `review@zweiplus.test` (Reviewer), `admin@zweiplus.test` (Admin).

Als Kunde: „Onboarding starten“ legt den Prozess
`datenschutz_basis_onboarding` an und öffnet das Dashboard. Als Reviewer/Admin:
Prozessliste → Klick öffnet das jeweilige Dashboard.

## Befehle

| Befehl | Zweck |
|--------|-------|
| `npm run dev` | Dev-Server (HMR) auf Port 5173 |
| `npm run build` | Typecheck + Produktionsbuild nach `dist/` |
| `npm run preview` | Produktionsbuild lokal servieren |
| `npm test` | Vitest (einmalig) |
| `npm run test:watch` | Vitest im Watch-Modus |
| `npm run typecheck` | TypeScript-Typecheck |
| `npm run lint` | oxlint |

## Konfiguration

| Variable | Default | Zweck |
|----------|---------|-------|
| `VITE_API_URL` | `http://localhost:8000` | Basis-URL der Backend-API |

`.env` wird nicht eingecheckt (siehe `.env.example`).

## Design-System (verbindlich)

`src/styles/tokens.css` ist die Kopie von `docs/design-system/tokens.css` und die
**einzige** Quelle für Designwerte. Components referenzieren ausschließlich
semantische Tokens (`--color-*`, `--space-*`, `--radius-*`, `--text-*`, `--shadow-*`)
— keine Hex-/px-Literale. Grün ist Signal, dunkle Tinte auf Grün
(`--color-on-primary`), Playfair nur für Headlines, Status immer mit Label + Icon.
Fonts sind via `@fontsource` selbst gehostet (Playfair Display, Hanken Grotesk,
IBM Plex Mono).

## Struktur

```
src/
  api/         http.ts (fetch + Bearer + {error,detail}-Mapping), client.ts (Endpunkte),
               types.ts (DTOs camelCase), index.ts (Barrel)
  auth/        AuthContext.tsx, ProtectedRoute.tsx
  components/  Button, Card, StatusPill, ProgressBar, Spinner, EmptyState,
               ErrorBanner, ChatPanel, AppShell, statusMeta.ts (+ ui.css)
  pages/       LoginPage, HomePage (Kunde-Bootstrap / Staff-Liste),
               DashboardView, ModuleCardView, ProcessDashboardPage,
               ModulePage (Modul-Start), StepPage (Step-Bearbeitung),
               QuestionField (dynamische Antworttypen + KI-Hilfe je Frage),
               TemplateList (Vorlagen), ReviewListPage, ReviewDetailPage,
               ImportPanel (DPMS-Vorschau + Import) (+ ModuleFlow.css)
  styles/      tokens.css, global.css
  test/        setup.ts (Vitest + RTL)
```

## Routen

- `/login` — öffentlich
- `/` — Dashboard (Kunde) bzw. Prozessliste (Reviewer/Admin)
- `/processes/:processInstanceId` — Dashboard eines Prozesses (Staff)
- `/modules/:moduleInstanceId` — Modul-Start (Intro, Status, Fortschritt, Step-Liste, Vorlagen, KI-Hilfe)
- `/steps/:stepInstanceId` — Step-Bearbeitung (dynamische Fragefelder, Validierung, KI-Hilfe, Vorlagen)
- `/review` — Review-Aufgabenliste, nur Reviewer/Admin
- `/review/:moduleInstanceId` — Modul-Review (Antworten + Herkunft + Validierungen, Freigabe/Korrektur, DPMS-Import)

Alle außer `/login` sind über `ProtectedRoute` geschützt; nicht angemeldete
Nutzer werden nach `/login` umgeleitet.
