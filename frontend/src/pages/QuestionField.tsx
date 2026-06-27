import { useRef, useState } from "react";
import {
  aiChat,
  aiSuggest,
  ApiError,
  downloadUpload,
  uploadFile,
} from "../api";
import type {
  AiSuggestion,
  BackendValidationError,
  BackendValidationWarning,
  Question,
} from "../api";
import { Button } from "../components/Button";
import { Spinner } from "../components/Spinner";

const ACCEPT = ".pdf,.docx,.xlsx,.png,.jpg,.jpeg";
const ALLOWED_EXT = ["pdf", "docx", "xlsx", "png", "jpg", "jpeg"];
const MAX_BYTES = 10 * 1024 * 1024;

interface QuestionFieldProps {
  question: Question;
  stepInstanceId: string;
  value: unknown;
  /** Display name of an uploaded file, if known (for file_upload). */
  fileName?: string;
  /** Whether the current (possibly unsaved) value came from an AI suggestion. */
  aiSuggested?: boolean;
  errors: BackendValidationError[];
  warnings: BackendValidationWarning[];
  onChange: (value: unknown, meta?: { fileName?: string; aiSuggested?: boolean }) => void;
}

/**
 * Renders one dynamic question field by type (§9.4, FR-Q-002…007) plus its
 * inline backend validation hints and the per-question AI help (§10.5):
 * explain (chat) + suggest ("Übernehmen" writes the value with an origin badge).
 */
export function QuestionField({
  question,
  stepInstanceId,
  value,
  fileName,
  aiSuggested,
  errors,
  warnings,
  onChange,
}: QuestionFieldProps) {
  const showAiBadge = aiSuggested ?? question.answer?.aiSuggested ?? false;
  return (
    <div className="question">
      <div className="question__head">
        <div>
          <p className="question__label">
            {question.label}
            {question.required && (
              <span className="question__req" aria-hidden="true">
                *
              </span>
            )}
          </p>
          {question.description && <p className="question__desc">{question.description}</p>}
        </div>
        {showAiBadge && (
          <span className="origin-badge">
            <span aria-hidden="true">✦</span> KI-Vorschlag
          </span>
        )}
      </div>

      <FieldControl
        question={question}
        stepInstanceId={stepInstanceId}
        value={value}
        fileName={fileName}
        onChange={onChange}
      />

      {errors.map((e, i) => (
        <p className="field-hint field-hint--error" role="alert" key={`e${i}`}>
          <span aria-hidden="true">⚠</span> {e.message}
        </p>
      ))}
      {warnings.map((w, i) => (
        <p className="field-hint field-hint--warning" key={`w${i}`}>
          <span aria-hidden="true">!</span> {w.message}
        </p>
      ))}

      {question.aiHelpEnabled && (
        <AiHelp question={question} stepInstanceId={stepInstanceId} onAccept={onChange} />
      )}
    </div>
  );
}

// --- type-specific controls ------------------------------------------------

function FieldControl({
  question,
  stepInstanceId,
  value,
  fileName,
  onChange,
}: Pick<QuestionFieldProps, "question" | "stepInstanceId" | "value" | "fileName" | "onChange">) {
  switch (question.type) {
    case "single_select":
      return (
        <div className="option-list" role="radiogroup" aria-label={question.label}>
          {(question.options ?? []).map((opt) => (
            <label className="option" key={opt}>
              <input
                type="radio"
                name={question.key}
                value={opt}
                checked={value === opt}
                onChange={() => onChange(opt)}
              />
              <span className="option__text">{opt}</span>
            </label>
          ))}
        </div>
      );

    case "multi_select": {
      const selected = Array.isArray(value) ? (value as string[]) : [];
      return (
        <div className="option-list" role="group" aria-label={question.label}>
          {(question.options ?? []).map((opt) => (
            <label className="option" key={opt}>
              <input
                type="checkbox"
                value={opt}
                checked={selected.includes(opt)}
                onChange={(e) =>
                  onChange(
                    e.target.checked
                      ? [...selected, opt]
                      : selected.filter((v) => v !== opt),
                  )
                }
              />
              <span className="option__text">{opt}</span>
            </label>
          ))}
        </div>
      );
    }

    case "text":
      return (
        <textarea
          className="textarea"
          rows={4}
          aria-label={question.label}
          value={typeof value === "string" ? value : ""}
          onChange={(e) => onChange(e.target.value)}
        />
      );

    case "file_upload":
      return (
        <FileField
          question={question}
          stepInstanceId={stepInstanceId}
          uploadId={typeof value === "string" ? value : undefined}
          fileName={fileName}
          onChange={onChange}
        />
      );

    default:
      return null;
  }
}

function FileField({
  question,
  stepInstanceId,
  uploadId,
  fileName,
  onChange,
}: {
  question: Question;
  stepInstanceId: string;
  uploadId?: string;
  fileName?: string;
  onChange: QuestionFieldProps["onChange"];
}) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [busy, setBusy] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handle(file: File) {
    setError(null);
    const ext = file.name.split(".").pop()?.toLowerCase() ?? "";
    if (!ALLOWED_EXT.includes(ext)) {
      setError("Dateityp nicht erlaubt. Erlaubt: PDF, DOCX, XLSX, PNG, JPG.");
      return;
    }
    if (file.size > MAX_BYTES) {
      setError("Datei zu groß (max. 10 MB).");
      return;
    }
    setBusy(true);
    try {
      const res = await uploadFile(file, stepInstanceId, question.key);
      onChange(res.id, { fileName: res.originalName });
    } catch (err) {
      if (err instanceof ApiError && err.status === 415) {
        setError("Dateityp nicht erlaubt.");
      } else if (err instanceof ApiError && err.status === 413) {
        setError("Datei zu groß (max. 10 MB).");
      } else {
        setError(err instanceof ApiError ? err.detail : "Upload fehlgeschlagen.");
      }
    } finally {
      setBusy(false);
    }
  }

  if (uploadId) {
    return (
      <div className="uploaded-file">
        <span aria-hidden="true">📎</span>
        <span className="uploaded-file__name">{fileName ?? "Hochgeladene Datei"}</span>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => downloadUpload(uploadId, fileName ?? "datei")}
        >
          Herunterladen
        </Button>
        <Button variant="ghost" size="sm" onClick={() => onChange(undefined, { fileName: undefined })}>
          Entfernen
        </Button>
      </div>
    );
  }

  return (
    <>
      <button
        type="button"
        className={`dropzone ${dragOver ? "dropzone--active" : ""}`}
        onClick={() => inputRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragOver(false);
          const file = e.dataTransfer.files[0];
          if (file) void handle(file);
        }}
        disabled={busy}
      >
        <span className="dropzone__icon" aria-hidden="true">
          ↑
        </span>
        <span className="dropzone__title">
          {busy ? "Wird hochgeladen…" : "Datei hierher ziehen oder klicken"}
        </span>
        <span className="dropzone__hint">PDF, DOCX, XLSX, PNG, JPG · max. 10 MB</span>
      </button>
      <input
        ref={inputRef}
        type="file"
        accept={ACCEPT}
        hidden
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) void handle(file);
          e.target.value = "";
        }}
      />
      {error && (
        <p className="field-hint field-hint--error" role="alert">
          <span aria-hidden="true">⚠</span> {error}
        </p>
      )}
    </>
  );
}

// --- per-question AI help --------------------------------------------------

function AiHelp({
  question,
  stepInstanceId,
  onAccept,
}: {
  question: Question;
  stepInstanceId: string;
  onAccept: QuestionFieldProps["onChange"];
}) {
  const [suggestion, setSuggestion] = useState<AiSuggestion | null>(null);
  const [explanation, setExplanation] = useState<string | null>(null);
  const [loading, setLoading] = useState<"suggest" | "explain" | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function suggest() {
    setError(null);
    setLoading("suggest");
    try {
      setSuggestion(await aiSuggest(stepInstanceId, question.key));
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "KI-Vorschlag fehlgeschlagen.");
    } finally {
      setLoading(null);
    }
  }

  async function explain() {
    setError(null);
    setLoading("explain");
    try {
      const res = await aiChat({
        context: "question",
        contextRef: question.key,
        message: `Bitte erkläre die Frage „${question.label}“ und gib Beispiele.`,
      });
      setExplanation(res.reply);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "KI-Erklärung fehlgeschlagen.");
    } finally {
      setLoading(null);
    }
  }

  function accept() {
    if (!suggestion) return;
    let value = suggestion.proposedValue;
    // multi_select expects string[]; coerce a scalar proposal.
    if (question.type === "multi_select" && !Array.isArray(value)) {
      value = value == null ? [] : [String(value)];
    }
    onAccept(value, { aiSuggested: true });
    setSuggestion(null);
  }

  return (
    <div className="ai-help">
      <div className="ai-help__bar">
        <span className="ai-help__hint">
          <span aria-hidden="true">✦</span> KI-Hilfe
        </span>
        <Button variant="ghost" size="sm" onClick={explain} disabled={loading !== null}>
          Erklären
        </Button>
        <Button variant="secondary" size="sm" onClick={suggest} disabled={loading !== null}>
          Vorschlag
        </Button>
        {loading && <Spinner label="KI denkt nach…" />}
      </div>

      {explanation && <p className="ai-explain">{explanation}</p>}

      {suggestion && (
        <div className="ai-suggestion">
          <span className="ai-suggestion__meta">
            KI-Vorschlag
            {typeof suggestion.confidence === "number" &&
              ` · Konfidenz ${Math.round(suggestion.confidence * 100)}%`}
          </span>
          <p className="ai-suggestion__value">
            {Array.isArray(suggestion.proposedValue)
              ? (suggestion.proposedValue as string[]).join(", ")
              : String(suggestion.proposedValue ?? "—")}
          </p>
          {suggestion.openQuestions && suggestion.openQuestions.length > 0 && (
            <ul className="ai-suggestion__open">
              {suggestion.openQuestions.map((q, i) => (
                <li key={i}>{q}</li>
              ))}
            </ul>
          )}
          <Button size="sm" onClick={accept}>
            Übernehmen
          </Button>
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
