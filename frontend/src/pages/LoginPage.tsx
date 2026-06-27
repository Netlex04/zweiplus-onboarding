import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { ApiError } from "../api";
import { Button } from "../components/Button";
import { ErrorBanner } from "../components/ErrorBanner";
import "./LoginPage.css";

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await login(email.trim(), password);
      navigate("/", { replace: true });
    } catch (err) {
      const msg =
        err instanceof ApiError
          ? err.status === 401
            ? "E-Mail oder Passwort ist falsch."
            : err.detail
          : "Anmeldung fehlgeschlagen.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="login">
      <div className="login__card reveal">
        <div className="login__brand">
          <span className="login__brand-plus" aria-hidden="true">
            +
          </span>
          <b>zweiplus</b>
          <span>·onboarding</span>
        </div>
        <h1 className="login__title">Willkommen zurück.</h1>
        <p className="login__lede">
          Melden Sie sich an, um Ihr Datenschutz-Onboarding fortzusetzen.
        </p>

        {error && (
          <div className="login__error">
            <ErrorBanner message={error} />
          </div>
        )}

        <form onSubmit={onSubmit}>
          <div className="field">
            <label className="field__label" htmlFor="email">
              E-Mail
            </label>
            <input
              id="email"
              className="input"
              type="email"
              autoComplete="username"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="name@beispiel.de"
              required
            />
          </div>
          <div className="field">
            <label className="field__label" htmlFor="password">
              Passwort
            </label>
            <input
              id="password"
              className="input"
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
            />
          </div>
          <Button type="submit" block disabled={loading}>
            {loading ? "Anmelden…" : "Anmelden"}
          </Button>
        </form>

        <p className="login__hint">
          Demo-Zugänge (Passwort <code>demo1234</code>): <code>kunde@demo.test</code>,{" "}
          <code>review@zweiplus.test</code>, <code>admin@zweiplus.test</code>.
        </p>
      </div>
    </div>
  );
}
