"""Build a master seat completion worklist across election and demographic gaps."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass, field

import pandas as pd

from src.demographics.manual.common import (
    COMPLETION_BY_STATE_PATH,
    COMPLETION_CHECKLIST_MD_PATH,
    COMPLETION_CORE_FIELDS,
    COMPLETION_WORKLIST_PATH,
    CONSTITUENCIES_JSON_PATH,
    DELIMITATION_PATH,
    GEOJSON_PATH,
    MAJOR_STATE_KEYS,
    MANUAL_CSV_PATH,
    MASTER_PATH,
    MASTER_WITH_MANUAL_PATH,
    PRIORITY_SEAT_LIST_PATH,
    clean_delimitation_constituency_name,
    data_quality_label_from_row,
    default_unit,
    ensure_dirs,
    generated_value_for_variable,
    lookup_key,
    nan_to_none,
    normalize_key,
    to_float,
)
from src.demographics.manual.validate_manual_demographics import validate_manual_csv

COMPLETION_CATEGORIES = [
    "complete_generated",
    "complete_manual",
    "mixed_sources",
    "election_only_needs_demographics",
    "low_coverage_needs_review",
    "partial_demographics_missing_core_fields",
    "no_election_data_needs_election_results",
    "reference_only_not_in_current_election",
    "unknown_gap",
]

INCOMPLETE_CATEGORIES = {
    "election_only_needs_demographics",
    "low_coverage_needs_review",
    "partial_demographics_missing_core_fields",
    "no_election_data_needs_election_results",
    "reference_only_not_in_current_election",
    "unknown_gap",
}

CHECKLIST_SECTIONS = {
    "election_only_needs_demographics": "Election-only / needs demographics",
    "no_election_data_needs_election_results": "No election data",
    "reference_only_not_in_current_election": "Reference only / not in current election",
    "low_coverage_needs_review": "Low coverage",
    "partial_demographics_missing_core_fields": "Partial demographics / missing core fields",
    "unknown_gap": "Unknown gaps",
}


@dataclass
class SeatRecord:
    key: str
    state: str = ""
    constituency: str = ""
    state_key: str = ""
    constituency_key: str = ""
    exists_in_election_master: bool = False
    exists_in_frontend_constituencies: bool = False
    exists_in_geojson: bool = False
    exists_in_delimitation_reference: bool = False
    master_row: dict[str, object] = field(default_factory=dict)
    frontend_row: dict[str, object] = field(default_factory=dict)
    priority_rank: int | None = None
    priority_reason: str = ""


def _load_master() -> pd.DataFrame:
    path = MASTER_WITH_MANUAL_PATH if MASTER_WITH_MANUAL_PATH.exists() else MASTER_PATH
    return pd.read_csv(path)


def _load_manual_rows() -> pd.DataFrame:
    if not MANUAL_CSV_PATH.exists():
        return pd.DataFrame()
    manual = pd.read_csv(MANUAL_CSV_PATH)
    if manual.empty:
        return manual
    return manual[manual["value"].notna() & (manual["value"].astype(str).str.strip() != "")].copy()


def _valid_manual_keys() -> set[tuple[str, str, str]]:
    report = validate_manual_csv()
    if report.empty or "status" not in report.columns:
        return set()
    valid = report[report["status"] == "valid"]
    return {
        (str(row["state_key"]).strip(), str(row["constituency_key"]).strip(), str(row["variable"]).strip())
        for _, row in valid.iterrows()
    }


def _load_priority_lookup() -> dict[str, dict[str, object]]:
    if not PRIORITY_SEAT_LIST_PATH.exists():
        return {}
    df = pd.read_csv(PRIORITY_SEAT_LIST_PATH)
    lookup: dict[str, dict[str, object]] = {}
    for _, row in df.iterrows():
        key = lookup_key(str(row["state"]), str(row["constituency"]))
        lookup[key] = {
            "priority_rank": int(row.get("priority_rank", 9999)),
            "priority_reason": str(row.get("reason", "")),
            "priority_score": float(row.get("priority_score", 0) or 0),
        }
    return lookup


def _load_geojson_seats() -> dict[str, dict[str, str]]:
    if not GEOJSON_PATH.exists():
        return {}
    payload = json.loads(GEOJSON_PATH.read_text(encoding="utf-8"))
    seats: dict[str, dict[str, str]] = {}
    for feature in payload.get("features", []):
        props = feature.get("properties", {})
        state = str(props.get("st_name", "")).strip()
        constituency = str(props.get("pc_name", "")).strip()
        if not state or not constituency:
            continue
        state_key = normalize_key(state)
        constituency_key = normalize_key(constituency)
        key = lookup_key(state_key, constituency_key)
        seats[key] = {
            "state": state,
            "constituency": constituency,
            "state_key": state_key,
            "constituency_key": constituency_key,
        }
    return seats


def _load_delimitation_seats() -> dict[str, dict[str, str]]:
    if not DELIMITATION_PATH.exists():
        return {}
    df = pd.read_csv(DELIMITATION_PATH)
    seats: dict[str, dict[str, str]] = {}
    for _, row in df.iterrows():
        state = str(row.get("state", "")).strip()
        constituency_raw = clean_delimitation_constituency_name(row.get("lok_sabha_constituency", ""))
        if not state or not constituency_raw:
            continue
        state_key = normalize_key(state)
        constituency_key = normalize_key(constituency_raw)
        key = lookup_key(state_key, constituency_key)
        seats[key] = {
            "state": state,
            "constituency": constituency_raw,
            "state_key": state_key,
            "constituency_key": constituency_key,
        }
    return seats


def _load_frontend_seats() -> dict[str, dict[str, object]]:
    if not CONSTITUENCIES_JSON_PATH.exists():
        return {}
    records = json.loads(CONSTITUENCIES_JSON_PATH.read_text(encoding="utf-8"))
    seats: dict[str, dict[str, object]] = {}
    for row in records:
        state_key = str(row.get("state_key", "")).strip()
        constituency_key = str(row.get("constituency_key", "")).strip()
        key = lookup_key(state_key, constituency_key)
        seats[key] = row
    return seats


def _compact_key_part(value: object) -> str:
    text = normalize_key(value)
    for token in ("AND", "THE", "LOK SABHA"):
        text = text.replace(token, " ")
    return re.sub(r"\s+", " ", text).strip()


def _names_similar(left: str, right: str) -> bool:
    if left == right:
        return True
    if not left or not right:
        return False
    if left in right or right in left:
        return min(len(left), len(right)) >= 5
    prefix = min(len(left), len(right), 6)
    return left[:prefix] == right[:prefix] and prefix >= 5


def build_master_alias_map(master: pd.DataFrame) -> tuple[dict[str, str], dict[str, list[tuple[str, str]]]]:
    aliases: dict[str, str] = {}
    master_by_state: dict[str, list[tuple[str, str]]] = {}

    for _, row in master.iterrows():
        canonical = lookup_key(str(row["state_key"]), str(row["constituency_key"]))
        state_norm = normalize_key(row["state_key"])
        master_by_state.setdefault(state_norm, []).append(
            (canonical, _compact_key_part(row["constituency_key"]))
        )
        candidates = {
            lookup_key(str(row["state_key"]), str(row["constituency_key"])),
            lookup_key(str(row["state"]), str(row["constituency"])),
            lookup_key(_compact_key_part(row["state_key"]), _compact_key_part(row["constituency_key"])),
            lookup_key(_compact_key_part(row["state"]), _compact_key_part(row["constituency"])),
        }
        for candidate in candidates:
            aliases[candidate] = canonical
    return aliases, master_by_state


def resolve_canonical_key(
    key: str,
    alias_map: dict[str, str],
    master_by_state: dict[str, list[tuple[str, str]]],
) -> str:
    if key in alias_map:
        return alias_map[key]
    compact = lookup_key(
        _compact_key_part(key.split("::", 1)[0]),
        _compact_key_part(key.split("::", 1)[1]) if "::" in key else "",
    )
    if compact in alias_map:
        return alias_map[compact]

    state_part, constituency_part = key.split("::", 1) if "::" in key else (key, "")
    state_norm = normalize_key(state_part)
    pc = _compact_key_part(constituency_part)
    for canonical, master_pc in master_by_state.get(state_norm, []):
        if _names_similar(pc, master_pc):
            return canonical
    return alias_map.get(compact, key)


def build_seat_universe() -> dict[str, SeatRecord]:
    master = _load_master()
    alias_map, master_by_state = build_master_alias_map(master)
    frontend = _load_frontend_seats()
    geojson = _load_geojson_seats()
    delimitation = _load_delimitation_seats()
    priority = _load_priority_lookup()

    universe: dict[str, SeatRecord] = {}

    def ensure(key: str) -> SeatRecord:
        canonical = resolve_canonical_key(key, alias_map, master_by_state)
        if canonical not in universe:
            universe[canonical] = SeatRecord(key=canonical)
        return universe[canonical]

    def attach_source_flags(
        seat: SeatRecord,
        source_key: str,
        *,
        geo: bool = False,
        delimit: bool = False,
        frontend_flag: bool = False,
    ) -> None:
        if geo:
            seat.exists_in_geojson = True
        if delimit:
            seat.exists_in_delimitation_reference = True
        if frontend_flag:
            seat.exists_in_frontend_constituencies = True
        if source_key != seat.key and source_key in priority:
            if seat.priority_rank is None:
                seat.priority_rank = int(priority[source_key]["priority_rank"])
                seat.priority_reason = str(priority[source_key].get("priority_reason", ""))

    for _, row in master.iterrows():
        state_key = str(row["state_key"]).strip()
        constituency_key = str(row["constituency_key"]).strip()
        key = lookup_key(state_key, constituency_key)
        seat = ensure(key)
        seat.state = str(row["state"])
        seat.constituency = str(row["constituency"])
        seat.state_key = state_key
        seat.constituency_key = constituency_key
        seat.exists_in_election_master = True
        seat.master_row = row.to_dict()

    for key, row in frontend.items():
        seat = ensure(key)
        seat.exists_in_frontend_constituencies = True
        seat.frontend_row = row
        attach_source_flags(seat, key, frontend_flag=True)
        if not seat.state:
            seat.state = str(row.get("state", ""))
            seat.constituency = str(row.get("constituency", ""))
            seat.state_key = str(row.get("state_key", "")).strip()
            seat.constituency_key = str(row.get("constituency_key", "")).strip()

    for key, row in geojson.items():
        seat = ensure(key)
        attach_source_flags(seat, key, geo=True)
        if not seat.state:
            seat.state = row["state"]
            seat.constituency = row["constituency"]
            seat.state_key = row["state_key"]
            seat.constituency_key = row["constituency_key"]

    for key, row in delimitation.items():
        seat = ensure(key)
        attach_source_flags(seat, key, delimit=True)
        if not seat.state:
            seat.state = row["state"]
            seat.constituency = row["constituency"]
            seat.state_key = row["state_key"]
            seat.constituency_key = row["constituency_key"]

    for key, info in priority.items():
        seat = ensure(key)
        if seat.priority_rank is None:
            seat.priority_rank = int(info["priority_rank"])
            seat.priority_reason = str(info.get("priority_reason", ""))

    return universe


def _has_election_data(seat: SeatRecord) -> bool:
    if not seat.exists_in_election_master:
        return False
    row = seat.master_row
    for col in (
        "winner_2024",
        "winner_party_2024",
        "bjp_vote_share_2024",
        "inc_vote_share_2024",
        "margin_2024",
        "turnout_2024",
    ):
        if nan_to_none(row.get(col)) is not None:
            return True
    return False


def _core_field_satisfied(
    seat: SeatRecord,
    variable: str,
    valid_manual_keys: set[tuple[str, str, str]],
) -> bool:
    if seat.exists_in_election_master:
        row = pd.Series(seat.master_row)
        if generated_value_for_variable(row, variable) is not None:
            return True
    triple = (seat.state_key, seat.constituency_key, variable)
    return triple in valid_manual_keys


def _missing_core_fields(seat: SeatRecord, valid_manual_keys: set[tuple[str, str, str]]) -> list[str]:
    return [var for var in COMPLETION_CORE_FIELDS if not _core_field_satisfied(seat, var, valid_manual_keys)]


def _has_demographic_data(seat: SeatRecord) -> bool:
    if seat.frontend_row:
        source_type = str(nan_to_none(seat.frontend_row.get("demographic_source_type")) or "")
        if source_type and source_type != "election_only":
            return True
        label = str(nan_to_none(seat.frontend_row.get("data_quality_label")) or "")
        if label and label != "election_only":
            return True
    if seat.exists_in_election_master:
        row = pd.Series(seat.master_row)
        coverage = to_float(row.get("nfhs5_coverage_share"))
        source_type = str(nan_to_none(row.get("demographic_source_type")) or "")
        if source_type not in {"", "election_only"}:
            return True
        if coverage is not None and coverage > 0:
            return True
        if any(generated_value_for_variable(row, var) is not None for var in COMPLETION_CORE_FIELDS):
            return True
    return False


def classify_seat(seat: SeatRecord, valid_manual_keys: set[tuple[str, str, str]]) -> tuple[str, list[str], str]:
    missing_core = _missing_core_fields(seat, valid_manual_keys)
    has_election = _has_election_data(seat)
    has_demo = _has_demographic_data(seat)

    if not seat.exists_in_election_master:
        if seat.exists_in_delimitation_reference and not seat.exists_in_geojson and not seat.exists_in_frontend_constituencies:
            return "reference_only_not_in_current_election", missing_core, "Seat in delimitation reference only"
        if seat.exists_in_geojson or seat.exists_in_frontend_constituencies:
            return "no_election_data_needs_election_results", missing_core, "Seat in GeoJSON/frontend but missing from election master"
        if seat.exists_in_delimitation_reference:
            return "reference_only_not_in_current_election", missing_core, "Seat in delimitation reference only"
        return "unknown_gap", missing_core, "Seat known from reference sources but not election master"

    row = pd.Series(seat.master_row)
    source_type = str(nan_to_none(row.get("demographic_source_type")) or "election_only")
    coverage = to_float(row.get("nfhs5_coverage_share"))

    if not has_election:
        return "no_election_data_needs_election_results", missing_core, "Listed in election master but missing 2024 election fields"

    if source_type == "mixed":
        if not missing_core:
            return "mixed_sources", missing_core, "Generated and manual demographic sources present"
        return "partial_demographics_missing_core_fields", missing_core, "Mixed sources but core fields incomplete"

    if source_type == "manual" and not missing_core:
        return "complete_manual", missing_core, "Manual core demographic profile complete"

    if coverage is not None and 0 < coverage < 0.5:
        if not missing_core:
            return "low_coverage_needs_review", missing_core, "Low NFHS coverage share; review recommended"
        return "partial_demographics_missing_core_fields", missing_core, "Low coverage with missing core fields"

    if source_type == "election_only" or not has_demo:
        return "election_only_needs_demographics", missing_core, "Election data present; demographics missing"

    if not missing_core:
        if source_type == "manual":
            return "complete_manual", missing_core, "Manual demographic profile complete"
        return "complete_generated", missing_core, "Generated demographic profile complete"

    if has_demo:
        return "partial_demographics_missing_core_fields", missing_core, "Partial demographics; core fields missing"

    return "unknown_gap", missing_core, "Unclassified data gap"


def _is_politically_hot(seat: SeatRecord) -> bool:
    if seat.priority_rank is not None and seat.priority_rank <= 50:
        return True
    reason = (seat.priority_reason or "").lower()
    if any(token in reason for token in ("seat_flip", "closest_2024", "top_bjp", "top_inc", "major_constituency")):
        return True
    if seat.exists_in_election_master:
        row = seat.master_row
        if bool(row.get("winner_changed")):
            return True
        margin = to_float(row.get("margin_2024"))
        if margin is not None and margin < 5:
            return True
        swing = max(abs(to_float(row.get("bjp_swing_2019_2024")) or 0), abs(to_float(row.get("inc_swing_2019_2024")) or 0))
        if swing >= 10:
            return True
    return False


def assign_priority(
    seat: SeatRecord,
    category: str,
    state_missing_counts: dict[str, int],
) -> int:
    if category in {"complete_generated", "complete_manual", "mixed_sources"}:
        if category == "mixed_sources" and _missing_core_fields(seat, set()):
            return 3
        return 3

    score = 0
    if seat.priority_rank is not None:
        score += 4
    if category == "no_election_data_needs_election_results":
        score += 5
    if category == "election_only_needs_demographics" and normalize_key(seat.state_key) in MAJOR_STATE_KEYS:
        score += 3
    if _is_politically_hot(seat):
        score += 3
    if state_missing_counts.get(normalize_key(seat.state_key), 0) >= 10:
        score += 2
    if category == "low_coverage_needs_review":
        score += 2
    if category == "partial_demographics_missing_core_fields":
        score += 2
    if category == "election_only_needs_demographics":
        score += 1
    if category in {"reference_only_not_in_current_election", "unknown_gap"}:
        score += 1

    if score >= 5:
        return 1
    if score >= 2:
        return 2
    return 3


def build_worklist_rows(universe: dict[str, SeatRecord]) -> pd.DataFrame:
    valid_manual_keys = _valid_manual_keys()
    state_missing: dict[str, int] = {}
    for seat in universe.values():
        category, _, _ = classify_seat(seat, valid_manual_keys)
        if category in INCOMPLETE_CATEGORIES:
            state_missing[normalize_key(seat.state_key)] = state_missing.get(normalize_key(seat.state_key), 0) + 1

    rows: list[dict[str, object]] = []
    for seat in sorted(universe.values(), key=lambda item: (item.state, item.constituency)):
        category, missing_core, note = classify_seat(seat, valid_manual_keys)
        priority = assign_priority(seat, category, state_missing)

        master = seat.master_row
        frontend = seat.frontend_row
        row_series = pd.Series(master) if master else pd.Series(dtype=object)

        data_quality = str(
            nan_to_none(frontend.get("data_quality_label"))
            or (data_quality_label_from_row(row_series) if master else "election_only")
            or "election_only"
        )
        source_type = str(
            nan_to_none(frontend.get("demographic_source_type"))
            or nan_to_none(master.get("demographic_source_type"))
            or "election_only"
        )

        rows.append(
            {
                "state": seat.state,
                "constituency": seat.constituency,
                "state_key": seat.state_key,
                "constituency_key": seat.constituency_key,
                "exists_in_election_master": seat.exists_in_election_master,
                "exists_in_frontend_constituencies": seat.exists_in_frontend_constituencies,
                "exists_in_geojson": seat.exists_in_geojson,
                "exists_in_delimitation_reference": seat.exists_in_delimitation_reference,
                "has_election_data": _has_election_data(seat),
                "has_demographic_data": _has_demographic_data(seat),
                "demographic_source_type": source_type,
                "data_quality_label": data_quality,
                "nfhs5_coverage_share": to_float(master.get("nfhs5_coverage_share")) if master else None,
                "change_coverage_share": to_float(master.get("change_coverage_share")) if master else None,
                "districts_used": nan_to_none(master.get("districts_used")) if master else None,
                "districts_missing": nan_to_none(master.get("districts_missing")) if master else None,
                "winner_2019": nan_to_none(master.get("winner_2019")) if master else None,
                "winner_2024": nan_to_none(master.get("winner_2024")) if master else None,
                "winner_party_2019": nan_to_none(master.get("winner_party_2019")) if master else None,
                "winner_party_2024": nan_to_none(master.get("winner_party_2024")) if master else None,
                "bjp_vote_share_2019": to_float(master.get("bjp_vote_share_2019")) if master else None,
                "bjp_vote_share_2024": to_float(master.get("bjp_vote_share_2024")) if master else None,
                "inc_vote_share_2019": to_float(master.get("inc_vote_share_2019")) if master else None,
                "inc_vote_share_2024": to_float(master.get("inc_vote_share_2024")) if master else None,
                "bjp_swing_2019_2024": to_float(master.get("bjp_swing_2019_2024")) if master else None,
                "inc_swing_2019_2024": to_float(master.get("inc_swing_2019_2024")) if master else None,
                "margin_2024": to_float(master.get("margin_2024")) if master else None,
                "priority_rank": seat.priority_rank,
                "priority_reason": seat.priority_reason or None,
                "completion_category": category,
                "completion_priority": priority,
                "fields_to_fill": ";".join(missing_core),
                "notes": note,
            }
        )

    return pd.DataFrame(rows)


def build_state_summary(worklist: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for state, group in worklist.groupby("state", sort=True):
        total = len(group)
        category_counts = group["completion_category"].value_counts().to_dict()
        complete = (
            category_counts.get("complete_generated", 0)
            + category_counts.get("complete_manual", 0)
            + category_counts.get("mixed_sources", 0)
        )
        priority_gaps = int(
            group[
                group["completion_category"].isin(INCOMPLETE_CATEGORIES)
                & (group["completion_priority"] == 1)
            ].shape[0]
        )
        row = {
            "state": state,
            "total_known_seats": total,
            "complete_generated": category_counts.get("complete_generated", 0),
            "complete_manual": category_counts.get("complete_manual", 0),
            "mixed_sources": category_counts.get("mixed_sources", 0),
            "election_only_needs_demographics": category_counts.get("election_only_needs_demographics", 0),
            "low_coverage_needs_review": category_counts.get("low_coverage_needs_review", 0),
            "partial_demographics_missing_core_fields": category_counts.get(
                "partial_demographics_missing_core_fields", 0
            ),
            "no_election_data_needs_election_results": category_counts.get(
                "no_election_data_needs_election_results", 0
            ),
            "reference_only_not_in_current_election": category_counts.get(
                "reference_only_not_in_current_election", 0
            ),
            "unknown_gap": category_counts.get("unknown_gap", 0),
            "completion_pct": round(100.0 * complete / total, 2) if total else 100.0,
            "priority_gaps": priority_gaps,
        }
        rows.append(row)
    return pd.DataFrame(rows)


def build_checklist_markdown(worklist: pd.DataFrame, state_summary: pd.DataFrame) -> str:
    total = len(worklist)
    complete = int(
        worklist["completion_category"].isin({"complete_generated", "complete_manual", "mixed_sources"}).sum()
    )
    election_only = int((worklist["completion_category"] == "election_only_needs_demographics").sum())
    no_election = int((worklist["completion_category"] == "no_election_data_needs_election_results").sum())
    low_coverage = int((worklist["completion_category"] == "low_coverage_needs_review").sum())
    partial = int((worklist["completion_category"] == "partial_demographics_missing_core_fields").sum())

    lines = [
        "# Master Seat Completion Checklist",
        "",
        "## Summary",
        f"- Total known seats: {total}",
        f"- Complete: {complete}",
        f"- Election-only: {election_only}",
        f"- No election data: {no_election}",
        f"- Low coverage: {low_coverage}",
        f"- Partial demographics: {partial}",
        "",
    ]

    incomplete = worklist[worklist["completion_category"].isin(INCOMPLETE_CATEGORIES)].copy()
    if incomplete.empty:
        lines.append("_All seats are complete._")
        return "\n".join(lines)

    for state in sorted(incomplete["state"].unique()):
        state_rows = incomplete[incomplete["state"] == state]
        lines.append(f"## {state}")
        lines.append("")

        for category, heading in CHECKLIST_SECTIONS.items():
            section = state_rows[state_rows["completion_category"] == category]
            if section.empty:
                continue
            lines.append(f"### {heading}")
            for _, row in section.sort_values(["completion_priority", "constituency"]).iterrows():
                fields = str(row.get("fields_to_fill") or "")
                if category == "no_election_data_needs_election_results":
                    task = "research election results"
                elif fields:
                    task = "fill core demographic fields"
                    if fields:
                        task += f" ({fields.replace(';', ', ')})"
                else:
                    task = str(row.get("notes") or "review data gap")
                lines.append(f"- [ ] {row['constituency']} — {task}")
            lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def print_console_summary(worklist: pd.DataFrame) -> None:
    print("Master seat completion worklist")
    print(f"  Total known seats: {len(worklist)}")
    print(f"  Seats with election data: {int(worklist['has_election_data'].sum())}")
    print(f"  Seats with no election data: {int((~worklist['has_election_data']).sum())}")
    print(
        "  Election-only seats: "
        f"{int((worklist['completion_category'] == 'election_only_needs_demographics').sum())}"
    )
    print(
        "  Low coverage seats: "
        f"{int((worklist['completion_category'] == 'low_coverage_needs_review').sum())}"
    )
    print(
        "  Partial demographic seats: "
        f"{int((worklist['completion_category'] == 'partial_demographics_missing_core_fields').sum())}"
    )

    incomplete = worklist[worklist["completion_category"].isin(INCOMPLETE_CATEGORIES)]
    if not incomplete.empty:
        top_states = (
            incomplete.groupby("state")
            .size()
            .sort_values(ascending=False)
            .head(10)
        )
        print("\n  Top 10 states by missing count:")
        for state, count in top_states.items():
            print(f"    {state}: {count}")

    print("\n  Output files:")
    print(f"    {COMPLETION_WORKLIST_PATH}")
    print(f"    {COMPLETION_BY_STATE_PATH}")
    print(f"    {COMPLETION_CHECKLIST_MD_PATH}")


def run_master_completion_worklist() -> tuple[pd.DataFrame, pd.DataFrame]:
    ensure_dirs()
    universe = build_seat_universe()
    worklist = build_worklist_rows(universe)
    state_summary = build_state_summary(worklist)
    checklist = build_checklist_markdown(worklist, state_summary)

    worklist.to_csv(COMPLETION_WORKLIST_PATH, index=False)
    state_summary.to_csv(COMPLETION_BY_STATE_PATH, index=False)
    COMPLETION_CHECKLIST_MD_PATH.write_text(checklist, encoding="utf-8")

    print_console_summary(worklist)
    return worklist, state_summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    run_master_completion_worklist()


if __name__ == "__main__":
    main()
