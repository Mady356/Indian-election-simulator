import type { ReactNode } from "react";

export function MetricCard({
  label,
  value,
  hint,
  accent,
}: {
  label: string;
  value: ReactNode;
  hint?: string;
  accent?: "primary" | "accent" | "warning" | "danger";
}) {
  const accentClass =
    accent === "accent"
      ? "text-accent"
      : accent === "warning"
        ? "text-warning"
        : accent === "danger"
          ? "text-danger"
          : "text-primary";

  return (
    <div className="rounded-xl border border-border bg-card p-4 shadow-card">
      <div className="text-xs font-medium uppercase tracking-wide text-muted">{label}</div>
      <div className={`mt-2 text-2xl font-semibold tabular-nums ${accentClass}`}>{value}</div>
      {hint ? <div className="mt-1 text-xs text-muted">{hint}</div> : null}
    </div>
  );
}
