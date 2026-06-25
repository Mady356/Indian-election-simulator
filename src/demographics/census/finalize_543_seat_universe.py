"""Finalize the current Lok Sabha seat universe for manual sourcing."""

from __future__ import annotations

import argparse
import json

import pandas as pd

from src.demographics.census.common import (
    CLEANED_WORKLIST_PATH,
    COMPLETION_WORKLIST_PATH,
    CONSTITUENCY_ALIASES,
    FINAL_543_UNIVERSE_PATH,
    NON_543_EXCLUDE_PATH,
    STATE_ALIASES,
    canonical_constituency_keys,
    canonical_seat_key,
    canonical_state_key,
    ensure_dirs,
    load_frontend_seats,
    load_geojson_seats,
    lookup_key,
    normalize_key,
)
from src.demographics.manual.common import (
    DELIMITATION_PATH,
    MASTER_WITH_MANUAL_PATH,
    clean_delimitation_constituency_name,
)

SPECIAL_SEAT_NOTES = {
    lookup_key("GUJARAT", "SURAT"): (
        "2024 uncontested Lok Sabha seat (BJP unopposed); present in GeoJSON/delimitation "
        "but excluded from election master because no contested poll results were recorded."
    ),
}


def _load_delimitation_pc_keys() -> set[str]:
    if not DELIMITATION_PATH.exists():
        return set()
    delim = pd.read_csv(DELIMITATION_PATH)
    keys: set[str] = set()
    for _, row in delim.iterrows():
        pc = clean_delimitation_constituency_name(row.get("lok_sabha_constituency", ""))
        state_key, constituency_key = canonical_constituency_keys(row.get("state", ""), pc)
        keys.add(lookup_key(state_key, constituency_key))
    return keys


def _alias_label(state_key: str, constituency_key: str) -> str:
    state = canonical_state_key(state_key)
    constituency = normalize_key(constituency_key)
    if state in STATE_ALIASES and normalize_key(state_key) != state:
        return f"state:{normalize_key(state_key)}->{state}"
    alias = CONSTITUENCY_ALIASES.get((state, constituency))
    if alias:
        return f"constituency:{constituency}->{alias[1]}"
    return ""


def build_platform_universe() -> pd.DataFrame:
    frontend = load_frontend_seats()
    master = pd.read_csv(MASTER_WITH_MANUAL_PATH)
    geojson = load_geojson_seats()
    delim_keys = _load_delimitation_pc_keys()

    master_by_key = {
        lookup_key(str(row["state_key"]), str(row["constituency_key"])): row
        for _, row in master.iterrows()
    }

    rows: list[dict[str, object]] = []
    for key, row in sorted(frontend.items(), key=lambda item: (item[1].get("state", ""), item[1].get("constituency", ""))):
        state_key, constituency_key = canonical_constituency_keys(row.get("state_key", ""), row.get("constituency_key", ""))
        canon_key = lookup_key(state_key, constituency_key)
        master_row = master_by_key.get(canon_key)
        rows.append(
            {
                "state": row.get("state"),
                "constituency": row.get("constituency"),
                "state_key": state_key,
                "constituency_key": constituency_key,
                "canonical_seat_key": canon_key,
                "in_platform_master": master_row is not None,
                "in_frontend_constituencies": True,
                "in_geojson": canon_key in geojson,
                "in_delimitation_reference": canon_key in delim_keys,
                "demographic_source_type": row.get("demographic_source_type"),
                "data_quality_label": row.get("data_quality_label"),
                "completion_category": "",
                "election_result_status": "contested",
                "notes": "",
            }
        )

    return pd.DataFrame(rows)


def build_exclusion_table(
    universe: pd.DataFrame,
    worklist: pd.DataFrame,
    repair_report: pd.DataFrame | None,
) -> pd.DataFrame:
    universe_keys = set(universe["canonical_seat_key"])
    geojson = load_geojson_seats()
    rows: list[dict[str, object]] = []

    repair_by_index = {}
    if repair_report is not None and not repair_report.empty:
        repair_by_index = {int(row["row_index"]): row for _, row in repair_report.iterrows()}

    for idx, row in worklist.iterrows():
        canon_key = canonical_seat_key(row.get("state_key", ""), row.get("constituency_key", ""))
        if canon_key in universe_keys:
            continue

        repair = repair_by_index.get(idx)
        repair_class = str(repair.get("repair_class", "")) if repair is not None else ""
        exclude_reason = repair_class or str(row.get("completion_category", "unknown"))

        if canon_key in SPECIAL_SEAT_NOTES:
            exclude_reason = "uncontested_2024_not_in_election_master"

        if normalize_key(row.get("state_key", "")) in STATE_ALIASES and canonical_state_key(row.get("state_key", "")) in universe_keys:
            exclude_reason = "state_alias_duplicate"

        rows.append(
            {
                "state": row.get("state"),
                "constituency": row.get("constituency"),
                "state_key": row.get("state_key"),
                "constituency_key": row.get("constituency_key"),
                "canonical_seat_key": canon_key,
                "exclude_reason": exclude_reason,
                "repair_class": repair_class,
                "completion_category": row.get("completion_category"),
                "exists_in_election_master": row.get("exists_in_election_master"),
                "exists_in_frontend_constituencies": row.get("exists_in_frontend_constituencies"),
                "exists_in_geojson": row.get("exists_in_geojson"),
                "exists_in_delimitation_reference": row.get("exists_in_delimitation_reference"),
                "possible_alias": _alias_label(str(row.get("state_key", "")), str(row.get("constituency_key", ""))),
                "notes": SPECIAL_SEAT_NOTES.get(canon_key, ""),
            }
        )

    for key, meta in geojson.items():
        if key in universe_keys:
            continue
        if any(row.get("canonical_seat_key") == key for row in rows):
            continue
        rows.append(
            {
                "state": meta.get("state"),
                "constituency": meta.get("constituency"),
                "state_key": meta.get("state_key"),
                "constituency_key": meta.get("constituency_key"),
                "canonical_seat_key": key,
                "exclude_reason": "geojson_only_not_in_platform_universe",
                "repair_class": "",
                "completion_category": "",
                "exists_in_election_master": False,
                "exists_in_frontend_constituencies": False,
                "exists_in_geojson": True,
                "exists_in_delimitation_reference": key in _load_delimitation_pc_keys(),
                "possible_alias": "",
                "notes": SPECIAL_SEAT_NOTES.get(key, ""),
            }
        )

    return pd.DataFrame(rows)


def finalize_543_seat_universe() -> tuple[pd.DataFrame, pd.DataFrame]:
    ensure_dirs()
    universe = build_platform_universe()

    worklist_path = CLEANED_WORKLIST_PATH if CLEANED_WORKLIST_PATH.exists() else COMPLETION_WORKLIST_PATH
    worklist = pd.read_csv(worklist_path)
    repair_report = None
    from src.demographics.census.common import ALIAS_REPAIR_REPORT_PATH

    if ALIAS_REPAIR_REPORT_PATH.exists():
        repair_report = pd.read_csv(ALIAS_REPAIR_REPORT_PATH)

    worklist_by_key = {
        canonical_seat_key(row.get("state_key", ""), row.get("constituency_key", "")): row
        for _, row in worklist.iterrows()
    }
    for idx, row in universe.iterrows():
        wl = worklist_by_key.get(str(row["canonical_seat_key"]))
        if wl is not None:
            universe.at[idx, "completion_category"] = wl.get("completion_category", "")

    exclusions = build_exclusion_table(universe, worklist, repair_report)
    universe.to_csv(FINAL_543_UNIVERSE_PATH, index=False)
    exclusions.to_csv(NON_543_EXCLUDE_PATH, index=False)
    return universe, exclusions


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    universe, exclusions = finalize_543_seat_universe()
    print("Final Lok Sabha seat universe")
    print(f"  Platform universe seats: {len(universe)}")
    print(f"  Excluded non-platform records: {len(exclusions)}")
    print(f"  Output: {FINAL_543_UNIVERSE_PATH}")
    print(f"  Output: {NON_543_EXCLUDE_PATH}")
    if not exclusions.empty:
        print("\n  Top exclusion reasons:")
        for reason, count in exclusions["exclude_reason"].value_counts().head(10).items():
            print(f"    {reason}: {count}")


if __name__ == "__main__":
    main()
