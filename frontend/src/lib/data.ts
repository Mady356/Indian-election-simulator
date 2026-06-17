import { DATA_URLS } from "./constants";
import { normalizeKey } from "./format";

export type DataQualityLabel = "high" | "medium" | "low" | "election_only";

export interface DemographicsNfhs5 {
  fertility_rate?: number | null;
  electricity_pct?: number | null;
  improved_sanitation_pct?: number | null;
  lpg_pct?: number | null;
  mobile_phone_pct?: number | null;
  bank_account_pct?: number | null;
  women_secondary_edu_pct?: number | null;
  female_literacy_pct?: number | null;
  male_literacy_pct?: number | null;
  wealth_index_mean?: number | null;
  urban_pct?: number | null;
}

export interface DemographicsChange {
  fertility_rate_change?: number | null;
  electricity_pct_change?: number | null;
  improved_sanitation_pct_change?: number | null;
  lpg_pct_change?: number | null;
  mobile_phone_pct_change?: number | null;
  bank_account_pct_change?: number | null;
  women_secondary_edu_pct_change?: number | null;
  female_literacy_pct_change?: number | null;
  male_literacy_pct_change?: number | null;
  wealth_index_mean_change?: number | null;
  urban_pct_change?: number | null;
}

export interface ConstituencyRecord {
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
  bjp_swing_2019_2024?: number | null;
  inc_swing_2019_2024?: number | null;
  winner_changed?: boolean | null;
  margin_2019?: number | null;
  margin_2024?: number | null;
  turnout_2019?: number | null;
  turnout_2024?: number | null;
  demographics_nfhs5: DemographicsNfhs5;
  demographics_change: DemographicsChange;
  nfhs5_coverage_share?: number | null;
  change_coverage_share?: number | null;
  change_quality_flag?: string | null;
  districts_used?: string | null;
  districts_missing?: string | null;
  data_quality_label: DataQualityLabel;
}

export interface TopGain {
  constituency: string;
  constituency_key: string;
  swing?: number | null;
  party?: string | null;
}

export interface StateSummary {
  state: string;
  state_key: string;
  total_constituencies: number;
  constituencies_with_demographics: number;
  demographic_coverage_pct?: number | null;
  bjp_seats_2019: number;
  bjp_seats_2024: number;
  inc_seats_2019: number;
  inc_seats_2024: number;
  winner_changes: number;
  average_bjp_swing?: number | null;
  average_inc_swing?: number | null;
  average_turnout_change?: number | null;
  top_bjp_gain?: TopGain | null;
  top_inc_gain?: TopGain | null;
  mean_nfhs5_coverage_share?: number | null;
  data_quality_label: DataQualityLabel;
}

export interface InsightRow {
  feature: string;
  correlation?: number | null;
  n_observations?: number | null;
  direction?: string;
  interpretation?: string;
}

export interface InsightsBundle {
  bjp_swing_positive: InsightRow[];
  bjp_swing_negative: InsightRow[];
  inc_swing_positive: InsightRow[];
  inc_swing_negative: InsightRow[];
  disclaimer: string;
}

export interface CoverageSummary {
  election_constituencies_total: number;
  constituencies_with_any_nfhs5_value: number;
  constituencies_with_demographic_coverage: number;
  constituencies_with_change_features: number;
  demographic_coverage_pct?: number | null;
  election_coverage_pct: number;
  state_coverage: Array<{
    state: string;
    total_constituencies: number;
    constituencies_with_demographics: number;
    coverage_pct?: number | null;
    mean_nfhs5_coverage_share?: number | null;
  }>;
  missing_reason_counts: Record<string, number>;
  sources: string[];
  csds_status: string;
  notes: string[];
}

export interface SwingRow {
  rank?: number | null;
  state: string;
  constituency: string;
  bjp_swing_2019_2024?: number | null;
  bjp_vote_share_2019?: number | null;
  bjp_vote_share_2024?: number | null;
  inc_swing_2019_2024?: number | null;
  inc_vote_share_2019?: number | null;
  inc_vote_share_2024?: number | null;
  winner_party_2024?: string | null;
  winner_2024?: string | null;
  margin_2019?: number | null;
  margin_2024?: number | null;
  margin_change?: number | null;
}

export interface VariableCoverageRow {
  variable: string;
  non_null_count: number;
  non_null_pct?: number | null;
  states_available?: number | null;
  constituencies_available?: number | null;
  correlation_ready_count?: number | null;
}

export interface DashboardData {
  constituencies: ConstituencyRecord[];
  states: StateSummary[];
  insights: InsightsBundle;
  coverageSummary: CoverageSummary;
  topSwing: Record<string, SwingRow[]>;
  variableCoverage: VariableCoverageRow[];
  constituencyByKey: Map<string, ConstituencyRecord>;
  stateByKey: Map<string, StateSummary>;
}

async function fetchJson<T>(url: string): Promise<T> {
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error(`Failed to load ${url}: ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export function constituencyLookupKey(stateKey: string, constituencyKey: string): string {
  return `${normalizeKey(stateKey)}::${normalizeKey(constituencyKey)}`;
}

export function matchGeoConstituency(
  stName: string,
  pcName: string,
  lookup: Map<string, ConstituencyRecord>,
): ConstituencyRecord | undefined {
  const key = constituencyLookupKey(stName, pcName);
  if (lookup.has(key)) return lookup.get(key);

  const stateNorm = normalizeKey(stName);
  for (const record of lookup.values()) {
    if (normalizeKey(record.state_key) === stateNorm && normalizeKey(record.constituency) === normalizeKey(pcName)) {
      return record;
    }
  }
  return undefined;
}

export async function loadDashboardData(): Promise<DashboardData> {
  const [
    constituencies,
    states,
    insights,
    coverageSummary,
    topSwing,
    variableCoverage,
  ] = await Promise.all([
    fetchJson<ConstituencyRecord[]>(DATA_URLS.constituencies),
    fetchJson<StateSummary[]>(DATA_URLS.states),
    fetchJson<InsightsBundle>(DATA_URLS.insights),
    fetchJson<CoverageSummary>(DATA_URLS.coverageSummary),
    fetchJson<Record<string, SwingRow[]>>(DATA_URLS.topSwing),
    fetchJson<VariableCoverageRow[]>(DATA_URLS.variableCoverage),
  ]);

  const constituencyByKey = new Map<string, ConstituencyRecord>();
  for (const row of constituencies) {
    constituencyByKey.set(constituencyLookupKey(row.state_key, row.constituency_key), row);
  }

  const stateByKey = new Map<string, StateSummary>();
  for (const row of states) {
    stateByKey.set(normalizeKey(row.state_key), row);
  }

  return {
    constituencies,
    states,
    insights,
    coverageSummary,
    topSwing,
    variableCoverage,
    constituencyByKey,
    stateByKey,
  };
}

export function hasDemographics(record: ConstituencyRecord): boolean {
  return record.data_quality_label !== "election_only";
}

export function nationalSeatTotals(constituencies: ConstituencyRecord[]) {
  return {
    bjp_2019: constituencies.filter((c) => c.winner_party_2019 === "BJP").length,
    bjp_2024: constituencies.filter((c) => c.winner_party_2024 === "BJP").length,
    inc_2019: constituencies.filter((c) => c.winner_party_2019 === "INC").length,
    inc_2024: constituencies.filter((c) => c.winner_party_2024 === "INC").length,
    flips: constituencies.filter((c) => c.winner_changed).length,
  };
}
