import { AlertTriangle } from "lucide-react";

export function CoverageWarning({
  title = "Limited demographic coverage",
  message,
}: {
  title?: string;
  message: string;
}) {
  return (
    <div className="flex gap-3 rounded-xl border border-warning/30 bg-warning/10 p-4 text-sm">
      <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-warning" />
      <div>
        <div className="font-medium text-warning">{title}</div>
        <p className="mt-1 text-muted">{message}</p>
      </div>
    </div>
  );
}
