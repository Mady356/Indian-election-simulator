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
  if (value == null || Number.isNaN(value)) return "—";
  return `${value.toFixed(digits)}%`;
}

export function formatNumber(value?: number | null): string {
  if (value == null || Number.isNaN(value)) return "—";
  return new Intl.NumberFormat("en-IN").format(Math.round(value));
}

export function partyColor(party?: string | null): string {
  const p = (party || "").toUpperCase();
  if (p.includes("BJP")) return "#FF9933";
  if (p.includes("INC") || p === "CONGRESS") return "#19AAED";
  if (p.includes("TDP")) return "#FFFF00";
  if (p.includes("YSRCP") || p.includes("YSR")) return "#006400";
  if (p.includes("AAP")) return "#0072BC";
  if (p.includes("CPI")) return "#FF0000";
  if (p.includes("DMK")) return "#000000";
  if (p.includes("AITC") || p.includes("TMC")) return "#20C997";
  return "#4F8CFF";
}

export function matchStateName(a: string, b: string): boolean {
  return normalizeKey(a) === normalizeKey(b);
}

export function parseCsv(text: string): Record<string, string>[] {
  const lines = text.trim().split("\n");
  if (lines.length < 2) return [];
  const headers = lines[0].split(",").map((h) => h.trim());
  return lines.slice(1).map((line) => {
    const values: string[] = [];
    let current = "";
    let inQuotes = false;
    for (const ch of line) {
      if (ch === '"') {
        inQuotes = !inQuotes;
      } else if (ch === "," && !inQuotes) {
        values.push(current.trim());
        current = "";
      } else {
        current += ch;
      }
    }
    values.push(current.trim());
    const row: Record<string, string> = {};
    headers.forEach((h, i) => {
      row[h] = values[i] ?? "";
    });
    return row;
  });
}
