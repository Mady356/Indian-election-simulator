"""Merge validated manual demographic overrides into the master panel."""

from __future__ import annotations

import argparse
import json

import pandas as pd

from src.demographics.manual.common import (
    ALLOWED_VARIABLES,
    MANUAL_CSV_PATH,
    MASTER_PATH,
    MASTER_WITH_MANUAL_PATH,
    PROCESSED_PANEL_PATH,
    VARIABLE_TO_NFHS5,
    ensure_dirs,
    generated_value_for_variable,
    lookup_key,
    nan_to_none,
    to_float,
)
from src.demographics.manual.validate_manual_demographics import validate_manual_csv


def parse_bool(value: object) -> bool:
    cleaned = nan_to_none(value)
    if cleaned is None:
        return False
    return str(cleaned).strip().lower() in {"1", "true", "yes", "y"}


def apply_manual_rows(master: pd.DataFrame, manual: pd.DataFrame, report: pd.DataFrame) -> pd.DataFrame:
    valid_rows = report[report["status"] == "valid"] if "status" in report.columns else report.iloc[0:0]
    if valid_rows.empty:
        return master.copy()

    master = master.copy()
    master_index = {
        lookup_key(str(row["state_key"]), str(row["constituency_key"])): idx
        for idx, row in master.iterrows()
    }

    for _, report_row in valid_rows.iterrows():
        row_index = int(report_row["row_index"])
        manual_row = manual.loc[row_index]
        key = lookup_key(str(manual_row["state_key"]), str(manual_row["constituency_key"]))
        if key not in master_index:
            continue

        idx = master_index[key]
        variable = str(manual_row["variable"]).strip()
        manual_value = to_float(manual_row["value"])
        if manual_value is None:
            continue

        override_allowed = parse_bool(manual_row.get("override_allowed"))
        generated_col = VARIABLE_TO_NFHS5.get(variable, variable)
        generated_value = generated_value_for_variable(master.loc[idx], variable)

        source_name = str(nan_to_none(manual_row.get("source_name")) or "")
        source_year = str(nan_to_none(manual_row.get("source_year")) or "")
        method = str(nan_to_none(manual_row.get("method")) or "")
        confidence = str(nan_to_none(manual_row.get("confidence")) or "")

        master.at[idx, f"{variable}_source"] = source_name
        master.at[idx, f"{variable}_source_year"] = source_year
        master.at[idx, f"{variable}_method"] = method
        master.at[idx, f"{variable}_confidence"] = confidence

        if generated_value is None:
            master.at[idx, generated_col] = manual_value
            master.at[idx, f"{variable}_origin"] = "manual"
        elif override_allowed:
            master.at[idx, generated_col] = manual_value
            master.at[idx, f"{variable}_origin"] = "manual_override"
            master.at[idx, f"{variable}_generated_reference"] = generated_value
        else:
            master.at[idx, f"manual_{variable}"] = manual_value
            master.at[idx, f"{variable}_origin"] = "manual_reference"

    return master


def add_summary_fields(master: pd.DataFrame) -> pd.DataFrame:
    master = master.copy()

    manual_counts: list[int] = []
    source_counts: list[int] = []
    source_types: list[str] = []

    for _, row in master.iterrows():
        manual_fields = 0
        sources: set[str] = set()
        has_generated = False
        has_manual = False

        for variable in ALLOWED_VARIABLES:
            origin = str(nan_to_none(row.get(f"{variable}_origin")) or "")
            generated = generated_value_for_variable(row, variable) is not None

            if origin in {"manual", "manual_override"}:
                manual_fields += 1
                has_manual = True
                source = str(nan_to_none(row.get(f"{variable}_source")) or "")
                if source:
                    sources.add(source)
            elif origin == "manual_reference":
                has_manual = True
                source = str(nan_to_none(row.get(f"{variable}_source")) or "")
                if source:
                    sources.add(source)

            if generated and origin not in {"manual", "manual_override"}:
                has_generated = True

        manual_counts.append(manual_fields)
        source_counts.append(len(sources))

        if has_manual and has_generated:
            source_types.append("mixed")
        elif has_manual:
            source_types.append("manual")
        elif has_generated:
            source_types.append("generated")
        else:
            source_types.append("election_only")

    master["manual_demographic_fields_count"] = manual_counts
    master["manual_demographic_source_count"] = source_counts
    master["demographic_source_type"] = source_types
    return master


def merge_manual_demographics() -> pd.DataFrame:
    ensure_dirs()
    master = pd.read_csv(MASTER_PATH)

    if not MANUAL_CSV_PATH.exists():
        merged = add_summary_fields(master)
        merged.to_csv(MASTER_WITH_MANUAL_PATH, index=False)
        merged.to_csv(PROCESSED_PANEL_PATH, index=False)
        return merged

    manual = pd.read_csv(MANUAL_CSV_PATH)
    manual = manual[manual["value"].notna() & (manual["value"].astype(str).str.strip() != "")]
    report = validate_manual_csv()

    merged = apply_manual_rows(master, manual, report)
    merged = add_summary_fields(merged)
    merged.to_csv(MASTER_WITH_MANUAL_PATH, index=False)
    merged.to_csv(PROCESSED_PANEL_PATH, index=False)
    return merged


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()

    merged = merge_manual_demographics()
    summary = merged["demographic_source_type"].value_counts().to_dict()
    print(f"Wrote {len(merged)} rows")
    print(f"Output: {MASTER_WITH_MANUAL_PATH}")
    print(f"Output: {PROCESSED_PANEL_PATH}")
    print(f"Source types: {json.dumps(summary)}")


if __name__ == "__main__":
    main()
