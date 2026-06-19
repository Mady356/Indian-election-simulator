"""Shared helpers for Seat Intelligence Notes."""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
ANALYSIS_DIR = ROOT / "data" / "analysis"
COVERAGE_DIR = ANALYSIS_DIR / "coverage"
SEAT_ANALYSIS_DIR = ROOT / "data" / "seat_analysis"
GENERATED_DIR = SEAT_ANALYSIS_DIR / "generated"
MANUAL_DIR = SEAT_ANALYSIS_DIR / "manual"
PROCESSED_DIR = SEAT_ANALYSIS_DIR / "processed"
FRONTEND_DATA_DIR = ROOT / "frontend" / "public" / "data"

MASTER_PATH = ANALYSIS_DIR / "constituency_election_demographic_master.csv"
TOP_SWING_PATH = ANALYSIS_DIR / "top_swing_constituencies.csv"
CONSTITUENCY_COVERAGE_PATH = COVERAGE_DIR / "constituency_coverage.csv"
CONSTITUENCIES_JSON_PATH = FRONTEND_DATA_DIR / "constituencies.json"
STATES_JSON_PATH = FRONTEND_DATA_DIR / "states.json"

BASELINE_CSV_PATH = GENERATED_DIR / "seat_analysis_baseline.csv"
PRIORITY_CSV_PATH = GENERATED_DIR / "priority_seat_list.csv"
MANUAL_TEMPLATE_PATH = MANUAL_DIR / "manual_seat_notes_template.csv"
MANUAL_NOTES_PATH = MANUAL_DIR / "manual_seat_notes.csv"
FINAL_CSV_PATH = PROCESSED_DIR / "seat_analysis_final.csv"
FINAL_JSON_PATH = FRONTEND_DATA_DIR / "seat_analysis.json"

DEMOGRAPHIC_NFHS5_COLS = [
    "fertility_rate_nfhs5",
    "electricity_pct_nfhs5",
    "improved_sanitation_pct_nfhs5",
    "lpg_pct_nfhs5",
    "mobile_phone_pct_nfhs5",
    "bank_account_pct_nfhs5",
    "women_secondary_edu_pct_nfhs5",
    "female_literacy_pct_nfhs5",
    "male_literacy_pct_nfhs5",
    "wealth_index_mean_nfhs5",
    "urban_pct_nfhs5",
]

LARGE_SWING_THRESHOLD = 10.0
CLOSE_MARGIN_THRESHOLD = 5.0
HIGH_COVERAGE_THRESHOLD = 0.75
LOW_COVERAGE_THRESHOLD = 0.5
HIGH_TURNOUT_CHANGE_THRESHOLD = 5.0

MAJOR_CONSTITUENCIES = [
    "Varanasi",
    "Wayanad",
    "Rae Bareli",
    "Amethi",
    "Gandhinagar",
    "Nagpur",
    "Mumbai North",
    "Mumbai South",
    "Bangalore South",
    "Hyderabad",
    "Asansol",
    "Diamond Harbour",
    "Baramati",
    "Chennai South",
    "Coimbatore",
    "Thiruvananthapuram",
]

MANUAL_COLUMNS = [
    "state",
    "constituency",
    "state_key",
    "constituency_key",
    "manual_summary",
    "manual_electoral_movement",
    "manual_key_factors",
    "manual_demographic_context",
    "manual_local_context",
    "manual_what_to_watch",
    "manual_confidence",
    "analyst_name",
    "last_reviewed",
    "source_notes",
]

BASELINE_COLUMNS = [
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
    "data_quality_note",
    "what_to_watch",
    "confidence",
    "data_quality_label",
    "generated_from_fields",
    "last_updated",
]


def ensure_dirs() -> None:
    for path in (GENERATED_DIR, MANUAL_DIR, PROCESSED_DIR, FRONTEND_DATA_DIR):
        path.mkdir(parents=True, exist_ok=True)


def normalize_key(value: object) -> str:
    text = str(value).upper()
    text = text.replace("&", " AND ")
    text = re.sub(r"[–—\-/]", " ", text)
    text = re.sub(r"\((SC|ST)\)", "", text, flags=re.IGNORECASE)
    text = re.sub(r"[^A-Z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def lookup_key(state_key: str, constituency_key: str) -> str:
    return f"{normalize_key(state_key)}::{normalize_key(constituency_key)}"


def nan_to_none(value: object) -> object | None:
    if value is None:
        return None
    if isinstance(value, float) and pd.isna(value):
        return None
    if isinstance(value, str) and value.strip().lower() in {"", "nan", "none"}:
        return None
    return value


def to_float(value: object) -> float | None:
    cleaned = nan_to_none(value)
    if cleaned is None:
        return None
    try:
        return float(cleaned)
    except (TypeError, ValueError):
        return None


def to_bool(value: object) -> bool | None:
    cleaned = nan_to_none(value)
    if cleaned is None:
        return None
    if isinstance(cleaned, bool):
        return cleaned
    text = str(cleaned).strip().lower()
    if text in {"true", "1", "yes"}:
        return True
    if text in {"false", "0", "no"}:
        return False
    return None


def has_demographics(row: pd.Series) -> bool:
    return any(nan_to_none(row.get(col)) is not None for col in DEMOGRAPHIC_NFHS5_COLS)


def data_quality_label(nfhs5_coverage_share: float | None, has_demo: bool) -> str:
    if not has_demo or nfhs5_coverage_share is None or nfhs5_coverage_share <= 0:
        return "election_only"
    if nfhs5_coverage_share >= HIGH_COVERAGE_THRESHOLD:
        return "high"
    if nfhs5_coverage_share >= LOW_COVERAGE_THRESHOLD:
        return "medium"
    return "low"


def format_points(value: float | None, digits: int = 1) -> str | None:
    if value is None:
        return None
    sign = "+" if value > 0 else ""
    return f"{sign}{value:.{digits}f}"


def format_pct(value: float | None, digits: int = 1) -> str | None:
    if value is None:
        return None
    return f"{value:.{digits}f}%"


def load_master() -> pd.DataFrame:
    if not MASTER_PATH.exists():
        raise FileNotFoundError(f"Missing master dataset: {MASTER_PATH}")
    df = pd.read_csv(MASTER_PATH)
    if df.empty:
        raise ValueError("Master dataset is empty.")
    return df


def load_top_swing() -> pd.DataFrame:
    if not TOP_SWING_PATH.exists():
        return pd.DataFrame()
    return pd.read_csv(TOP_SWING_PATH)


def non_empty_text(value: object) -> bool:
    cleaned = nan_to_none(value)
    return cleaned is not None and str(cleaned).strip() != ""
