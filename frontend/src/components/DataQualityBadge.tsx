import { QUALITY_LABELS } from "@/lib/constants";
import { qualityBadgeClass } from "@/lib/format";

export function DataQualityBadge({ label }: { label?: string | null }) {
  if (!label) return null;
  const text = QUALITY_LABELS[label] || label;
  return (
    <span
      className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium ${qualityBadgeClass(label)}`}
    >
      {text}
    </span>
  );
}
