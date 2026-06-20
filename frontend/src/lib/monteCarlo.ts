import { DATA_URLS, COLORS } from "./constants";
import type { DataQualityLabel } from "./data";
import { constituencyLookupKey } from "./data";

export type SimulationCompleteness =
  | "full_party_shares"
  | "bjp_inc_limited"
  | "winner_margin_only";

export type ProjectionConfidence = "high" | "medium" | "low";
export type AllianceBucket = "NDA" | "INDIA" | "Others";

export interface PartyShare {
  party: string;
  vote_share: number;
}

export interface MonteCarloBaseRecord {
  state: string;
  constituency: string;
  state_key: string;
  constituency_key: string;
  winner_2024?: string | null;
  winner_party_2024?: string | null;
  bjp_vote_share_2024?: number | null;
  inc_vote_share_2024?: number | null;
  margin_2024?: number | null;
  turnout_2024?: number | null;
  data_quality_label: DataQualityLabel;
  party_vote_shares_2024?: Record<string, number> | null;
  top_parties_2024?: PartyShare[] | null;
  alliance_vote_shares_2024?: Record<string, number> | null;
  simulation_completeness: SimulationCompleteness;
}

export interface MonteCarloBaseBundle {
  meta: {
    generated_at: string;
    constituency_count: number;
    completeness_counts: Record<string, number>;
    majority_threshold: number;
    alliance_mapping_source?: string;
    results_source?: string | null;
  };
  alliance_mapping: Record<string, string>;
  constituencies: MonteCarloBaseRecord[];
}

export interface MonteCarloInputs {
  numSimulations: number;
  ndaSwing: number;
  indiaSwing: number;
  othersSwing: number;
  nationalSigma: number;
  stateSigma: number;
  seatSigma: number;
  stateFilter: string | null;
  onlySelectedState: boolean;
  includeLowConfidence: boolean;
  seed?: number | null;
}

export interface SeatSimulationStats {
  state: string;
  constituency: string;
  state_key: string;
  constituency_key: string;
  winner_party_2024?: string | null;
  winner_alliance_2024: AllianceBucket;
  most_common_simulated_winner: string;
  most_common_simulated_alliance: AllianceBucket;
  flip_probability: number;
  nda_win_probability: number;
  india_win_probability: number;
  others_win_probability: number;
  projection_confidence: ProjectionConfidence;
  simulation_completeness: SimulationCompleteness;
}

export interface MonteCarloSummary {
  simulations_run: number;
  nda_plurality_probability: number;
  india_plurality_probability: number;
  others_plurality_probability: number;
  nda_majority_probability: number;
  india_majority_probability: number;
  hung_parliament_probability: number;
  median_nda_seats: number;
  median_india_seats: number;
  median_others_seats: number;
  nda_seat_p10: number;
  nda_seat_p90: number;
  india_seat_p10: number;
  india_seat_p90: number;
  volatile_seat_count: number;
  timestamp: string;
}

export interface MonteCarloResult {
  summary: MonteCarloSummary;
  nda_seat_distribution: Array<{ seats: number; count: number }>;
  india_seat_distribution: Array<{ seats: number; count: number }>;
  others_seat_distribution: Array<{ seats: number; count: number }>;
  volatile_seats: SeatSimulationStats[];
  detail: {
    simulations_run: number;
    assumptions: MonteCarloInputs;
    seat_count_distribution: {
      nda: number[];
      india: number[];
      others: number[];
    };
    alliance_win_probabilities: {
      nda_plurality: number;
      india_plurality: number;
      others_plurality: number;
      nda_majority: number;
      india_majority: number;
      hung_parliament: number;
    };
    volatile_seats: SeatSimulationStats[];
    timestamp: string;
  };
}

const DEFAULT_INPUTS: MonteCarloInputs = {
  numSimulations: 1000,
  ndaSwing: 0,
  indiaSwing: 0,
  othersSwing: 0,
  nationalSigma: 2.5,
  stateSigma: 4.0,
  seatSigma: 6.0,
  stateFilter: null,
  onlySelectedState: false,
  includeLowConfidence: true,
  seed: null,
};

const MAJORITY_THRESHOLD = 272;

export function defaultMonteCarloInputs(): MonteCarloInputs {
  return { ...DEFAULT_INPUTS };
}

export async function loadMonteCarloBase(): Promise<MonteCarloBaseBundle | null> {
  try {
    const res = await fetch(DATA_URLS.monteCarloBase);
    if (!res.ok) return null;
    return (await res.json()) as MonteCarloBaseBundle;
  } catch {
    return null;
  }
}

function mulberry32(seed: number): () => number {
  let t = seed >>> 0;
  return () => {
    t += 0x6d2b79f5;
    let r = Math.imul(t ^ (t >>> 15), 1 | t);
    r ^= r + Math.imul(r ^ (r >>> 7), 61 | r);
    return ((r ^ (r >>> 14)) >>> 0) / 4294967296;
  };
}

function randomNormal(rng: () => number): number {
  let u = 0;
  let v = 0;
  while (u === 0) u = rng();
  while (v === 0) v = rng();
  return Math.sqrt(-2.0 * Math.log(u)) * Math.cos(2.0 * Math.PI * v);
}

export function addRandomError(rng: () => number, sigma: number): number {
  if (sigma <= 0) return 0;
  return randomNormal(rng) * sigma;
}

export function applySwing(shares: Record<AllianceBucket, number>, swings: Pick<MonteCarloInputs, "ndaSwing" | "indiaSwing" | "othersSwing">): Record<AllianceBucket, number> {
  return {
    NDA: (shares.NDA ?? 0) + swings.ndaSwing,
    INDIA: (shares.INDIA ?? 0) + swings.indiaSwing,
    Others: (shares.Others ?? 0) + swings.othersSwing,
  };
}

export function normalizeVoteShares(shares: Record<AllianceBucket, number>): Record<AllianceBucket, number> {
  const clamped: Record<AllianceBucket, number> = {
    NDA: Math.max(0, shares.NDA ?? 0),
    INDIA: Math.max(0, shares.INDIA ?? 0),
    Others: Math.max(0, shares.Others ?? 0),
  };
  const total = clamped.NDA + clamped.INDIA + clamped.Others;
  if (total <= 0) {
    return { NDA: 33.33, INDIA: 33.33, Others: 33.34 };
  }
  return {
    NDA: (clamped.NDA / total) * 100,
    INDIA: (clamped.INDIA / total) * 100,
    Others: (clamped.Others / total) * 100,
  };
}

function baseAllianceShares(record: MonteCarloBaseRecord): Record<AllianceBucket, number> | null {
  if (record.alliance_vote_shares_2024) {
    return {
      NDA: record.alliance_vote_shares_2024.NDA ?? 0,
      INDIA: record.alliance_vote_shares_2024.INDIA ?? 0,
      Others: record.alliance_vote_shares_2024.Others ?? 0,
    };
  }
  return null;
}

function partyAlliance(party: string, mapping: Record<string, string>): AllianceBucket {
  const key = party.toUpperCase();
  const alliance = mapping[key] || mapping[party] || "Others";
  if (alliance === "NDA") return "NDA";
  if (alliance === "INDIA") return "INDIA";
  return "Others";
}

function winnerAlliance2024(record: MonteCarloBaseRecord, mapping: Record<string, string>): AllianceBucket {
  const shares = baseAllianceShares(record);
  if (shares) {
    const winner = calculateAllianceWinner(shares);
    return winner;
  }
  if (record.winner_party_2024) {
    return partyAlliance(record.winner_party_2024, mapping);
  }
  return "Others";
}

export function calculateAllianceWinner(shares: Record<AllianceBucket, number>): AllianceBucket {
  let winner: AllianceBucket = "Others";
  let top = -1;
  for (const bucket of ["NDA", "INDIA", "Others"] as AllianceBucket[]) {
    if ((shares[bucket] ?? 0) > top) {
      top = shares[bucket] ?? 0;
      winner = bucket;
    }
  }
  return winner;
}

function simulatedWinnerParty(
  record: MonteCarloBaseRecord,
  allianceWinner: AllianceBucket,
  mapping: Record<string, string>,
): string {
  if (record.party_vote_shares_2024 && record.simulation_completeness === "full_party_shares") {
    let bestParty = record.winner_party_2024 || allianceWinner;
    let bestShare = -1;
    for (const [party, share] of Object.entries(record.party_vote_shares_2024)) {
      if (partyAlliance(party, mapping) !== allianceWinner) continue;
      if (share > bestShare) {
        bestShare = share;
        bestParty = party;
      }
    }
    return bestParty;
  }
  if (allianceWinner === "NDA") return "BJP";
  if (allianceWinner === "INDIA") return "INC";
  return record.winner_party_2024 || "Others";
}

function projectionConfidence(record: MonteCarloBaseRecord): ProjectionConfidence {
  if (record.simulation_completeness === "full_party_shares" && record.margin_2024 != null) {
    return "high";
  }
  if (record.simulation_completeness === "full_party_shares") {
    return "medium";
  }
  if (record.simulation_completeness === "bjp_inc_limited") {
    return "low";
  }
  return "low";
}

export function simulateSeat(
  record: MonteCarloBaseRecord,
  inputs: MonteCarloInputs,
  nationalError: number,
  stateError: number,
  seatError: number,
): { allianceWinner: AllianceBucket; winnerParty: string } | null {
  const base = baseAllianceShares(record);
  if (!base) return null;

  let shares = applySwing(base, inputs);
  shares = {
    NDA: shares.NDA + nationalError + stateError + seatError,
    INDIA: shares.INDIA + nationalError + stateError + seatError,
    Others: shares.Others + nationalError + stateError + seatError,
  };
  shares = normalizeVoteShares(shares);
  const allianceWinner = calculateAllianceWinner(shares);
  const winnerParty = simulatedWinnerParty(record, allianceWinner, {});
  return { allianceWinner, winnerParty };
}

function shouldInclude(record: MonteCarloBaseRecord, inputs: MonteCarloInputs): boolean {
  if (inputs.onlySelectedState && inputs.stateFilter && record.state !== inputs.stateFilter) {
    return false;
  }
  if (
    !inputs.includeLowConfidence &&
    (record.simulation_completeness !== "full_party_shares" ||
      record.data_quality_label === "election_only" ||
      record.data_quality_label === "low")
  ) {
    return false;
  }
  if (record.simulation_completeness === "winner_margin_only") {
    return inputs.includeLowConfidence;
  }
  return baseAllianceShares(record) != null;
}

export function simulateOneElection(
  records: MonteCarloBaseRecord[],
  inputs: MonteCarloInputs,
  mapping: Record<string, string>,
  rng: () => number,
  stateErrors: Record<string, number>,
): { nda: number; india: number; others: number; seatResults: Map<string, AllianceBucket> } {
  const nationalError = addRandomError(rng, inputs.nationalSigma);
  let nda = 0;
  let india = 0;
  let others = 0;
  const seatResults = new Map<string, AllianceBucket>();

  for (const record of records) {
    if (!shouldInclude(record, inputs)) continue;
    const base = baseAllianceShares(record);
    if (!base) continue;

    const stateError = stateErrors[record.state_key] ?? stateErrors[record.state] ?? 0;
    const seatError = addRandomError(rng, inputs.seatSigma);

    let shares = applySwing(base, inputs);
    shares = {
      NDA: shares.NDA + nationalError + stateError + seatError,
      INDIA: shares.INDIA + nationalError + stateError + seatError,
      Others: shares.Others + nationalError + stateError + seatError,
    };
    shares = normalizeVoteShares(shares);
    const winner = calculateAllianceWinner(shares);
    seatResults.set(constituencyLookupKey(record.state_key, record.constituency_key), winner);

    if (winner === "NDA") nda += 1;
    else if (winner === "INDIA") india += 1;
    else others += 1;
  }

  return { nda, india, others, seatResults };
}

function percentile(sorted: number[], p: number): number {
  if (!sorted.length) return 0;
  const idx = Math.floor(p * (sorted.length - 1));
  return sorted[Math.max(0, Math.min(sorted.length - 1, idx))];
}

function buildHistogram(values: number[]): Array<{ seats: number; count: number }> {
  const counts = new Map<number, number>();
  for (const value of values) {
    counts.set(value, (counts.get(value) ?? 0) + 1);
  }
  return [...counts.entries()]
    .map(([seats, count]) => ({ seats, count }))
    .sort((a, b) => a.seats - b.seats);
}

export function summarizeSimulationResults(
  inputs: MonteCarloInputs,
  ndaSeats: number[],
  indiaSeats: number[],
  othersSeats: number[],
  seatStats: SeatSimulationStats[],
): MonteCarloResult {
  const n = ndaSeats.length;
  const ndaSorted = [...ndaSeats].sort((a, b) => a - b);
  const indiaSorted = [...indiaSeats].sort((a, b) => a - b);

  let ndaPlurality = 0;
  let indiaPlurality = 0;
  let othersPlurality = 0;
  let ndaMajority = 0;
  let indiaMajority = 0;
  let hung = 0;

  for (let i = 0; i < n; i += 1) {
    const nda = ndaSeats[i];
    const india = indiaSeats[i];
    const others = othersSeats[i];
    if (nda >= india && nda >= others) ndaPlurality += 1;
    else if (india >= nda && india >= others) indiaPlurality += 1;
    else othersPlurality += 1;

    if (nda >= MAJORITY_THRESHOLD) ndaMajority += 1;
    else if (india >= MAJORITY_THRESHOLD) indiaMajority += 1;
    else hung += 1;
  }

  const volatileSeats = seatStats
    .filter((s) => s.flip_probability >= 0.15)
    .sort((a, b) => b.flip_probability - a.flip_probability)
    .slice(0, 50);

  const timestamp = new Date().toISOString();
  const summary: MonteCarloSummary = {
    simulations_run: n,
    nda_plurality_probability: ndaPlurality / n,
    india_plurality_probability: indiaPlurality / n,
    others_plurality_probability: othersPlurality / n,
    nda_majority_probability: ndaMajority / n,
    india_majority_probability: indiaMajority / n,
    hung_parliament_probability: hung / n,
    median_nda_seats: percentile(ndaSorted, 0.5),
    median_india_seats: percentile(indiaSorted, 0.5),
    median_others_seats: percentile([...othersSeats].sort((a, b) => a - b), 0.5),
    nda_seat_p10: percentile(ndaSorted, 0.1),
    nda_seat_p90: percentile(ndaSorted, 0.9),
    india_seat_p10: percentile(indiaSorted, 0.1),
    india_seat_p90: percentile(indiaSorted, 0.9),
    volatile_seat_count: seatStats.filter((s) => s.flip_probability >= 0.15).length,
    timestamp,
  };

  return {
    summary,
    nda_seat_distribution: buildHistogram(ndaSeats),
    india_seat_distribution: buildHistogram(indiaSeats),
    others_seat_distribution: buildHistogram(othersSeats),
    volatile_seats: volatileSeats,
    detail: {
      simulations_run: n,
      assumptions: inputs,
      seat_count_distribution: { nda: ndaSeats, india: indiaSeats, others: othersSeats },
      alliance_win_probabilities: {
        nda_plurality: summary.nda_plurality_probability,
        india_plurality: summary.india_plurality_probability,
        others_plurality: summary.others_plurality_probability,
        nda_majority: summary.nda_majority_probability,
        india_majority: summary.india_majority_probability,
        hung_parliament: summary.hung_parliament_probability,
      },
      volatile_seats: volatileSeats,
      timestamp,
    },
  };
}

export function runMonteCarloElection(
  base: MonteCarloBaseBundle,
  inputs: MonteCarloInputs,
): MonteCarloResult {
  const rng = mulberry32(inputs.seed ?? Date.now());
  const records = base.constituencies;
  const mapping = base.alliance_mapping;

  const included = records.filter((r) => shouldInclude(r, inputs) && baseAllianceShares(r));
  const states = [...new Set(included.map((r) => r.state_key))];

  const ndaSeats: number[] = [];
  const indiaSeats: number[] = [];
  const othersSeats: number[] = [];

  const seatWinCounts = new Map<
    string,
    { nda: number; india: number; others: number; flip: number; winners: Map<string, number> }
  >();

  for (const record of included) {
    const key = constituencyLookupKey(record.state_key, record.constituency_key);
    seatWinCounts.set(key, { nda: 0, india: 0, others: 0, flip: 0, winners: new Map() });
  }

  for (let sim = 0; sim < inputs.numSimulations; sim += 1) {
    const stateErrors: Record<string, number> = {};
    for (const stateKey of states) {
      stateErrors[stateKey] = addRandomError(rng, inputs.stateSigma);
    }

    const nationalError = addRandomError(rng, inputs.nationalSigma);
    let nda = 0;
    let india = 0;
    let others = 0;

    for (const record of included) {
      const baseShares = baseAllianceShares(record)!;
      const stateError = stateErrors[record.state_key] ?? 0;
      const seatError = addRandomError(rng, inputs.seatSigma);

      let shares = applySwing(baseShares, inputs);
      shares = {
        NDA: shares.NDA + nationalError + stateError + seatError,
        INDIA: shares.INDIA + nationalError + stateError + seatError,
        Others: shares.Others + nationalError + stateError + seatError,
      };
      shares = normalizeVoteShares(shares);
      const winner = calculateAllianceWinner(shares);
      const winnerParty = simulatedWinnerParty(record, winner, mapping);
      const key = constituencyLookupKey(record.state_key, record.constituency_key);
      const stats = seatWinCounts.get(key)!;
      const baseAlliance = winnerAlliance2024(record, mapping);

      if (winner === "NDA") {
        nda += 1;
        stats.nda += 1;
      } else if (winner === "INDIA") {
        india += 1;
        stats.india += 1;
      } else {
        others += 1;
        stats.others += 1;
      }
      if (winner !== baseAlliance) stats.flip += 1;
      stats.winners.set(winnerParty, (stats.winners.get(winnerParty) ?? 0) + 1);
    }

    ndaSeats.push(nda);
    indiaSeats.push(india);
    othersSeats.push(others);
  }

  const n = inputs.numSimulations;
  const seatStats: SeatSimulationStats[] = included.map((record) => {
    const key = constituencyLookupKey(record.state_key, record.constituency_key);
    const stats = seatWinCounts.get(key)!;
    let mostCommonWinner = record.winner_party_2024 || "Unknown";
    let mostCommonCount = 0;
    for (const [party, count] of stats.winners.entries()) {
      if (count > mostCommonCount) {
        mostCommonCount = count;
        mostCommonWinner = party;
      }
    }
    let mostCommonAlliance: AllianceBucket = "Others";
    let best = -1;
    if (stats.nda > best) {
      best = stats.nda;
      mostCommonAlliance = "NDA";
    }
    if (stats.india > best) {
      best = stats.india;
      mostCommonAlliance = "INDIA";
    }
    if (stats.others > best) {
      mostCommonAlliance = "Others";
    }

    return {
      state: record.state,
      constituency: record.constituency,
      state_key: record.state_key,
      constituency_key: record.constituency_key,
      winner_party_2024: record.winner_party_2024,
      winner_alliance_2024: winnerAlliance2024(record, mapping),
      most_common_simulated_winner: mostCommonWinner,
      most_common_simulated_alliance: mostCommonAlliance,
      flip_probability: stats.flip / n,
      nda_win_probability: stats.nda / n,
      india_win_probability: stats.india / n,
      others_win_probability: stats.others / n,
      projection_confidence: projectionConfidence(record),
      simulation_completeness: record.simulation_completeness,
    };
  });

  return summarizeSimulationResults(inputs, ndaSeats, indiaSeats, othersSeats, seatStats);
}

export function formatProbability(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

export function formatSwingLabel(value: number): string {
  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(1)} pp`;
}

export const ALLIANCE_COLORS: Record<AllianceBucket, string> = {
  NDA: COLORS.warning,
  INDIA: COLORS.primary,
  Others: COLORS.muted,
};
