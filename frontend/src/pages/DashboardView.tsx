import type { Dashboard } from "../api";
import { ProgressBar } from "../components/ProgressBar";
import { ChatPanel } from "../components/ChatPanel";
import { ModuleCardView } from "./ModuleCardView";
import "./Dashboard.css";

/**
 * Presentational dashboard (§9.1): greeting, overall progress, module grid and
 * the dockable dashboard AI chat (FR-DASH-004). Pure render from a Dashboard DTO.
 */
export function DashboardView({ dashboard }: { dashboard: Dashboard }) {
  return (
    <>
      <header className="dash__header reveal">
        <span className="eyebrow">Onboarding</span>
        <h1 className="dash__greeting">
          Hallo <em>{dashboard.customerName}</em>.
        </h1>
        <p className="dash__lede">
          Hier sehen Sie alle Module Ihres Datenschutz-Onboardings, deren Status und die jeweils
          nächste empfohlene Aktion. Gesperrte Module werden nach Abschluss der Voraussetzungen
          freigeschaltet.
        </p>

        <div className="dash__progress">
          <div className="dash__progress-head">
            <span className="dash__progress-label">Gesamtfortschritt</span>
            <span className="dash__progress-value">{dashboard.overallProgress}%</span>
          </div>
          <ProgressBar
            value={dashboard.overallProgress}
            label="Gesamtfortschritt"
            showValue={false}
          />
        </div>
      </header>

      <section className="module-grid" aria-label="Module">
        {dashboard.modules.map((m) => (
          <ModuleCardView key={m.moduleInstanceId} module={m} />
        ))}
      </section>

      <ChatPanel
        context="dashboard"
        contextRef={dashboard.processInstanceId}
        title="Onboarding-Assistent"
        subtitle="Allgemeine Fragen & Orientierung"
      />
    </>
  );
}
