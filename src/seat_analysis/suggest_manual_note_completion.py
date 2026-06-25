"""Generate low-confidence suggested manual notes from research packets."""

from __future__ import annotations

import json
import sys
from datetime import date

import pandas as pd

from src.seat_analysis.common import (
    COVERAGE_REPORT_PATH,
    MANUAL_NOTES_DIR,
    MANUAL_SUGGESTED_DIR,
    RESEARCH_PACKETS_JSON_DIR,
    ensure_dirs,
    non_empty_text,
    packet_filename,
    to_float,
)
from src.seat_analysis.markdown_notes import list_note_files, render_note_markdown


AUTO_SOURCE_NOTES = (
    "Auto-suggested from structured The 543 data; requires human review."
)
DEFAULT_CAVEATS = (
    "This note is based on structured election and demographic data. "
    "Local causal explanations require further source review."
)
DEFAULT_KEY_FACTORS = (
    "candidate profile;alliance arithmetic;turnout;local context;state mood"
)


def _fmt_points(value: object | None) -> str | None:
    num = to_float(value)
    if num is None:
        return None
    sign = "+" if num > 0 else ""
    return f"{sign}{num:.1f}"


def _election_sentence(packet: dict) -> str:
    election = packet["election_facts"]
    identity = packet["identity"]
    name = identity["constituency"]
    party_2019 = election.get("winner_party_2019")
    party_2024 = election.get("winner_party_2024")
    changed = election.get("winner_changed")
    parts: list[str] = []

    if changed is True:
        parts.append(
            f"Available data indicates {name} flipped from {party_2019} to {party_2024} between 2019 and 2024."
        )
    elif party_2024:
        parts.append(f"Available data indicates {name} was retained by {party_2024} in 2024.")

    bjp_swing = _fmt_points(election.get("bjp_swing_2019_2024"))
    inc_swing = _fmt_points(election.get("inc_swing_2019_2024"))
    if bjp_swing is not None:
        parts.append(f"BJP vote share changed by {bjp_swing} percentage points versus 2019.")
    if inc_swing is not None:
        parts.append(f"INC vote share changed by {inc_swing} percentage points versus 2019.")

    margin_2019 = election.get("margin_2019")
    margin_2024 = election.get("margin_2024")
    if margin_2019 is not None and margin_2024 is not None:
        parts.append(
            f"The winning margin moved from {float(margin_2019):.1f}% in 2019 "
            f"to {float(margin_2024):.1f}% in 2024."
        )

    turnout_change = _fmt_points(election.get("turnout_change"))
    if turnout_change is not None:
        parts.append(f"Turnout changed by {turnout_change} percentage points between 2019 and 2024.")

    if not parts:
        return (
            f"Structured election movement data for {name} is limited in the current dataset."
        )
    parts.append(
        "This section describes observed election movement only and is not a causal explanation."
    )
    return " ".join(parts)


def _why_it_mattered(packet: dict) -> str:
    identity = packet["identity"]
    flags = packet["rank_context_flags"]
    demo = packet["demographic_context"]
    state_ctx = packet["state_context"]
    reasons: list[str] = []

    priority_reason = flags.get("priority_reason")
    if non_empty_text(priority_reason):
        reasons.append(
            f"This seat is on the priority review list because {priority_reason}."
        )

    if flags.get("is_flipped_seat"):
        reasons.append("The 2024 seat change may make this constituency useful for tracking post-election stability.")
    if flags.get("is_close_2024"):
        reasons.append("The 2024 margin was relatively close, which may make the seat analytically sensitive to small shifts.")
    if flags.get("is_large_bjp_gain") or flags.get("is_large_bjp_loss"):
        reasons.append("The BJP swing between 2019 and 2024 was large relative to the project threshold.")
    if flags.get("is_large_inc_gain") or flags.get("is_large_inc_loss"):
        reasons.append("The INC swing between 2019 and 2024 was large relative to the project threshold.")

    state_bjp = state_ctx.get("state_average_bjp_swing")
    if state_bjp is not None:
        reasons.append(
            f"The seat sits within {identity['state']}, where the average BJP swing was {float(state_bjp):+.1f} points."
        )

    urban = demo.get("nfhs5_indicators", {}).get("urban_pct_nfhs5") if isinstance(demo.get("nfhs5_indicators"), dict) else None
    if urban is not None:
        profile = "urban-linked" if float(urban) >= 50 else "rural-linked" if float(urban) < 30 else "mixed urban-rural"
        reasons.append(
            f"Available NFHS-linked indicators may suggest a relatively {profile} profile (urban share about {float(urban):.1f}%)."
        )

    if demo.get("data_quality_label") == "election_only":
        reasons.append(
            "Demographic indicators are currently unavailable, so the seat is mainly useful as an election-movement profile."
        )
    elif demo.get("nfhs5_coverage_share") is not None and float(demo["nfhs5_coverage_share"]) < 0.5:
        reasons.append("District-linked demographic coverage is limited, which may constrain interpretation.")

    if not reasons:
        reasons.append(
            f"{identity['constituency']} may be useful for comparing constituency-level movement against broader state patterns."
        )
    return " ".join(reasons)


def _factors(packet: dict) -> str:
    flags = packet["rank_context_flags"]
    demo = packet["demographic_context"]
    factors: list[str] = []

    if flags.get("is_flipped_seat") or flags.get("is_close_2024"):
        factors.append("Candidate profile may have mattered")
        factors.append("Alliance arithmetic may have mattered")
    if flags.get("is_large_bjp_gain") or flags.get("is_large_bjp_loss") or flags.get("is_large_inc_gain") or flags.get("is_large_inc_loss"):
        factors.append("State-level swing may have mattered")
    if to_float(packet["election_facts"].get("turnout_change")) is not None:
        factors.append("Turnout movement may have mattered")
    if demo.get("data_quality_label") == "election_only" or (to_float(demo.get("nfhs5_coverage_share")) or 0) < 0.5:
        factors.append("Demographic interpretation is limited by coverage")
    factors.append("Local context requires further source review")

    existing = packet.get("existing_analysis", {})
    manual = existing.get("manual_note")
    if isinstance(manual, dict) and non_empty_text(manual.get("factors")):
        return str(manual["factors"])

    return "; ".join(dict.fromkeys(factors)) + "."


def _demographic_context(packet: dict) -> str:
    demo = packet["demographic_context"]
    existing = packet.get("existing_analysis", {})
    generated_demo = existing.get("generated_demographic_context")
    generated_district = existing.get("generated_district_context")

    if demo.get("data_quality_label") == "election_only":
        return (
            "Demographic indicators are currently unavailable for this constituency, "
            "so this remains an election-only profile."
        )

    lines: list[str] = []
    if non_empty_text(generated_demo):
        lines.append(str(generated_demo))
    if non_empty_text(generated_district):
        lines.append(str(generated_district))

    nfhs5 = demo.get("nfhs5_indicators", {})
    if isinstance(nfhs5, dict):
        available = [k for k, v in nfhs5.items() if v is not None]
        if available:
            lines.append(
                "Available NFHS-5-linked fields in the packet include: "
                + ", ".join(available[:6])
                + ("..." if len(available) > 6 else "")
                + "."
            )

    if not lines:
        return (
            "Demographic indicators are currently unavailable for this constituency, "
            "so this remains an election-only profile."
        )
    return "\n\n".join(lines)


def _what_to_watch(packet: dict) -> str:
    flags = packet["rank_context_flags"]
    parts: list[str] = []

    if flags.get("is_flipped_seat"):
        parts.append("Whether the 2024 seat change stabilises or remains volatile in future cycles.")
    elif flags.get("is_close_2024"):
        parts.append("Whether the seat remains competitive or drifts toward a safer margin.")
    else:
        parts.append("Whether the current seat profile remains stable across subsequent elections.")

    if flags.get("is_large_bjp_gain") or flags.get("is_large_bjp_loss") or flags.get("is_large_inc_gain") or flags.get("is_large_inc_loss"):
        parts.append("Whether the 2019→2024 swing consolidates or partially reverses.")

    parts.append("Whether state-level alliance patterns continue to shape this constituency.")
    if packet["demographic_context"].get("data_quality_label") == "election_only":
        parts.append("Whether future demographic coverage improves interpretation.")
    return " ".join(parts)


def suggest_note_markdown(packet: dict) -> str:
    identity = packet["identity"]
    constituency = {
        "state": identity["state"],
        "constituency": identity["constituency"],
        "state_key": identity["state_key"],
        "constituency_key": identity["constituency_key"],
    }
    return render_note_markdown(
        constituency,
        what_happened=_election_sentence(packet),
        why_it_mattered=_why_it_mattered(packet),
        factors=_factors(packet),
        demographic_context=_demographic_context(packet),
        what_to_watch=_what_to_watch(packet),
        notes_caveats=DEFAULT_CAVEATS,
        key_factors=DEFAULT_KEY_FACTORS,
        analyst_name="The 543 auto-suggest",
        source_notes=AUTO_SOURCE_NOTES,
        last_reviewed=date.today().isoformat(),
        manual_confidence="low",
    )


def has_manual_note(packet: dict, manual_note_paths: set[str]) -> bool:
    identity = packet["identity"]
    filename = packet_filename(identity["state_key"], identity["constituency_key"], "md")
    if filename in manual_note_paths:
        return True
    existing = packet.get("existing_analysis", {})
    if existing.get("has_manual_markdown"):
        return True
    source = str(existing.get("analysis_source") or "")
    if source == "manual":
        return True
    if source == "mixed" and non_empty_text(existing.get("final_local_context")):
        return True
    return False


def needs_manual_review(packet: dict, has_manual: bool) -> tuple[bool, str]:
    flags = packet["rank_context_flags"]
    demo = packet["demographic_context"]
    reasons: list[str] = []

    if flags.get("is_priority_seat"):
        reasons.append("priority seat")
    if flags.get("is_flipped_seat"):
        reasons.append("flipped seat")
    if flags.get("is_close_2024"):
        reasons.append("close 2024 contest")
    if any(
        flags.get(key)
        for key in (
            "is_large_bjp_gain",
            "is_large_bjp_loss",
            "is_large_inc_gain",
            "is_large_inc_loss",
        )
    ):
        reasons.append("large swing")
    if not has_manual:
        reasons.append("manual note missing")
    if demo.get("data_quality_label") == "election_only" and (
        flags.get("is_priority_seat") or flags.get("is_flipped_seat")
    ):
        reasons.append("important seat with election-only demographics")

    return bool(reasons), "; ".join(reasons)


def promote_suggestions() -> int:
    promoted = 0
    for path in sorted(MANUAL_SUGGESTED_DIR.glob("*.md")):
        target = MANUAL_NOTES_DIR / path.name
        if target.exists():
            continue
        target.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
        promoted += 1
    return promoted


def main() -> int:
    ensure_dirs()
    if not RESEARCH_PACKETS_JSON_DIR.exists() or not any(RESEARCH_PACKETS_JSON_DIR.glob("*.json")):
        print("Research packets not found. Run python -m src.seat_analysis.build_seat_research_packets first.")
        return 1

    manual_note_paths = {p.name for p in list_note_files(MANUAL_NOTES_DIR)}
    report_rows: list[dict[str, object]] = []
    suggested_count = 0

    for json_path in sorted(RESEARCH_PACKETS_JSON_DIR.glob("*.json")):
        packet = json.loads(json_path.read_text(encoding="utf-8"))
        identity = packet["identity"]
        state_key = identity["state_key"]
        constituency_key = identity["constituency_key"]
        filename = packet_filename(state_key, constituency_key, "md")

        suggested_path = MANUAL_SUGGESTED_DIR / filename
        suggested_path.write_text(suggest_note_markdown(packet), encoding="utf-8")
        suggested_count += 1

        has_manual = has_manual_note(packet, manual_note_paths)
        review_needed, review_reason = needs_manual_review(packet, has_manual)
        existing = packet.get("existing_analysis", {})

        report_rows.append(
            {
                "state": identity["state"],
                "constituency": identity["constituency"],
                "has_generated_note": True,
                "has_manual_note": has_manual,
                "has_suggested_note": True,
                "manual_confidence": existing.get("manual_confidence") or ("medium" if has_manual else "low"),
                "data_quality_label": packet["demographic_context"].get("data_quality_label"),
                "is_priority_seat": packet["rank_context_flags"].get("is_priority_seat", False),
                "needs_manual_review": review_needed,
                "suggested_review_reason": review_reason,
            }
        )

    report = pd.DataFrame(report_rows)
    report.to_csv(COVERAGE_REPORT_PATH, index=False)
    print(f"Wrote {suggested_count} suggested notes to {MANUAL_SUGGESTED_DIR}")
    print(f"Wrote coverage report to {COVERAGE_REPORT_PATH}")
    print(f"Needs manual review: {int(report['needs_manual_review'].sum())} / {len(report)}")

    if "--promote-suggestions" in sys.argv:
        promoted = promote_suggestions()
        print(f"Promoted {promoted} suggested note(s) into {MANUAL_NOTES_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
