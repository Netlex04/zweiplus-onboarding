import { useEffect, useRef, useState } from "react";
import { aiChat, ApiError } from "../api";
import type { AiChatContext, AiChatMessage } from "../api";
import { Button } from "./Button";
import { Spinner } from "./Spinner";
import { ErrorBanner } from "./ErrorBanner";
import "./ChatPanel.css";

interface ChatPanelProps {
  context: AiChatContext;
  contextRef?: string;
  title?: string;
  subtitle?: string;
  placeholder?: string;
}

/**
 * Dockable AI chat. History is kept client-side and sent with each request.
 * Used on the dashboard (context="dashboard"); reusable for module/step/question.
 */
export function ChatPanel({
  context,
  contextRef,
  title = "KI-Assistent",
  subtitle = "Fragen zum Onboarding",
  placeholder = "Frage stellen…",
}: ChatPanelProps) {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<AiChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const logRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    logRef.current?.scrollTo({ top: logRef.current.scrollHeight });
  }, [messages, loading]);

  async function send(e: React.FormEvent) {
    e.preventDefault();
    const text = input.trim();
    if (!text || loading) return;

    const history = messages;
    const userMsg: AiChatMessage = { role: "user", content: text };
    setMessages([...history, userMsg]);
    setInput("");
    setError(null);
    setLoading(true);
    try {
      const res = await aiChat({ context, contextRef, message: text, history });
      setMessages((prev) => [...prev, { role: "assistant", content: res.reply }]);
    } catch (err) {
      const msg = err instanceof ApiError ? err.detail : "Antwort konnte nicht geladen werden.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="chat-dock">
      {open && (
        <section className="chat-panel" aria-label={title}>
          <header className="chat-panel__head">
            <div>
              <div className="chat-panel__title">{title}</div>
              <div className="chat-panel__subtitle">{subtitle}</div>
            </div>
            <button
              type="button"
              className="chat-panel__close"
              onClick={() => setOpen(false)}
              aria-label="Chat schließen"
            >
              ×
            </button>
          </header>

          <div className="chat-panel__log" ref={logRef}>
            {messages.length === 0 && !loading && (
              <p className="chat-panel__empty">
                Stellen Sie Fragen zu Ihrem Onboarding, gesperrten Modulen oder den nächsten
                Schritten.
              </p>
            )}
            {messages.map((m, i) => (
              <div
                key={i}
                className={`chat-bubble ${m.role === "user" ? "chat-bubble--user" : "chat-bubble--ai"}`}
              >
                {m.content}
              </div>
            ))}
            {loading && <Spinner label="KI denkt nach…" />}
          </div>

          {error && (
            <div className="chat-panel__error">
              <ErrorBanner message={error} />
            </div>
          )}

          <form className="chat-panel__form" onSubmit={send}>
            <input
              className="chat-panel__input"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={placeholder}
              aria-label="Nachricht"
              disabled={loading}
            />
            <Button type="submit" size="sm" disabled={loading || input.trim() === ""}>
              Senden
            </Button>
          </form>
        </section>
      )}

      <button
        type="button"
        className="chat-fab"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
      >
        <span aria-hidden="true">✦</span>
        {open ? "Schließen" : "KI-Assistent"}
      </button>
    </div>
  );
}
