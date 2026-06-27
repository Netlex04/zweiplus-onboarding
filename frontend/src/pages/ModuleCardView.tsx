import { useNavigate } from "react-router-dom";
import type { ModuleCard } from "../api";
import { Card } from "../components/Card";
import { StatusPill } from "../components/StatusPill";
import { ProgressBar } from "../components/ProgressBar";
import { Button } from "../components/Button";
import { moduleStatusMeta } from "../components/statusMeta";

/**
 * A single module card (FR-DASH-001/002/003, §9.2). Locked modules are greyed,
 * carry a lock icon + unlock hint and have no active CTA. The CTA only
 * navigates when the module is not locked.
 */
export function ModuleCardView({ module }: { module: ModuleCard }) {
  const navigate = useNavigate();
  const meta = moduleStatusMeta(module.status);
  const cta = module.nextAction ?? "Öffnen";

  return (
    <Card
      interactive={!module.locked}
      muted={module.locked}
      className={`module-card ${module.locked ? "module-card--locked" : ""}`}
      aria-disabled={module.locked || undefined}
    >
      <div className="module-card__top">
        <h3 className="module-card__name">
          {module.locked && (
            <span className="module-card__lock" aria-hidden="true">
              🔒
            </span>
          )}
          {module.name}
        </h3>
        <StatusPill
          variant={meta.variant}
          label={meta.label}
          icon={module.locked ? "🔒" : undefined}
        />
      </div>

      <p className="module-card__explainer">{module.explainer}</p>

      <ProgressBar value={module.progress} label="Fortschritt" />

      <div className="module-card__meta">
        <div className="module-card__meta-item">
          <span className="module-card__meta-key">Zuständig</span>
          <span className="module-card__meta-val">{module.responsibleRole}</span>
        </div>
        <div className="module-card__meta-item">
          <span className="module-card__meta-key">Aufwand</span>
          <span className="module-card__meta-val">{module.estimatedEffort}</span>
        </div>
      </div>

      {module.locked && module.unlockHint && (
        <p className="module-card__unlock">
          <span aria-hidden="true">🔒</span>
          {module.unlockHint}
        </p>
      )}

      <div className="module-card__footer">
        <Button
          variant={module.locked ? "secondary" : "primary"}
          disabled={module.locked}
          onClick={() =>
            !module.locked && navigate(`/modules/${module.moduleInstanceId}`)
          }
        >
          {module.locked ? "Gesperrt" : cta}
        </Button>
      </div>
    </Card>
  );
}
