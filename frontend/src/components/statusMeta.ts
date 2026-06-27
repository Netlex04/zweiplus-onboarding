/**
 * Maps the API ModuleStatus enum onto a design-system pill variant + label.
 * Variants follow the styleguide pills:
 *   success  -> green   (completed / import_ready / imported)
 *   info     -> blue    (in progress, waiting on a party)
 *   neutral  -> grey    (locked / available / not started)
 *   danger   -> red     (backend validation failed)
 *   warning  -> amber   (ai check pending)
 */

import type { ModuleStatus, StepStatus } from "../api";

export type PillVariant = "success" | "info" | "neutral" | "danger" | "warning";

interface StatusMeta {
  variant: PillVariant;
  label: string;
}

const MODULE_STATUS_META: Record<ModuleStatus, StatusMeta> = {
  locked: { variant: "neutral", label: "Gesperrt" },
  available: { variant: "neutral", label: "Verfügbar" },
  not_started: { variant: "neutral", label: "Nicht gestartet" },
  in_progress: { variant: "info", label: "In Bearbeitung" },
  waiting_customer: { variant: "info", label: "Wartet auf Kunde" },
  waiting_zweiplus: { variant: "info", label: "Wartet auf Zweiplus" },
  ai_check_pending: { variant: "warning", label: "KI-Prüfung offen" },
  backend_validation_failed: { variant: "danger", label: "Validierung fehlgeschlagen" },
  completed: { variant: "success", label: "Abgeschlossen" },
  import_ready: { variant: "success", label: "Importbereit" },
  imported: { variant: "success", label: "Importiert" },
};

export function moduleStatusMeta(status: ModuleStatus): StatusMeta {
  return MODULE_STATUS_META[status] ?? { variant: "neutral", label: status };
}

const STEP_STATUS_META: Record<StepStatus, StatusMeta> = {
  not_started: { variant: "neutral", label: "Nicht gestartet" },
  in_progress: { variant: "info", label: "In Bearbeitung" },
  incomplete: { variant: "warning", label: "Unvollständig" },
  complete: { variant: "success", label: "Vollständig" },
  ai_check_pending: { variant: "warning", label: "KI-Prüfung offen" },
  backend_validation_failed: { variant: "danger", label: "Validierung fehlgeschlagen" },
  review_pending: { variant: "info", label: "In Prüfung" },
  completed: { variant: "success", label: "Abgeschlossen" },
};

export function stepStatusMeta(status: StepStatus): StatusMeta {
  return STEP_STATUS_META[status] ?? { variant: "neutral", label: status };
}
