import type { PillVariant } from "./statusMeta";

const VARIANT_ICON: Record<PillVariant, string> = {
  success: "✓",
  info: "•",
  neutral: "•",
  danger: "!",
  warning: "!",
};

interface StatusPillProps {
  variant: PillVariant;
  label: string;
  /** Optional leading icon override (e.g. a lock for locked modules). */
  icon?: string;
}

/**
 * Status is never communicated by color alone — the pill always carries a
 * text label plus an icon (design-system §7).
 */
export function StatusPill({ variant, label, icon }: StatusPillProps) {
  return (
    <span className={`pill pill--${variant}`}>
      <span className="pill__icon" aria-hidden="true">
        {icon ?? VARIANT_ICON[variant]}
      </span>
      {label}
    </span>
  );
}
