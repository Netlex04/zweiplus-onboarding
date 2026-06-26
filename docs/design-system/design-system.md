# Zweiplus Context — Design System

> **Verbindliche Referenz für alle Frontend-Arbeiten.** Vor jedem neuen Component und jeder UI-Änderung ist dieses Dokument zu konsultieren. Tokens werden referenziert, nicht dupliziert.

**Dateien**
- [`tokens.css`](tokens.css) — kanonische Design-Tokens (Single Source of Truth, Light + Dark).
- [`styleguide.html`](styleguide.html) — lebende Vorschau aller Bausteine (im Browser öffnen).
- `design-system.md` — dieses Dokument (Prinzipien, Nutzung, Do/Don't).

---

## 1. Designhaltung: „Calm Compliance"

Zweiplus ist Datenschutz- und Sicherheitsberatung. Das Produkt muss **Vertrauen, Klarheit und Kontrolle** ausstrahlen. Die Gestaltung ist auf der zweiplus Corporate Identity aufgebaut und bewusst **modernisiert** — nicht neu erfunden.

**Drei Leitlinien:**

1. **Grün ist ein Signal, kein Dekor.** Das zweiplus-Grün (`#6ec829`) markiert Aktion, Erfolg und Fokus — nicht ganze Flächen. Sparsamer Einsatz erhöht seine Wirkung.
2. **Ruhe durch Raum.** Großzügiger Weißraum, klare Hierarchie, dezente grün-getönte Tiefe statt flacher Bootstrap-Flächen.
3. **Serife für Menschliches, Grotesk für Funktion.** Playfair Display für editoriale Momente; eine moderne Grotesk für das dichte Produkt-UI.

---

## 2. Verhältnis zur zweiplus CI

| CI-Element (zwei.plus) | Im Design System | Begründung |
|------------------------|------------------|------------|
| Signalgrün `#6ec829`, `#84d049`, `#58a021` | **Beibehalten** als Primary/Signal inkl. abgeleiteter Skala | Kern-Wiedererkennung der Marke |
| Amber `#fed136` | **Beibehalten** als sparsamer Sekundärakzent / Warning | CI-Treue |
| Playfair Display (Headlines) | **Beibehalten** für Display/Headings | Distinktive, on-brand Serife |
| Montserrat (Body) | **Modernisiert** → Hanken Grotesk (Montserrat bleibt Fallback) | Frischer, besser im dichten UI; CI-Lineage über Fallback erhalten |
| Weiß / `#f8f9fa`, dunkler Text `#212529` | **Modernisiert** zu grün-getönten Neutrals | Kohärenz aus einem Guss |
| Bootstrap-Defaults (eckig, harte Schatten) | **Ersetzt** durch weiche Radien & grün-getönte Elevation | „deutlich moderner" |

> Wenn eine neue Designentscheidung von der CI abweichen würde: zuerst hier prüfen, dann begründen. Die CI-Treue (Grün + Playfair) ist nicht verhandelbar.

---

## 3. Farben

Immer **semantische Tokens** verwenden (`--color-*`), nie Primitive (`--zp-*`) oder Hex-Werte direkt im Component.

| Token | Verwendung |
|-------|-----------|
| `--color-primary` | Primäraktionen, aktive Zustände, Fokus-Signal |
| `--color-primary-strong` | Grüner Text/Links auf hellem Grund (AA-konform) |
| `--color-primary-subtle` | Getönte Hintergründe, Hover-Flächen |
| `--color-on-primary` | Dunkle Tinte (`#11210a`) auf grünen Flächen — **nie weißer Text auf Grün** |
| `--color-accent` | Amber, sparsam (Highlights, Hinweise) |
| `--color-text` / `-secondary` / `-muted` | Text-Hierarchie |
| `--color-bg` / `--color-surface` / `--color-surface-sunken` | Flächen-Ebenen |
| `--color-border` / `-strong` | Linien, Eingabefelder |
| `--color-success/-warning/-danger/-info` (+ `-subtle`) | Statuszustände |

**Kontrast:** `#6ec829` hat auf Weiß **keinen** ausreichenden Textkontrast. Daher: grüne Flächen mit dunkler Tinte (`--color-on-primary`), grüner Text nur über `--color-primary-strong`.

---

## 4. Typografie

| Rolle | Font | Token | Einsatz |
|-------|------|-------|---------|
| Display | Playfair Display 700/800 | `--font-display` | Login-Titel, Dashboard-Begrüßung, Section-Headlines, Leerzustände |
| UI / Body | Hanken Grotesk 400–700 | `--font-sans` | Alle Bedienelemente, Fließtext, Tabellen, Formulare |
| Mono | IBM Plex Mono | `--font-mono` | Ingestion-IDs, Dateinamen, Quellen, technische Werte |

Größen über `--text-xs … --text-display`. Display-Text mit `--tracking-tight`; Eyebrow-Labels uppercase mit `--tracking-label`. Playfair **nicht** für dichte Fließtexte oder kleine UI-Labels verwenden.

---

## 5. Bausteine (Tokens beachten)

- **Buttons** — voll gerundet (`--radius-full`). Primär = grüne Fläche + dunkle Tinte + `--shadow-brand`. Sekundär = Outline. Ghost = transparent. Pro Ansicht **eine** Primäraktion.
- **Status-Pills** — direkt aus den API-Enums (`DocumentStatus`, `IngestionStatus`): success→grün, processing→info-blau, pending→neutral, failed→danger, unsicher→warning-amber.
- **Karten** — `--color-surface`, `--radius-lg`, `--shadow-sm`; interaktiv: Hover hebt an (`translateY(-3px)`) + grüne Border.
- **Formulare** — `--radius-md`, Fokus = grüner Ring (`--ring`) + grüne Border.
- **Upload-Dropzone** — gestrichelte Border, Hover färbt grün (`--color-primary-subtle`).
- **Chat** — User-Bubble grün (dunkle Tinte), AI-Bubble Surface mit Border; Quellen als Mono-Chips unter der Antwort.
- **Tabellen** — Mono für IDs, Zeilen-Hover grün getönt, Uppercase-Header.

Konkrete, abgestimmte Implementierungen siehe [`styleguide.html`](styleguide.html).

---

## 6. Maße, Tiefe, Bewegung

- **Spacing**: 4px-Basis (`--space-1 … --space-9`). Keine willkürlichen px-Werte.
- **Radien**: `--radius-xs … --radius-2xl`, `--radius-full`. Modern weich, aber nicht verspielt.
- **Elevation**: `--shadow-xs … --shadow-lg`; `--shadow-brand` als grüner Glow nur für primäre CTAs.
- **Motion**: `--dur-fast/-/-slow` mit `--ease-out`/`--ease-spring`. Ein gut orchestrierter Page-Load (gestaffelte Reveals) schlägt verstreute Mikro-Animationen. `prefers-reduced-motion` wird in den Tokens respektiert.
- **Atmosphäre**: `--gradient-mesh` (dezentes grün/amber Mesh) statt reinem Weiß; optional feine Grain-Textur.

---

## 7. Theming & Barrierefreiheit

- **Light = Default** (CI-konform). `data-theme="dark"` auf `<html>` aktiviert den Dark-Mode — alle Tokens schalten automatisch um.
- Ziel **WCAG AA**: Text ≥ 4.5:1, große Headlines/UI ≥ 3:1. Grüne Flächen tragen dunkle Tinte.
- Fokus immer sichtbar über `--ring` (grünes Signal). Interaktive Elemente brauchen `:focus-visible`.
- Status nie nur über Farbe kommunizieren — immer mit Label/Icon (siehe Pills).

---

## 8. Do / Don't

**Do**
- Tokens aus `tokens.css` referenzieren; neue Werte dort ergänzen, nicht im Component.
- Grün als Signal dosieren; Playfair für Headlines, Grotesk fürs UI.
- Dunkle Tinte auf grünen Flächen.

**Don't**
- Keine Hex-/px-Literale in Components.
- Kein weißer Text auf `#6ec829`.
- Playfair nicht für Fließtext/kleine Labels.
- Keine Bootstrap-Defaults (eckige Ecken, harte graue Schatten, `#007bff`-Blau).
- Lila/Generic-AI-Gradients haben hier nichts verloren.

---

## 9. Nutzung im Code (ab Phase 1)

```css
/* index.css / global */
@import "./design-system/tokens.css"; /* oder Pfad im frontend-Projekt */
```

```tsx
// Beispiel: Button referenziert ausschließlich Tokens
const Button = styled.button`
  background: var(--color-primary);
  color: var(--color-on-primary);
  border-radius: var(--radius-full);
  padding: var(--space-3) var(--space-5);
  box-shadow: var(--shadow-brand);
  font-family: var(--font-sans);
  font-weight: var(--weight-semibold);
`;
```

Beim Aufbau des React-Frontends wird `tokens.css` in das Projekt übernommen (z. B. `frontend/src/styles/tokens.css`) und bleibt die einzige Quelle für Designwerte.
