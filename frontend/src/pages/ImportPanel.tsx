import { useState } from "react";
import {
  ApiError,
  createImportJob,
  generateCanonical,
  getImportPreview,
  runImportJob,
} from "../api";
import type { ImportJob, ImportPreview, ModuleStatus } from "../api";
import { Button } from "../components/Button";
import { Card } from "../components/Card";
import { StatusPill } from "../components/StatusPill";

const IMPORT_STATUS_LABEL: Record<string, string> = {
  not_prepared: "Nicht vorbereitet",
  mapping_ready: "Mapping bereit",
  validated: "Validiert",
  approved: "Freigegeben",
  importing: "Import läuft",
  imported: "Importiert",
  import_failed: "Import fehlgeschlagen",
  reimport_required: "Reimport nötig",
};

/**
 * DPMS import flow (§9.6, FR-INT-004/005/006): generate the canonical model,
 * show the import preview (mapped/unmapped/warnings/errors) and run the import
 * job through to `imported`.
 */
export function ImportPanel({
  moduleInstanceId,
  initialStatus,
}: {
  moduleInstanceId: string;
  initialStatus: ModuleStatus;
}) {
  const [preview, setPreview] = useState<ImportPreview | null>(null);
  const [job, setJob] = useState<ImportJob | null>(null);
  const [loading, setLoading] = useState<"preview" | "import" | null>(null);
  const [error, setError] = useState<string | null>(null);
  const alreadyImported = initialStatus === "imported";

  async function loadPreview() {
    setError(null);
    setLoading("preview");
    try {
      // Canonical must exist before a preview can be mapped.
      await generateCanonical(moduleInstanceId);
      setPreview(await getImportPreview(moduleInstanceId, "dpms_v1"));
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Importvorschau fehlgeschlagen.");
    } finally {
      setLoading(null);
    }
  }

  async function startImport() {
    setError(null);
    setLoading("import");
    try {
      const created = await createImportJob(moduleInstanceId, "dpms_v1");
      setJob(await runImportJob(created.id));
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Import fehlgeschlagen.");
    } finally {
      setLoading(null);
    }
  }

  const hasErrors = (preview?.errors.length ?? 0) > 0;

  return (
    <Card className="import-block">
      <div className="flow-head__top">
        <h2 className="flow-section__title">DPMS-Import</h2>
        {(job || alreadyImported) && (
          <StatusPill
            variant={
              (job?.status ?? initialStatus) === "imported"
                ? "success"
                : (job?.status ?? "").includes("failed")
                  ? "danger"
                  : "info"
            }
            label={IMPORT_STATUS_LABEL[job?.status ?? initialStatus] ?? (job?.status ?? "")}
          />
        )}
      </div>

      {!preview && !alreadyImported && (
        <div className="step-actions">
          <Button onClick={loadPreview} disabled={loading !== null}>
            {loading === "preview" ? "Erstellt Vorschau…" : "Importvorschau erstellen"}
          </Button>
        </div>
      )}

      {preview && (
        <>
          <p className="ai-suggestion__meta">Zielsystem: {preview.targetSystem}</p>

          <h3 className="template__title">Gemappte Objekte ({preview.mappedObjects.length})</h3>
          {preview.mappedObjects.map((obj, i) => (
            <pre className="mapped-obj" key={i}>
              {JSON.stringify(obj, null, 2)}
            </pre>
          ))}

          {preview.unmappedFields.length > 0 && (
            <>
              <h3 className="template__title">Nicht gemappte Felder</h3>
              <div className="tag-list">
                {preview.unmappedFields.map((f) => (
                  <span className="tag" key={f}>
                    {f}
                  </span>
                ))}
              </div>
            </>
          )}

          {preview.warnings.map((w, i) => (
            <p className="field-hint field-hint--warning" key={`w${i}`}>
              <span aria-hidden="true">!</span> {w}
            </p>
          ))}
          {preview.errors.map((e, i) => (
            <p className="field-hint field-hint--error" key={`e${i}`} role="alert">
              <span aria-hidden="true">⚠</span> {e}
            </p>
          ))}

          {job?.status !== "imported" && (
            <div className="step-actions">
              <Button onClick={startImport} disabled={loading !== null || hasErrors}>
                {loading === "import" ? "Importiert…" : "Import starten"}
              </Button>
              {hasErrors && (
                <span className="ai-help__hint">Import wegen Fehlern blockiert.</span>
              )}
            </div>
          )}
        </>
      )}

      {(job?.status === "imported" || alreadyImported) && (
        <p className="flow-toast" role="status">
          ✓ Import abgeschlossen – die Daten wurden an DPMS übergeben.
        </p>
      )}

      {error && (
        <p className="field-hint field-hint--error" role="alert">
          <span aria-hidden="true">⚠</span> {error}
        </p>
      )}
    </Card>
  );
}
