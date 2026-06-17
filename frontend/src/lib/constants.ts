export const API_BASE = "/api";

export const APP_NAME = "The 543";
export const APP_SUBTITLE = "Indian Election Intelligence";
export const APP_DESCRIPTION =
  "Explore India's Lok Sabha elections through constituency results, demographic indicators, swing analysis, and data coverage transparency.";
export const APP_META_DESCRIPTION =
  "The 543 is an Indian election intelligence platform for exploring Lok Sabha results, constituency demographics, swing analysis, and political change.";
export const APP_DISCLAIMER =
  "The 543 is an independent educational data project. Election results are available for 542 constituencies. Demographic indicators are available where coverage permits and are not imputed. Exploratory relationships are correlations, not causal claims.";

export const GEO_URLS = {
  states: "/geo/india_states.geojson",
  districts: "/geo/india_districts.geojson",
  constituencies: "/geo/india_constituencies.geojson",
} as const;

export const DATA_URLS = {
  constituencies: "/data/constituencies.json",
  states: "/data/states.json",
  insights: "/data/insights.json",
  coverageSummary: "/data/coverage_summary.json",
  topSwing: "/data/top_swing_constituencies.json",
  variableCoverage: "/data/variable_coverage.json",
} as const;

export const COLORS = {
  bg: "#0B1020",
  card: "#131A2D",
  border: "#1E2942",
  primary: "#4F8CFF",
  accent: "#7AE582",
  warning: "#FBBF24",
  danger: "#F87171",
  text: "#F8FAFC",
  muted: "#94A3B8",
} as const;

export const INDIA_BOUNDS: [[number, number], [number, number]] = [
  [68.0, 6.5],
  [97.5, 37.5],
];

export const MAP_COLOR_MODES = [
  { id: "winner_2024", label: "Winner 2024" },
  { id: "bjp_swing", label: "BJP swing" },
  { id: "inc_swing", label: "INC swing" },
  { id: "data_coverage", label: "Data coverage" },
] as const;

export type MapColorMode = (typeof MAP_COLOR_MODES)[number]["id"];

export const QUALITY_LABELS: Record<string, string> = {
  high: "High coverage",
  medium: "Medium coverage",
  low: "Low coverage",
  election_only: "Election only",
};
