"""Auto-fill missing constituency core demographics from Census 2011 district data."""

from __future__ import annotations

import argparse
from datetime import date

import pandas as pd

from src.demographics.census.common import (
    ALIAS_REPAIR_REPORT_PATH,
    AUTOFILL_CANDIDATES_PATH,
    AUTOFILL_TARGET_CATEGORIES,
    CENSUS_DISTRICT_CORE_PATH,
    CENSUS_DISTRICT_RELIGION_PATH,
    CENSUS_SOURCE_NAME,
    CENSUS_SOURCE_URL,
    CENSUS_SOURCE_YEAR,
    CLEANED_WORKLIST_PATH,
    COMPLETION_CORE_FIELDS,
    DELIMITATION_CENSUS_ALIAS_PATH,
    DELIMITATION_PATH,
    FINAL_543_UNIVERSE_PATH,
    MANUAL_AUTOFILL_CANDIDATES_PATH,
    MANUAL_CSV_PATH,
    MANUAL_ENTRY_COLUMNS,
    MASTER_WITH_MANUAL_PATH,
    VARIABLE_UNITS,
    canonical_constituency_keys,
    canonical_state_key,
    canonical_seat_key,
    clean_delimitation_constituency_name,
    ensure_dirs,
    field_already_present,
    lookup_key,
    normalize_key,
    weighted_average,
)
from src.demographics.census.clean_completion_worklist_aliases import run_alias_cleaning
from src.demographics.manual.common import nan_to_none

VARIABLE_TO_CORE_COLUMN = {
    "urban_pct": "urban_pct",
    "literacy_rate": "literacy_rate",
    "female_literacy_pct": "female_literacy_pct",
    "male_literacy_pct": "male_literacy_pct",
    "sc_pct": "sc_pct",
    "st_pct": "st_pct",
    "sex_ratio": "sex_ratio",
    "population_density": "population_density",
}

VARIABLE_TO_RELIGION_COLUMN = {
    "religion_hindu_pct": "religion_hindu_pct",
    "religion_muslim_pct": "religion_muslim_pct",
    "religion_christian_pct": "religion_christian_pct",
    "religion_sikh_pct": "religion_sikh_pct",
}


def _load_manual_keys() -> set[tuple[str, str, str]]:
    keys: set[tuple[str, str, str]] = set()
    if not MANUAL_CSV_PATH.exists():
        return keys
    manual = pd.read_csv(MANUAL_CSV_PATH)
    for _, row in manual.iterrows():
        if nan_to_none(row.get("value")) is None:
            continue
        keys.add(
            (
                str(row["state_key"]).strip(),
                str(row["constituency_key"]).strip(),
                str(row["variable"]).strip(),
            )
        )
    return keys


def _load_worklist_targets(repair_report: pd.DataFrame) -> pd.DataFrame:
    path = CLEANED_WORKLIST_PATH if CLEANED_WORKLIST_PATH.exists() else None
    if path is None:
        from src.demographics.census.common import COMPLETION_WORKLIST_PATH

        worklist = pd.read_csv(COMPLETION_WORKLIST_PATH)
    else:
        worklist = pd.read_csv(CLEANED_WORKLIST_PATH)

    excluded = set(
        repair_report[repair_report["repair_class"] == "alias_duplicate"]["row_index"].astype(int).tolist()
    )
    if excluded and "row_index" not in worklist.columns:
        worklist = worklist.reset_index().rename(columns={"index": "row_index"})

    targets = worklist[
        worklist["completion_category"].isin(AUTOFILL_TARGET_CATEGORIES)
        & worklist["exists_in_election_master"].astype(bool)
    ].copy()
    if excluded and "row_index" in targets.columns:
        targets = targets[~targets["row_index"].isin(excluded)]

    if FINAL_543_UNIVERSE_PATH.exists():
        universe = pd.read_csv(FINAL_543_UNIVERSE_PATH)
        allowed = set(universe["canonical_seat_key"])
        targets = targets[
            targets.apply(
                lambda row: canonical_seat_key(row["state_key"], row["constituency_key"]) in allowed,
                axis=1,
            )
        ]

    targets["canonical_key"] = targets.apply(
        lambda row: canonical_seat_key(row["state_key"], row["constituency_key"]),
        axis=1,
    )
    return targets.drop_duplicates("canonical_key")


def _build_delimitation_map() -> pd.DataFrame:
    delim = pd.read_csv(DELIMITATION_PATH)
    delim["pc_name"] = delim["lok_sabha_constituency"].map(clean_delimitation_constituency_name)
    delim["state_key"] = delim["state"].map(canonical_state_key)
    delim["constituency_key"] = delim["pc_name"].map(normalize_key)
    for idx, row in delim.iterrows():
        state_key, constituency_key = canonical_constituency_keys(row["state"], row["pc_name"])
        delim.at[idx, "state_key"] = state_key
        delim.at[idx, "constituency_key"] = constituency_key
    return delim


def _district_rows_for_constituency(
    state_key: str,
    constituency_key: str,
    delim_map: pd.DataFrame,
    alias_table: pd.DataFrame,
    census_core: pd.DataFrame,
    census_religion: pd.DataFrame,
) -> tuple[pd.DataFrame, list[str]]:
    subset = delim_map[
        (delim_map["state_key"] == state_key) & (delim_map["constituency_key"] == constituency_key)
    ]
    if subset.empty:
        return pd.DataFrame(), []

    rows: list[dict[str, object]] = []
    missing: list[str] = []
    for _, row in subset.iterrows():
        district_name = str(row["district"])
        weight = float(row.get("district_segment_share") or 0)
        alias = alias_table[
            (alias_table["delimitation_state"].map(normalize_key) == normalize_key(row["state"]))
            & (alias_table["delimitation_district"].map(normalize_key) == normalize_key(district_name))
        ]
        if alias.empty:
            census_match = census_core[
                (census_core["state_key"] == state_key)
                & (census_core["district_key"] == normalize_key(district_name))
            ]
            alias_confidence = "low"
        else:
            alias_row = alias.iloc[0]
            census_state = str(alias_row.get("nfhs_state") or alias_row.get("census_state") or state_key)
            census_district_key = str(alias_row.get("census_district_key") or normalize_key(district_name))
            census_match = census_core[
                (census_core["state_key"] == normalize_key(census_state))
                & (census_core["district_key"] == normalize_key(census_district_key))
            ]
            alias_confidence = str(alias_row.get("confidence") or "medium")

        if census_match.empty:
            missing.append(district_name)
            continue

        core = census_match.iloc[0].to_dict()
        religion_match = census_religion[
            (census_religion["state_key"] == core.get("state_key"))
            & (census_religion["district_key"] == core.get("district_key"))
        ]
        if not religion_match.empty:
            core.update(religion_match.iloc[0].to_dict())

        core["weight"] = weight
        core["alias_confidence"] = alias_confidence
        core["delimitation_district"] = district_name
        rows.append(core)

    if not rows:
        return pd.DataFrame(), missing

    out = pd.DataFrame(rows)
    weight_sum = out["weight"].sum()
    if weight_sum <= 0:
        out["weight"] = 1.0
    else:
        out["weight"] = out["weight"] / weight_sum
    return out, missing


def _estimate_value(district_rows: pd.DataFrame, variable: str) -> float | None:
    if district_rows.empty:
        return None
    column = VARIABLE_TO_CORE_COLUMN.get(variable) or VARIABLE_TO_RELIGION_COLUMN.get(variable)
    if not column or column not in district_rows.columns:
        return None
    if variable == "population_density" and district_rows[column].isna().all():
        return None
    return weighted_average(district_rows[column], district_rows["weight"])


def _method_for_rows(district_rows: pd.DataFrame) -> str:
    if len(district_rows) <= 1:
        return "district_proxy"
    return "district_weighted_estimate"


def _confidence_for_rows(district_rows: pd.DataFrame, missing_districts: list[str]) -> str:
    if missing_districts:
        return "low"
    confidences = {str(value).lower() for value in district_rows.get("alias_confidence", pd.Series(dtype=str))}
    if confidences == {"high"}:
        return "medium"
    if "low" in confidences:
        return "low"
    return "medium"


def _notes_for_estimate(
    variable: str,
    district_rows: pd.DataFrame,
    missing_districts: list[str],
    method: str,
) -> str:
    districts = ", ".join(district_rows["delimitation_district"].astype(str).tolist())
    base = (
        f"Census 2011 district-level {variable} aggregated for mapped component districts "
        f"({districts}) using delimitation segment weights. "
        "Constituency boundaries may not align exactly with districts; this is a district-level approximation."
    )
    if missing_districts:
        base += f" Missing district mapping for: {', '.join(missing_districts)}."
    if method == "district_proxy":
        base += " Single-district proxy used."
    return base


def autofill_constituency_core_demographics(refresh_aliases: bool = True) -> tuple[pd.DataFrame, pd.DataFrame]:
    ensure_dirs()

    if not CENSUS_DISTRICT_CORE_PATH.exists():
        from src.demographics.census.build_census_district_core import build_census_district_core

        build_census_district_core()
    if not CENSUS_DISTRICT_RELIGION_PATH.exists():
        from src.demographics.census.build_census_religion_district import build_census_district_religion

        build_census_district_religion()

    repair_report = pd.read_csv(ALIAS_REPAIR_REPORT_PATH) if ALIAS_REPAIR_REPORT_PATH.exists() else pd.DataFrame()
    if refresh_aliases or repair_report.empty:
        repair_report, _ = run_alias_cleaning()

    master = pd.read_csv(MASTER_WITH_MANUAL_PATH)
    master_by_key = {
        lookup_key(str(row["state_key"]), str(row["constituency_key"])): row for _, row in master.iterrows()
    }
    targets = _load_worklist_targets(repair_report)
    delim_map = _build_delimitation_map()
    alias_table = pd.read_csv(DELIMITATION_CENSUS_ALIAS_PATH) if DELIMITATION_CENSUS_ALIAS_PATH.exists() else pd.DataFrame()
    census_core = pd.read_csv(CENSUS_DISTRICT_CORE_PATH)
    census_religion = pd.read_csv(CENSUS_DISTRICT_RELIGION_PATH) if CENSUS_DISTRICT_RELIGION_PATH.exists() else pd.DataFrame()
    manual_keys = _load_manual_keys()

    candidate_rows: list[dict[str, object]] = []
    manual_rows: list[dict[str, str]] = []
    skipped_rows: list[dict[str, object]] = []

    for _, seat in targets.iterrows():
        state_key, constituency_key = canonical_constituency_keys(seat["state_key"], seat["constituency_key"])
        key = lookup_key(state_key, constituency_key)
        master_row = master_by_key.get(key)
        if master_row is None:
            skipped_rows.append({"canonical_key": key, "skip_reason": "not_in_election_master"})
            continue

        district_rows, missing_districts = _district_rows_for_constituency(
            state_key,
            constituency_key,
            delim_map,
            alias_table,
            census_core,
            census_religion,
        )
        if district_rows.empty:
            skipped_rows.append({"canonical_key": key, "skip_reason": "no_district_mapping"})
            continue

        fields = [part for part in str(seat.get("fields_to_fill") or "").split(";") if part in COMPLETION_CORE_FIELDS]
        for var in VARIABLE_TO_RELIGION_COLUMN:
            if var in COMPLETION_CORE_FIELDS and var not in fields:
                fields.append(var)
        if not fields:
            fields = list(COMPLETION_CORE_FIELDS)

        method = _method_for_rows(district_rows)
        confidence = _confidence_for_rows(district_rows, missing_districts)
        geography_level = "district" if method == "district_proxy" else "district_weighted_estimate"

        for variable in fields:
            if field_already_present(master_row, variable):
                continue
            if (state_key, constituency_key, variable) in manual_keys:
                continue

            value = _estimate_value(district_rows, variable)
            if value is None:
                skipped_rows.append(
                    {
                        "canonical_key": key,
                        "variable": variable,
                        "skip_reason": "census_value_unavailable",
                    }
                )
                continue

            notes = _notes_for_estimate(variable, district_rows, missing_districts, method)
            candidate_rows.append(
                {
                    "state": seat["state"],
                    "constituency": seat["constituency"],
                    "state_key": state_key,
                    "constituency_key": constituency_key,
                    "variable": variable,
                    "value": round(float(value), 4),
                    "unit": VARIABLE_UNITS.get(variable, ""),
                    "method": method,
                    "confidence": confidence,
                    "geography_level": geography_level,
                    "districts_used": ", ".join(district_rows["delimitation_district"].astype(str).tolist()),
                    "districts_missing": ", ".join(missing_districts),
                    "mapping_share": round(float(1.0 - len(missing_districts) / max(len(district_rows) + len(missing_districts), 1)), 4),
                    "source_name": CENSUS_SOURCE_NAME,
                    "source_year": CENSUS_SOURCE_YEAR,
                    "notes": notes,
                    "skipped": False,
                    "skip_reason": "",
                }
            )
            manual_rows.append(
                {
                    "state": str(seat["state"]),
                    "constituency": str(seat["constituency"]),
                    "state_key": state_key,
                    "constituency_key": constituency_key,
                    "variable": variable,
                    "value": str(round(float(value), 4)),
                    "unit": VARIABLE_UNITS.get(variable, ""),
                    "source_name": CENSUS_SOURCE_NAME,
                    "source_url_or_document": CENSUS_SOURCE_URL,
                    "source_year": CENSUS_SOURCE_YEAR,
                    "geography_level": geography_level,
                    "method": method,
                    "confidence": confidence,
                    "notes": notes,
                    "entered_by": "census_autofill_pipeline",
                    "last_updated": date.today().isoformat(),
                }
            )

    candidates = pd.DataFrame(candidate_rows)
    manual_candidates = pd.DataFrame(manual_rows, columns=MANUAL_ENTRY_COLUMNS)
    candidates.to_csv(AUTOFILL_CANDIDATES_PATH, index=False)
    manual_candidates.to_csv(MANUAL_AUTOFILL_CANDIDATES_PATH, index=False)
    return candidates, pd.DataFrame(skipped_rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-refresh-aliases", action="store_true")
    args = parser.parse_args()

    candidates, skipped = autofill_constituency_core_demographics(
        refresh_aliases=not args.no_refresh_aliases,
    )

    seats = candidates[["state_key", "constituency_key"]].drop_duplicates() if not candidates.empty else pd.DataFrame()
    print("\nCensus 2011 constituency autofill candidates")
    print(f"  Candidate rows: {len(candidates)}")
    print(f"  Seats with candidates: {len(seats)}")
    print(f"  Fields covered: {sorted(candidates['variable'].unique().tolist()) if not candidates.empty else []}")
    print(f"  Skipped entries: {len(skipped)}")
    if not skipped.empty:
        print("\n  Top skip reasons:")
        for reason, count in skipped["skip_reason"].value_counts().head(10).items():
            print(f"    {reason}: {count}")
    print(f"\n  Review before merge:")
    print(f"    {AUTOFILL_CANDIDATES_PATH}")
    print(f"    {MANUAL_AUTOFILL_CANDIDATES_PATH}")
    print("\n  These candidates were NOT appended to manual_constituency_demographics.csv.")
    print("  Review source notes and confidence, then append approved rows manually.")


if __name__ == "__main__":
    main()
