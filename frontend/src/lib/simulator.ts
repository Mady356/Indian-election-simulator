import { DATA_URLS } from "./constants";
import type { DataQualityLabel } from "./data";
import { constituencyLookupKey } from "./data";

export type SimulationCompleteness = "full" | "limited";
export type ProjectionConfidence = "high" | "medium" | "low";

export interface PartyShare {
  party: string;
  vote_share: number;
}

export interface SimulationBaseRecord {
  state: string;
  constituency: string;
  state_key: string;
  constituency_key: string;
  winner_2019?: string | null;
  winner_2024?: string | null;
  winner_party_2019?: string | null;
  winner_party_2024?: string | null;
  bjp_vote_share_2019?: number | null;
  bjp_vote_share_2024?: number | null;
  inc_vote_share_2019?: number | null;
  inc_vote_share_2024?: number | null;
  margin_2024?: number | null;
  turnout_2024?: number | null;
  data_quality_label: DataQualityLabel;
  nfhs5_coverage_share?: number | null;
  simulation_completeness: SimulationCompleteness;
  simulation_notes?: string;
  available_party_vote_shares_2024?: Record<string, number> | null;
  top_parties_2024?: PartyShare[] | null;
}

export interface SimulationBaseBundle {
  meta: {
    generated_at: string;
    constituency_count: number;
    full_completeness_count: number;
    limited_completeness_count: number;
    results_source?: string | null;
  };
  constituencies: SimulationBaseRecord[];
}

export interface StateSwingOverride {
  bjp?: number;
  inc?: number;
  others?: number;
}

export interface ScenarioInputs {
  bjpSwing: number;
  incSwing: number;
  othersSwing: number;
  turnoutChange: number;
  stateFilter: string | null;
  onlySelectedStates: boolean;
  includeLowQuality: boolean;
  stateSwings?: Record<string, StateSwingOverride>;
}

export interface ProjectedConstituency {
  state: string;
  constituency: string;
  state_key: string;
  constituency_key: string;
  winner_party_2024?: string | null;
  projected_winner: string;
  projected_bjp_share: number | null;
  projected_inc_share: number | null;
  projected_margin: number | null;
  winner_changed: boolean;
  projection_confidence: ProjectionConfidence;
  simulation_completeness: SimulationCompleteness;
  data_quality_label: DataQualityLabel;
  limited_projection_note?: string;
}

export interface ScenarioSummary {
  projected_bjp_seats: number;
  projected_inc_seats: number;
  projected_other_seats: number;
  seats_changed_from_2024: number;
  low_confidence_projections: number;
  constituencies_simulated: number;
  average_bjp_swing_applied: number;
  average_inc_swing_applied: number;
  average_others_swing_applied: number;
}

export interface ScenarioResult {
  summary: ScenarioSummary;
  projections: ProjectedConstituency[];
}

const DEFAULT_SCENARIO: ScenarioInputs = {
  bjpSwing: 0,
  incSwing: 0,
  othersSwing: 0,
  turnoutChange: 0,
  stateFilter: null,
  onlySelectedStates: false,
  includeLowQuality: true,
};

export function defaultScenarioInputs(): ScenarioInputs {
  return { ...DEFAULT_SCENARIO };
}

export async function loadSimulationBase(): Promise<SimulationBaseBundle | null> {
  try {
    const res = await fetch(DATA_URLS.simulationBase);
    if (!res.ok) return null;
    return (await res.json()) as SimulationBaseBundle;
  } catch {
    return null;
  }
}

export function clampVoteShares(shares: Record<string, number>): Record<string, number> {
  const clamped: Record<string, number> = {};
  for (const [party, value] of Object.entries(shares)) {
    clamped[party] = Math.max(0, Math.min(100, value));
  }
  return clamped;
}

export function renormalizeVoteShares(shares: Record<string, number>): Record<string, number> {
  const total = Object.values(shares).reduce((sum, value) => sum + value, 0);
  if (total <= 0) return shares;
  const normalized: Record<string, number> = {};
  for (const [party, value] of Object.entries(shares)) {
    normalized[party] = (value / total) * 100;
  }
  return normalized;
}

export function applyUniformSwing(
  shares: Record<string, number>,
  party: string,
  swing: number,
): Record<string, number> {
  if (!swing) return { ...shares };
  const next = { ...shares };
  next[party] = (next[party] ?? 0) + swing;
  return next;
}

export function applyStateSwing(
  shares: Record<string, number>,
  base: SimulationBaseRecord,
  inputs: ScenarioInputs,
): Record<string, number> {
  const override = inputs.stateSwings?.[base.state_key] ?? inputs.stateSwings?.[base.state];
  if (!override) return shares;

  let next = { ...shares };
  if (override.bjp) next = applyUniformSwing(next, "BJP", override.bjp);
  if (override.inc) next = applyUniformSwing(next, "INC", override.inc);
  if (override.others) {
    next = applyOthersSwing(next, override.others);
  }
  return next;
}

function applyOthersSwing(shares: Record<string, number>, swing: number): Record<string, number> {
  if (!swing) return shares;
  const next = { ...shares };
  for (const party of Object.keys(next)) {
    if (party !== "BJP" && party !== "INC") {
      next[party] = (next[party] ?? 0) + swing;
    }
  }
  return next;
}

function buildLimitedShares(base: SimulationBaseRecord): Record<string, number> {
  const bjp = base.bjp_vote_share_2024 ?? 0;
  const inc = base.inc_vote_share_2024 ?? 0;
  const winner = (base.winner_party_2024 || "OTHERS").toUpperCase();
  let others = Math.max(0, 100 - bjp - inc);

  const shares: Record<string, number> = { BJP: bjp, INC: inc };
  if (winner === "BJP" || winner === "INC") {
    shares.OTHERS = others;
  } else {
    shares[winner] = others;
  }
  return shares;
}

function buildBaseShares(base: SimulationBaseRecord): Record<string, number> {
  if (base.available_party_vote_shares_2024 && Object.keys(base.available_party_vote_shares_2024).length > 0) {
    return { ...base.available_party_vote_shares_2024 };
  }
  return buildLimitedShares(base);
}

export function calculateProjectedWinner(shares: Record<string, number>): string {
  let winner = "UNKNOWN";
  let top = -1;
  for (const [party, value] of Object.entries(shares)) {
    if (value > top) {
      top = value;
      winner = party;
    }
  }
  return winner;
}

function calculateMargin(shares: Record<string, number>): number | null {
  const ranked = Object.values(shares).sort((a, b) => b - a);
  if (ranked.length < 2) return ranked[0] ?? null;
  return ranked[0] - ranked[1];
}

function projectionConfidence(
  base: SimulationBaseRecord,
  shares: Record<string, number>,
): ProjectionConfidence {
  if (base.simulation_completeness === "full" && base.margin_2024 != null) {
    return "high";
  }
  if (base.top_parties_2024 && base.top_parties_2024.length >= 2) {
    return "medium";
  }
  if (Object.keys(shares).length > 2) {
    return "medium";
  }
  return "low";
}

function shouldSimulate(base: SimulationBaseRecord, inputs: ScenarioInputs): boolean {
  if (inputs.onlySelectedStates && inputs.stateFilter && base.state !== inputs.stateFilter) {
    return false;
  }
  if (
    !inputs.includeLowQuality &&
    (base.data_quality_label === "election_only" || base.data_quality_label === "low")
  ) {
    return false;
  }
  return true;
}

function projectConstituency(base: SimulationBaseRecord, inputs: ScenarioInputs): ProjectedConstituency | null {
  if (!shouldSimulate(base, inputs)) return null;

  let shares = buildBaseShares(base);
  shares = applyUniformSwing(shares, "BJP", inputs.bjpSwing);
  shares = applyUniformSwing(shares, "INC", inputs.incSwing);
  shares = applyOthersSwing(shares, inputs.othersSwing);
  shares = applyStateSwing(shares, base, inputs);
  shares = clampVoteShares(shares);
  shares = renormalizeVoteShares(shares);

  const projectedWinner = calculateProjectedWinner(shares);
  const winner2024 = (base.winner_party_2024 || "").toUpperCase();
  const confidence = projectionConfidence(base, shares);

  return {
    state: base.state,
    constituency: base.constituency,
    state_key: base.state_key,
    constituency_key: base.constituency_key,
    winner_party_2024: base.winner_party_2024,
    projected_winner: projectedWinner,
    projected_bjp_share: shares.BJP ?? null,
    projected_inc_share: shares.INC ?? null,
    projected_margin: calculateMargin(shares),
    winner_changed: winner2024 !== projectedWinner,
    projection_confidence: confidence,
    simulation_completeness: base.simulation_completeness,
    data_quality_label: base.data_quality_label,
    limited_projection_note:
      base.simulation_completeness === "limited"
        ? "Simulation available with limited confidence because full party vote shares are not available for this constituency."
        : undefined,
  };
}

export function summarizeScenario(projections: ProjectedConstituency[], inputs: ScenarioInputs): ScenarioSummary {
  const bjpSeats = projections.filter((p) => p.projected_winner === "BJP").length;
  const incSeats = projections.filter((p) => p.projected_winner === "INC").length;
  const otherSeats = projections.length - bjpSeats - incSeats;

  return {
    projected_bjp_seats: bjpSeats,
    projected_inc_seats: incSeats,
    projected_other_seats: otherSeats,
    seats_changed_from_2024: projections.filter((p) => p.winner_changed).length,
    low_confidence_projections: projections.filter((p) => p.projection_confidence === "low").length,
    constituencies_simulated: projections.length,
    average_bjp_swing_applied: inputs.bjpSwing,
    average_inc_swing_applied: inputs.incSwing,
    average_others_swing_applied: inputs.othersSwing,
  };
}

export function runScenario(
  base: SimulationBaseRecord[],
  inputs: ScenarioInputs,
): ScenarioResult {
  const projections = base
    .map((record) => projectConstituency(record, inputs))
    .filter((record): record is ProjectedConstituency => record != null);

  return {
    summary: summarizeScenario(projections, inputs),
    projections,
  };
}

export function lookupProjection(
  projections: ProjectedConstituency[],
  stateKey: string,
  constituencyKey: string,
): ProjectedConstituency | undefined {
  const key = constituencyLookupKey(stateKey, constituencyKey);
  return projections.find(
    (p) => constituencyLookupKey(p.state_key, p.constituency_key) === key,
  );
}

export function formatConfidenceLabel(confidence: ProjectionConfidence): string {
  return confidence.charAt(0).toUpperCase() + confidence.slice(1);
}

export function formatSwingLabel(value: number): string {
  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(1)} pp`;
}
