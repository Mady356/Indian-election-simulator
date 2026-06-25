"""Track manual demographic entry progress by state, constituency, and variable."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass

import pandas as pd

from src.demographics.manual.common import (
    CONSTITUENCIES_JSON_PATH,
    CORE_FIELDS,
    MANUAL_CSV_PATH,
    MANUAL_TEMPLATE_PATH,
    MASTER_WITH_MANUAL_PATH,
    PROGRESS_BY_CONSTITUENCY_PATH,
    PROGRESS_BY_STATE_PATH,
    PROGRESS_BY_VARIABLE_PATH,
    ensure_dirs,
    generated_value_for_variable,
    lookup_key,
    nan_to_none,
    non_empty_text,
)
from src.demographics.manual.validate_manual_demographics import validate_manual_csv

BATCH_COLUMNS = [
    "state",
    "constituency",
    "state_key",
    "constituency_key",
    "variable",
    "value",
    "unit",
    "source_name",
    "source_url_or_document",
    "source_year",
    "geography_level",
    "method",
    "confidence",
    "notes",
    "entered_by",
    "last_updated",
]


@dataclass
class ProgressContext:
    master: pd.DataFrame
    manual: pd.DataFrame
    template: pd.DataFrame
    quality_report: pd.DataFrame
    constituencies_json: list[dict[str, object]]
    valid_manual_keys: set[tuple[str, str, str]]


def _load_manual_rows() -> pd.DataFrame:
    if not MANUAL_CSV_PATH.exists():
        return pd.DataFrame(columns=BATCH_COLUMNS)
    manual = pd.read_csv(MANUAL_CSV_PATH)
    if manual.empty:
        return manual
    return manual[manual["value"].notna() & (manual["value"].astype(str).str.strip() != "")].copy()


def _load_template_rows() -> pd.DataFrame:
    if not MANUAL_TEMPLATE_PATH.exists():
        return pd.DataFrame(columns=BATCH_COLUMNS + ["override_allowed"])
    return pd.read_csv(MANUAL_TEMPLATE_PATH)


def _load_master() -> pd.DataFrame:
    if MASTER_WITH_MANUAL_PATH.exists():
        return pd.read_csv(MASTER_WITH_MANUAL_PATH)
    raise FileNotFoundError(f"Missing merged master panel: {MASTER_WITH_MANUAL_PATH}")


def _load_constituencies_json() -> list[dict[str, object]]:
    if not CONSTITUENCIES_JSON_PATH.exists():
        return []
    return json.loads(CONSTITUENCIES_JSON_PATH.read_text(encoding="utf-8"))


def _valid_manual_keys(quality_report: pd.DataFrame) -> set[tuple[str, str, str]]:
    if quality_report.empty or "status" not in quality_report.columns:
        return set()
    valid = quality_report[quality_report["status"] == "valid"]
    keys: set[tuple[str, str, str]] = set()
    for _, row in valid.iterrows():
        keys.add(
            (
                str(row["state_key"]).strip(),
                str(row["constituency_key"]).strip(),
                str(row["variable"]).strip(),
            )
        )
    return keys


def load_progress_context() -> ProgressContext:
    ensure_dirs()
    master = _load_master()
    manual = _load_manual_rows()
    template = _load_template_rows()
    quality_report = validate_manual_csv()
    constituencies_json = _load_constituencies_json()
    valid_keys = _valid_manual_keys(quality_report)
    return ProgressContext(
        master=master,
        manual=manual,
        template=template,
        quality_report=quality_report,
        constituencies_json=constituencies_json,
        valid_manual_keys=valid_keys,
    )


def _manual_rows_for_constituency(manual: pd.DataFrame, state_key: str, constituency_key: str) -> pd.DataFrame:
    if manual.empty:
        return manual
    mask = (
        manual["state_key"].astype(str).str.strip() == state_key
    ) & (
        manual["constituency_key"].astype(str).str.strip() == constituency_key
    )
    return manual[mask]


def _field_satisfied(
    master_row: pd.Series,
    manual_rows: pd.DataFrame,
    variable: str,
    valid_manual_keys: set[tuple[str, str, str]],
) -> bool:
    if generated_value_for_variable(master_row, variable) is not None:
        return True
    state_key = str(master_row["state_key"]).strip()
    constituency_key = str(master_row["constituency_key"]).strip()
    if (state_key, constituency_key, variable) in valid_manual_keys:
        return True
    if not manual_rows.empty:
        var_rows = manual_rows[manual_rows["variable"].astype(str).str.strip() == variable]
        if not var_rows.empty:
            return True
    return False


def build_constituency_progress(ctx: ProgressContext) -> pd.DataFrame:
    rows: list[dict[str, object]] = []

    for _, master_row in ctx.master.iterrows():
        state = str(master_row["state"])
        constituency = str(master_row["constituency"])
        state_key = str(master_row["state_key"]).strip()
        constituency_key = str(master_row["constituency_key"]).strip()
        source_type = str(nan_to_none(master_row.get("demographic_source_type")) or "election_only")

        manual_rows = _manual_rows_for_constituency(ctx.manual, state_key, constituency_key)
        manual_fields_entered = len(manual_rows)

        core_completed = 0
        missing_core: list[str] = []
        for variable in CORE_FIELDS:
            if _field_satisfied(master_row, manual_rows, variable, ctx.valid_manual_keys):
                core_completed += 1
            else:
                missing_core.append(variable)

        confidences: list[str] = []
        sources: set[str] = set()
        needs_review = False

        if not manual_rows.empty and not ctx.quality_report.empty:
            for idx in manual_rows.index:
                report_row = ctx.quality_report[ctx.quality_report["row_index"] == idx]
                if report_row.empty:
                    continue
                status = str(report_row.iloc[0]["status"])
                if status == "needs_review":
                    needs_review = True
                if status not in {"valid", "needs_review"}:
                    needs_review = True

        for _, manual_row in manual_rows.iterrows():
            confidence = str(nan_to_none(manual_row.get("confidence")) or "").strip().lower()
            if confidence:
                confidences.append(confidence)
            source_name = nan_to_none(manual_row.get("source_name"))
            if source_name:
                sources.add(str(source_name).strip())

        if source_type == "election_only" and core_completed < len(CORE_FIELDS):
            needs_review = True

        confidence_summary = ""
        if confidences:
            counts: dict[str, int] = {}
            for item in confidences:
                counts[item] = counts.get(item, 0) + 1
            confidence_summary = ", ".join(f"{key}:{counts[key]}" for key in sorted(counts))

        rows.append(
            {
                "state": state,
                "constituency": constituency,
                "state_key": state_key,
                "constituency_key": constituency_key,
                "demographic_source_type": source_type,
                "has_generated_data": source_type in {"generated", "mixed"},
                "has_manual_data": manual_fields_entered > 0 or source_type in {"manual", "mixed"},
                "manual_fields_entered": manual_fields_entered,
                "core_fields_completed": core_completed,
                "missing_core_fields": ";".join(missing_core),
                "confidence_summary": confidence_summary,
                "source_count": len(sources),
                "needs_review": needs_review,
            }
        )

    return pd.DataFrame(rows)


def build_state_progress(constituency_progress: pd.DataFrame, ctx: ProgressContext) -> pd.DataFrame:
    rows: list[dict[str, object]] = []

    for state, group in constituency_progress.groupby("state", sort=True):
        state_key = str(group.iloc[0]["state_key"])
        total = len(group)
        generated = int(group["has_generated_data"].sum())
        election_only = int((group["demographic_source_type"] == "election_only").sum())
        started = int((group["manual_fields_entered"] > 0).sum())
        completed_core = int((group["core_fields_completed"] >= len(CORE_FIELDS)).sum())

        state_manual = ctx.manual[ctx.manual["state_key"].astype(str).str.strip() == state_key] if not ctx.manual.empty else ctx.manual
        manual_entered = len(state_manual)

        valid_manual = 0
        if not ctx.quality_report.empty and not state_manual.empty:
            valid_idx = set(ctx.quality_report[ctx.quality_report["status"] == "valid"]["row_index"].tolist())
            valid_manual = int(state_manual.index.isin(valid_idx).sum())

        denominator = election_only if election_only > 0 else total
        completion_pct = round(100.0 * completed_core / denominator, 2) if denominator else 100.0

        rows.append(
            {
                "state": state,
                "state_key": state_key,
                "total_constituencies": total,
                "generated_demographic_constituencies": generated,
                "election_only_constituencies": election_only,
                "manual_constituencies_started": started,
                "manual_constituencies_completed_core": completed_core,
                "manual_values_entered": manual_entered,
                "valid_manual_values": valid_manual,
                "completion_pct": completion_pct,
            }
        )

    return pd.DataFrame(rows)


def build_variable_progress(ctx: ProgressContext, constituency_progress: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []

    master_by_key = {
        lookup_key(str(row["state_key"]), str(row["constituency_key"])): row
        for _, row in ctx.master.iterrows()
    }

    variables = sorted(set(ctx.template["variable"].dropna().astype(str).tolist())) if not ctx.template.empty else CORE_FIELDS

    for variable in variables:
        if not ctx.template.empty:
            template_var = ctx.template[ctx.template["variable"].astype(str) == variable]
            needed_keys = {
                lookup_key(str(row["state_key"]), str(row["constituency_key"]))
                for _, row in template_var.iterrows()
            }
        else:
            needed_keys = set()

        if not needed_keys:
            for key, master_row in master_by_key.items():
                manual_rows = _manual_rows_for_constituency(
                    ctx.manual,
                    str(master_row["state_key"]).strip(),
                    str(master_row["constituency_key"]).strip(),
                )
                if not _field_satisfied(master_row, manual_rows, variable, ctx.valid_manual_keys):
                    needed_keys.add(key)

        satisfied = 0
        for key in needed_keys:
            master_row = master_by_key.get(key)
            if master_row is None:
                continue
            manual_rows = _manual_rows_for_constituency(
                ctx.manual,
                str(master_row["state_key"]).strip(),
                str(master_row["constituency_key"]).strip(),
            )
            if _field_satisfied(master_row, manual_rows, variable, ctx.valid_manual_keys):
                satisfied += 1

        manual_entered = 0
        valid_values = 0
        if not ctx.manual.empty:
            var_manual = ctx.manual[ctx.manual["variable"].astype(str).str.strip() == variable]
            manual_entered = len(var_manual)
            if not ctx.quality_report.empty:
                valid_idx = set(ctx.quality_report[ctx.quality_report["status"] == "valid"]["row_index"].tolist())
                valid_values = int(var_manual.index.isin(valid_idx).sum())

        constituencies_needed = len(needed_keys) if needed_keys else len(master_by_key)
        completion_pct = round(100.0 * satisfied / constituencies_needed, 2) if constituencies_needed else 100.0

        rows.append(
            {
                "variable": variable,
                "constituencies_needed": constituencies_needed,
                "fields_satisfied": satisfied,
                "manual_values_entered": manual_entered,
                "valid_values": valid_values,
                "completion_pct": completion_pct,
            }
        )

    return pd.DataFrame(rows)


def print_console_summary(
    constituency_progress: pd.DataFrame,
    state_progress: pd.DataFrame,
    variable_progress: pd.DataFrame,
) -> None:
    election_only = int((constituency_progress["demographic_source_type"] == "election_only").sum())
    started = int((constituency_progress["manual_fields_entered"] > 0).sum())
    completed_core = int((constituency_progress["core_fields_completed"] >= len(CORE_FIELDS)).sum())

    print("Manual demographic progress")
    print(f"  Election-only seats: {election_only}")
    print(f"  Manual seats started: {started}")
    print(f"  Manual seats completed (core fields): {completed_core}")

    if not state_progress.empty:
        low_states = state_progress.sort_values(
            ["completion_pct", "election_only_constituencies"],
            ascending=[True, False],
        ).head(10)
        print("\n  Top 10 states still missing coverage:")
        for _, row in low_states.iterrows():
            print(
                f"    {row['state']}: {row['completion_pct']}% core complete "
                f"({row['election_only_constituencies']} election-only)"
            )

    if not variable_progress.empty:
        core_vars = variable_progress[
            variable_progress["variable"].isin(CORE_FIELDS)
        ].sort_values(["completion_pct", "constituencies_needed"], ascending=[True, False])
        print("\n  Top 10 core variables still missing:")
        for _, row in core_vars.head(10).iterrows():
            print(
                f"    {row['variable']}: {row['completion_pct']}% "
                f"({row['fields_satisfied']}/{row['constituencies_needed']} satisfied)"
            )


def run_progress_tracker() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    ctx = load_progress_context()
    constituency_progress = build_constituency_progress(ctx)
    state_progress = build_state_progress(constituency_progress, ctx)
    variable_progress = build_variable_progress(ctx, constituency_progress)

    constituency_progress.to_csv(PROGRESS_BY_CONSTITUENCY_PATH, index=False)
    state_progress.to_csv(PROGRESS_BY_STATE_PATH, index=False)
    variable_progress.to_csv(PROGRESS_BY_VARIABLE_PATH, index=False)

    print_console_summary(constituency_progress, state_progress, variable_progress)
    print(f"\nWrote: {PROGRESS_BY_STATE_PATH}")
    print(f"Wrote: {PROGRESS_BY_CONSTITUENCY_PATH}")
    print(f"Wrote: {PROGRESS_BY_VARIABLE_PATH}")

    return state_progress, constituency_progress, variable_progress


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    run_progress_tracker()


if __name__ == "__main__":
    main()
