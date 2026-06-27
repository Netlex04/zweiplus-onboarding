import { describe, expect, it, vi } from "vitest";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { DashboardView } from "./DashboardView";
import type { Dashboard } from "../api";

const navigateMock = vi.fn();
vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual<typeof import("react-router-dom")>("react-router-dom");
  return { ...actual, useNavigate: () => navigateMock };
});

const dashboard: Dashboard = {
  processInstanceId: "proc-1",
  customerName: "Demo Kunde",
  overallProgress: 33,
  modules: [
    {
      moduleInstanceId: "mod-available",
      key: "software_inventory",
      name: "Software-Erfassung",
      explainer: "Erfassen Sie Ihre Systeme.",
      status: "available",
      progress: 0,
      responsibleRole: "IT-Verantwortlicher",
      estimatedEffort: "10–20 Minuten",
      locked: false,
      unlockHint: null,
      nextAction: "Modul starten",
    },
    {
      moduleInstanceId: "mod-locked",
      key: "tom_erfassung",
      name: "TOM-Erfassung",
      explainer: "Maßnahmen beschreiben.",
      status: "locked",
      progress: 0,
      responsibleRole: "IT-Verantwortlicher",
      estimatedEffort: "20–30 Minuten",
      locked: true,
      unlockHint: "Wird freigeschaltet nach Abschluss von: software_inventory",
      nextAction: null,
    },
  ],
};

function renderView() {
  return render(
    <MemoryRouter>
      <DashboardView dashboard={dashboard} />
    </MemoryRouter>,
  );
}

describe("DashboardView", () => {
  it("renders greeting and overall progress", () => {
    renderView();
    expect(screen.getByText("Demo Kunde")).toBeInTheDocument();
    expect(screen.getByText("33%")).toBeInTheDocument();
  });

  it("renders a card per module from the DTO", () => {
    renderView();
    expect(screen.getByText("Software-Erfassung")).toBeInTheDocument();
    expect(screen.getByText("TOM-Erfassung")).toBeInTheDocument();
  });

  it("shows the lock hint and a disabled CTA for a locked module", () => {
    renderView();
    expect(
      screen.getByText("Wird freigeschaltet nach Abschluss von: software_inventory"),
    ).toBeInTheDocument();
    const lockedCard = screen.getByText("TOM-Erfassung").closest(".card") as HTMLElement;
    expect(within(lockedCard).getByRole("button")).toBeDisabled();
  });

  it("navigates to the module when an available CTA is clicked", async () => {
    navigateMock.mockClear();
    renderView();
    const card = screen.getByText("Software-Erfassung").closest(".card") as HTMLElement;
    await userEvent.click(within(card).getByRole("button", { name: "Modul starten" }));
    expect(navigateMock).toHaveBeenCalledWith("/modules/mod-available");
  });

  it("does not navigate from a locked module CTA", async () => {
    navigateMock.mockClear();
    renderView();
    const card = screen.getByText("TOM-Erfassung").closest(".card") as HTMLElement;
    const btn = within(card).getByRole("button");
    await userEvent.click(btn).catch(() => undefined);
    expect(navigateMock).not.toHaveBeenCalled();
  });
});
