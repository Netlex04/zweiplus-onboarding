import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { ApiError, getModule } from "../api";
import type { ModuleDetail } from "../api";
import { Button } from "../components/Button";
import { Card } from "../components/Card";
import { Spinner } from "../components/Spinner";
import { ErrorBanner } from "../components/ErrorBanner";
import { ChatPanel } from "../components/ChatPanel";
import { ProgressBar } from "../components/ProgressBar";
import { StatusPill } from "../components/StatusPill";
import { moduleStatusMeta, stepStatusMeta } from "../components/statusMeta";
import { TemplateList } from "./TemplateList";
import "./ModuleFlow.css";

const DONE_STEP = new Set(["complete", "completed", "review_pending"]);

/**
 * Module start screen (§9.3): intro, status, progress, step list, module-scope
 * templates and a Start/Continue CTA jumping to the first open step. Module AI
 * help is available via the dockable ChatPanel (context="module").
 */
export function ModulePage() {
  const { moduleInstanceId } = useParams<{ moduleInstanceId: string }>();
  const navigate = useNavigate();
  const [module, setModule] = useState<ModuleDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!moduleInstanceId) return;
    setError(null);
    setModule(null);
    getModule(moduleInstanceId)
      .then(setModule)
      .catch((err) =>
        setError(err instanceof ApiError ? err.detail : "Modul konnte nicht geladen werden."),
      );
  }, [moduleInstanceId]);

  if (error) return <ErrorBanner message={error} />;
  if (!module) return <Spinner center />;

  const meta = moduleStatusMeta(module.status);
  const firstOpen = module.steps.find((s) => !DONE_STEP.has(s.status)) ?? module.steps[0];
  const started = module.steps.some((s) => s.status !== "not_started");
  const allDone = module.steps.length > 0 && module.steps.every((s) => DONE_STEP.has(s.status));

  const intro = [
    ["Ziel", module.intro.goal],
    ["Warum", module.intro.why],
    ["Wer", module.intro.who],
    ["Aufwand", module.intro.effort],
  ].filter(([, v]) => Boolean(v)) as [string, string][];

  return (
    <div className="reveal">
      <button type="button" className="flow-back" onClick={() => navigate("/")}>
        <span aria-hidden="true">←</span> Zurück zum Dashboard
      </button>

      <header className="flow-head">
        <div className="flow-head__top">
          <div>
            <span className="eyebrow">Modul</span>
            <h1 className="flow-title">{module.name}</h1>
          </div>
          <StatusPill variant={meta.variant} label={meta.label} />
        </div>

        {module.intro.explainer && <p className="flow-lede">{module.intro.explainer}</p>}

        <div className="flow-progress">
          <ProgressBar value={module.progress} label="Fortschritt" />
        </div>
      </header>

      {intro.length > 0 && (
        <Card>
          <div className="intro-grid">
            {intro.map(([k, v]) => (
              <div className="intro-item" key={k}>
                <span className="intro-item__key">{k}</span>
                <p className="intro-item__val">{v}</p>
              </div>
            ))}
          </div>
        </Card>
      )}

      <section className="flow-section" aria-label="Schritte">
        <h2 className="flow-section__title">Schritte</h2>
        <ol className="step-list">
          {module.steps.map((s) => {
            const done = DONE_STEP.has(s.status);
            const sm = stepStatusMeta(s.status);
            return (
              <li className="step-list__item" key={s.stepInstanceId}>
                <span
                  className={`step-list__check ${done ? "step-list__check--done" : ""}`}
                  aria-hidden="true"
                >
                  {done ? "✓" : "○"}
                </span>
                <button
                  type="button"
                  className="step-list__title flow-back"
                  style={{ margin: 0 }}
                  onClick={() =>
                    navigate(`/steps/${s.stepInstanceId}`, {
                      state: { moduleInstanceId: module.moduleInstanceId },
                    })
                  }
                >
                  {s.title}
                </button>
                <StatusPill variant={sm.variant} label={sm.label} />
              </li>
            );
          })}
        </ol>
      </section>

      {module.templates.length > 0 && (
        <section className="flow-section" aria-label="Vorlagen">
          <h2 className="flow-section__title">Vorlagen</h2>
          <TemplateList templates={module.templates} moduleInstanceId={module.moduleInstanceId} />
        </section>
      )}

      <div className="step-actions">
        {!allDone && firstOpen && (
          <Button
            onClick={() =>
              navigate(`/steps/${firstOpen.stepInstanceId}`, {
                state: { moduleInstanceId: module.moduleInstanceId },
              })
            }
          >
            {started ? "Fortsetzen" : "Starten"}
          </Button>
        )}
        {allDone && (
          <span className="flow-toast" role="status">
            ✓ Alle Schritte abgeschlossen – das Modul ist in Prüfung.
          </span>
        )}
      </div>

      <ChatPanel
        context="module"
        contextRef={module.moduleInstanceId}
        title="Modul-Assistent"
        subtitle={`Fragen zu „${module.name}“`}
      />
    </div>
  );
}
