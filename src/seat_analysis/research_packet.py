"""Build and render Seat Intelligence research packets."""

from __future__ import annotations

import json
from datetime import date
from typing import Any

import pandas as pd

from src.seat_analysis.common import (
    BASELINE_CSV_PATH,
    CLOSE_MARGIN_THRESHOLD,
    CONSTITUENCY_COVERAGE_PATH,
    DEMOGRAPHIC_CHANGE_COLS,
    DEMOGRAPHIC_NFHS5_COLS,
    FINAL_CSV_PATH,
    LARGE_SWING_THRESHOLD,
    MANUAL_NOTES_DIR,
    MANUAL_NOTES_PATH,
    PRIORITY_CSV_PATH,
    STATES_JSON_PATH,
    data_quality_label,
    has_demographics,
    lookup_key,
    nan_to_none,
    non_empty_text,
    to_bool,
    to_float,
)
from src.seat_analysis.markdown_notes import (
    list_note_files,
    parse_markdown_note,
)


def _clean_value(value: object) -> object | None:
    cleaned = nan_to_none(value)
    if cleaned is None:
        return None
    if isinstance(cleaned, float):
        return round(cleaned, 4)
    return cleaned


def _series_dict(row: pd.Series, columns: list[str]) -> dict[str, object | None]:
    return {col: _clean_value(row.get(col)) for col in columns}


def _compute_rank_flags(row: pd.Series, quality: str, is_priority: bool) -> dict[str, object]:
    bjp_swing = to_float(row.get("bjp_swing_2019_2024"))
    inc_swing = to_float(row.get("inc_swing_2019_2024"))
    margin_2024 = to_float(row.get("margin_2024"))
    return {
        "is_flipped_seat": bool(to_bool(row.get("winner_changed"))),
        "is_close_2024": margin_2024 is not None and margin_2024 <= CLOSE_MARGIN_THRESHOLD,
        "is_large_bjp_gain": bjp_swing is not None and bjp_swing >= LARGE_SWING_THRESHOLD,
        "is_large_bjp_loss": bjp_swing is not None and bjp_swing <= -LARGE_SWING_THRESHOLD,
        "is_large_inc_gain": inc_swing is not None and inc_swing >= LARGE_SWING_THRESHOLD,
        "is_large_inc_loss": inc_swing is not None and inc_swing <= -LARGE_SWING_THRESHOLD,
        "is_priority_seat": is_priority,
    }


def load_monte_carlo_lookup(path) -> dict[str, dict[str, object]]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    lookup: dict[str, dict[str, object]] = {}
    for record in payload.get("constituencies", []):
        key = lookup_key(str(record["state_key"]), str(record["constituency_key"]))
        lookup[key] = record
    return lookup


def load_state_lookup() -> dict[str, dict[str, object]]:
    if not STATES_JSON_PATH.exists():
        return {}
    states = json.loads(STATES_JSON_PATH.read_text(encoding="utf-8"))
    return {str(row["state_key"]): row for row in states}


def load_priority_lookup() -> dict[str, dict[str, object]]:
    if not PRIORITY_CSV_PATH.exists():
        return {}
    df = pd.read_csv(PRIORITY_CSV_PATH)
    lookup: dict[str, dict[str, object]] = {}
    for _, row in df.iterrows():
        key = lookup_key(str(row["state"]), str(row["constituency"]))
        lookup[key] = {
            "priority_rank": _clean_value(row.get("priority_rank")),
            "priority_reason": nan_to_none(row.get("reason")),
            "priority_score": _clean_value(row.get("priority_score")),
            "suggested_manual_review": nan_to_none(row.get("suggested_manual_review")),
        }
    return lookup


def load_priority_lookup_by_keys(master: pd.DataFrame, priority_df: pd.DataFrame) -> dict[str, dict[str, object]]:
    name_lookup = {
        f"{str(row['state']).strip().lower()}::{str(row['constituency']).strip().lower()}": lookup_key(
            str(row["state_key"]),
            str(row["constituency_key"]),
        )
        for _, row in master.iterrows()
    }
    lookup: dict[str, dict[str, object]] = {}
    for _, row in priority_df.iterrows():
        name_key = f"{str(row['state']).strip().lower()}::{str(row['constituency']).strip().lower()}"
        packet_key = name_lookup.get(name_key)
        if not packet_key:
            continue
        lookup[packet_key] = {
            "priority_rank": _clean_value(row.get("priority_rank")),
            "priority_reason": nan_to_none(row.get("reason")),
            "priority_score": _clean_value(row.get("priority_score")),
            "suggested_manual_review": nan_to_none(row.get("suggested_manual_review")),
        }
    return lookup


def load_manual_markdown_lookup() -> dict[str, dict[str, str]]:
    lookup: dict[str, dict[str, str]] = {}
    for path in list_note_files(MANUAL_NOTES_DIR):
        note = parse_markdown_note(path)
        key = lookup_key(note.state_key, note.constituency_key)
        lookup[key] = {
            "path": str(path),
            "why_it_mattered": note.sections.get("Why it mattered", ""),
            "factors": note.sections.get("Factors that may have mattered", ""),
            "what_to_watch": note.sections.get("What to watch next", ""),
            "notes_caveats": note.sections.get("Notes / caveats", ""),
            "analyst_name": str(note.frontmatter.get("analyst_name", "")),
            "manual_confidence": str(note.frontmatter.get("manual_confidence", "")),
            "source_notes": str(note.frontmatter.get("source_notes", "")),
        }
    return lookup


def load_manual_csv_lookup() -> dict[str, pd.Series]:
    if not MANUAL_NOTES_PATH.exists():
        return {}
    df = pd.read_csv(MANUAL_NOTES_PATH)
    lookup: dict[str, pd.Series] = {}
    for _, row in df.iterrows():
        if not any(non_empty_text(row.get(col)) for col in ["manual_summary", "manual_local_context", "manual_electoral_movement"]):
            continue
        key = lookup_key(str(row["state_key"]), str(row["constituency_key"]))
        lookup[key] = row
    return lookup


def build_research_packet(
    row: pd.Series,
    *,
    state_lookup: dict[str, dict[str, object]],
    priority_lookup: dict[str, dict[str, object]],
    baseline_lookup: dict[str, pd.Series],
    final_lookup: dict[str, pd.Series],
    coverage_lookup: dict[str, pd.Series],
    monte_carlo_lookup: dict[str, dict[str, object]],
    manual_md_lookup: dict[str, dict[str, str]],
    manual_csv_lookup: dict[str, pd.Series],
) -> dict[str, object]:
    state_key = str(row["state_key"])
    constituency_key = str(row["constituency_key"])
    key = lookup_key(state_key, constituency_key)

    nfhs5_share = to_float(row.get("nfhs5_coverage_share"))
    quality = data_quality_label(nfhs5_share, has_demographics(row))
    priority = priority_lookup.get(key, {})
    is_priority = bool(priority)

    election_cols = [
        "winner_2019",
        "winner_2024",
        "winner_party_2019",
        "winner_party_2024",
        "winner_changed",
        "bjp_vote_share_2019",
        "bjp_vote_share_2024",
        "inc_vote_share_2019",
        "inc_vote_share_2024",
        "bjp_swing_2019_2024",
        "inc_swing_2019_2024",
        "margin_2019",
        "margin_2024",
        "margin_change",
        "turnout_2019",
        "turnout_2024",
        "turnout_change",
    ]

    rank_flags = _compute_rank_flags(row, quality, is_priority)
    rank_flags["priority_reason"] = priority.get("priority_reason")
    rank_flags["priority_rank"] = priority.get("priority_rank")

    state_ctx = state_lookup.get(state_key, {})
    state_context = {
        "state_total_seats": _clean_value(state_ctx.get("total_constituencies")),
        "bjp_seats_2019": _clean_value(state_ctx.get("bjp_seats_2019")),
        "bjp_seats_2024": _clean_value(state_ctx.get("bjp_seats_2024")),
        "inc_seats_2019": _clean_value(state_ctx.get("inc_seats_2019")),
        "inc_seats_2024": _clean_value(state_ctx.get("inc_seats_2024")),
        "state_average_bjp_swing": _clean_value(state_ctx.get("average_bjp_swing")),
        "state_average_inc_swing": _clean_value(state_ctx.get("average_inc_swing")),
        "state_demographic_coverage_pct": _clean_value(state_ctx.get("demographic_coverage_pct")),
    }

    demographic = {
        "nfhs5_indicators": _series_dict(row, DEMOGRAPHIC_NFHS5_COLS),
        "change_indicators": _series_dict(row, DEMOGRAPHIC_CHANGE_COLS),
        "nfhs5_coverage_share": _clean_value(row.get("nfhs5_coverage_share")),
        "change_coverage_share": _clean_value(row.get("change_coverage_share")),
        "change_quality_flag": nan_to_none(row.get("change_quality_flag")),
        "data_quality_label": quality,
        "districts_used": nan_to_none(row.get("districts_used")),
        "districts_missing": nan_to_none(row.get("districts_missing")),
    }

    coverage_row = coverage_lookup.get(key)
    if coverage_row is not None:
        demographic["coverage_diagnostics"] = {
            "has_election_data": _clean_value(coverage_row.get("has_election_data")),
            "has_nfhs5_any": _clean_value(coverage_row.get("has_nfhs5_any")),
            "has_change_any": _clean_value(coverage_row.get("has_change_any")),
            "missing_features_count": _clean_value(coverage_row.get("missing_features_count")),
            "available_features_count": _clean_value(coverage_row.get("available_features_count")),
        }

    mc = monte_carlo_lookup.get(key)
    simulation_context: dict[str, object] | None = None
    if mc:
        simulation_context = {
            "simulation_completeness": mc.get("simulation_completeness"),
            "winner_2024": mc.get("winner_2024"),
            "winner_party_2024": mc.get("winner_party_2024"),
            "data_quality_label": mc.get("data_quality_label"),
            "projection_confidence_hint": (
                "high"
                if mc.get("simulation_completeness") == "full_party_shares"
                else "low"
            ),
        }

    baseline = baseline_lookup.get(key)
    final = final_lookup.get(key)
    manual_md = manual_md_lookup.get(key)
    manual_csv = manual_csv_lookup.get(key)

    existing_analysis: dict[str, object] = {
        "generated_baseline_summary": nan_to_none(baseline.get("summary")) if baseline is not None else None,
        "generated_electoral_movement": nan_to_none(baseline.get("electoral_movement")) if baseline is not None else None,
        "generated_key_factors": nan_to_none(baseline.get("key_factors")) if baseline is not None else None,
        "generated_demographic_context": nan_to_none(baseline.get("demographic_context")) if baseline is not None else None,
        "generated_district_context": nan_to_none(baseline.get("district_context")) if baseline is not None else None,
        "generated_what_to_watch": nan_to_none(baseline.get("what_to_watch")) if baseline is not None else None,
        "final_summary": nan_to_none(final.get("summary")) if final is not None else None,
        "final_electoral_movement": nan_to_none(final.get("electoral_movement")) if final is not None else None,
        "final_local_context": nan_to_none(final.get("local_context")) if final is not None else None,
        "final_what_to_watch": nan_to_none(final.get("what_to_watch")) if final is not None else None,
        "analysis_source": nan_to_none(final.get("analysis_source")) if final is not None else "generated",
        "manual_confidence": nan_to_none(final.get("confidence")) if final is not None else None,
    }

    if manual_md:
        existing_analysis["manual_note"] = manual_md
        existing_analysis["has_manual_markdown"] = True
    else:
        existing_analysis["has_manual_markdown"] = False

    if manual_csv is not None:
        existing_analysis["manual_csv_note"] = {
            col.replace("manual_", ""): nan_to_none(manual_csv.get(col))
            for col in manual_csv.index
            if str(col).startswith("manual_") and non_empty_text(manual_csv.get(col))
        }

    writing_prompts = build_writing_prompts(
        constituency=str(row["constituency"]),
        state=str(row["state"]),
        election=_series_dict(row, election_cols),
        rank_flags=rank_flags,
        state_context=state_context,
        demographic=demographic,
        existing_analysis=existing_analysis,
        priority_reason=priority.get("priority_reason"),
    )

    return {
        "meta": {
            "generated_at": date.today().isoformat(),
            "packet_version": "1",
        },
        "identity": {
            "state": str(row["state"]),
            "constituency": str(row["constituency"]),
            "state_key": state_key,
            "constituency_key": constituency_key,
        },
        "election_facts": _series_dict(row, election_cols),
        "state_context": state_context,
        "rank_context_flags": rank_flags,
        "demographic_context": demographic,
        "simulation_context": simulation_context,
        "existing_analysis": existing_analysis,
        "writing_prompts": writing_prompts,
    }


def build_writing_prompts(
    *,
    constituency: str,
    state: str,
    election: dict[str, object | None],
    rank_flags: dict[str, object],
    state_context: dict[str, object | None],
    demographic: dict[str, object],
    existing_analysis: dict[str, object],
    priority_reason: object | None,
) -> dict[str, str]:
    return {
        "what_happened_prompt": (
            f"Describe observed 2019→2024 election movement for {constituency}, {state} "
            "using winner, vote-share, margin, and turnout fields only."
        ),
        "why_it_mattered_prompt": (
            f"Explain why {constituency} may be analytically useful using priority reason "
            f"({priority_reason or 'none'}), contest closeness, swings, and state context."
        ),
        "factors_prompt": (
            "List only cautious factors such as candidate profile, alliance arithmetic, "
            "state-level swing, turnout movement, or limited demographic coverage."
        ),
        "demographic_prompt": (
            "Summarise available NFHS-linked indicators and district mapping. "
            "If unavailable, state that the profile remains election-only."
        ),
        "what_to_watch_prompt": (
            "Use forward-looking but non-predictive language about seat stability, "
            "swing consolidation, and coverage improvements."
        ),
        "caveat_prompt": (
            "State that local causal explanations require further source review."
        ),
    }


def render_packet_markdown(packet: dict[str, object]) -> str:
    identity = packet["identity"]
    election = packet["election_facts"]
    state_ctx = packet["state_context"]
    flags = packet["rank_context_flags"]
    demo = packet["demographic_context"]
    existing = packet["existing_analysis"]
    prompts = packet["writing_prompts"]
    sim = packet.get("simulation_context")

    lines = [
        f"# Research packet: {identity['constituency']}, {identity['state']}",
        "",
        f"_Generated {packet['meta']['generated_at']}. Evidence-backed prompts only; no invented local facts._",
        "",
        "## Identity",
        f"- State: {identity['state']} (`{identity['state_key']}`)",
        f"- Constituency: {identity['constituency']} (`{identity['constituency_key']}`)",
        "",
        "## Election facts (2019 → 2024)",
    ]

    for label, key in [
        ("Winner 2019", "winner_2019"),
        ("Winner 2024", "winner_2024"),
        ("Party 2019", "winner_party_2019"),
        ("Party 2024", "winner_party_2024"),
        ("Winner changed", "winner_changed"),
        ("BJP vote share 2019", "bjp_vote_share_2019"),
        ("BJP vote share 2024", "bjp_vote_share_2024"),
        ("INC vote share 2019", "inc_vote_share_2019"),
        ("INC vote share 2024", "inc_vote_share_2024"),
        ("BJP swing", "bjp_swing_2019_2024"),
        ("INC swing", "inc_swing_2019_2024"),
        ("Margin 2019", "margin_2019"),
        ("Margin 2024", "margin_2024"),
        ("Margin change", "margin_change"),
        ("Turnout 2019", "turnout_2019"),
        ("Turnout 2024", "turnout_2024"),
        ("Turnout change", "turnout_change"),
    ]:
        lines.append(f"- {label}: {election.get(key, 'N/A')}")

    lines.extend(
        [
            "",
            "## State context",
            f"- State seats: {state_ctx.get('state_total_seats', 'N/A')}",
            f"- BJP seats 2019/2024: {state_ctx.get('bjp_seats_2019', 'N/A')} / {state_ctx.get('bjp_seats_2024', 'N/A')}",
            f"- INC seats 2019/2024: {state_ctx.get('inc_seats_2019', 'N/A')} / {state_ctx.get('inc_seats_2024', 'N/A')}",
            f"- State avg BJP swing: {state_ctx.get('state_average_bjp_swing', 'N/A')}",
            f"- State avg INC swing: {state_ctx.get('state_average_inc_swing', 'N/A')}",
            f"- State demographic coverage: {state_ctx.get('state_demographic_coverage_pct', 'N/A')}%",
            "",
            "## Rank / context flags",
        ]
    )
    for flag_key in [
        "is_flipped_seat",
        "is_close_2024",
        "is_large_bjp_gain",
        "is_large_bjp_loss",
        "is_large_inc_gain",
        "is_large_inc_loss",
        "is_priority_seat",
        "priority_reason",
        "priority_rank",
    ]:
        lines.append(f"- {flag_key}: {flags.get(flag_key)}")

    lines.extend(["", "## Demographic context", f"- data_quality_label: {demo.get('data_quality_label')}"])
    nfhs5 = demo.get("nfhs5_indicators", {})
    if isinstance(nfhs5, dict):
        for key, value in nfhs5.items():
            if value is not None:
                lines.append(f"- {key}: {value}")
    lines.append(f"- nfhs5_coverage_share: {demo.get('nfhs5_coverage_share')}")
    lines.append(f"- change_coverage_share: {demo.get('change_coverage_share')}")
    lines.append(f"- change_quality_flag: {demo.get('change_quality_flag')}")
    lines.append(f"- districts_used: {demo.get('districts_used') or 'N/A'}")
    lines.append(f"- districts_missing: {demo.get('districts_missing') or 'N/A'}")

    if sim:
        lines.extend(["", "## Simulation context"])
        for key, value in sim.items():
            lines.append(f"- {key}: {value}")

    lines.extend(
        [
            "",
            "## Existing analysis",
            f"- analysis_source: {existing.get('analysis_source')}",
            f"- generated summary: {existing.get('generated_baseline_summary')}",
            f"- generated movement: {existing.get('generated_electoral_movement')}",
            f"- has manual markdown: {existing.get('has_manual_markdown')}",
        ]
    )
    if existing.get("manual_note"):
        lines.append("- manual note present in `manual/notes/`")

    lines.extend(["", "## Writing prompts", ""])
    for key, value in prompts.items():
        lines.append(f"- **{key}**: {value}")

    return "\n".join(lines) + "\n"
