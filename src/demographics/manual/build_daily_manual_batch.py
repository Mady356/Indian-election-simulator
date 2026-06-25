"""Build a daily CSV batch for manual demographic entry (core fields first)."""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

import pandas as pd

from src.demographics.manual.common import (
    CORE_FIELDS,
    DAILY_BATCHES_DIR,
    DAILY_BATCH_SIZE,
    MANUAL_TEMPLATE_PATH,
    PRIORITY_SEAT_LIST_PATH,
    PROGRESS_BY_STATE_PATH,
    SEAT_NOTE_COVERAGE_PATH,
    default_unit,
    ensure_dirs,
    lookup_key,
    nan_to_none,
)
from src.demographics.manual.manual_progress_tracker import (
    BATCH_COLUMNS,
    ProgressContext,
    _field_satisfied,
    _load_manual_rows,
    _manual_rows_for_constituency,
    build_constituency_progress,
    load_progress_context,
    run_progress_tracker,
)


def _load_priority_seats() -> dict[str, dict[str, object]]:
    if not PRIORITY_SEAT_LIST_PATH.exists():
        return {}
    df = pd.read_csv(PRIORITY_SEAT_LIST_PATH)
    lookup: dict[str, dict[str, object]] = {}
    for _, row in df.iterrows():
        key = lookup_key(str(row["state"]), str(row["constituency"]))
        lookup[key] = {
            "priority_rank": int(row.get("priority_rank", 9999)),
            "priority_score": float(row.get("priority_score", 0) or 0),
            "reason": str(row.get("reason", "")),
        }
    return lookup


def _load_manual_note_seats() -> set[str]:
    if not SEAT_NOTE_COVERAGE_PATH.exists():
        return set()
    df = pd.read_csv(SEAT_NOTE_COVERAGE_PATH)
    if "has_manual_note" not in df.columns:
        return set()
    noted = df[df["has_manual_note"].astype(str).str.lower().isin({"true", "1", "yes"})]
    return {lookup_key(str(row["state"]), str(row["constituency"])) for _, row in noted.iterrows()}


def _existing_manual_keys(manual: pd.DataFrame) -> set[tuple[str, str, str]]:
    keys: set[tuple[str, str, str]] = set()
    if manual.empty:
        return keys
    for _, row in manual.iterrows():
        keys.add(
            (
                str(row["state_key"]).strip(),
                str(row["constituency_key"]).strip(),
                str(row["variable"]).strip(),
            )
        )
    return keys


def _state_coverage_scores(state_progress: pd.DataFrame) -> dict[str, float]:
    scores: dict[str, float] = {}
    if state_progress.empty:
        return scores
    for _, row in state_progress.iterrows():
        state_key = str(row["state_key"]).strip()
        completion = float(row.get("completion_pct", 0) or 0)
        election_only = int(row.get("election_only_constituencies", 0) or 0)
        scores[state_key] = (100.0 - completion) + (election_only * 2)
    return scores


def score_constituency_for_batch(
    row: pd.Series,
    priority_lookup: dict[str, dict[str, object]],
    manual_note_seats: set[str],
    state_coverage_scores: dict[str, float],
) -> float:
    key = lookup_key(str(row["state_key"]), str(row["constituency_key"]))
    score = 0.0

    if row["demographic_source_type"] == "election_only":
        score += 200.0

    priority = priority_lookup.get(key)
    if priority:
        score += 150.0
        score += max(0.0, 120.0 - float(priority["priority_rank"]))
        score += float(priority.get("priority_score", 0) or 0) * 0.5

    if key in manual_note_seats:
        score += 80.0

    state_key = str(row["state_key"]).strip()
    score += state_coverage_scores.get(state_key, 0.0)

    if row.get("missing_core_fields"):
        missing_count = len([part for part in str(row["missing_core_fields"]).split(";") if part])
        score += missing_count * 5.0

    if row.get("needs_review"):
        score += 10.0

    return score


def select_batch_constituencies(
    constituency_progress: pd.DataFrame,
    state_progress: pd.DataFrame,
    batch_size: int = DAILY_BATCH_SIZE,
) -> pd.DataFrame:
    priority_lookup = _load_priority_seats()
    manual_note_seats = _load_manual_note_seats()
    state_scores = _state_coverage_scores(state_progress)

    candidates = constituency_progress[
        constituency_progress["core_fields_completed"] < len(CORE_FIELDS)
    ].copy()

    if candidates.empty:
        return candidates

    candidates["batch_priority_score"] = candidates.apply(
        lambda row: score_constituency_for_batch(
            row,
            priority_lookup,
            manual_note_seats,
            state_scores,
        ),
        axis=1,
    )

    return candidates.sort_values(
        ["batch_priority_score", "state", "constituency"],
        ascending=[False, True, True],
    ).head(batch_size)


def build_batch_rows(
    selected: pd.DataFrame,
    ctx: ProgressContext,
    existing_keys: set[tuple[str, str, str]],
) -> pd.DataFrame:
    rows: list[dict[str, str]] = []
    template = pd.read_csv(MANUAL_TEMPLATE_PATH) if MANUAL_TEMPLATE_PATH.exists() else pd.DataFrame()

    master_by_key = {
        lookup_key(str(row["state_key"]), str(row["constituency_key"])): row
        for _, row in ctx.master.iterrows()
    }

    for _, seat in selected.iterrows():
        state_key = str(seat["state_key"]).strip()
        constituency_key = str(seat["constituency_key"]).strip()
        key = lookup_key(state_key, constituency_key)
        master_row = master_by_key.get(key)
        if master_row is None:
            continue

        missing = str(seat.get("missing_core_fields", "")).split(";")
        missing_vars = [item for item in missing if item in CORE_FIELDS]
        if not missing_vars:
            missing_vars = list(CORE_FIELDS)

        manual_rows = _manual_rows_for_constituency(ctx.manual, state_key, constituency_key)

        for variable in CORE_FIELDS:
            if variable not in missing_vars:
                continue
            if _field_satisfied(master_row, manual_rows, variable, ctx.valid_manual_keys):
                continue
            if (state_key, constituency_key, variable) in existing_keys:
                continue

            template_row = None
            if not template.empty:
                matches = template[
                    (template["state_key"].astype(str).str.strip() == state_key)
                    & (template["constituency_key"].astype(str).str.strip() == constituency_key)
                    & (template["variable"].astype(str).str.strip() == variable)
                ]
                if not matches.empty:
                    template_row = matches.iloc[0]

            rows.append(
                {
                    "state": str(seat["state"]),
                    "constituency": str(seat["constituency"]),
                    "state_key": state_key,
                    "constituency_key": constituency_key,
                    "variable": variable,
                    "value": "",
                    "unit": str(template_row["unit"]) if template_row is not None and nan_to_none(template_row.get("unit")) else default_unit(variable),
                    "source_name": "",
                    "source_url_or_document": "",
                    "source_year": "",
                    "geography_level": "",
                    "method": "",
                    "confidence": "",
                    "notes": "",
                    "entered_by": "",
                    "last_updated": "",
                }
            )

    return pd.DataFrame(rows, columns=BATCH_COLUMNS)


def build_daily_batch(
    batch_size: int = DAILY_BATCH_SIZE,
    refresh_progress: bool = True,
) -> tuple[Path, pd.DataFrame, pd.DataFrame]:
    ensure_dirs()

    if refresh_progress:
        state_progress, constituency_progress, _ = run_progress_tracker()
    else:
        ctx = load_progress_context()
        constituency_progress = build_constituency_progress(ctx)
        state_progress = pd.read_csv(PROGRESS_BY_STATE_PATH)

    ctx = load_progress_context()
    selected = select_batch_constituencies(constituency_progress, state_progress, batch_size=batch_size)
    existing_keys = _existing_manual_keys(_load_manual_rows())
    batch = build_batch_rows(selected, ctx, existing_keys)

    batch_date = date.today().strftime("%Y_%m_%d")
    output_path = DAILY_BATCHES_DIR / f"manual_batch_{batch_date}.csv"
    batch.to_csv(output_path, index=False)
    return output_path, batch, selected


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch-size", type=int, default=DAILY_BATCH_SIZE)
    parser.add_argument("--no-refresh", action="store_true", help="Skip regenerating progress reports")
    args = parser.parse_args()

    output_path, batch, selected = build_daily_batch(
        batch_size=args.batch_size,
        refresh_progress=not args.no_refresh,
    )

    states = sorted(batch["state"].dropna().unique().tolist()) if not batch.empty else []
    variables = sorted(batch["variable"].dropna().unique().tolist()) if not batch.empty else []

    print("\nDaily manual batch")
    print(f"  Batch file: {output_path}")
    print(f"  Constituencies: {len(selected)}")
    print(f"  Rows: {len(batch)}")
    print(f"  States: {', '.join(states) if states else 'none'}")
    print(f"  Core variables: {', '.join(variables) if variables else 'none'}")


if __name__ == "__main__":
    main()
