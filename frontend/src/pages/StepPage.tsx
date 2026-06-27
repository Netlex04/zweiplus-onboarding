import { useCallback, useEffect, useState } from "react";
import { useLocation, useNavigate, useParams } from "react-router-dom";
import {
  aiValidate,
  ApiError,
  completeStep,
  getModule,
  getStep,
  saveStepAnswers,
} from "../api";
import type {
  AiValidationResult,
  AnswerInput,
  BackendValidationResult,
  ModuleDetail,
  StepDetail,
} from "../api";
import { Button } from "../components/Button";
import { Card } from "../components/Card";
import { Spinner } from "../components/Spinner";
import { ErrorBanner } from "../components/ErrorBanner";
import { ChatPanel } from "../components/ChatPanel";
import { ProgressBar } from "../components/ProgressBar";
import { QuestionField } from "./QuestionField";
import { TemplateList } from "./TemplateList";
import "./ModuleFlow.css";

const DONE_STEP = new Set(["complete", "completed", "review_pending"]);

interface LocalAnswer {
  value: unknown;
  fileName?: string;
  aiSuggested?: boolean;
}

/** Map of questionKey -> current local answer value. */
type Answers = Record<string, LocalAnswer>;

function initialAnswers(step: StepDetail): Answers {
  const map: Answers = {};
  for (const q of step.questions) {
    if (q.answer) map[q.key] = { value: q.answer.value, aiSuggested: q.answer.aiSuggested };
  }
  return map;
}

/**
 * Step editing screen (§9.4): step navigation, module progress, dynamic
 * question fields, inline validation, save and complete (with 409 handling),
 * per-question AI help, the prüf-KI button and step/module templates.
 */
export function StepPage() {
  const { stepInstanceId } = useParams<{ stepInstanceId: string }>();
  const navigate = useNavigate();

  const [step, setStep] = useState<StepDetail | null>(null);
  const [module, setModule] = useState<ModuleDetail | null>(null);
  const [answers, setAnswers] = useState<Answers>({});
  const [validation, setValidation] = useState<BackendValidationResult | null>(null);
  const [aiResult, setAiResult] = useState<AiValidationResult | null>(null);
  const [busy, setBusy] = useState<"save" | "complete" | "ai" | null>(null);
  const [message, setMessage] = useState<{ text: string; kind: "ok" | "error" } | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadStep = useCallback(async (id: string) => {
    const fresh = await getStep(id);
    setStep(fresh);
    setAnswers(initialAnswers(fresh));
    // The module that owns this step is discovered from the step list lookup.
    return fresh;
  }, []);

  useEffect(() => {
    if (!stepInstanceId) return;
    setError(null);
    setStep(null);
    setValidation(null);
    setAiResult(null);
    setMessage(null);
    loadStep(stepInstanceId).catch((err) =>
      setError(err instanceof ApiError ? err.detail : "Schritt konnte nicht geladen werden."),
    );
  }, [stepInstanceId, loadStep]);

  // Resolve the owning module for navigation + progress. The module id is
  // carried in router location state when navigating from the module/step page.
  const location = useLocation();
  const moduleHint = (location.state as { moduleInstanceId?: string } | null)?.moduleInstanceId;
  useEffect(() => {
    if (!moduleHint) return;
    // Re-fetch on step change so the step-nav reflects up-to-date statuses.
    getModule(moduleHint).then(setModule).catch(() => undefined);
  }, [moduleHint, stepInstanceId]);

  function setAnswer(key: string, value: unknown, meta?: { fileName?: string; aiSuggested?: boolean }) {
    setAnswers((prev) => ({
      ...prev,
      [key]: {
        value,
        fileName: meta?.fileName ?? prev[key]?.fileName,
        aiSuggested: meta?.aiSuggested ?? false,
      },
    }));
  }

  function answersPayload(): AnswerInput[] {
    return Object.entries(answers)
      .filter(([, a]) => a.value !== undefined)
      .map(([questionKey, a]) => ({ questionKey, value: a.value }));
  }

  /**
   * Persist answers and re-fetch the step so conditional questions update.
   * Returns whether the backend validation passed. Does NOT set user messages
   * (callers decide), but always refreshes inline field validation.
   */
  async function persist(): Promise<boolean> {
    if (!step) return false;
    const res = await saveStepAnswers(step.stepInstanceId, answersPayload());
    setValidation(res.validation);
    const fresh = await getStep(step.stepInstanceId);
    setStep(fresh);
    setAnswers((prev) => {
      const merged = initialAnswers(fresh);
      for (const [k, v] of Object.entries(prev)) merged[k] = { ...merged[k], ...v };
      return merged;
    });
    return res.validation.passed;
  }

  async function save(): Promise<boolean> {
    if (!step) return false;
    setBusy("save");
    setMessage(null);
    try {
      const passed = await persist();
      if (passed) setMessage({ text: "Gespeichert. Eingaben sind gültig.", kind: "ok" });
      return passed;
    } catch (err) {
      setMessage({
        text: err instanceof ApiError ? err.detail : "Speichern fehlgeschlagen.",
        kind: "error",
      });
      return false;
    } finally {
      setBusy(null);
    }
  }

  async function complete() {
    if (!step) return;
    setMessage(null);
    setBusy("complete");
    try {
      const passed = await persist();
      if (!passed) {
        setMessage({
          text: "Bitte korrigieren Sie die markierten Felder, bevor Sie abschließen.",
          kind: "error",
        });
        return;
      }
      await completeStep(step.stepInstanceId);
      // Re-fetch the module so the next-open-step decision uses fresh statuses
      // (the cached copy still lists the just-completed step as open).
      let steps = module?.steps ?? [];
      if (moduleHint) {
        try {
          const fresh = await getModule(moduleHint);
          setModule(fresh);
          steps = fresh.steps;
        } catch {
          /* fall back to the cached module */
        }
      }
      const next = steps.find(
        (s) => s.stepInstanceId !== step.stepInstanceId && !DONE_STEP.has(s.status),
      );
      if (next) {
        navigate(`/steps/${next.stepInstanceId}`, { state: { moduleInstanceId: moduleHint } });
      } else if (moduleHint) {
        navigate(`/modules/${moduleHint}`);
      } else {
        navigate("/");
      }
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        // Re-load to surface backend validation on the affected fields, then
        // keep the 409 hint visible.
        await persist().catch(() => undefined);
        setMessage({
          text: `${err.detail} Bitte prüfen Sie die markierten Pflichtfelder.`,
          kind: "error",
        });
      } else {
        setMessage({
          text: err instanceof ApiError ? err.detail : "Abschluss fehlgeschlagen.",
          kind: "error",
        });
      }
    } finally {
      setBusy(null);
    }
  }

  async function runAiCheck() {
    if (!step) return;
    setBusy("ai");
    setError(null);
    try {
      setAiResult(await aiValidate(step.stepInstanceId));
    } catch (err) {
      setMessage({
        text: err instanceof ApiError ? err.detail : "KI-Prüfung fehlgeschlagen.",
        kind: "error",
      });
    } finally {
      setBusy(null);
    }
  }

  if (error) return <ErrorBanner message={error} />;
  if (!step) return <Spinner center />;

  const errorsFor = (key: string) =>
    validation?.errors.filter((e) => e.questionKey === key) ?? [];
  const warningsFor = (key: string) =>
    validation?.warnings.filter((w) => w.questionKey === key) ?? [];

  const visible = step.questions.filter((q) => q.visible);

  return (
    <div className="reveal">
      <button
        type="button"
        className="flow-back"
        onClick={() => (moduleHint ? navigate(`/modules/${moduleHint}`) : navigate("/"))}
      >
        <span aria-hidden="true">←</span> Zurück zum Modul
      </button>

      {module && (
        <nav className="step-nav" aria-label="Schritte">
          {module.steps.map((s) => {
            const done = DONE_STEP.has(s.status);
            const current = s.stepInstanceId === step.stepInstanceId;
            return (
              <button
                type="button"
                key={s.stepInstanceId}
                className={`step-nav__item ${current ? "step-nav__item--current" : ""} ${
                  done ? "step-nav__item--done" : ""
                }`}
                onClick={() =>
                  navigate(`/steps/${s.stepInstanceId}`, {
                    state: { moduleInstanceId: moduleHint },
                  })
                }
                aria-current={current ? "step" : undefined}
              >
                <span aria-hidden="true">{done ? "✓" : "○"}</span>
                {s.title}
              </button>
            );
          })}
        </nav>
      )}

      <header className="flow-head">
        <span className="eyebrow">Schritt</span>
        <h1 className="flow-title">{step.title}</h1>
        {step.description && <p className="flow-lede">{step.description}</p>}
        {module && (
          <div className="flow-progress">
            <ProgressBar value={module.progress} label="Modulfortschritt" />
          </div>
        )}
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

      <Card>
        {visible.map((q) => (
          <QuestionField
            key={q.key}
            question={q}
            stepInstanceId={step.stepInstanceId}
            value={answers[q.key]?.value}
            fileName={answers[q.key]?.fileName}
            aiSuggested={answers[q.key]?.aiSuggested}
            errors={errorsFor(q.key)}
            warnings={warningsFor(q.key)}
            onChange={(value, meta) => setAnswer(q.key, value, meta)}
          />
        ))}
      </Card>

      {aiResult && (
        <Card className="import-block">
          <h2 className="flow-section__title">KI-Prüfung</h2>
          <ul className="check-list">
            {aiResult.checks.map((c, i) => (
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
          {aiResult.issues.length > 0 && (
            <ul className="ai-suggestion__open">
              {aiResult.issues.map((iss, i) => (
                <li key={i}>{iss}</li>
              ))}
            </ul>
          )}
        </Card>
      )}

      <div className="step-actions">
        <Button onClick={save} variant="secondary" disabled={busy !== null}>
          {busy === "save" ? "Speichert…" : "Speichern"}
        </Button>
        <Button onClick={runAiCheck} variant="ghost" disabled={busy !== null}>
          {busy === "ai" ? "Prüft…" : "Eingaben prüfen"}
        </Button>
        <Button onClick={complete} disabled={busy !== null}>
          {busy === "complete" ? "Schließt ab…" : "Schritt abschließen"}
        </Button>
      </div>

      {step.templates.length > 0 && (
        <section className="flow-section" aria-label="Vorlagen">
          <h2 className="flow-section__title">Vorlagen</h2>
          <TemplateList templates={step.templates} moduleInstanceId={moduleHint} />
        </section>
      )}

      <ChatPanel
        context="step"
        contextRef={step.stepInstanceId}
        title="Schritt-Assistent"
        subtitle={`Fragen zu „${step.title}“`}
      />
    </div>
  );
}
