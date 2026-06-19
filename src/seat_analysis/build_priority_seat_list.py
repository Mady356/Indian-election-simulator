"""Build priority seat list and manual notes template."""

from __future__ import annotations

import pandas as pd

from src.seat_analysis.common import (
    MAJOR_CONSTITUENCIES,
    MANUAL_COLUMNS,
    MANUAL_TEMPLATE_PATH,
    PRIORITY_CSV_PATH,
    ensure_dirs,
    load_master,
    load_top_swing,
    lookup_key,
    normalize_key,
    to_bool,
)


REASON_SCORES = {
    "seat_flip": 30,
    "closest_2024": 25,
    "top_bjp_gain": 20,
    "top_bjp_loss": 20,
    "top_inc_gain": 20,
    "top_inc_loss": 20,
    "major_constituency": 15,
}


def _major_lookup() -> set[str]:
    return {normalize_key(name) for name in MAJOR_CONSTITUENCIES}


def _match_master_row(master: pd.DataFrame, state: str, constituency: str) -> pd.Series | None:
    state_norm = normalize_key(state)
    constituency_norm = normalize_key(constituency)
    for _, row in master.iterrows():
        if (
            normalize_key(row["state"]) == state_norm
            or normalize_key(row["state_key"]) == state_norm
        ) and normalize_key(row["constituency"]) == constituency_norm:
            return row
    return None


def _add_reason(
    seat_reasons: dict[str, dict[str, object]],
    row: pd.Series,
    reason: str,
    score: int,
) -> None:
    key = lookup_key(str(row["state_key"]), str(row["constituency_key"]))
    entry = seat_reasons.setdefault(
        key,
        {
            "state": str(row["state"]),
            "constituency": str(row["constituency"]),
            "state_key": str(row["state_key"]),
            "constituency_key": str(row["constituency_key"]),
            "reasons": [],
            "priority_score": 0,
        },
    )
    if reason not in entry["reasons"]:
        entry["reasons"].append(reason)
    entry["priority_score"] = int(entry["priority_score"]) + score


def build_priority_seats(master: pd.DataFrame, top_swing: pd.DataFrame) -> pd.DataFrame:
    seat_reasons: dict[str, dict[str, object]] = {}
    majors = _major_lookup()

    for _, row in master.iterrows():
        if to_bool(row.get("winner_changed")):
            _add_reason(seat_reasons, row, "seat_flip", REASON_SCORES["seat_flip"])

        if normalize_key(row["constituency"]) in majors:
            _add_reason(seat_reasons, row, "major_constituency", REASON_SCORES["major_constituency"])

    if not top_swing.empty:
        section_map = {
            "top_25_bjp_gains": ("top_bjp_gain", REASON_SCORES["top_bjp_gain"]),
            "top_25_bjp_losses": ("top_bjp_loss", REASON_SCORES["top_bjp_loss"]),
            "top_25_inc_gains": ("top_inc_gain", REASON_SCORES["top_inc_gain"]),
            "top_25_inc_losses": ("top_inc_loss", REASON_SCORES["top_inc_loss"]),
            "closest_25_seats_2024": ("closest_2024", REASON_SCORES["closest_2024"]),
        }
        for section, (reason, score) in section_map.items():
            section_rows = top_swing[top_swing["table_section"] == section]
            for _, swing_row in section_rows.iterrows():
                matched = _match_master_row(
                    master,
                    str(swing_row.get("state", "")),
                    str(swing_row.get("constituency", "")),
                )
                if matched is not None:
                    _add_reason(seat_reasons, matched, reason, score)

    closest = master[master["margin_2024"].notna()].copy()
    if not closest.empty:
        closest["margin_2024"] = closest["margin_2024"].astype(float)
        for _, row in closest.nsmallest(25, "margin_2024").iterrows():
            _add_reason(seat_reasons, row, "closest_2024", REASON_SCORES["closest_2024"])

    for party, col in (("bjp", "bjp_swing_2019_2024"), ("inc", "inc_swing_2019_2024")):
        valid = master[master[col].notna()].copy()
        if valid.empty:
            continue
        valid[col] = valid[col].astype(float)
        for _, row in valid.nlargest(25, col).iterrows():
            _add_reason(seat_reasons, row, f"top_{party}_gain", REASON_SCORES[f"top_{party}_gain"])
        for _, row in valid.nsmallest(25, col).iterrows():
            _add_reason(seat_reasons, row, f"top_{party}_loss", REASON_SCORES[f"top_{party}_loss"])

    priority_rows: list[dict[str, object]] = []
    for entry in sorted(
        seat_reasons.values(),
        key=lambda item: (-int(item["priority_score"]), str(item["constituency"])),
    ):
        reasons = list(entry["reasons"])
        priority_rows.append(
            {
                "state": entry["state"],
                "constituency": entry["constituency"],
                "reason": ";".join(reasons),
                "priority_score": entry["priority_score"],
                "suggested_manual_review": "yes" if int(entry["priority_score"]) >= 30 else "optional",
            }
        )

    priority = pd.DataFrame(priority_rows)
    if priority.empty:
        return priority
    priority.insert(0, "priority_rank", range(1, len(priority) + 1))
    return priority


def build_manual_template(priority: pd.DataFrame, master: pd.DataFrame) -> pd.DataFrame:
    if priority.empty:
        return pd.DataFrame(columns=MANUAL_COLUMNS)

    merged = priority.merge(
        master[["state", "constituency", "state_key", "constituency_key"]],
        on=["state", "constituency"],
        how="inner",
    ).drop_duplicates(subset=["state_key", "constituency_key"])

    template_rows: list[dict[str, object]] = []
    for _, row in merged.iterrows():
        template_rows.append(
            {
                "state": row["state"],
                "constituency": row["constituency"],
                "state_key": row["state_key"],
                "constituency_key": row["constituency_key"],
                "manual_summary": "",
                "manual_electoral_movement": "",
                "manual_key_factors": "",
                "manual_demographic_context": "",
                "manual_local_context": "",
                "manual_what_to_watch": "",
                "manual_confidence": "",
                "analyst_name": "",
                "last_reviewed": "",
                "source_notes": "",
            }
        )

    return pd.DataFrame(template_rows, columns=MANUAL_COLUMNS)


def main() -> None:
    ensure_dirs()
    master = load_master()
    top_swing = load_top_swing()

    priority = build_priority_seats(master, top_swing)
    priority.to_csv(PRIORITY_CSV_PATH, index=False)

    template = build_manual_template(priority, master)
    template.to_csv(MANUAL_TEMPLATE_PATH, index=False)

    print(f"Wrote {len(priority)} priority seats to {PRIORITY_CSV_PATH}")
    print(f"Wrote {len(template)} manual template rows to {MANUAL_TEMPLATE_PATH}")


if __name__ == "__main__":
    main()
