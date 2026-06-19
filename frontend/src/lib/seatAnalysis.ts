import { DATA_URLS } from "./constants";
import { constituencyLookupKey } from "./data";
import type { DataQualityLabel } from "./data";

export type SeatAnalysisSource = "generated" | "manual" | "mixed";

export interface SeatAnalysisRecord {
  state: string;
  constituency: string;
  state_key: string;
  constituency_key: string;
  summary: string;
  electoral_movement: string;
  key_factors: string;
  demographic_context: string;
  district_context: string;
  local_context?: string;
  what_to_watch: string;
  confidence: string;
  data_quality_note: string;
  analysis_source: SeatAnalysisSource;
  data_quality_label?: DataQualityLabel;
  last_updated?: string;
}

const KEY_FACTOR_LABELS: Record<string, string> = {
  seat_flip: "Seat flip",
  close_contest_2024: "Close contest (2024)",
  large_bjp_gain: "Large BJP gain",
  large_bjp_loss: "Large BJP loss",
  large_inc_gain: "Large INC gain",
  large_inc_loss: "Large INC loss",
  high_turnout_change: "High turnout change",
  urban_profile: "Urban profile",
  rural_profile: "Rural profile",
  high_demographic_coverage: "High demographic coverage",
  low_demographic_coverage: "Low demographic coverage",
  election_only_profile: "Election-only profile",
  district_coverage_gap: "District coverage gap",
};

export function formatKeyFactor(tag: string): string {
  const trimmed = tag.trim();
  if (!trimmed) return "";
  if (KEY_FACTOR_LABELS[trimmed]) return KEY_FACTOR_LABELS[trimmed];
  return trimmed
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

export function parseKeyFactors(value?: string | null): string[] {
  if (!value?.trim()) return [];
  return value
    .split(";")
    .map((tag) => tag.trim())
    .filter(Boolean);
}

export function analysisSourceLabel(source?: SeatAnalysisSource | string | null): string {
  switch (source) {
    case "manual":
      return "Manual";
    case "mixed":
      return "Mixed";
    case "generated":
    default:
      return "Generated";
  }
}

export async function loadSeatAnalysis(): Promise<Map<string, SeatAnalysisRecord>> {
  try {
    const res = await fetch(DATA_URLS.seatAnalysis);
    if (!res.ok) return new Map();
    const raw = (await res.json()) as Record<string, SeatAnalysisRecord>;
    return new Map(Object.entries(raw));
  } catch {
    return new Map();
  }
}

export function getSeatAnalysis(
  lookup: Map<string, SeatAnalysisRecord>,
  stateKey: string,
  constituencyKey: string,
): SeatAnalysisRecord | undefined {
  return lookup.get(constituencyLookupKey(stateKey, constituencyKey));
}
