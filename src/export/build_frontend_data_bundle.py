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
MASTER_WITH_MANUAL_PATH = ANALYSIS_DIR / "constituency_election_demographic_master_with_manual.csv"
MANUAL_SOURCES_JSON_PATH = FRONTEND_DATA_DIR / "manual_demographic_sources.json"
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

MANUAL_DEMOGRAPHIC_VARIABLES = [
    "urban_pct",
    "literacy_rate",
    "female_literacy_pct",
    "male_literacy_pct",
    "sc_pct",
    "st_pct",
    "religion_hindu_pct",
    "religion_muslim_pct",
    "religion_christian_pct",
    "religion_sikh_pct",
    "population_density",
    "sex_ratio",
    "electricity_pct",
    "lpg_pct",
    "improved_sanitation_pct",
    "mobile_phone_pct",
    "bank_account_pct",
    "wealth_index_mean",
    "fertility_rate",
]

VARIABLE_TO_NFHS5 = {
    "urban_pct": "urban_pct_nfhs5",
    "female_literacy_pct": "female_literacy_pct_nfhs5",
    "male_literacy_pct": "male_literacy_pct_nfhs5",
    "electricity_pct": "electricity_pct_nfhs5",
    "lpg_pct": "lpg_pct_nfhs5",
    "improved_sanitation_pct": "improved_sanitation_pct_nfhs5",
    "mobile_phone_pct": "mobile_phone_pct_nfhs5",
    "bank_account_pct": "bank_account_pct_nfhs5",
    "wealth_index_mean": "wealth_index_mean_nfhs5",
    "fertility_rate": "fertility_rate_nfhs5",
}

MANUAL_ONLY_VARIABLES = set(MANUAL_DEMOGRAPHIC_VARIABLES) - set(VARIABLE_TO_NFHS5.keys())


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
    if any(_nan_to_none(row.get(col)) is not None for col in cols):
        return True
    for variable in MANUAL_ONLY_VARIABLES:
        if _nan_to_none(row.get(variable)) is not None:
            return True
    origin_col = f"{MANUAL_DEMOGRAPHIC_VARIABLES[0]}_origin"
    if origin_col in row.index and _nan_to_none(row.get(origin_col)) is not None:
        return True
    source_type = _nan_to_none(row.get("demographic_source_type"))
    return source_type in {"manual", "mixed", "generated"}


def _manual_field_sources(row: pd.Series) -> dict[str, dict[str, object]]:
    sources: dict[str, dict[str, object]] = {}
    for variable in MANUAL_DEMOGRAPHIC_VARIABLES:
        source_name = _nan_to_none(row.get(f"{variable}_source"))
        if source_name is None:
            continue
        sources[variable] = {
            "source_name": str(source_name),
            "source_year": _nan_to_none(row.get(f"{variable}_source_year")),
            "method": _nan_to_none(row.get(f"{variable}_method")),
            "confidence": _nan_to_none(row.get(f"{variable}_confidence")),
            "value_origin": _nan_to_none(row.get(f"{variable}_origin")) or "manual",
            "manual_reference_value": _round_num(row.get(f"manual_{variable}")),
        }
    return sources


def _manual_demographics(row: pd.Series) -> dict[str, float | None]:
    manual: dict[str, float | None] = {}
    for variable in MANUAL_ONLY_VARIABLES:
        manual[variable] = _round_num(row.get(variable))
    for variable in MANUAL_DEMOGRAPHIC_VARIABLES:
        origin = _nan_to_none(row.get(f"{variable}_origin"))
        if origin == "manual_reference":
            manual[variable] = _round_num(row.get(f"manual_{variable}"))
    return {key: value for key, value in manual.items() if value is not None}


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
    demographic_field_sources = _manual_field_sources(row)
    demographics_manual = _manual_demographics(row)
    demographic_source_type = _nan_to_none(row.get("demographic_source_type")) or (
        "generated" if has_demo else "election_only"
    )
    manual_fields_count = int(row.get("manual_demographic_fields_count", 0) or 0)

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
        "demographics_manual": demographics_manual,
        "demographic_field_sources": demographic_field_sources,
        "demographic_source_type": demographic_source_type,
        "manual_demographic_fields_count": manual_fields_count,
        "manual_demographic_source_count": int(row.get("manual_demographic_source_count", 0) or 0),
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


def build_manual_sources_catalog(constituencies: list[dict[str, object]]) -> dict[str, object]:
    seats_with_manual: list[dict[str, object]] = []
    source_catalog: dict[str, dict[str, object]] = {}

    for record in constituencies:
        source_type = record.get("demographic_source_type")
        if source_type not in {"manual", "mixed"}:
            continue

        field_sources = record.get("demographic_field_sources") or {}
        if not field_sources:
            continue

        seats_with_manual.append(
            {
                "state": record["state"],
                "constituency": record["constituency"],
                "state_key": record["state_key"],
                "constituency_key": record["constituency_key"],
                "demographic_source_type": source_type,
                "manual_demographic_fields_count": record.get("manual_demographic_fields_count", 0),
                "fields": list(field_sources.keys()),
            }
        )

        for variable, meta in field_sources.items():
            source_name = str(meta.get("source_name", "")).strip()
            if not source_name:
                continue
            catalog_key = source_name.lower()
            if catalog_key not in source_catalog:
                source_catalog[catalog_key] = {
                    "source_name": source_name,
                    "source_years": sorted(
                        {
                            str(meta.get("source_year"))
                            for meta in field_sources.values()
                            if meta.get("source_name") == source_name and meta.get("source_year")
                        }
                    ),
                    "variables": [],
                    "constituency_count": 0,
                }
            if variable not in source_catalog[catalog_key]["variables"]:
                source_catalog[catalog_key]["variables"].append(variable)

    for entry in source_catalog.values():
        entry["variables"] = sorted(entry["variables"])

    constituency_keys = {
        f"{item['state_key']}::{item['constituency_key']}" for item in seats_with_manual
    }
    for entry in source_catalog.values():
        entry["constituency_count"] = len(constituency_keys)

    return {
        "disclaimer": (
            "Some demographic values for listed constituencies were manually sourced from "
            "public documents. Manual values supplement — but do not silently replace — "
            "generated NFHS/Census-linked pipeline data unless explicitly overridden."
        ),
        "seats_with_manual_demographics": seats_with_manual,
        "sources": sorted(source_catalog.values(), key=lambda item: str(item["source_name"])),
    }


def build_bundle() -> dict[str, int]:
    master_path = MASTER_WITH_MANUAL_PATH if MASTER_WITH_MANUAL_PATH.exists() else MASTER_PATH
    master = pd.read_csv(master_path)
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
    manual_sources_json = build_manual_sources_catalog(constituencies)

    write_json(FRONTEND_DATA_DIR / "constituencies.json", constituencies)
    write_json(FRONTEND_DATA_DIR / "states.json", states)
    write_json(FRONTEND_DATA_DIR / "insights.json", insights)
    write_json(FRONTEND_DATA_DIR / "coverage_summary.json", coverage_summary)
    write_json(FRONTEND_DATA_DIR / "top_swing_constituencies.json", top_swing_json)
    write_json(FRONTEND_DATA_DIR / "variable_coverage.json", variable_cov_json)
    write_json(MANUAL_SOURCES_JSON_PATH, manual_sources_json)

    return {
        "constituencies": len(constituencies),
        "states": len(states),
        "top_swing_sections": len(top_swing_json),
        "variables": len(variable_cov_json),
        "manual_demographic_seats": len(manual_sources_json.get("seats_with_manual_demographics", [])),
    }


def main() -> None:
    counts = build_bundle()
    print("Frontend data bundle")
    print(f"  Constituencies: {counts['constituencies']}")
    print(f"  States: {counts['states']}")
    print(f"  Top swing sections: {counts['top_swing_sections']}")
    print(f"  Variables tracked: {counts['variables']}")
    print(f"  Manual demographic seats: {counts['manual_demographic_seats']}")
    print(f"  Output: {FRONTEND_DATA_DIR}")


if __name__ == "__main__":
    main()
