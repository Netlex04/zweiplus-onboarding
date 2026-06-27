import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ApiError, getReviewTasks } from "../api";
import type { ReviewTask } from "../api";
import { Spinner } from "../components/Spinner";
import { ErrorBanner } from "../components/ErrorBanner";
import { EmptyState } from "../components/EmptyState";
import { StatusPill } from "../components/StatusPill";
import "./ModuleFlow.css";

const TASK_META: Record<ReviewTask["status"], { variant: "info" | "warning" | "success" | "neutral"; label: string }> = {
  open: { variant: "warning", label: "Offen" },
  in_review: { variant: "info", label: "In Prüfung" },
  changes_requested: { variant: "neutral", label: "Korrektur angefragt" },
  approved: { variant: "success", label: "Freigegeben" },
};

/** Reviewer/admin task list (§9.6). Each row opens the module review detail. */
export function ReviewListPage() {
  const navigate = useNavigate();
  const [tasks, setTasks] = useState<ReviewTask[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getReviewTasks()
      .then(setTasks)
      .catch((err) =>
        setError(err instanceof ApiError ? err.detail : "Review-Aufgaben konnten nicht geladen werden."),
      );
  }, []);

  if (error) return <ErrorBanner message={error} />;
  if (!tasks) return <Spinner center />;

  return (
    <div className="reveal">
      <header className="flow-head">
        <span className="eyebrow">Zweiplus</span>
        <h1 className="flow-title">Review-Aufgaben</h1>
        <p className="flow-lede">
          Module, die von Kunden eingereicht wurden und auf Ihre Prüfung warten.
        </p>
      </header>

      {tasks.length === 0 ? (
        <EmptyState
          title="Keine offenen Aufgaben"
          body="Sobald ein Kunde ein Modul einreicht, erscheint es hier zur Prüfung."
        />
      ) : (
        <table className="review-task-table">
          <thead>
            <tr>
              <th>Kunde</th>
              <th>Modul</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {tasks.map((t) => {
              const meta = TASK_META[t.status] ?? { variant: "neutral" as const, label: t.status };
              return (
                <tr
                  key={t.id}
                  tabIndex={0}
                  role="button"
                  onClick={() => navigate(`/review/${t.moduleInstanceId}`)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ") {
                      e.preventDefault();
                      navigate(`/review/${t.moduleInstanceId}`);
                    }
                  }}
                >
                  <td>{t.customerName ?? "—"}</td>
                  <td>{t.moduleName}</td>
                  <td>
                    <StatusPill variant={meta.variant} label={meta.label} />
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}
    </div>
  );
}
