import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { TemplateList } from "./TemplateList";
import type { Template } from "../api";
import * as api from "../api";

vi.mock("../api", async () => {
  const actual = await vi.importActual<typeof import("../api")>("../api");
  return { ...actual, getTemplate: vi.fn(), downloadTemplateFile: vi.fn() };
});

const emailTemplate: Template = {
  key: "software_vendor_email",
  type: "email",
  title: "E-Mail an Anbieter",
  subject: "Rückfragen",
  body: "Sehr geehrte Damen und Herren",
};

const fileTemplate: Template = {
  key: "software_vendor_questionnaire",
  type: "file",
  title: "Fragebogen",
  fileName: "fragebogen.docx",
  fileType: "docx",
};

describe("TemplateList", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (api.getTemplate as ReturnType<typeof vi.fn>).mockResolvedValue(emailTemplate);
    Object.assign(navigator, {
      clipboard: { writeText: vi.fn().mockResolvedValue(undefined) },
    });
  });

  it("copies subject + body to the clipboard for an email template", async () => {
    render(<TemplateList templates={[emailTemplate]} moduleInstanceId="m1" />);
    await userEvent.click(screen.getByRole("button", { name: "Kopieren" }));
    expect(navigator.clipboard.writeText).toHaveBeenCalledWith(
      expect.stringContaining("Rückfragen"),
    );
    expect(navigator.clipboard.writeText).toHaveBeenCalledWith(
      expect.stringContaining("Sehr geehrte Damen und Herren"),
    );
  });

  it("downloads a file template via the authed client helper", async () => {
    render(<TemplateList templates={[fileTemplate]} />);
    await userEvent.click(screen.getByRole("button", { name: "Herunterladen" }));
    expect(api.downloadTemplateFile).toHaveBeenCalledWith(
      "software_vendor_questionnaire",
      "fragebogen.docx",
    );
  });
});
