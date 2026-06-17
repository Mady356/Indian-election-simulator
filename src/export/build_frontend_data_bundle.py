"""
Build static JSON bundles for the deployable frontend dashboard.

Run:
    python -m src.export.build_frontend_data_bundle
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
ANALYSIS_DIR = ROOT / "data" / "analysis"
COVERAGE_DIR = ANALYSIS_DIR / "coverage"
FRONTEND_DATA_DIR = ROOT / "frontend" / "public" / "data"

MASTER_PATH = ANALYSIS_DIR / "constituency_election_demographic_master.csv"
CORRELATIONS_PATH = ANALYSIS_DIR / "vote_share_driver_correlations.csv"
TOP_SWING_PATH = ANALYSIS_DIR / "top_swing_constituencies.csv"
STATE_COVERAGE_PATH = COVERAGE_DIR / "state_coverage.csv"
VARIABLE_COVERAGE_PATH = COVERAGE_DIR / "variable_coverage.csv"
CONSTITUENCY_COVERAGE_PATH = COVERAGE_DIR / "constituency_coverage.csv"
MISSING_REASONS_PATH = COVERAGE_DIR / "missing_coverage_reasons.csv"

DEMOGRAPHIC_NFHS5_COLS = [
    "fertility_rate_nfhs5",
    "electricity_pct_nfhs5",
    "improved_sanitation_pct_nfhs5",
    "lpg_pct_nfhs5",
    "mobile_phone_pct_nfhs5",
    "bank_account_pct_nfhs5",
    "women_secondary_edu_pct_nfhs5",
    "female_literacy_pct_nfhs5",
    "male_literacy_pct_nfhs5",
    "wealth_index_mean_nfhs5",
    "urban_pct_nfhs5",
]

DEMOGRAPHIC_CHANGE_COLS = [
    "fertility_rate_change",
    "electricity_pct_change",
    "improved_sanitation_pct_change",
    "lpg_pct_change",
    "mobile_phone_pct_change",
    "bank_account_pct_change",
    "women_secondary_edu_pct_change",
    "female_literacy_pct_change",
    "male_literacy_pct_change",
    "wealth_index_mean_change",
    "urban_pct_change",
]


def _nan_to_none(value: object) -> object | None:
    if value is None:
        return None
    if isinstance(value, float) and pd.isna(value):
        return None
    if isinstance(value, str) and value.strip().lower() in {"", "nan", "none"}:
        return None
    return value


def _round_num(value: object, digits: int = 2) -> float | None:
    cleaned = _nan_to_none(value)
    if cleaned is None:
        return None
    try:
        return round(float(cleaned), digits)
    except (TypeError, ValueError):
        return None


def _bool_val(value: object) -> bool | None:
    cleaned = _nan_to_none(value)
    if cleaned is None:
        return None
    if isinstance(cleaned, bool):
        return cleaned
    text = str(cleaned).strip().lower()
    if text in {"true", "1", "yes"}:
        return True
    if text in {"false", "0", "no"}:
        return False
    return None


def data_quality_label(nfhs5_coverage_share: float | None, has_demographics: bool) -> str:
    if not has_demographics or nfhs5_coverage_share is None or nfhs5_coverage_share <= 0:
        return "election_only"
    if nfhs5_coverage_share >= 0.75:
        return "high"
    if nfhs5_coverage_share >= 0.5:
        return "medium"
    return "low"


def _has_demographics(row: pd.Series) -> bool:
    cols = DEMOGRAPHIC_NFHS5_COLS + DEMOGRAPHIC_CHANGE_COLS
    return any(_nan_to_none(row.get(col)) is not None for col in cols)


def build_constituency_record(row: pd.Series) -> dict[str, object]:
    nfhs5_share = _round_num(row.get("nfhs5_coverage_share"), 4)
    change_share = _round_num(row.get("change_coverage_share"), 4)
    has_demo = _has_demographics(row)

    demographics_nfhs5 = {
        col.replace("_nfhs5", ""): _round_num(row.get(col))
        for col in DEMOGRAPHIC_NFHS5_COLS
    }
    demographics_change = {
        col.replace("_change", "_change"): _round_num(row.get(col))
        for col in DEMOGRAPHIC_CHANGE_COLS
    }

    districts_used = _nan_to_none(row.get("districts_used"))
    districts_missing = _nan_to_none(row.get("districts_missing"))

    return {
        "state": str(row["state"]),
        "constituency": str(row["constituency"]),
        "state_key": str(row["state_key"]),
        "constituency_key": str(row["constituency_key"]),
        "winner_2019": _nan_to_none(row.get("winner_2019")),
        "winner_2024": _nan_to_none(row.get("winner_2024")),
        "winner_party_2019": _nan_to_none(row.get("winner_party_2019")),
        "winner_party_2024": _nan_to_none(row.get("winner_party_2024")),
        "bjp_vote_share_2019": _round_num(row.get("bjp_vote_share_2019")),
        "bjp_vote_share_2024": _round_num(row.get("bjp_vote_share_2024")),
        "inc_vote_share_2019": _round_num(row.get("inc_vote_share_2019")),
        "inc_vote_share_2024": _round_num(row.get("inc_vote_share_2024")),
        "bjp_swing_2019_2024": _round_num(row.get("bjp_swing_2019_2024")),
        "inc_swing_2019_2024": _round_num(row.get("inc_swing_2019_2024")),
        "winner_changed": _bool_val(row.get("winner_changed")),
        "margin_2019": _round_num(row.get("margin_2019")),
        "margin_2024": _round_num(row.get("margin_2024")),
        "turnout_2019": _round_num(row.get("turnout_2019")),
        "turnout_2024": _round_num(row.get("turnout_2024")),
        "demographics_nfhs5": demographics_nfhs5,
        "demographics_change": demographics_change,
        "nfhs5_coverage_share": nfhs5_share,
        "change_coverage_share": change_share,
        "change_quality_flag": _nan_to_none(row.get("change_quality_flag")),
        "districts_used": str(districts_used) if districts_used is not None else None,
        "districts_missing": str(districts_missing) if districts_missing is not None else None,
        "data_quality_label": data_quality_label(
            nfhs5_share if isinstance(nfhs5_share, float) else None,
            has_demo,
        ),
    }


def build_state_summaries(constituencies: list[dict[str, object]]) -> list[dict[str, object]]:
    df = pd.DataFrame(constituencies)
    states: list[dict[str, object]] = []

    for state_key, group in df.groupby("state_key", sort=True):
        state_name = str(group.iloc[0]["state"])
        with_demo = group[group["data_quality_label"] != "election_only"]
        demo_count = len(with_demo)
        total = len(group)

        def _top_gain(party_col: str, swing_col: str) -> dict[str, object] | None:
            valid = group[group[swing_col].notna()].copy()
            if valid.empty:
                return None
            row = valid.loc[valid[swing_col].astype(float).idxmax()]
            return {
                "constituency": row["constituency"],
                "constituency_key": row["constituency_key"],
                "swing": _round_num(row[swing_col]),
                "party": row[party_col],
            }

        bjp_gains = group[group["bjp_swing_2019_2024"].notna()]
        inc_gains = group[group["inc_swing_2019_2024"].notna()]

        avg_bjp_swing = _round_num(bjp_gains["bjp_swing_2019_2024"].astype(float).mean()) if not bjp_gains.empty else None
        avg_inc_swing = _round_num(inc_gains["inc_swing_2019_2024"].astype(float).mean()) if not inc_gains.empty else None
        turnout_valid = group[group["turnout_2019"].notna() & group["turnout_2024"].notna()]
        avg_turnout_change = None
        if not turnout_valid.empty:
            avg_turnout_change = _round_num(
                (turnout_valid["turnout_2024"].astype(float) - turnout_valid["turnout_2019"].astype(float)).mean()
            )

        mean_coverage = _round_num(with_demo["nfhs5_coverage_share"].astype(float).mean()) if demo_count else 0.0
        quality_counts = group["data_quality_label"].value_counts()
        if quality_counts.get("high", 0) >= total * 0.5:
            state_quality = "high"
        elif quality_counts.get("election_only", 0) == total:
            state_quality = "election_only"
        elif demo_count == 0:
            state_quality = "election_only"
        elif mean_coverage and mean_coverage >= 0.75:
            state_quality = "high"
        elif mean_coverage and mean_coverage >= 0.5:
            state_quality = "medium"
        elif demo_count > 0:
            state_quality = "low"
        else:
            state_quality = "election_only"

        states.append(
            {
                "state": state_name,
                "state_key": str(state_key),
                "total_constituencies": int(total),
                "constituencies_with_demographics": int(demo_count),
                "demographic_coverage_pct": _round_num(100.0 * demo_count / total if total else 0),
                "bjp_seats_2019": int((group["winner_party_2019"] == "BJP").sum()),
                "bjp_seats_2024": int((group["winner_party_2024"] == "BJP").sum()),
                "inc_seats_2019": int((group["winner_party_2019"] == "INC").sum()),
                "inc_seats_2024": int((group["winner_party_2024"] == "INC").sum()),
                "winner_changes": int(group["winner_changed"].fillna(False).astype(bool).sum()),
                "average_bjp_swing": avg_bjp_swing,
                "average_inc_swing": avg_inc_swing,
                "average_turnout_change": avg_turnout_change,
                "top_bjp_gain": _top_gain("winner_party_2024", "bjp_swing_2019_2024"),
                "top_inc_gain": _top_gain("winner_party_2024", "inc_swing_2019_2024"),
                "mean_nfhs5_coverage_share": mean_coverage,
                "data_quality_label": state_quality,
            }
        )

    return sorted(states, key=lambda item: str(item["state"]))


def build_insights(correlations: pd.DataFrame) -> dict[str, object]:
    insights: dict[str, object] = {
        "bjp_swing_positive": [],
        "bjp_swing_negative": [],
        "inc_swing_positive": [],
        "inc_swing_negative": [],
        "disclaimer": (
            "Correlations are constituency-level exploratory relationships between "
            "demographic indicators and vote swings. They are not causal claims."
        ),
    }

    if correlations.empty:
        return insights

    for target, key_pos, key_neg in [
        ("bjp_swing_2019_2024", "bjp_swing_positive", "bjp_swing_negative"),
        ("inc_swing_2019_2024", "inc_swing_positive", "inc_swing_negative"),
    ]:
        subset = correlations[correlations["target"] == target].copy()
        if subset.empty:
            continue
        subset["abs_correlation"] = subset["abs_correlation"].astype(float)
        pos = subset[subset["correlation"].astype(float) > 0].sort_values("abs_correlation", ascending=False).head(8)
        neg = subset[subset["correlation"].astype(float) < 0].sort_values("abs_correlation", ascending=False).head(8)

        def _rows(frame: pd.DataFrame) -> list[dict[str, object]]:
            out: list[dict[str, object]] = []
            for _, row in frame.iterrows():
                out.append(
                    {
                        "feature": str(row["feature"]),
                        "correlation": _round_num(row["correlation"], 4),
                        "n_observations": int(row["n_observations"]) if pd.notna(row["n_observations"]) else None,
                        "direction": str(row.get("direction", "")),
                        "interpretation": str(row.get("interpretation_stub", "")),
                    }
                )
            return out

        insights[key_pos] = _rows(pos)
        insights[key_neg] = _rows(neg)

    return insights


def build_coverage_summary(
    master: pd.DataFrame,
    state_coverage: pd.DataFrame,
    variable_coverage: pd.DataFrame,
    missing_reasons: pd.DataFrame,
) -> dict[str, object]:
    total = len(master)
    with_nfhs5 = int((master[DEMOGRAPHIC_NFHS5_COLS].notna().any(axis=1)).sum())
    with_any_demo = int((master["nfhs5_coverage_share"].fillna(0) > 0).sum())
    with_change = int((master[DEMOGRAPHIC_CHANGE_COLS].notna().any(axis=1)).sum())

    reason_counts: dict[str, int] = {}
    if not missing_reasons.empty and "suspected_reason" in missing_reasons.columns:
        reason_counts = (
            missing_reasons["suspected_reason"].fillna("unknown").astype(str).value_counts().to_dict()
        )

    state_rows: list[dict[str, object]] = []
    if not state_coverage.empty:
        for _, row in state_coverage.iterrows():
            state_rows.append(
                {
                    "state": str(row["state"]),
                    "total_constituencies": int(row.get("total_election_constituencies", 0)),
                    "constituencies_with_demographics": int(row.get("constituencies_with_nfhs5_any", 0)),
                    "coverage_pct": _round_num(row.get("coverage_pct")),
                    "mean_nfhs5_coverage_share": _round_num(row.get("mean_nfhs5_coverage_share")),
                }
            )

    return {
        "election_constituencies_total": total,
        "constituencies_with_any_nfhs5_value": with_nfhs5,
        "constituencies_with_demographic_coverage": with_any_demo,
        "constituencies_with_change_features": with_change,
        "demographic_coverage_pct": _round_num(100.0 * with_any_demo / total if total else 0),
        "election_coverage_pct": 100.0,
        "state_coverage": state_rows,
        "missing_reason_counts": reason_counts,
        "sources": [
            "Election Commission of India results (2019, 2024)",
            "Census / delimitation district-to-constituency mappings",
            "NFHS-4 / NFHS-5 district-level indicators",
        ],
        "csds_status": "pending",
        "notes": [
            "Missing demographic values are not imputed.",
            "coverage_share reflects the share of mapped district population represented in NFHS features.",
            "Analysis is exploratory; correlations are not causal.",
        ],
    }


def build_top_swing(top_swing: pd.DataFrame) -> dict[str, list[dict[str, object]]]:
    if top_swing.empty:
        return {}

    grouped: dict[str, list[dict[str, object]]] = {}
    for section, frame in top_swing.groupby("table_section"):
        rows: list[dict[str, object]] = []
        for _, row in frame.iterrows():
            rows.append(
                {
                    "rank": int(row["rank"]) if pd.notna(row.get("rank")) else None,
                    "state": str(row.get("state", "")),
                    "constituency": str(row.get("constituency", "")),
                    "bjp_swing_2019_2024": _round_num(row.get("bjp_swing_2019_2024")),
                    "bjp_vote_share_2019": _round_num(row.get("bjp_vote_share_2019")),
                    "bjp_vote_share_2024": _round_num(row.get("bjp_vote_share_2024")),
                    "inc_swing_2019_2024": _round_num(row.get("inc_swing_2019_2024")),
                    "inc_vote_share_2019": _round_num(row.get("inc_vote_share_2019")),
                    "inc_vote_share_2024": _round_num(row.get("inc_vote_share_2024")),
                    "winner_party_2024": _nan_to_none(row.get("winner_party_2024")),
                    "winner_2024": _nan_to_none(row.get("winner_2024")),
                    "margin_2019": _round_num(row.get("margin_2019")),
                    "margin_2024": _round_num(row.get("margin_2024")),
                    "margin_change": _round_num(row.get("margin_change")),
                }
            )
        grouped[str(section)] = rows
    return grouped


def build_variable_coverage(variable_coverage: pd.DataFrame) -> list[dict[str, object]]:
    if variable_coverage.empty:
        return []
    rows: list[dict[str, object]] = []
    for _, row in variable_coverage.iterrows():
        rows.append(
            {
                "variable": str(row["variable"]),
                "non_null_count": int(row.get("non_null_count", 0)),
                "non_null_pct": _round_num(row.get("non_null_pct")),
                "states_available": int(row.get("states_available", 0)) if pd.notna(row.get("states_available")) else None,
                "constituencies_available": int(row.get("constituencies_available", 0))
                if pd.notna(row.get("constituencies_available"))
                else None,
                "correlation_ready_count": int(row.get("correlation_ready_count", 0))
                if pd.notna(row.get("correlation_ready_count"))
                else None,
            }
        )
    return rows


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)


def build_bundle() -> dict[str, int]:
    master = pd.read_csv(MASTER_PATH)
    correlations = pd.read_csv(CORRELATIONS_PATH)
    top_swing = pd.read_csv(TOP_SWING_PATH)
    state_coverage = pd.read_csv(STATE_COVERAGE_PATH)
    variable_coverage = pd.read_csv(VARIABLE_COVERAGE_PATH)
    missing_reasons = pd.read_csv(MISSING_REASONS_PATH)

    constituencies = [build_constituency_record(row) for _, row in master.iterrows()]
    states = build_state_summaries(constituencies)
    insights = build_insights(correlations)
    coverage_summary = build_coverage_summary(master, state_coverage, variable_coverage, missing_reasons)
    top_swing_json = build_top_swing(top_swing)
    variable_cov_json = build_variable_coverage(variable_coverage)

    write_json(FRONTEND_DATA_DIR / "constituencies.json", constituencies)
    write_json(FRONTEND_DATA_DIR / "states.json", states)
    write_json(FRONTEND_DATA_DIR / "insights.json", insights)
    write_json(FRONTEND_DATA_DIR / "coverage_summary.json", coverage_summary)
    write_json(FRONTEND_DATA_DIR / "top_swing_constituencies.json", top_swing_json)
    write_json(FRONTEND_DATA_DIR / "variable_coverage.json", variable_cov_json)

    return {
        "constituencies": len(constituencies),
        "states": len(states),
        "top_swing_sections": len(top_swing_json),
        "variables": len(variable_cov_json),
    }


def main() -> None:
    counts = build_bundle()
    print("Frontend data bundle")
    print(f"  Constituencies: {counts['constituencies']}")
    print(f"  States: {counts['states']}")
    print(f"  Top swing sections: {counts['top_swing_sections']}")
    print(f"  Variables tracked: {counts['variables']}")
    print(f"  Output: {FRONTEND_DATA_DIR}")


if __name__ == "__main__":
    main()
