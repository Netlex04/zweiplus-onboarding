import { useState } from "react";
import { ApiError, downloadTemplateFile, getTemplate } from "../api";
import type { Template } from "../api";
import { Button } from "../components/Button";
import { Card } from "../components/Card";

/**
 * Renders module/step templates (§9.5, FR-TPL-004):
 * - email: show subject + body, "Kopieren" copies subject+body to the clipboard.
 * - file: "Herunterladen" fetches the protected file and saves it.
 * Email bodies are fetched on demand (rendered placeholders) when a moduleId
 * is provided so the customer always sees the resolved text.
 */
export function TemplateList({
  templates,
  moduleInstanceId,
}: {
  templates: Template[];
  moduleInstanceId?: string;
}) {
  return (
    <div className="template-list">
      {templates.map((t) => (
        <TemplateItem key={t.key} template={t} moduleInstanceId={moduleInstanceId} />
      ))}
    </div>
  );
}

function TemplateItem({
  template,
  moduleInstanceId,
}: {
  template: Template;
  moduleInstanceId?: string;
}) {
  const [resolved, setResolved] = useState<Template>(template);
  const [open, setOpen] = useState(false);
  const [copied, setCopied] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function show() {
    if (!open) {
      setError(null);
      setBusy(true);
      try {
        // Re-fetch so placeholders are rendered for this module instance.
        const fresh = await getTemplate(template.key, moduleInstanceId);
        setResolved(fresh);
      } catch (err) {
        setError(err instanceof ApiError ? err.detail : "Vorlage konnte nicht geladen werden.");
      } finally {
        setBusy(false);
      }
    }
    setOpen((v) => !v);
  }

  async function copy() {
    const text = [resolved.subject ? `Betreff: ${resolved.subject}` : "", resolved.body ?? ""]
      .filter(Boolean)
      .join("\n\n");
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      setError("Kopieren nicht möglich. Bitte manuell markieren.");
    }
  }

  async function download() {
    setError(null);
    setBusy(true);
    try {
      await downloadTemplateFile(template.key, template.fileName ?? `${template.key}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Download fehlgeschlagen.");
    } finally {
      setBusy(false);
    }
  }

  const isEmail = template.type === "email";

  return (
    <Card>
      <div className="template__head">
        <div>
          <p className="template__title">{template.title ?? template.key}</p>
          {template.fileName && (
            <span className="ai-suggestion__meta">{template.fileName}</span>
          )}
        </div>
        <div className="ai-help__bar">
          {isEmail ? (
            <>
              <Button variant="secondary" size="sm" onClick={show} disabled={busy}>
                {open ? "Ausblenden" : "Anzeigen"}
              </Button>
              <Button size="sm" onClick={copy}>
                {copied ? "Kopiert ✓" : "Kopieren"}
              </Button>
            </>
          ) : (
            <Button size="sm" onClick={download} disabled={busy}>
              {busy ? "Lädt…" : "Herunterladen"}
            </Button>
          )}
        </div>
      </div>

      {isEmail && open && (
        <>
          {resolved.subject && <p className="template__subject">Betreff: {resolved.subject}</p>}
          {resolved.body && <pre className="template__body">{resolved.body}</pre>}
        </>
      )}

      {error && (
        <p className="field-hint field-hint--error" role="alert">
          <span aria-hidden="true">⚠</span> {error}
        </p>
      )}
    </Card>
  );
}
