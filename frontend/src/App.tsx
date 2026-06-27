import type { ReactNode } from "react";
import { BrowserRouter, Navigate, Route, Routes, useLocation } from "react-router-dom";
import { AuthProvider, useAuth } from "./auth/AuthContext";
import { ProtectedRoute } from "./auth/ProtectedRoute";
import { AppShell } from "./components/AppShell";
import { LoginPage } from "./pages/LoginPage";
import { HomePage } from "./pages/HomePage";
import { ProcessDashboardPage } from "./pages/ProcessDashboardPage";
import { PlaceholderPage } from "./pages/PlaceholderPage";

function LoginRoute() {
  const { isAuthenticated } = useAuth();
  const location = useLocation();
  const from = (location.state as { from?: string } | null)?.from ?? "/";
  if (isAuthenticated) return <Navigate to={from} replace />;
  return <LoginPage />;
}

function ProtectedShell({ children }: { children: ReactNode }) {
  return (
    <ProtectedRoute>
      <AppShell>{children}</AppShell>
    </ProtectedRoute>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginRoute />} />

          <Route
            path="/"
            element={
              <ProtectedShell>
                <HomePage />
              </ProtectedShell>
            }
          />
          <Route
            path="/processes/:processInstanceId"
            element={
              <ProtectedShell>
                <ProcessDashboardPage />
              </ProtectedShell>
            }
          />
          <Route
            path="/modules/:moduleInstanceId"
            element={
              <ProtectedShell>
                <PlaceholderPage title="Modul-Detail" />
              </ProtectedShell>
            }
          />
          <Route
            path="/steps/:stepInstanceId"
            element={
              <ProtectedShell>
                <PlaceholderPage title="Step-Bearbeitung" />
              </ProtectedShell>
            }
          />
          <Route
            path="/review"
            element={
              <ProtectedRoute roles={["reviewer", "admin"]}>
                <AppShell>
                  <PlaceholderPage title="Review-Übersicht" />
                </AppShell>
              </ProtectedRoute>
            }
          />
          <Route
            path="/review/:moduleInstanceId"
            element={
              <ProtectedRoute roles={["reviewer", "admin"]}>
                <AppShell>
                  <PlaceholderPage title="Modul-Review" />
                </AppShell>
              </ProtectedRoute>
            }
          />

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
