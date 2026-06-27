import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { Button } from "./Button";
import "./AppShell.css";

const ROLE_LABEL: Record<string, string> = {
  customer: "Kunde",
  reviewer: "Reviewer",
  admin: "Admin",
};

export function AppShell({ children }: { children: ReactNode }) {
  const { user, logout } = useAuth();
  return (
    <div className="app-shell">
      <header className="topbar">
        <Link to="/" className="wordmark" aria-label="Zweiplus — Startseite">
          <span className="wordmark__plus" aria-hidden="true">
            +
          </span>
          <span className="wordmark__brand">zweiplus</span>
          <span className="wordmark__suffix">·onboarding</span>
        </Link>
        {user && (
          <div className="topbar__actions">
            <div className="topbar__user">
              <span className="topbar__name">{user.name}</span>
              <span className="topbar__role">{ROLE_LABEL[user.role] ?? user.role}</span>
            </div>
            <Button variant="secondary" size="sm" onClick={logout}>
              Abmelden
            </Button>
          </div>
        )}
      </header>
      <main className="app-main">{children}</main>
    </div>
  );
}
