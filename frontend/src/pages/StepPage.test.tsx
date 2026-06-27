import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { StepPage } from "./StepPage";
import type { SaveAnswersResponse, StepDetail } from "../api";
import { ApiError } from "../api";
import * as api from "../api";

vi.mock("../api", async () => {
  const actual = await vi.importActual<typeof import("../api")>("../api");
  return {
    ...actual,
    getStep: vi.fn(),
    getModule: vi.fn(),
    saveStepAnswers: vi.fn(),
    completeStep: vi.fn(),
  };
});

const step: StepDetail = {
  stepInstanceId: "step-1",
  title: "Datenübermittlung",
  description: "Bitte ausfüllen.",
  status: "in_progress",
  templates: [],
  questions: [
    {
      key: "third_country",
      label: "Drittland?",
      type: "single_select",
      required: true,
      options: ["ja", "nein"],
      visible: true,
    },
    {
      key: "third_country_details",
      label: "Details",
      type: "text",
      required: false,
      visible: false, // hidden until third_country = ja
    },
  ],
};

function renderStep() {
  render(
    <MemoryRouter initialEntries={["/steps/step-1"]}>
      <Routes>
        <Route path="/steps/:stepInstanceId" element={<StepPage />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("StepPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (api.getStep as ReturnType<typeof vi.fn>).mockResolvedValue(step);
    (api.getModule as ReturnType<typeof vi.fn>).mockResolvedValue(null);
  });

  it("renders only visible questions", async () => {
    renderStep();
    expect(await screen.findByText("Drittland?")).toBeInTheDocument();
    expect(screen.queryByText("Details")).not.toBeInTheDocument();
  });

  it("renders inline validation errors from the save response", async () => {
    const resp: SaveAnswersResponse = {
      stepStatus: "incomplete",
      validation: {
        passed: false,
        errors: [{ questionKey: "third_country", code: "required", message: "Bitte wählen" }],
        warnings: [],
      },
    };
    (api.saveStepAnswers as ReturnType<typeof vi.fn>).mockResolvedValue(resp);
    renderStep();
    await screen.findByText("Drittland?");
    await userEvent.click(screen.getByRole("button", { name: "Speichern" }));
    expect(await screen.findByText("Bitte wählen")).toBeInTheDocument();
  });

  it("shows a hint when complete returns 409", async () => {
    (api.saveStepAnswers as ReturnType<typeof vi.fn>).mockResolvedValue({
      stepStatus: "complete",
      validation: { passed: true, errors: [], warnings: [] },
    });
    (api.completeStep as ReturnType<typeof vi.fn>).mockRejectedValue(
      new ApiError(409, "conflict", "Schritt unvollständig."),
    );
    renderStep();
    await screen.findByText("Drittland?");
    await userEvent.click(screen.getByRole("button", { name: "Schritt abschließen" }));
    await waitFor(() =>
      expect(screen.getByText(/Schritt unvollständig\./)).toBeInTheDocument(),
    );
  });

  it("re-fetches the step after saving so conditional fields appear", async () => {
    (api.saveStepAnswers as ReturnType<typeof vi.fn>).mockResolvedValue({
      stepStatus: "in_progress",
      validation: { passed: true, errors: [], warnings: [] },
    });
    // After saving, the backend reveals third_country_details.
    (api.getStep as ReturnType<typeof vi.fn>)
      .mockResolvedValueOnce(step)
      .mockResolvedValue({
        ...step,
        questions: step.questions.map((q) =>
          q.key === "third_country_details" ? { ...q, visible: true } : q,
        ),
      });
    renderStep();
    await screen.findByText("Drittland?");
    await userEvent.click(screen.getByRole("button", { name: "Speichern" }));
    expect(await screen.findByText("Details")).toBeInTheDocument();
  });
});
