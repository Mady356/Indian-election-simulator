"""Diagnose seats skipped by the Census autofill pipeline."""

from __future__ import annotations

import argparse

import pandas as pd

from src.demographics.census.autofill_constituency_core_demographics import (
    _build_delimitation_map,
    _district_rows_for_constituency,
    _load_worklist_targets,
)
from src.demographics.census.common import (
    ALIAS_REPAIR_REPORT_PATH,
    AUTOFILL_CANDIDATES_PATH,
    CENSUS_DISTRICT_CORE_PATH,
    CENSUS_DISTRICT_RELIGION_PATH,
    COMPLETION_CORE_FIELDS,
    DELIMITATION_CENSUS_ALIAS_PATH,
    FINAL_543_UNIVERSE_PATH,
    SKIPPED_DIAGNOSTICS_MD_PATH,
    SKIPPED_DIAGNOSTICS_PATH,
    canonical_constituency_keys,
    canonical_seat_key,
    canonical_state_key,
    clean_delimitation_constituency_name,
    closest_name_match,
    ensure_dirs,
    load_frontend_seats,
    load_geojson_seats,
    lookup_key,
    names_similar,
    normalize_key,
)
from src.demographics.manual.common import DELIMITATION_PATH, MASTER_WITH_MANUAL_PATH


def _recommended_action(
    skip_reason: str,
    repair_class: str,
    exists_master: bool,
    exists_frontend: bool,
    possible_alias: str,
) -> str:
    if repair_class == "alias_duplicate" or skip_reason == "likely_duplicate":
        return "likely_duplicate"
    if repair_class == "reference_old_name":
        return "exclude_old_reference_name"
    if possible_alias:
        return "map_alias_to_current_name"
    if skip_reason == "no_delimitation_mapping":
        return "add_missing_delimitation_mapping"
    if not exists_master and exists_frontend:
        return "manual_research_required"
    if not exists_master:
        return "exclude_old_reference_name"
    return "manual_research_required"


def _closest_delimitation_match(state_key: str, constituency_key: str, delim: pd.DataFrame) -> str:
    state_norm = canonical_state_key(state_key)
    pc_norm = normalize_key(constituency_key)
    best = ""
    for _, row in delim.iterrows():
        if canonical_state_key(row.get("state", "")) != state_norm:
            continue
        pc = normalize_key(clean_delimitation_constituency_name(row.get("lok_sabha_constituency", "")))
        if names_similar(pc_norm, pc) or pc_norm in pc or pc in pc_norm:
            return str(row.get("lok_sabha_constituency"))
    return best


def diagnose_skipped_seats() -> pd.DataFrame:
    ensure_dirs()
    repair_report = pd.read_csv(ALIAS_REPAIR_REPORT_PATH) if ALIAS_REPAIR_REPORT_PATH.exists() else pd.DataFrame()
    targets = _load_worklist_targets(repair_report)

    if FINAL_543_UNIVERSE_PATH.exists():
        universe = pd.read_csv(FINAL_543_UNIVERSE_PATH)
        universe_keys = set(universe["canonical_seat_key"])
        targets = targets[
            targets["canonical_key"].isin(universe_keys)
            | targets.apply(
                lambda row: canonical_seat_key(row["state_key"], row["constituency_key"]) in universe_keys,
                axis=1,
            )
        ]

    candidates = pd.read_csv(AUTOFILL_CANDIDATES_PATH) if AUTOFILL_CANDIDATES_PATH.exists() else pd.DataFrame()
    candidate_counts: dict[str, int] = {}
    if not candidates.empty:
        candidate_counts = (
            candidates.assign(
                key=candidates.apply(
                    lambda row: lookup_key(str(row["state_key"]), str(row["constituency_key"])),
                    axis=1,
                )
            )
            .groupby("key")
            .size()
            .to_dict()
        )

    master = pd.read_csv(MASTER_WITH_MANUAL_PATH)
    master_keys = {lookup_key(str(r.state_key), str(r.constituency_key)) for _, r in master.iterrows()}
    frontend = load_frontend_seats()
    geojson = load_geojson_seats()
    delim_raw = pd.read_csv(DELIMITATION_PATH)
    delim_map = _build_delimitation_map()
    alias_table = pd.read_csv(DELIMITATION_CENSUS_ALIAS_PATH) if DELIMITATION_CENSUS_ALIAS_PATH.exists() else pd.DataFrame()
    census_core = pd.read_csv(CENSUS_DISTRICT_CORE_PATH) if CENSUS_DISTRICT_CORE_PATH.exists() else pd.DataFrame()
    census_religion = pd.read_csv(CENSUS_DISTRICT_RELIGION_PATH) if CENSUS_DISTRICT_RELIGION_PATH.exists() else pd.DataFrame()

    repair_by_key: dict[str, str] = {}
    if not repair_report.empty:
        for _, row in repair_report.iterrows():
            key = canonical_seat_key(row.get("state_key", ""), row.get("constituency_key", ""))
            repair_by_key[key] = str(row.get("repair_class", ""))

    rows: list[dict[str, object]] = []
    for _, seat in targets.iterrows():
        state_key, constituency_key = canonical_constituency_keys(seat["state_key"], seat["constituency_key"])
        key = lookup_key(state_key, constituency_key)
        filled = candidate_counts.get(key, 0)
        fields_to_fill = [part for part in str(seat.get("fields_to_fill") or "").split(";") if part in COMPLETION_CORE_FIELDS]
        expected_fields = len(fields_to_fill) if fields_to_fill else len(COMPLETION_CORE_FIELDS)

        district_rows, missing_districts = _district_rows_for_constituency(
            state_key, constituency_key, delim_map, alias_table, census_core, census_religion
        )

        if filled == 0 and district_rows.empty:
            skip_reason = "no_delimitation_mapping"
        elif filled == 0:
            skip_reason = "census_value_unavailable"
        elif filled < expected_fields:
            skip_reason = "partial_field_skip"
        else:
            continue

        possible_alias = ""
        if key not in master_keys:
            possible_alias = closest_name_match(state_key, constituency_key, frontend) or closest_name_match(
                state_key, constituency_key, geojson
            )

        repair_class = repair_by_key.get(key, "")
        exists_master = key in master_keys
        exists_frontend = key in frontend

        rows.append(
            {
                "state": seat.get("state"),
                "constituency": seat.get("constituency"),
                "state_key": state_key,
                "constituency_key": constituency_key,
                "completion_category": seat.get("completion_category"),
                "exists_in_election_master": exists_master,
                "exists_in_frontend_constituencies": exists_frontend,
                "exists_in_geojson": key in geojson,
                "exists_in_delimitation_reference": bool(
                    _closest_delimitation_match(state_key, constituency_key, delim_raw)
                ),
                "possible_state_alias": _alias_label_state(str(seat.get("state_key", ""))),
                "possible_constituency_alias": possible_alias,
                "closest_delimitation_match": _closest_delimitation_match(state_key, constituency_key, delim_raw),
                "closest_frontend_match": closest_name_match(state_key, constituency_key, frontend),
                "skip_reason": skip_reason,
                "districts_missing": ", ".join(missing_districts),
                "autofill_rows_created": filled,
                "expected_core_fields": expected_fields,
                "recommended_action": _recommended_action(
                    skip_reason,
                    repair_class,
                    exists_master,
                    exists_frontend,
                    possible_alias,
                ),
            }
        )

    diagnostics = pd.DataFrame(rows)
    diagnostics.to_csv(SKIPPED_DIAGNOSTICS_PATH, index=False)
    SKIPPED_DIAGNOSTICS_MD_PATH.write_text(_build_markdown(diagnostics), encoding="utf-8")
    return diagnostics


def _alias_label_state(state_key: str) -> str:
    raw = normalize_key(state_key)
    canonical = canonical_state_key(state_key)
    if raw != canonical:
        return f"{raw} -> {canonical}"
    return ""


def _build_markdown(diagnostics: pd.DataFrame) -> str:
    lines = [
        "# Skipped Census autofill diagnostics",
        "",
        f"- Total skipped seats: {len(diagnostics)}",
        "",
    ]
    if diagnostics.empty:
        lines.append("_No skipped seats._")
        return "\n".join(lines) + "\n"

    lines.append("## By skip reason")
    lines.append("")
    for reason, group in diagnostics.groupby("skip_reason"):
        lines.append(f"### {reason} ({len(group)})")
        for _, row in group.sort_values(["state", "constituency"]).head(25).iterrows():
            lines.append(
                f"- {row['state']} / {row['constituency']}: {row['recommended_action']} "
                f"(delimitation match: {row.get('closest_delimitation_match') or 'none'})"
            )
        if len(group) > 25:
            lines.append(f"- ... and {len(group) - 25} more")
        lines.append("")

    lines.append("## By recommended action")
    lines.append("")
    for action, count in diagnostics["recommended_action"].value_counts().items():
        lines.append(f"- {action}: {count}")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    diagnostics = diagnose_skipped_seats()
    print("Skipped autofill seat diagnostics")
    print(f"  Skipped seats: {len(diagnostics)}")
    if not diagnostics.empty:
        print("\n  Skip reasons:")
        for reason, count in diagnostics["skip_reason"].value_counts().items():
            print(f"    {reason}: {count}")
        print("\n  Recommended actions:")
        for action, count in diagnostics["recommended_action"].value_counts().items():
            print(f"    {action}: {count}")
    print(f"\n  Output: {SKIPPED_DIAGNOSTICS_PATH}")
    print(f"  Output: {SKIPPED_DIAGNOSTICS_MD_PATH}")


if __name__ == "__main__":
    main()
