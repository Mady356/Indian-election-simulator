export type MapMode = "state" | "district" | "constituency";

export interface District {
  id: number;
  state: string;
  district: string;
  normalized_name: string;
}

export interface DemographicFeature {
  geography_type: string;
  survey?: string | null;
  survey_year?: number | null;
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

export interface DistrictDetail extends District {
  demographics: DemographicFeature[];
}

export interface ConstituencyDistrictLink {
  district_id: number;
  district: string;
  state: string;
  assembly_segments_in_district?: number | null;
  total_assembly_segments?: number | null;
  district_segment_share?: number | null;
  source?: string | null;
}

export interface ConstituencyYearSummary {
  year: number;
  winner_party?: string | null;
  winner_alliance?: string | null;
  winner_vote_share?: number | null;
  runner_up_party?: string | null;
  margin_votes?: number | null;
  margin_pct?: number | null;
  turnout_pct?: number | null;
}

export interface ElectionResult {
  year: number;
  party: string;
  alliance?: string | null;
  candidate?: string | null;
  votes?: number | null;
  vote_share?: number | null;
  rank?: number | null;
  won: boolean;
}

export interface Constituency {
  id: number;
  state: string;
  constituency: string;
  normalized_name: string;
  constituency_no?: number | null;
  reservation_status?: string | null;
}

export interface ConstituencyDetail extends Constituency {
  districts: ConstituencyDistrictLink[];
  election_history: ConstituencyYearSummary[];
}

export interface ConstituencyDemographics {
  constituency_id: number;
  constituency: string;
  state: string;
  demographics: DemographicFeature;
  method: string;
}

export interface ConstituencyResults {
  constituency_id: number;
  results: Record<string, ElectionResult[]>;
}

export interface VariableEffect {
  party: string;
  effect_per_unit: number;
}

export interface SimulationRequest {
  base_year: number;
  party_swings: Record<string, number>;
  variable_effects: Record<string, VariableEffect>;
}

export interface ConstituencyProjection {
  constituency_id: number;
  state: string;
  constituency: string;
  base_winner?: string | null;
  projected_winner?: string | null;
  changed: boolean;
  projected_shares: Record<string, number>;
}

export interface SimulationResponse {
  base_year: number;
  constituencies_projected: number;
  seats_changed: number;
  projected_seat_totals: Record<string, number>;
  base_seat_totals: Record<string, number>;
  sample_changes: ConstituencyProjection[];
}

export interface WinnerComparisonRow {
  state: string;
  constituency: string;
  party_2019: string;
  winner_2019: string;
  vote_share_2019: string;
  party_2024: string;
  winner_2024: string;
  vote_share_2024: string;
  seat_flipped: string;
}

export interface SearchResult {
  type: "state" | "district" | "constituency";
  id: number | string;
  label: string;
  sublabel: string;
  state: string;
}

export interface SelectionState {
  mapMode: MapMode;
  selectedState: string | null;
  selectedDistrictId: number | null;
  selectedDistrictName: string | null;
  selectedConstituencyId: number | null;
  selectedConstituencyName: string | null;
  highlightGeoId: string | null;
}
