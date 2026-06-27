import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { ApiError, getDashboard } from "../api";
import type { Dashboard } from "../api";
import { Spinner } from "../components/Spinner";
import { ErrorBanner } from "../components/ErrorBanner";
import { DashboardView } from "./DashboardView";

/** Opens a specific process dashboard by id (used by reviewer/admin). */
export function ProcessDashboardPage() {
  const { processInstanceId } = useParams<{ processInstanceId: string }>();
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!processInstanceId) return;
    setError(null);
    setDashboard(null);
    getDashboard(processInstanceId)
      .then(setDashboard)
      .catch((err) =>
        setError(err instanceof ApiError ? err.detail : "Dashboard konnte nicht geladen werden."),
      );
  }, [processInstanceId]);

  if (error) return <ErrorBanner message={error} />;
  if (!dashboard) return <Spinner center />;
  return <DashboardView dashboard={dashboard} />;
}
