import { useCallback, useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  approveModule,
  ApiError,
  getReviewModule,
  patchReviewAnswer,
  requestModuleChanges,
} from "../api";
import type { ReviewView } from "../api";
import { Button } from "../components/Button";
import { Card } from "../components/Card";
import { Spinner } from "../components/Spinner";
import { ErrorBanner } from "../components/ErrorBanner";
import { StatusPill } from "../components/StatusPill";
import { moduleStatusMeta } from "../components/statusMeta";
import { ImportPanel } from "./ImportPanel";
import "./ModuleFlow.css";

function formatValue(value: unknown): string {
  if (value == null || value === "") return "—";
  if (Array.isArray(value)) return value.join(", ");
  return String(value);
}

const SOURCE_LABEL: Record<string, string> = {
  user: "Kunde",
  ai: "KI",
  document: "Dokument",
  manual: "Reviewer",
};

const IMPORTABLE = new Set(["completed", "import_ready", "imported"]);

/**
 * Module review detail (§9.6): per-step answers with provenance, AI suggestions,
 * AI + backend validation; reviewer can edit answers, approve or request changes.
 * Once the module is approved, the DPMS import preview + import flow is shown.
 */
export function ReviewDetailPage() {
  const { moduleInstanceId } = useParams<{ moduleInstanceId: string }>();
  const navigate = useNavigate();

  const [view, setView] = useState<ReviewView | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<"approve" | "changes" | null>(null);
  const [message, setMessage] = useState<{ text: string; kind: "ok" | "error" } | null>(null);
  const [notes, setNotes] = useState("");

  const load = useCallback(async () => {
    if (!moduleInstanceId) return;
    setError(null);
    try {
      setView(await getReviewModule(moduleInstanceId));
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Review konnte nicht geladen werden.");
    }
  }, [moduleInstanceId]);

  useEffect(() => {
    setView(null);
    void load();
  }, [load]);

  async function approve() {
    if (!moduleInstanceId) return;
    setBusy("approve");
    setMessage(null);
    try {
      await approveModule(moduleInstanceId);
      setMessage({ text: "Modul freigegeben. Sie können jetzt den Import vorbereiten.", kind: "ok" });
      await load();
    } catch (err) {
      setMessage({
        text: err instanceof ApiError ? err.detail : "Freigabe fehlgeschlagen.",
        kind: "error",
      });
    } finally {
      setBusy(null);
    }
  }

  async function requestChanges() {
    if (!moduleInstanceId) return;
    setBusy("changes");
    setMessage(null);
    try {
      await requestModuleChanges(moduleInstanceId, notes || undefined);
      setMessage({ text: "Zur Korrektur an den Kunden zurückgegeben.", kind: "ok" });
      await load();
    } catch (err) {
      setMessage({
        text: err instanceof ApiError ? err.detail : "Aktion fehlgeschlagen.",
        kind: "error",
      });
    } finally {
      setBusy(null);
    }
  }

  if (error) return <ErrorBanner message={error} />;
  if (!view) return <Spinner center />;

  const meta = moduleStatusMeta(view.moduleStatus);
  const canApprove = view.moduleStatus === "waiting_zweiplus";
  const canImport = IMPORTABLE.has(view.moduleStatus);

  return (
    <div className="reveal">
      <button type="button" className="flow-back" onClick={() => navigate("/review")}>
        <span aria-hidden="true">←</span> Zurück zu den Aufgaben
      </button>

      <header className="flow-head">
        <div className="flow-head__top">
          <div>
            <span className="eyebrow">Review · {view.customerName ?? ""}</span>
            <h1 className="flow-title">{view.moduleName}</h1>
          </div>
          <StatusPill variant={meta.variant} label={meta.label} />
        </div>
      </header>

      {message && (
        <p
          className={message.kind === "ok" ? "flow-toast" : "field-hint field-hint--error"}
          role={message.kind === "error" ? "alert" : "status"}
        >
          {message.kind === "ok" ? "✓ " : "⚠ "}
          {message.text}
        </p>
      )}

      <div className="stack">
        {view.steps.map((s) => (
          <Card key={s.stepInstanceId}>
            <h2 className="flow-section__title">{s.title}</h2>

            {s.questions.map((q) => (
              <ReviewQuestionRow key={q.key} question={q} onPatched={load} />
            ))}

            {(s.aiValidation || s.backendValidation) && (
              <div className="import-block">
                {s.backendValidation && (
                  <p className="field-hint field-hint--ok" style={{ marginTop: 0 }}>
                    <span aria-hidden="true">{s.backendValidation.passed ? "✓" : "✗"}</span>{" "}
                    Backend-Validierung: {s.backendValidation.passed ? "bestanden" : "fehlgeschlagen"}
                  </p>
                )}
                {s.aiValidation && (
                  <ul className="check-list">
                    {s.aiValidation.checks.map((c, i) => (
                      <li className="check-list__item" key={i}>
                        <span
                          className={c.ok ? "check-list__icon--ok" : "check-list__icon--fail"}
                          aria-hidden="true"
                        >
                          {c.ok ? "✓" : "✗"}
                        </span>
                        <span>
                          <strong>{c.question}</strong>
                          {c.note ? ` – ${c.note}` : ""}
                        </span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            )}
          </Card>
        ))}
      </div>

      <Card className="import-block">
        <h2 className="flow-section__title">Entscheidung</h2>
        <div className="field">
          <label className="field__label" htmlFor="review-notes">
            Hinweis bei Rückgabe (optional)
          </label>
          <textarea
            id="review-notes"
            className="textarea"
            rows={2}
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Was soll der Kunde korrigieren?"
          />
        </div>
        <div className="step-actions">
          <Button onClick={approve} disabled={busy !== null || !canApprove}>
            {busy === "approve" ? "Gibt frei…" : "Freigeben"}
          </Button>
          <Button variant="secondary" onClick={requestChanges} disabled={busy !== null}>
            {busy === "changes" ? "Sendet…" : "Zur Korrektur zurückgeben"}
          </Button>
          {!canApprove && !canImport && (
            <span className="ai-help__hint">
              Freigabe nur möglich, solange das Modul auf Zweiplus wartet.
            </span>
          )}
        </div>
      </Card>

      {canImport && moduleInstanceId && (
        <ImportPanel moduleInstanceId={moduleInstanceId} initialStatus={view.moduleStatus} />
      )}
    </div>
  );
}

// --- single review question row -------------------------------------------

function ReviewQuestionRow({
  question,
  onPatched,
}: {
  question: ReviewView["steps"][number]["questions"][number];
  onPatched: () => Promise<void> | void;
}) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const answer = question.answer;
  const sourceLabel = answer?.source ? SOURCE_LABEL[answer.source] ?? answer.source : null;

  function startEdit() {
    setError(null);
    setDraft(
      Array.isArray(answer?.value) ? (answer!.value as string[]).join(", ") : formatValue(answer?.value) === "—" ? "" : String(answer?.value ?? ""),
    );
    setEditing(true);
  }

  async function save() {
    if (!answer) return;
    setBusy(true);
    setError(null);
    try {
      // Keep arrays as arrays when the original answer was multi-valued.
      const value = Array.isArray(answer.value)
        ? draft.split(",").map((s) => s.trim()).filter(Boolean)
        : draft;
      await patchReviewAnswer(answer.id, value);
      setEditing(false);
      await onPatched();
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Speichern fehlgeschlagen.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="review-q">
      <p className="review-q__label">{question.label}</p>
      <div className="review-answer">
        {editing ? (
          <input
            className="input review-answer__value"
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            aria-label={`Antwort bearbeiten: ${question.label}`}
          />
        ) : (
          <span className="review-answer__value">{formatValue(answer?.value)}</span>
        )}

        {sourceLabel && (
          <span className="origin-badge">
            {answer?.aiSuggested ? "✦ " : ""}
            {sourceLabel}
          </span>
        )}

        {answer &&
          (editing ? (
            <>
              <Button size="sm" onClick={save} disabled={busy}>
                {busy ? "Speichert…" : "Speichern"}
              </Button>
              <Button size="sm" variant="ghost" onClick={() => setEditing(false)} disabled={busy}>
                Abbrechen
              </Button>
            </>
          ) : (
            <Button size="sm" variant="ghost" onClick={startEdit}>
              Bearbeiten
            </Button>
          ))}
      </div>

      {question.aiSuggestions.length > 0 && (
        <div className="ai-suggestion">
          <span className="ai-suggestion__meta">KI-Vorschläge</span>
          {question.aiSuggestions.map((s) => (
            <p className="ai-suggestion__value" key={s.id}>
              {Array.isArray(s.proposedValue)
                ? (s.proposedValue as string[]).join(", ")
                : String(s.proposedValue ?? "—")}
              {typeof s.confidence === "number" && (
                <span className="ai-suggestion__meta">
                  {" "}
                  · Konfidenz {Math.round(s.confidence * 100)}%
                </span>
              )}
            </p>
          ))}
        </div>
      )}

      {error && (
        <p className="field-hint field-hint--error" role="alert">
          <span aria-hidden="true">⚠</span> {error}
        </p>
      )}
    </div>
  );
}
