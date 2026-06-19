"""Merge generated baseline notes with optional manual analyst overrides."""

from __future__ import annotations

import json

import pandas as pd

from src.seat_analysis.common import (
    BASELINE_CSV_PATH,
    FINAL_CSV_PATH,
    FINAL_JSON_PATH,
    MANUAL_NOTES_PATH,
    MANUAL_TEMPLATE_PATH,
    ensure_dirs,
    lookup_key,
    nan_to_none,
    non_empty_text,
)


FINAL_COLUMNS = [
    "state",
    "constituency",
    "state_key",
    "constituency_key",
    "analysis_type",
    "summary",
    "electoral_movement",
    "key_factors",
    "demographic_context",
    "district_context",
    "local_context",
    "data_quality_note",
    "what_to_watch",
    "confidence",
    "data_quality_label",
    "analysis_source",
    "generated_from_fields",
    "last_updated",
]

MANUAL_FIELD_MAP = {
    "manual_summary": "summary",
    "manual_electoral_movement": "electoral_movement",
    "manual_key_factors": "key_factors",
    "manual_demographic_context": "demographic_context",
    "manual_local_context": "local_context",
    "manual_what_to_watch": "what_to_watch",
    "manual_confidence": "confidence",
}


def _load_manual_notes() -> pd.DataFrame:
    if MANUAL_NOTES_PATH.exists():
        manual = pd.read_csv(MANUAL_NOTES_PATH)
        if not manual.empty:
            return manual.drop_duplicates(subset=["state_key", "constituency_key"], keep="last")

    if not MANUAL_TEMPLATE_PATH.exists():
        return pd.DataFrame()

    template = pd.read_csv(MANUAL_TEMPLATE_PATH)
    if template.empty:
        return pd.DataFrame()

    manual_cols = list(MANUAL_FIELD_MAP.keys()) + ["analyst_name", "source_notes"]
    has_manual = template[manual_cols].apply(
        lambda row: any(non_empty_text(value) for value in row),
        axis=1,
    )
    return template.loc[has_manual].drop_duplicates(subset=["state_key", "constituency_key"], keep="last")


def _merge_row(baseline_row: pd.Series, manual_row: pd.Series | None) -> dict[str, object]:
    merged = baseline_row.to_dict()
    merged["local_context"] = ""
    merged["analysis_type"] = "final"
    manual_used = 0
    generated_used = 0

    for manual_col, final_col in MANUAL_FIELD_MAP.items():
        manual_value = None
        if manual_row is not None:
            manual_value = nan_to_none(manual_row.get(manual_col))
        if non_empty_text(manual_value):
            merged[final_col] = str(manual_value).strip()
            manual_used += 1
        elif nan_to_none(merged.get(final_col)) is not None:
            generated_used += 1

    if manual_used and generated_used:
        merged["analysis_source"] = "mixed"
    elif manual_used:
        merged["analysis_source"] = "manual"
    else:
        merged["analysis_source"] = "generated"

    if manual_row is not None and non_empty_text(manual_row.get("last_reviewed")):
        merged["last_updated"] = str(manual_row.get("last_reviewed")).strip()
    elif non_empty_text(manual_row.get("analyst_name") if manual_row is not None else None):
        merged["last_updated"] = str(baseline_row.get("last_updated"))

    return merged


def build_final_dataframe(baseline: pd.DataFrame, manual: pd.DataFrame) -> pd.DataFrame:
    manual_by_key: dict[str, pd.Series] = {}
    if not manual.empty:
        for _, row in manual.iterrows():
            key = lookup_key(str(row["state_key"]), str(row["constituency_key"]))
            manual_by_key[key] = row

    rows = []
    for _, baseline_row in baseline.iterrows():
        key = lookup_key(str(baseline_row["state_key"]), str(baseline_row["constituency_key"]))
        rows.append(_merge_row(baseline_row, manual_by_key.get(key)))

    return pd.DataFrame(rows, columns=FINAL_COLUMNS)


def build_frontend_json(final_df: pd.DataFrame) -> dict[str, dict[str, object]]:
    payload: dict[str, dict[str, object]] = {}
    for _, row in final_df.iterrows():
        key = lookup_key(str(row["state_key"]), str(row["constituency_key"]))
        payload[key] = {
            "state": row["state"],
            "constituency": row["constituency"],
            "state_key": row["state_key"],
            "constituency_key": row["constituency_key"],
            "summary": row["summary"],
            "electoral_movement": row["electoral_movement"],
            "key_factors": row["key_factors"],
            "demographic_context": row["demographic_context"],
            "district_context": row["district_context"],
            "local_context": row.get("local_context") or "",
            "what_to_watch": row["what_to_watch"],
            "confidence": row["confidence"],
            "data_quality_note": row["data_quality_note"],
            "analysis_source": row["analysis_source"],
            "data_quality_label": row["data_quality_label"],
            "last_updated": row["last_updated"],
        }
    return payload


def main() -> None:
    ensure_dirs()
    if not BASELINE_CSV_PATH.exists():
        raise FileNotFoundError(
            f"Missing baseline notes at {BASELINE_CSV_PATH}. "
            "Run python -m src.seat_analysis.build_seat_analysis_baseline first."
        )

    baseline = pd.read_csv(BASELINE_CSV_PATH)
    manual = _load_manual_notes()
    final_df = build_final_dataframe(baseline, manual)
    final_df.to_csv(FINAL_CSV_PATH, index=False)

    payload = build_frontend_json(final_df)
    FINAL_JSON_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    source_counts = final_df["analysis_source"].value_counts().to_dict()
    print(f"Wrote {len(final_df)} final seat notes to {FINAL_CSV_PATH}")
    print(f"Wrote frontend JSON to {FINAL_JSON_PATH}")
    print(f"Analysis sources: {source_counts}")


if __name__ == "__main__":
    main()
