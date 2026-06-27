import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QuestionField } from "./QuestionField";
import type { Question } from "../api";
import * as api from "../api";

vi.mock("../api", async () => {
  const actual = await vi.importActual<typeof import("../api")>("../api");
  return { ...actual, aiSuggest: vi.fn(), uploadFile: vi.fn() };
});

function makeQuestion(overrides: Partial<Question>): Question {
  return {
    key: "q",
    label: "Frage",
    type: "text",
    required: false,
    visible: true,
    ...overrides,
  };
}

function renderField(q: Question, value: unknown, onChange = vi.fn()) {
  render(
    <QuestionField
      question={q}
      stepInstanceId="step-1"
      value={value}
      errors={[]}
      warnings={[]}
      onChange={onChange}
    />,
  );
  return onChange;
}

describe("QuestionField", () => {
  beforeEach(() => vi.clearAllMocks());

  it("renders a radio group for single_select", () => {
    renderField(makeQuestion({ type: "single_select", options: ["ja", "nein"] }), undefined);
    expect(screen.getAllByRole("radio")).toHaveLength(2);
  });

  it("emits a string value for single_select", async () => {
    const onChange = renderField(
      makeQuestion({ type: "single_select", options: ["ja", "nein"] }),
      undefined,
    );
    await userEvent.click(screen.getByLabelText("ja"));
    expect(onChange).toHaveBeenCalledWith("ja");
  });

  it("renders checkboxes for multi_select and emits a string[] value", async () => {
    const onChange = renderField(
      makeQuestion({ type: "multi_select", options: ["A", "B"] }),
      [],
    );
    expect(screen.getAllByRole("checkbox")).toHaveLength(2);
    await userEvent.click(screen.getByLabelText("A"));
    expect(onChange).toHaveBeenCalledWith(["A"]);
  });

  it("renders a textarea for text", async () => {
    const onChange = renderField(makeQuestion({ type: "text" }), "");
    const ta = screen.getByRole("textbox");
    await userEvent.type(ta, "hi");
    expect(onChange).toHaveBeenCalled();
  });

  it("renders an upload dropzone for file_upload", () => {
    renderField(makeQuestion({ type: "file_upload" }), undefined);
    expect(screen.getByText(/Datei hierher ziehen/i)).toBeInTheDocument();
  });

  it("shows backend validation errors inline", () => {
    render(
      <QuestionField
        question={makeQuestion({ type: "text" })}
        stepInstanceId="s"
        value=""
        errors={[{ questionKey: "q", code: "required", message: "Pflichtfeld" }]}
        warnings={[]}
        onChange={vi.fn()}
      />,
    );
    expect(screen.getByText("Pflichtfeld")).toBeInTheDocument();
  });

  it("AI suggestion 'Übernehmen' sets the value and marks it ai-suggested", async () => {
    (api.aiSuggest as ReturnType<typeof vi.fn>).mockResolvedValue({
      id: "s1",
      proposedValue: "Microsoft 365",
      confidence: 0.6,
      openQuestions: [],
    });
    const onChange = vi.fn();
    render(
      <QuestionField
        question={makeQuestion({ type: "multi_select", options: ["Microsoft 365"], aiHelpEnabled: true })}
        stepInstanceId="s"
        value={[]}
        errors={[]}
        warnings={[]}
        onChange={onChange}
      />,
    );
    await userEvent.click(screen.getByRole("button", { name: "Vorschlag" }));
    const apply = await screen.findByRole("button", { name: "Übernehmen" });
    await userEvent.click(apply);
    // multi_select coerces a scalar proposal into a string[].
    expect(onChange).toHaveBeenCalledWith(["Microsoft 365"], { aiSuggested: true });
  });

  it("shows the origin badge when the answer was ai-suggested", () => {
    renderField(
      makeQuestion({
        type: "text",
        answer: { id: "a", questionKey: "q", value: "x", aiSuggested: true },
      }),
      "x",
    );
    expect(screen.getByText(/KI-Vorschlag/)).toBeInTheDocument();
  });
});
