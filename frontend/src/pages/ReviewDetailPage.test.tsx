import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { ReviewDetailPage } from "./ReviewDetailPage";
import type { ReviewView } from "../api";
import * as api from "../api";

vi.mock("../api", async () => {
  const actual = await vi.importActual<typeof import("../api")>("../api");
  return {
    ...actual,
    getReviewModule: vi.fn(),
    approveModule: vi.fn(),
    requestModuleChanges: vi.fn(),
    patchReviewAnswer: vi.fn(),
  };
});

const view: ReviewView = {
  moduleInstanceId: "mod-1",
  moduleName: "Software-Erfassung",
  moduleStatus: "waiting_zweiplus",
  customerName: "Demo Kunde",
  reviewStatus: "open",
  steps: [
    {
      stepInstanceId: "step-1",
      title: "Grunddaten",
      backendValidation: { passed: true, errors: [], warnings: [] },
      aiValidation: {
        id: "v1",
        passed: true,
        checks: [{ question: "used_software", ok: true, note: "plausibel" }],
        issues: [],
      },
      questions: [
        {
          key: "used_software",
          label: "Welche Software?",
          answer: {
            id: "ans-1",
            questionKey: "used_software",
            value: ["Microsoft 365"],
            source: "user",
            aiSuggested: false,
          },
          aiSuggestions: [],
        },
      ],
    },
  ],
};

function renderDetail() {
  render(
    <MemoryRouter initialEntries={["/review/mod-1"]}>
      <Routes>
        <Route path="/review/:moduleInstanceId" element={<ReviewDetailPage />} />
        <Route path="/review" element={<div>Aufgabenliste</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("ReviewDetailPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (api.getReviewModule as ReturnType<typeof vi.fn>).mockResolvedValue(view);
    (api.approveModule as ReturnType<typeof vi.fn>).mockResolvedValue({});
    (api.requestModuleChanges as ReturnType<typeof vi.fn>).mockResolvedValue({});
    (api.patchReviewAnswer as ReturnType<typeof vi.fn>).mockResolvedValue({});
  });

  it("renders answers with provenance and validations", async () => {
    renderDetail();
    expect(await screen.findByText("Welche Software?")).toBeInTheDocument();
    expect(screen.getByText("Microsoft 365")).toBeInTheDocument();
    expect(screen.getByText("Kunde")).toBeInTheDocument(); // source badge
    expect(screen.getByText(/Backend-Validierung: bestanden/)).toBeInTheDocument();
    expect(screen.getByText(/plausibel/)).toBeInTheDocument();
  });

  it("calls approveModule on Freigeben", async () => {
    renderDetail();
    await screen.findByText("Welche Software?");
    await userEvent.click(screen.getByRole("button", { name: "Freigeben" }));
    await waitFor(() => expect(api.approveModule).toHaveBeenCalledWith("mod-1"));
  });

  it("calls requestModuleChanges with notes", async () => {
    renderDetail();
    await screen.findByText("Welche Software?");
    await userEvent.type(screen.getByLabelText(/Hinweis bei Rückgabe/), "Bitte ergänzen");
    await userEvent.click(screen.getByRole("button", { name: "Zur Korrektur zurückgeben" }));
    await waitFor(() =>
      expect(api.requestModuleChanges).toHaveBeenCalledWith("mod-1", "Bitte ergänzen"),
    );
  });

  it("patches an edited answer", async () => {
    renderDetail();
    await screen.findByText("Welche Software?");
    await userEvent.click(screen.getByRole("button", { name: "Bearbeiten" }));
    const input = screen.getByLabelText(/Antwort bearbeiten/);
    await userEvent.clear(input);
    await userEvent.type(input, "DATEV");
    await userEvent.click(screen.getByRole("button", { name: "Speichern" }));
    await waitFor(() =>
      // array answer stays an array
      expect(api.patchReviewAnswer).toHaveBeenCalledWith("ans-1", ["DATEV"]),
    );
  });
});
