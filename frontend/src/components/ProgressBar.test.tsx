import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { ProgressBar } from "./ProgressBar";

describe("ProgressBar", () => {
  it("renders an accessible progressbar with the clamped value", () => {
    render(<ProgressBar value={42} />);
    const bar = screen.getByRole("progressbar");
    expect(bar).toHaveAttribute("aria-valuenow", "42");
    expect(bar).toHaveAttribute("aria-valuemin", "0");
    expect(bar).toHaveAttribute("aria-valuemax", "100");
  });

  it("sets the fill width to the percentage", () => {
    const { container } = render(<ProgressBar value={75} />);
    const fill = container.querySelector(".progress__fill") as HTMLElement;
    expect(fill.style.width).toBe("75%");
  });

  it("clamps out-of-range values", () => {
    const { container, rerender } = render(<ProgressBar value={-10} />);
    expect(screen.getByRole("progressbar")).toHaveAttribute("aria-valuenow", "0");
    rerender(<ProgressBar value={150} />);
    const fill = container.querySelector(".progress__fill") as HTMLElement;
    expect(fill.style.width).toBe("100%");
  });
});
