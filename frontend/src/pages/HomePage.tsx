import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import {
  ApiError,
  createProcess,
  getDashboard,
  getProcessDefinitions,
  getProcesses,
} from "../api";
import type { Dashboard, ProcessDefinition, ProcessSummary } from "../api";
import { Button } from "../components/Button";
import { Spinner } from "../components/Spinner";
import { ErrorBanner } from "../components/ErrorBanner";
import { EmptyState } from "../components/EmptyState";
import { StatusPill } from "../components/StatusPill";
import { DashboardView } from "./DashboardView";
import "./HomePage.css";

const PROCESS_DEF_KEY = "datenschutz_basis_onboarding";

/** Remember a customer's process id locally so a reload reopens the dashboard
 * instead of creating a duplicate process. */
function processStorageKey(name: string): string {
  return `zweiplus.process.${name}`;
}

export function HomePage() {
  const { user } = useAuth();
  if (!user) return null;
  return user.role === "customer" ? <CustomerHome /> : <StaffHome />;
}

// --- Customer: bootstrap a process or show its dashboard -------------------

function CustomerHome() {
  const { user } = useAuth();
  const name = user!.name;
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [def, setDef] = useState<ProcessDefinition | null>(null);
  const [loading, setLoading] = useState(true);
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const storedId = localStorage.getItem(processStorageKey(name));
      if (storedId) {
        try {
          setDashboard(await getDashboard(storedId));
          return;
        } catch (err) {
          if (!(err instanceof ApiError) || err.status !== 404) throw err;
          localStorage.removeItem(processStorageKey(name)); // stale id
        }
      }
      const defs = await getProcessDefinitions();
      setDef(defs.find((d) => d.key === PROCESS_DEF_KEY) ?? defs[0] ?? null);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Daten konnten nicht geladen werden.");
    } finally {
      setLoading(false);
    }
  }, [name]);

  useEffect(() => {
    void load();
  }, [load]);

  async function start() {
    setStarting(true);
    setError(null);
    try {
      const dash = await createProcess({
        processDefKey: def?.key ?? PROCESS_DEF_KEY,
        customerName: name,
      });
      localStorage.setItem(processStorageKey(name), dash.processInstanceId);
      setDashboard(dash);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Onboarding konnte nicht gestartet werden.");
    } finally {
      setStarting(false);
    }
  }

  if (loading) return <Spinner center />;
  if (dashboard) return <DashboardView dashboard={dashboard} />;

  return (
    <div className="bootstrap reveal">
      {error && <ErrorBanner message={error} />}
      <span className="eyebrow">Willkommen, {name}</span>
      <h1 className="bootstrap__title">Starten Sie Ihr Datenschutz-Onboarding.</h1>
      <p className="bootstrap__lede">
        {def?.description ??
          "Wir führen Sie Schritt für Schritt durch die Erfassung Ihrer datenschutzrelevanten Informationen."}
      </p>
      {def && (
        <p className="bootstrap__def">
          Prozess: <strong>{def.name}</strong> · {def.modules.length} Module
        </p>
      )}
      <Button onClick={start} disabled={starting}>
        {starting ? "Wird gestartet…" : "Onboarding starten"}
      </Button>
    </div>
  );
}

// --- Reviewer / admin: list processes, open a dashboard -------------------

function StaffHome() {
  const navigate = useNavigate();
  const [processes, setProcesses] = useState<ProcessSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getProcesses()
      .then(setProcesses)
      .catch((err) =>
        setError(err instanceof ApiError ? err.detail : "Prozesse konnten nicht geladen werden."),
      );
  }, []);

  if (error) return <ErrorBanner message={error} />;
  if (!processes) return <Spinner center />;

  return (
    <div className="reveal">
      <header className="process-list__head">
        <span className="eyebrow">Zweiplus</span>
        <h1 className="process-list__title">Onboarding-Prozesse</h1>
        <p className="dash__lede">
          Wählen Sie einen Kundenprozess, um das Dashboard zu öffnen.
        </p>
      </header>

      {processes.length === 0 ? (
        <EmptyState
          title="Noch keine Prozesse"
          body="Sobald ein Kunde ein Onboarding startet, erscheint es hier."
        />
      ) : (
        <table className="process-table">
          <thead>
            <tr>
              <th>Kunde</th>
              <th>Organisation</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {processes.map((p) => (
              <tr
                key={p.id}
                tabIndex={0}
                role="button"
                onClick={() => navigate(`/processes/${p.id}`)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" || e.key === " ") {
                    e.preventDefault();
                    navigate(`/processes/${p.id}`);
                  }
                }}
              >
                <td>{p.customerName}</td>
                <td>{p.customerOrg ?? "—"}</td>
                <td>
                  <StatusPill variant="info" label={p.status} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
