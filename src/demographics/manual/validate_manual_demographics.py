"""Validate manually entered constituency demographic overrides."""

from __future__ import annotations

import argparse

from pathlib import Path

import pandas as pd

from src.demographics.manual.common import (
    ALLOWED_CONFIDENCE,
    ALLOWED_GEOGRAPHY_LEVELS,
    ALLOWED_VARIABLES,
    MANUAL_CSV_PATH,
    MANUAL_REPORTS_DIR,
    PERCENTAGE_VARIABLES,
    PROXY_GEOGRAPHY_LEVELS,
    QUALITY_REPORT_PATH,
    ensure_dirs,
    load_constituency_lookup,
    lookup_key,
    nan_to_none,
    non_empty_text,
    to_float,
)


def validate_row(
    row: pd.Series,
    constituency_lookup: dict[str, dict[str, str]],
    seen_keys: dict[tuple[str, str, str], set[tuple[str, str]]],
) -> tuple[str, list[str]]:
    issues: list[str] = []
    status = "valid"

    state_key = str(row.get("state_key", "")).strip()
    constituency_key = str(row.get("constituency_key", "")).strip()
    variable = str(row.get("variable", "")).strip()
    value = row.get("value")
    source_name = row.get("source_name")
    source_year = row.get("source_year")
    method = row.get("method")
    confidence = str(nan_to_none(row.get("confidence")) or "").strip().lower()
    notes = row.get("notes")
    geography_level = str(nan_to_none(row.get("geography_level")) or "").strip().lower()

    key = lookup_key(state_key, constituency_key)
    if key not in constituency_lookup:
        issues.append("state_key/constituency_key not found in constituencies")
        status = "needs_review"

    if variable not in ALLOWED_VARIABLES:
        issues.append(f"variable '{variable}' is not allowed")
        status = "invalid_value"

    numeric_value = to_float(value)
    if numeric_value is None:
        issues.append("value is missing or not numeric")
        status = "invalid_value"
    elif variable in PERCENTAGE_VARIABLES and not (0 <= numeric_value <= 100):
        issues.append("percentage value must be between 0 and 100")
        status = "invalid_value"

    if not non_empty_text(source_name):
        issues.append("source_name is required")
        status = "missing_source"

    if not non_empty_text(source_year):
        issues.append("source_year is required")
        if status == "valid":
            status = "missing_source"

    if not non_empty_text(method):
        issues.append("method is required")
        status = "missing_method"

    if confidence not in ALLOWED_CONFIDENCE:
        issues.append("confidence must be high, medium, or low")
        if status == "valid":
            status = "needs_review"

    if geography_level and geography_level not in ALLOWED_GEOGRAPHY_LEVELS:
        issues.append(f"geography_level '{geography_level}' is not allowed")
        if status == "valid":
            status = "needs_review"

    proxy_or_estimate = (
        geography_level in PROXY_GEOGRAPHY_LEVELS
        or (non_empty_text(method) and any(token in str(method).lower() for token in ("proxy", "estimate", "extrapol")))
    )
    if proxy_or_estimate and not non_empty_text(notes):
        issues.append("notes required for estimate/proxy values")
        if status == "valid":
            status = "needs_review"

    if geography_level in PROXY_GEOGRAPHY_LEVELS and confidence != "low":
        issues.append("proxy geography levels should use low confidence")
        if status == "valid":
            status = "needs_review"

    source_key = str(nan_to_none(source_name) or "").strip().lower()
    method_key = str(nan_to_none(method) or "").strip().lower()
    variable_key = (state_key, constituency_key, variable)
    source_method = (source_key, method_key)
    if variable_key in seen_keys:
        if source_method in seen_keys[variable_key]:
            issues.append("duplicate state_key + constituency_key + variable with same source/method")
            status = "duplicate_conflict"
        else:
            seen_keys[variable_key].add(source_method)
            issues.append("multiple manual values for same variable with different source/method")
            if status == "valid":
                status = "needs_review"
    else:
        seen_keys[variable_key] = {source_method}

    return status, issues


def validate_manual_csv(path: Path | None = None) -> pd.DataFrame:
    ensure_dirs()
    csv_path = path or MANUAL_CSV_PATH
    if not csv_path.exists():
        return pd.DataFrame(
            columns=[
                "row_index",
                "state_key",
                "constituency_key",
                "variable",
                "status",
                "issues",
            ]
        )

    manual = pd.read_csv(csv_path)
    manual = manual[manual["value"].notna() & (manual["value"].astype(str).str.strip() != "")]
    constituency_lookup = load_constituency_lookup()

    seen_keys: dict[tuple[str, str, str], set[tuple[str, str]]] = {}
    report_rows: list[dict[str, object]] = []

    for idx, row in manual.iterrows():
        status, issues = validate_row(row, constituency_lookup, seen_keys)
        report_rows.append(
            {
                "row_index": idx,
                "state": row.get("state", ""),
                "constituency": row.get("constituency", ""),
                "state_key": row.get("state_key", ""),
                "constituency_key": row.get("constituency_key", ""),
                "variable": row.get("variable", ""),
                "status": status,
                "issues": "; ".join(issues),
            }
        )

    if report_rows:
        return pd.DataFrame(report_rows)

    return pd.DataFrame(
        columns=[
            "row_index",
            "state",
            "constituency",
            "state_key",
            "constituency_key",
            "variable",
            "status",
            "issues",
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()

    report = validate_manual_csv()
    report.to_csv(QUALITY_REPORT_PATH, index=False)
    report.to_csv(MANUAL_REPORTS_DIR / "manual_demographic_quality_report.csv", index=False)

    valid = int((report["status"] == "valid").sum()) if not report.empty else 0
    total = len(report)
    print(f"Validated {total} manual rows ({valid} valid)")
    print(f"Output: {QUALITY_REPORT_PATH}")


if __name__ == "__main__":
    main()
