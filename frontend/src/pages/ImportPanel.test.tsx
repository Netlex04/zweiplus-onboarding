import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ImportPanel } from "./ImportPanel";
import type { ImportPreview } from "../api";
import * as api from "../api";

vi.mock("../api", async () => {
  const actual = await vi.importActual<typeof import("../api")>("../api");
  return {
    ...actual,
    generateCanonical: vi.fn(),
    getImportPreview: vi.fn(),
    createImportJob: vi.fn(),
    runImportJob: vi.fn(),
  };
});

const preview: ImportPreview = {
  targetSystem: "dpms_v1",
  mappedObjects: [{ type: "system", name: "Microsoft 365" }],
  unmappedFields: ["additional_notes"],
  warnings: ["Feld additional_notes nur als Freitext."],
  errors: [],
};

describe("ImportPanel", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (api.generateCanonical as ReturnType<typeof vi.fn>).mockResolvedValue({});
    (api.getImportPreview as ReturnType<typeof vi.fn>).mockResolvedValue(preview);
    (api.createImportJob as ReturnType<typeof vi.fn>).mockResolvedValue({ id: "job-1", status: "mapping_ready" });
    (api.runImportJob as ReturnType<typeof vi.fn>).mockResolvedValue({ id: "job-1", status: "imported", errors: [] });
  });

  it("renders mapped objects, unmapped fields and warnings", async () => {
    render(<ImportPanel moduleInstanceId="mod-1" initialStatus="completed" />);
    await userEvent.click(screen.getByRole("button", { name: "Importvorschau erstellen" }));
    expect(await screen.findByText(/Gemappte Objekte/)).toBeInTheDocument();
    expect(screen.getByText(/Microsoft 365/)).toBeInTheDocument();
    expect(screen.getByText("additional_notes")).toBeInTheDocument();
    expect(screen.getByText(/nur als Freitext/)).toBeInTheDocument();
  });

  it("runs the import job through to imported", async () => {
    render(<ImportPanel moduleInstanceId="mod-1" initialStatus="completed" />);
    await userEvent.click(screen.getByRole("button", { name: "Importvorschau erstellen" }));
    await screen.findByText(/Gemappte Objekte/);
    await userEvent.click(screen.getByRole("button", { name: "Import starten" }));
    await waitFor(() => {
      expect(api.createImportJob).toHaveBeenCalledWith("mod-1", "dpms_v1");
      expect(api.runImportJob).toHaveBeenCalledWith("job-1");
    });
    expect(await screen.findByText(/Import abgeschlossen/)).toBeInTheDocument();
  });
});
