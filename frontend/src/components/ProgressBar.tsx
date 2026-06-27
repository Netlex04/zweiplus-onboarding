interface ProgressBarProps {
  /** 0–100. Clamped defensively. */
  value: number;
  label?: string;
  showValue?: boolean;
}

export function ProgressBar({ value, label, showValue = true }: ProgressBarProps) {
  const clamped = Math.max(0, Math.min(100, Math.round(value)));
  const ariaLabel = label ?? "Fortschritt";
  return (
    <div className="progress">
      <div
        className="progress__track"
        role="progressbar"
        aria-valuenow={clamped}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={ariaLabel}
      >
        <div className="progress__fill" style={{ width: `${clamped}%` }} />
      </div>
      {showValue && (
        <span className="progress__label">
          {label ? `${label} · ` : ""}
          {clamped}%
        </span>
      )}
    </div>
  );
}
