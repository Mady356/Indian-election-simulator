"""Shared helpers for CSDS QA, deduplication, and manual-review prioritization."""

from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

from src.postpoll.csds_manifest import EXTRACTED_DIR, FRONTEND_DATA_DIR, PROCESSED_DIR, REPORTS_DIR

VOTE_BEHAVIOR_PATH = PROCESSED_DIR / "csds_vote_behavior_tables.csv"
VOTE_BEHAVIOR_DEDUPED_PATH = PROCESSED_DIR / "csds_vote_behavior_tables_deduped.csv"
COMPARISON_PATH = PROCESSED_DIR / "csds_pre_post_comparison.csv"
COMPARISON_DEDUPED_PATH = PROCESSED_DIR / "csds_pre_post_comparison_deduped.csv"
MANUAL_REVIEW_PATH = REPORTS_DIR / "manual_extraction_needed.csv"

QUALITY_REPORT_PATH = REPORTS_DIR / "csds_vote_behavior_quality_report.csv"
DUPLICATE_KEYS_PATH = REPORTS_DIR / "csds_duplicate_keys.csv"
JOIN_AUDIT_PATH = REPORTS_DIR / "csds_pre_post_join_audit.csv"
MANUAL_PRIORITY_PATH = REPORTS_DIR / "manual_extraction_priority.csv"

ANALYTICAL_KEY = [
    "year",
    "poll_type",
    "geography_level",
    "state",
    "voter_group_type",
    "voter_group",
    "party_or_alliance",
]

JOIN_KEY = [
    "year",
    "geography_level",
    "state",
    "voter_group_type",
    "voter_group",
    "party_or_alliance",
]

VALID_YEARS = {2019, 2024}
VALID_POLL_TYPES = {"pre_poll", "post_poll"}
CONFIDENCE_RANK = {"high": 3, "medium": 2, "low": 1}
SHIFT_TOLERANCE = 0.5

VOTE_BEHAVIOR_BASE_COLUMNS = [
    "year",
    "poll_type",
    "geography_level",
    "state",
    "voter_group_type",
    "voter_group",
    "party_or_alliance",
    "vote_share",
    "sample_size",
    "source_table",
    "source_page",
    "confidence",
    "notes",
    "original_label",
]

DEDUPED_EXTRA_COLUMNS = [
    "dedupe_status",
    "duplicate_count",
    "conflict_flag",
    "dedupe_notes",
]

COMPARISON_DEDUPED_COLUMNS = [
    "year",
    "geography_level",
    "state",
    "voter_group_type",
    "voter_group",
    "party_or_alliance",
    "pre_poll_vote_share",
    "post_poll_vote_share",
    "pre_to_post_shift",
    "absolute_shift",
    "shift_direction",
    "pre_source_table",
    "post_source_table",
    "confidence",
    "notes",
]


def normalize_key_value(value: object) -> str:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return ""
    text = str(value).strip()
    if text.lower() in {"", "nan", "none", "null", "na", "n/a"}:
        return ""
    return text


def add_normalized_keys(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in ANALYTICAL_KEY:
        if col not in out.columns:
            out[col] = ""
        if col == "year":
            out[col] = pd.to_numeric(out[col], errors="coerce").astype("Int64")
        else:
            out[f"{col}_norm"] = out[col].map(normalize_key_value)
    return out


def analytical_key_tuple(row: pd.Series) -> tuple[object, ...]:
    year = row.get("year")
    return tuple(
        int(year) if pd.notna(year) else year,
        *[row.get(f"{col}_norm", normalize_key_value(row.get(col))) for col in ANALYTICAL_KEY[1:]],
    )


def join_key_tuple(row: pd.Series) -> tuple[object, ...]:
    year = row.get("year")
    values = [int(year) if pd.notna(year) else year]
    for col in JOIN_KEY[1:]:
        values.append(row.get(f"{col}_norm", normalize_key_value(row.get(col))))
    return tuple(values)


def confidence_rank(value: object) -> int:
    return CONFIDENCE_RANK.get(normalize_key_value(value).lower(), 0)


def parse_vote_share(value: object) -> float | None:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return None
    try:
        num = float(value)
    except (TypeError, ValueError):
        return None
    if 0 <= num <= 100:
        return round(num, 3)
    return None


def shift_direction(pre: float | None, post: float | None) -> str:
    if pre is None or post is None:
        return "unavailable"
    delta = post - pre
    if abs(delta) < SHIFT_TOLERANCE:
        return "unchanged"
    if delta > 0:
        return "increased_post_poll"
    return "decreased_post_poll"


def extract_table_file(reason: str) -> str:
    match = re.search(r"([\w]+_\d{4}_(?:pre|post)_poll_table_\d+\.csv)", reason, re.I)
    if match:
        return match.group(1)
    match = re.search(r"([\w]+\.csv)", reason)
    return match.group(1) if match else ""


def load_vote_behavior(path: Path | None = None) -> pd.DataFrame:
    source = path or VOTE_BEHAVIOR_PATH
    if not source.exists():
        return pd.DataFrame(columns=VOTE_BEHAVIOR_BASE_COLUMNS)
    return pd.read_csv(source)


def export_dashboard_json(vote_df: pd.DataFrame, comparison_df: pd.DataFrame) -> None:
    FRONTEND_DATA_DIR.mkdir(parents=True, exist_ok=True)

    def records(frame: pd.DataFrame) -> list[dict[str, object]]:
        if frame.empty:
            return []
        cleaned = frame.where(pd.notna(frame), None)
        return json.loads(cleaned.to_json(orient="records"))

    vote_payload = {
        "generated_at": pd.Timestamp.now("UTC").isoformat(),
        "source": str(VOTE_BEHAVIOR_DEDUPED_PATH),
        "deduped": True,
        "rows": records(vote_df),
        "row_count": len(vote_df),
    }
    comparison_payload = {
        "generated_at": pd.Timestamp.now("UTC").isoformat(),
        "source": str(COMPARISON_DEDUPED_PATH),
        "deduped": True,
        "rows": records(comparison_df),
        "row_count": len(comparison_df),
    }

    (FRONTEND_DATA_DIR / "csds_vote_behavior.json").write_text(
        json.dumps(vote_payload, indent=2),
        encoding="utf-8",
    )
    (FRONTEND_DATA_DIR / "csds_pre_post_comparison.json").write_text(
        json.dumps(comparison_payload, indent=2),
        encoding="utf-8",
    )
