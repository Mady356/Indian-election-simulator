"""Clean duplicate and name-mismatch records in the master completion worklist."""

from __future__ import annotations

import argparse

import pandas as pd

from src.demographics.census.common import (
    ALIAS_REPAIR_REPORT_PATH,
    CLEANED_WORKLIST_PATH,
    COMPLETION_WORKLIST_PATH,
    canonical_seat_key,
    canonical_state_key,
    ensure_dirs,
    lookup_key,
    normalize_key,
)
from src.demographics.manual.common import nan_to_none


def _names_similar(left: str, right: str) -> bool:
    if left == right:
        return True
    if not left or not right:
        return False
    if left in right or right in left:
        return min(len(left), len(right)) >= 5
    prefix = min(len(left), len(right), 6)
    return left[:prefix] == right[:prefix] and prefix >= 5


def classify_worklist_row(
    row: pd.Series,
    canonical_keys: dict[str, str],
    election_master_keys: set[str],
) -> tuple[str, str, str]:
    raw_key = lookup_key(str(row["state_key"]), str(row["constituency_key"]))
    canon_key = canonical_seat_key(row["state_key"], row["constituency_key"])

    if canon_key in canonical_keys and canonical_keys[canon_key] != raw_key:
        return "alias_duplicate", canon_key, f"Alias of canonical seat {canonical_keys[canon_key]}"

    exists_master = bool(row.get("exists_in_election_master"))
    exists_geo = bool(row.get("exists_in_geojson"))
    exists_delim = bool(row.get("exists_in_delimitation_reference"))
    category = str(row.get("completion_category", ""))

    if category == "reference_only_not_in_current_election":
        return "reference_old_name", canon_key, "Delimitation/reference old constituency name"

    if not exists_master and exists_geo and canon_key in election_master_keys:
        return "geojson_only", canon_key, "GeoJSON label variant of election master seat"

    if not exists_master and exists_geo:
        state_norm = canonical_state_key(row["state_key"])
        constituency_norm = normalize_key(row["constituency_key"])
        for master_key in election_master_keys:
            master_state, master_pc = master_key.split("::", 1)
            if canonical_state_key(master_state) == state_norm and _names_similar(
                constituency_norm, master_pc
            ):
                return "alias_duplicate", master_key, f"Name variant of election master seat {master_key}"

    if not exists_master and not exists_delim and not exists_geo:
        return "needs_manual_review", canon_key, "Seat key not matched to any source"

    if exists_master or category in {
        "election_only_needs_demographics",
        "partial_demographics_missing_core_fields",
        "low_coverage_needs_review",
        "mixed_sources",
    }:
        return "true_missing", canon_key, "Canonical seat with real data gap"

    if category == "no_election_data_needs_election_results":
        return "true_missing", canon_key, "Seat missing election results in master"

    return "needs_manual_review", canon_key, "Unclassified worklist row"


def build_alias_repair_report(worklist: pd.DataFrame, master: pd.DataFrame) -> pd.DataFrame:
    election_master_keys = {
        lookup_key(str(row["state_key"]), str(row["constituency_key"])) for _, row in master.iterrows()
    }

    canonical_keys: dict[str, str] = {}
    for _, row in worklist.iterrows():
        if not row.get("exists_in_election_master"):
            continue
        raw_key = lookup_key(str(row["state_key"]), str(row["constituency_key"]))
        canon_key = canonical_seat_key(row["state_key"], row["constituency_key"])
        if canon_key not in canonical_keys:
            canonical_keys[canon_key] = raw_key

    rows: list[dict[str, object]] = []
    for idx, row in worklist.iterrows():
        repair_class, canon_key, reason = classify_worklist_row(row, canonical_keys, election_master_keys)
        rows.append(
            {
                "row_index": idx,
                "state": row.get("state"),
                "constituency": row.get("constituency"),
                "state_key": row.get("state_key"),
                "constituency_key": row.get("constituency_key"),
                "canonical_state_key": canon_key.split("::", 1)[0] if "::" in canon_key else "",
                "canonical_constituency_key": canon_key.split("::", 1)[1] if "::" in canon_key else "",
                "repair_class": repair_class,
                "completion_category": row.get("completion_category"),
                "exists_in_election_master": row.get("exists_in_election_master"),
                "exists_in_geojson": row.get("exists_in_geojson"),
                "exists_in_delimitation_reference": row.get("exists_in_delimitation_reference"),
                "reason": reason,
            }
        )

    return pd.DataFrame(rows)


def build_cleaned_worklist(worklist: pd.DataFrame, repair_report: pd.DataFrame) -> pd.DataFrame:
    keep_classes = {"true_missing", "needs_manual_review"}
    keep_idx = repair_report[repair_report["repair_class"].isin(keep_classes)]["row_index"].tolist()
    cleaned = worklist.loc[keep_idx].copy()

    canon_map = {
        int(row["row_index"]): (
            row["canonical_state_key"],
            row["canonical_constituency_key"],
        )
        for _, row in repair_report.iterrows()
        if row["repair_class"] in keep_classes
    }
    for idx, (state_key, constituency_key) in canon_map.items():
        if idx not in cleaned.index:
            continue
        if state_key:
            cleaned.at[idx, "state_key"] = state_key
        if constituency_key:
            cleaned.at[idx, "constituency_key"] = constituency_key
    return cleaned.reset_index(drop=True)


def run_alias_cleaning() -> tuple[pd.DataFrame, pd.DataFrame]:
    ensure_dirs()
    if not COMPLETION_WORKLIST_PATH.exists():
        raise FileNotFoundError(f"Missing worklist: {COMPLETION_WORKLIST_PATH}")

    from src.demographics.census.common import MASTER_WITH_MANUAL_PATH

    worklist = pd.read_csv(COMPLETION_WORKLIST_PATH)
    master = pd.read_csv(MASTER_WITH_MANUAL_PATH)
    repair_report = build_alias_repair_report(worklist, master)
    cleaned = build_cleaned_worklist(worklist, repair_report)

    repair_report.to_csv(ALIAS_REPAIR_REPORT_PATH, index=False)
    cleaned.to_csv(CLEANED_WORKLIST_PATH, index=False)

    counts = repair_report["repair_class"].value_counts().to_dict()
    print("Completion worklist alias repair")
    print(f"  Input rows: {len(worklist)}")
    print(f"  Cleaned rows: {len(cleaned)}")
    print(f"  Classes: {counts}")
    print(f"  Report: {ALIAS_REPAIR_REPORT_PATH}")
    print(f"  Cleaned worklist: {CLEANED_WORKLIST_PATH}")
    return repair_report, cleaned


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    run_alias_cleaning()


if __name__ == "__main__":
    main()
