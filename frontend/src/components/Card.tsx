import type { HTMLAttributes, ReactNode } from "react";

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  interactive?: boolean;
  muted?: boolean;
  children: ReactNode;
}

export function Card({
  interactive = false,
  muted = false,
  className = "",
  children,
  ...rest
}: CardProps) {
  const classes = [
    "card",
    interactive ? "card--interactive" : "",
    muted ? "card--muted" : "",
    className,
  ]
    .filter(Boolean)
    .join(" ");
  return (
    <div className={classes} {...rest}>
      {children}
    </div>
  );
}
