interface SpinnerProps {
  center?: boolean;
  label?: string;
}

export function Spinner({ center = false, label = "Lädt…" }: SpinnerProps) {
  return (
    <span className={center ? "spinner spinner--center" : "spinner"} role="status">
      <span className="visually-hidden">{label}</span>
    </span>
  );
}
