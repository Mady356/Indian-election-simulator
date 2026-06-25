"""Build a daily manual completion batch from the master seat worklist."""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

import pandas as pd

from src.demographics.manual.build_master_completion_worklist import INCOMPLETE_CATEGORIES, run_master_completion_worklist
from src.demographics.manual.common import (
    COMPLETION_CORE_FIELDS,
    COMPLETION_WORKLIST_PATH,
    DAILY_BATCHES_DIR,
    DAILY_BATCH_SIZE,
    MANUAL_CSV_PATH,
    default_unit,
    ensure_dirs,
    nan_to_none,
)
from src.demographics.manual.manual_progress_tracker import BATCH_COLUMNS

BATCH_EXTRA_COLUMNS = BATCH_COLUMNS + ["needs_election_result_research"]


def _load_existing_manual_keys() -> set[tuple[str, str, str]]:
    keys: set[tuple[str, str, str]] = set()
    if not MANUAL_CSV_PATH.exists():
        return keys
    manual = pd.read_csv(MANUAL_CSV_PATH)
    if manual.empty:
        return keys
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


def select_batch_seats(worklist: pd.DataFrame, batch_size: int = DAILY_BATCH_SIZE) -> pd.DataFrame:
    incomplete = worklist[worklist["completion_category"].isin(INCOMPLETE_CATEGORIES)].copy()
    if incomplete.empty:
        return incomplete

    return incomplete.sort_values(
        ["completion_priority", "priority_rank", "state", "constituency"],
        ascending=[True, True, True, True],
        na_position="last",
    ).head(batch_size)


def build_completion_batch_rows(
    selected: pd.DataFrame,
    existing_keys: set[tuple[str, str, str]],
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []

    for _, seat in selected.iterrows():
        state_key = str(seat["state_key"]).strip()
        constituency_key = str(seat["constituency_key"]).strip()
        category = str(seat["completion_category"])
        fields_to_fill = [
            part for part in str(seat.get("fields_to_fill") or "").split(";") if part in COMPLETION_CORE_FIELDS
        ]

        if category == "no_election_data_needs_election_results":
            rows.append(
                {
                    "state": seat["state"],
                    "constituency": seat["constituency"],
                    "state_key": state_key,
                    "constituency_key": constituency_key,
                    "variable": "",
                    "value": "",
                    "unit": "",
                    "source_name": "",
                    "source_url_or_document": "",
                    "source_year": "",
                    "geography_level": "",
                    "method": "",
                    "confidence": "",
                    "notes": (
                        "Seat missing election results in master dataset. "
                        "Research official 2019/2024 ECI results before adding demographics."
                    ),
                    "entered_by": "",
                    "last_updated": "",
                    "needs_election_result_research": "true",
                }
            )
            continue

        if not fields_to_fill:
            fields_to_fill = list(COMPLETION_CORE_FIELDS)

        for variable in fields_to_fill:
            if (state_key, constituency_key, variable) in existing_keys:
                continue
            rows.append(
                {
                    "state": seat["state"],
                    "constituency": seat["constituency"],
                    "state_key": state_key,
                    "constituency_key": constituency_key,
                    "variable": variable,
                    "value": "",
                    "unit": default_unit(variable),
                    "source_name": "",
                    "source_url_or_document": "",
                    "source_year": "",
                    "geography_level": "",
                    "method": "",
                    "confidence": "",
                    "notes": "",
                    "entered_by": "",
                    "last_updated": "",
                    "needs_election_result_research": "false",
                }
            )

    return pd.DataFrame(rows, columns=BATCH_EXTRA_COLUMNS)


def build_manual_completion_batch(
    batch_size: int = DAILY_BATCH_SIZE,
    refresh_worklist: bool = True,
) -> tuple[Path, pd.DataFrame, pd.DataFrame]:
    ensure_dirs()

    if refresh_worklist or not COMPLETION_WORKLIST_PATH.exists():
        run_master_completion_worklist()
    worklist = pd.read_csv(COMPLETION_WORKLIST_PATH)

    selected = select_batch_seats(worklist, batch_size=batch_size)
    existing_keys = _load_existing_manual_keys()
    batch = build_completion_batch_rows(selected, existing_keys)

    output_path = DAILY_BATCHES_DIR / f"manual_completion_batch_{date.today().strftime('%Y_%m_%d')}.csv"
    batch.to_csv(output_path, index=False)
    return output_path, batch, selected


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch-size", type=int, default=DAILY_BATCH_SIZE)
    parser.add_argument("--no-refresh", action="store_true", help="Skip regenerating master worklist")
    args = parser.parse_args()

    output_path, batch, selected = build_manual_completion_batch(
        batch_size=args.batch_size,
        refresh_worklist=not args.no_refresh,
    )

    states = sorted(batch["state"].dropna().unique().tolist()) if not batch.empty else []
    high_priority = int((selected["completion_priority"] == 1).sum()) if not selected.empty else 0

    print("\nManual completion batch")
    print(f"  Batch file: {output_path}")
    print(f"  Seats: {len(selected)}")
    print(f"  Rows: {len(batch)}")
    print(f"  States: {', '.join(states) if states else 'none'}")
    print(f"  High-priority seats included: {high_priority}")


if __name__ == "__main__":
    main()
