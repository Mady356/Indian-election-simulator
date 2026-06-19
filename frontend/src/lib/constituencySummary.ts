import type { ConstituencyRecord } from "./data";
import { hasDemographics } from "./data";

export function turnoutChange(record: ConstituencyRecord): number | null {
  if (record.turnout_2019 == null || record.turnout_2024 == null) return null;
  return record.turnout_2024 - record.turnout_2019;
}

export function marginChange(record: ConstituencyRecord): number | null {
  if (record.margin_2019 == null || record.margin_2024 == null) return null;
  return record.margin_2024 - record.margin_2019;
}

export function formatSwingPoints(value?: number | null, digits = 1): string {
  if (value == null || Number.isNaN(value)) return "N/A";
  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(digits)} points`;
}

export function formatCoverageFraction(value?: number | null, digits = 1): string {
  if (value == null || Number.isNaN(value)) return "N/A";
  return `${(value * 100).toFixed(digits)}%`;
}

export function buildConstituencySummary(record: ConstituencyRecord): string {
  if (!hasDemographics(record)) {
    return "Election results are available. Demographic indicators are currently unavailable for this constituency.";
  }

  const party2024 = record.winner_party_2024 || "the winning party";
  const bjpSwing = formatSwingPoints(record.bjp_swing_2019_2024);
  const incSwing = formatSwingPoints(record.inc_swing_2019_2024);

  if (record.winner_changed) {
    const party2019 = record.winner_party_2019 || "another party";
    return `${record.constituency} flipped from ${party2019} to ${party2024} in 2024, with BJP vote share changing by ${bjpSwing} and INC vote share changing by ${incSwing}.`;
  }

  return `${record.constituency} remained with ${party2024} in 2024, with BJP vote share changing by ${bjpSwing} and INC vote share changing by ${incSwing}.`;
}
