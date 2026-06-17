import { COLORS } from "./constants";

export function normalizeKey(value: string): string {
  return value
    .toUpperCase()
    .replace(/&/g, " AND ")
    .replace(/[–—\-/]/g, " ")
    .replace(/\((SC|ST)\)/gi, "")
    .replace(/[^A-Z0-9]+/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

export function titleCase(value: string): string {
  return value
    .split(/\s+/)
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase())
    .join(" ");
}

export function formatPct(value?: number | null, digits = 1): string {
  if (value == null || Number.isNaN(value)) return "N/A";
  return `${value.toFixed(digits)}%`;
}

export function formatSwing(value?: number | null, digits = 1): string {
  if (value == null || Number.isNaN(value)) return "N/A";
  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(digits)} pp`;
}

export function formatNumber(value?: number | null, digits = 0): string {
  if (value == null || Number.isNaN(value)) return "N/A";
  if (digits > 0) return value.toFixed(digits);
  return new Intl.NumberFormat("en-IN").format(Math.round(value));
}

export function formatShare(value?: number | null, digits = 1): string {
  if (value == null || Number.isNaN(value)) return "N/A";
  return `${value.toFixed(digits)}%`;
}

export function partyColor(party?: string | null): string {
  const p = (party || "").toUpperCase();
  if (p.includes("BJP")) return "#FF9933";
  if (p.includes("INC") || p === "CONGRESS") return "#19AAED";
  if (p.includes("TDP")) return "#EAB308";
  if (p.includes("YSRCP") || p.includes("YSR")) return "#16A34A";
  if (p.includes("AAP")) return "#0072BC";
  if (p.includes("CPI")) return "#EF4444";
  if (p.includes("DMK")) return "#111827";
  if (p.includes("AITC") || p.includes("TMC")) return "#20C997";
  if (p.includes("SP")) return "#DC2626";
  if (p.includes("BJD")) return "#059669";
  return COLORS.primary;
}

export function swingColor(value?: number | null): string {
  if (value == null || Number.isNaN(value)) return COLORS.muted;
  if (value >= 10) return COLORS.accent;
  if (value >= 0) return "#86EFAC";
  if (value >= -10) return COLORS.warning;
  return COLORS.danger;
}

export function coverageColor(label?: string | null): string {
  switch (label) {
    case "high":
      return COLORS.accent;
    case "medium":
      return COLORS.primary;
    case "low":
      return COLORS.warning;
    default:
      return "#334155";
  }
}

export function qualityBadgeClass(label?: string | null): string {
  switch (label) {
    case "high":
      return "bg-accent/15 text-accent border-accent/30";
    case "medium":
      return "bg-primary/15 text-primary border-primary/30";
    case "low":
      return "bg-warning/15 text-warning border-warning/30";
    default:
      return "bg-muted/15 text-muted border-border";
  }
}

export function featureLabel(name: string): string {
  return name
    .replace(/_nfhs5$/, "")
    .replace(/_change$/, " change")
    .replace(/_pct/g, " %")
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

export function routeStateKey(stateKey: string): string {
  return encodeURIComponent(stateKey);
}

export function routeConstituencyKey(constituencyKey: string): string {
  return encodeURIComponent(constituencyKey);
}

export function parseRouteKey(value: string): string {
  return decodeURIComponent(value);
}
