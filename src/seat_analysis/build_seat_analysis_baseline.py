"""Generate baseline Seat Intelligence Notes for every constituency."""

from __future__ import annotations

from datetime import date

import pandas as pd

from src.seat_analysis.common import (
    BASELINE_COLUMNS,
    BASELINE_CSV_PATH,
    CLOSE_MARGIN_THRESHOLD,
    DEMOGRAPHIC_NFHS5_COLS,
    HIGH_COVERAGE_THRESHOLD,
    HIGH_TURNOUT_CHANGE_THRESHOLD,
    LARGE_SWING_THRESHOLD,
    LOW_COVERAGE_THRESHOLD,
    data_quality_label,
    ensure_dirs,
    format_pct,
    format_points,
    has_demographics,
    load_master,
    nan_to_none,
    to_bool,
    to_float,
)


def _compute_key_factors(row: pd.Series, quality: str) -> list[str]:
    factors: list[str] = []

    if to_bool(row.get("winner_changed")):
        factors.append("seat_flip")

    margin_2024 = to_float(row.get("margin_2024"))
    if margin_2024 is not None and margin_2024 <= CLOSE_MARGIN_THRESHOLD:
        factors.append("close_contest_2024")

    bjp_swing = to_float(row.get("bjp_swing_2019_2024"))
    if bjp_swing is not None:
        if bjp_swing >= LARGE_SWING_THRESHOLD:
            factors.append("large_bjp_gain")
        elif bjp_swing <= -LARGE_SWING_THRESHOLD:
            factors.append("large_bjp_loss")

    inc_swing = to_float(row.get("inc_swing_2019_2024"))
    if inc_swing is not None:
        if inc_swing >= LARGE_SWING_THRESHOLD:
            factors.append("large_inc_gain")
        elif inc_swing <= -LARGE_SWING_THRESHOLD:
            factors.append("large_inc_loss")

    turnout_change = to_float(row.get("turnout_change"))
    if turnout_change is None:
        turnout_2019 = to_float(row.get("turnout_2019"))
        turnout_2024 = to_float(row.get("turnout_2024"))
        if turnout_2019 is not None and turnout_2024 is not None:
            turnout_change = turnout_2024 - turnout_2019
    if turnout_change is not None and abs(turnout_change) >= HIGH_TURNOUT_CHANGE_THRESHOLD:
        factors.append("high_turnout_change")

    coverage = to_float(row.get("nfhs5_coverage_share"))
    urban_pct = to_float(row.get("urban_pct_nfhs5"))
    if urban_pct is not None:
        if urban_pct >= 50:
            factors.append("urban_profile")
        elif urban_pct < 30:
            factors.append("rural_profile")

    if coverage is not None:
        if coverage >= HIGH_COVERAGE_THRESHOLD:
            factors.append("high_demographic_coverage")
        elif coverage < LOW_COVERAGE_THRESHOLD:
            factors.append("low_demographic_coverage")

    if quality == "election_only":
        factors.append("election_only_profile")

    districts_missing = nan_to_none(row.get("districts_missing"))
    if districts_missing:
        factors.append("district_coverage_gap")

    return factors


def _build_electoral_movement(row: pd.Series) -> str:
    constituency = str(row["constituency"])
    party_2019 = nan_to_none(row.get("winner_party_2019"))
    party_2024 = nan_to_none(row.get("winner_party_2024"))
    flipped = to_bool(row.get("winner_changed"))

    parts: list[str] = []
    if flipped:
        parts.append(
            f"Available data indicates {constituency} flipped from {party_2019 or 'the 2019 winner'} "
            f"to {party_2024 or 'the 2024 winner'} between 2019 and 2024."
        )
    else:
        parts.append(
            f"Available data indicates {constituency} was retained by "
            f"{party_2024 or party_2019 or 'the incumbent party'} in 2024."
        )

    bjp_swing = format_points(to_float(row.get("bjp_swing_2019_2024")))
    inc_swing = format_points(to_float(row.get("inc_swing_2019_2024")))
    if bjp_swing:
        parts.append(f"BJP vote share changed by {bjp_swing} percentage points versus 2019.")
    if inc_swing:
        parts.append(f"INC vote share changed by {inc_swing} percentage points versus 2019.")

    margin_2019 = format_pct(to_float(row.get("margin_2019")))
    margin_2024 = format_pct(to_float(row.get("margin_2024")))
    if margin_2019 and margin_2024:
        parts.append(f"The winning margin moved from {margin_2019} in 2019 to {margin_2024} in 2024.")
    elif margin_2024:
        parts.append(f"The 2024 winning margin was {margin_2024}.")

    turnout_change = to_float(row.get("turnout_change"))
    if turnout_change is None:
        turnout_2019 = to_float(row.get("turnout_2019"))
        turnout_2024 = to_float(row.get("turnout_2024"))
        if turnout_2019 is not None and turnout_2024 is not None:
            turnout_change = turnout_2024 - turnout_2019
    turnout_delta = format_points(turnout_change)
    if turnout_delta:
        parts.append(f"Turnout changed by {turnout_delta} percentage points between 2019 and 2024.")

    parts.append("This section describes observed election movement only and is not a causal explanation.")
    return " ".join(parts)


def _build_summary(row: pd.Series) -> str:
    constituency = str(row["constituency"])
    party_2024 = nan_to_none(row.get("winner_party_2024")) or "the winning party"
    flipped = to_bool(row.get("winner_changed"))
    party_2019 = nan_to_none(row.get("winner_party_2019"))

    if flipped:
        opener = (
            f"{constituency} flipped from {party_2019 or 'the 2019 winner'} to {party_2024} in 2024."
        )
    else:
        opener = f"{constituency} was retained by {party_2024} in 2024."

    bjp_swing = format_points(to_float(row.get("bjp_swing_2019_2024")))
    inc_swing = format_points(to_float(row.get("inc_swing_2019_2024")))
    swing_bits: list[str] = []
    if bjp_swing:
        swing_bits.append(f"BJP vote share changed by {bjp_swing} points")
    if inc_swing:
        swing_bits.append(f"INC vote share changed by {inc_swing} points")
    swing_text = (
        f"{' and '.join(swing_bits)} compared with 2019."
        if swing_bits
        else "Vote-share swing data are limited for this seat."
    )

    margin_2024 = format_pct(to_float(row.get("margin_2024")))
    margin_text = f"The 2024 margin was {margin_2024}." if margin_2024 else ""

    return (
        f"{opener} {swing_text} {margin_text} "
        "This is a descriptive election profile, not a causal explanation."
    ).strip()


def _build_demographic_context(row: pd.Series, quality: str) -> str:
    if quality == "election_only" or not has_demographics(row):
        return (
            "Demographic indicators are currently unavailable for this constituency; "
            "the profile is election-only."
        )

    statements: list[str] = []
    urban_pct = to_float(row.get("urban_pct_nfhs5"))
    if urban_pct is not None:
        if urban_pct >= 50:
            statements.append(
                "Available NFHS-linked indicators may suggest a relatively urban-linked profile "
                f"(urban share about {urban_pct:.1f}%)."
            )
        elif urban_pct < 30:
            statements.append(
                "Available NFHS-linked indicators may suggest a relatively rural-linked profile "
                f"(urban share about {urban_pct:.1f}%)."
            )

    access_cols = [
        ("electricity_pct_nfhs5", "electricity"),
        ("lpg_pct_nfhs5", "LPG"),
        ("mobile_phone_pct_nfhs5", "mobile phone"),
        ("bank_account_pct_nfhs5", "bank account"),
    ]
    available_access = [label for col, label in access_cols if nan_to_none(row.get(col)) is not None]
    if available_access:
        joined = "/".join(available_access)
        statements.append(f"{joined.title()} access indicators are available for this seat.")

    coverage = to_float(row.get("nfhs5_coverage_share"))
    if coverage is not None and coverage < HIGH_COVERAGE_THRESHOLD:
        statements.append(
            "Demographic interpretation should be cautious because district-linked coverage is partial."
        )
    elif coverage is not None and coverage >= HIGH_COVERAGE_THRESHOLD:
        statements.append(
            "Available data indicates relatively high district-linked demographic coverage for this seat."
        )

    if not statements:
        statements.append(
            "Some district-linked NFHS indicators are present, but the available profile remains limited."
        )

    return " ".join(statements)


def _build_district_context(row: pd.Series) -> str:
    districts_used = nan_to_none(row.get("districts_used"))
    districts_missing = nan_to_none(row.get("districts_missing"))
    coverage = to_float(row.get("nfhs5_coverage_share"))
    change_coverage = to_float(row.get("change_coverage_share"))
    change_flag = nan_to_none(row.get("change_quality_flag"))

    parts: list[str] = []
    if districts_used:
        parts.append(f"District mapping uses: {districts_used}.")
    if districts_missing:
        parts.append(f"Some districts are not mapped: {districts_missing}.")
    if coverage is not None:
        parts.append(f"NFHS-5 coverage share is about {coverage * 100:.1f}%.")
    if change_coverage is not None:
        parts.append(f"Change-indicator coverage share is about {change_coverage * 100:.1f}%.")
    if change_flag:
        parts.append(f"Change quality flag: {change_flag}.")

    if not parts:
        return "District-linked demographic mapping details are not available for this seat."
    return " ".join(parts)


def _build_data_quality_note(row: pd.Series, quality: str) -> str:
    if quality == "election_only":
        return (
            "This is an election-only profile. Demographic values are missing and have not been imputed."
        )
    coverage = to_float(row.get("nfhs5_coverage_share"))
    if coverage is not None and coverage < LOW_COVERAGE_THRESHOLD:
        return (
            "Demographic indicators are available only with low district-linked coverage; "
            "interpretation should remain cautious."
        )
    if quality == "high":
        return "Election results and relatively strong district-linked demographic coverage are available."
    return "Election results are available with partial district-linked demographic coverage."


def _build_what_to_watch(row: pd.Series, factors: list[str]) -> str:
    items: list[str] = []
    if "seat_flip" in factors:
        items.append("Monitor whether the 2024 seat change stabilizes in future cycles.")
    if "close_contest_2024" in factors:
        items.append("The 2024 margin was narrow and may suggest a highly competitive seat profile.")
    if "large_bjp_gain" in factors or "large_inc_gain" in factors:
        items.append("Large major-party vote-share movement may warrant closer review of local competition patterns.")
    if "high_turnout_change" in factors:
        items.append("Turnout shifted materially between 2019 and 2024 and may be worth tracking.")
    if "district_coverage_gap" in factors:
        items.append("Incomplete district mapping may limit future demographic interpretation for this seat.")
    if "election_only_profile" in factors:
        items.append("Demographic context may remain limited until district-linked coverage improves.")

    if not items:
        items.append(
            "Track future election results and any improvements in district-linked demographic coverage."
        )
    return " ".join(items)


def _confidence(row: pd.Series, quality: str) -> str:
    election_fields = [
        "winner_party_2024",
        "bjp_swing_2019_2024",
        "inc_swing_2019_2024",
        "margin_2024",
    ]
    election_complete = all(nan_to_none(row.get(field)) is not None for field in election_fields)

    if quality == "election_only":
        return "medium" if election_complete else "low"
    if quality == "high" and election_complete:
        return "high"
    if quality in {"medium", "low"} and election_complete:
        return "medium"
    return "low"


def build_baseline_row(row: pd.Series, today: str) -> dict[str, object]:
    coverage = to_float(row.get("nfhs5_coverage_share"))
    has_demo = has_demographics(row)
    quality = data_quality_label(coverage, has_demo)
    factors = _compute_key_factors(row, quality)

    election_fields = [
        "winner_party_2019",
        "winner_party_2024",
        "winner_changed",
        "bjp_swing_2019_2024",
        "inc_swing_2019_2024",
        "margin_2019",
        "margin_2024",
        "turnout_2019",
        "turnout_2024",
        "turnout_change",
    ]
    demo_fields = [col for col in DEMOGRAPHIC_NFHS5_COLS if nan_to_none(row.get(col)) is not None]
    district_fields = [
        field
        for field in ("districts_used", "districts_missing", "nfhs5_coverage_share", "change_coverage_share")
        if nan_to_none(row.get(field)) is not None
    ]
    generated_from = election_fields + demo_fields + district_fields

    return {
        "state": str(row["state"]),
        "constituency": str(row["constituency"]),
        "state_key": str(row["state_key"]),
        "constituency_key": str(row["constituency_key"]),
        "analysis_type": "baseline",
        "summary": _build_summary(row),
        "electoral_movement": _build_electoral_movement(row),
        "key_factors": ";".join(factors),
        "demographic_context": _build_demographic_context(row, quality),
        "district_context": _build_district_context(row),
        "data_quality_note": _build_data_quality_note(row, quality),
        "what_to_watch": _build_what_to_watch(row, factors),
        "confidence": _confidence(row, quality),
        "data_quality_label": quality,
        "generated_from_fields": ";".join(generated_from),
        "last_updated": today,
    }


def main() -> None:
    ensure_dirs()
    master = load_master()
    today = date.today().isoformat()

    rows = [build_baseline_row(row, today) for _, row in master.iterrows()]
    baseline = pd.DataFrame(rows, columns=BASELINE_COLUMNS)
    baseline.to_csv(BASELINE_CSV_PATH, index=False)

    print(f"Wrote {len(baseline)} baseline seat notes to {BASELINE_CSV_PATH}")


if __name__ == "__main__":
    main()
