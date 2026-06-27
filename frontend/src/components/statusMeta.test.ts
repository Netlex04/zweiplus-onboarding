import { describe, expect, it } from "vitest";
import { moduleStatusMeta } from "./statusMeta";
import type { PillVariant } from "./statusMeta";
import type { ModuleStatus } from "../api";

describe("moduleStatusMeta", () => {
  const cases: [ModuleStatus, PillVariant][] = [
    ["completed", "success"],
    ["import_ready", "success"],
    ["imported", "success"],
    ["in_progress", "info"],
    ["waiting_customer", "info"],
    ["waiting_zweiplus", "info"],
    ["backend_validation_failed", "danger"],
    ["ai_check_pending", "warning"],
    ["locked", "neutral"],
    ["available", "neutral"],
    ["not_started", "neutral"],
  ];

  it.each(cases)("maps %s -> %s variant", (status, variant) => {
    expect(moduleStatusMeta(status as ModuleStatus).variant).toBe(variant);
  });

  it("always provides a non-empty human label", () => {
    for (const [status] of cases) {
      expect(moduleStatusMeta(status).label.length).toBeGreaterThan(0);
    }
  });
});
