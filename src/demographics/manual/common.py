"""Shared helpers for manual constituency demographic overrides."""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
ANALYSIS_DIR = ROOT / "data" / "analysis"
DEMOGRAPHICS_DIR = ROOT / "data" / "demographics"
MANUAL_DIR = DEMOGRAPHICS_DIR / "manual"
MANUAL_REPORTS_DIR = MANUAL_DIR / "reports"
PROCESSED_DIR = DEMOGRAPHICS_DIR / "processed"
FRONTEND_DATA_DIR = ROOT / "frontend" / "public" / "data"

MASTER_PATH = ANALYSIS_DIR / "constituency_election_demographic_master.csv"
MASTER_WITH_MANUAL_PATH = ANALYSIS_DIR / "constituency_election_demographic_master_with_manual.csv"
CONSTITUENCIES_JSON_PATH = FRONTEND_DATA_DIR / "constituencies.json"
MANUAL_TEMPLATE_PATH = MANUAL_DIR / "manual_constituency_demographics_template.csv"
MANUAL_CSV_PATH = MANUAL_DIR / "manual_constituency_demographics.csv"
QUALITY_REPORT_PATH = MANUAL_DIR / "manual_demographic_quality_report.csv"
PROCESSED_PANEL_PATH = PROCESSED_DIR / "constituency_demographic_panel_with_manual.csv"
MANUAL_SOURCES_JSON_PATH = FRONTEND_DATA_DIR / "manual_demographic_sources.json"
DAILY_BATCHES_DIR = MANUAL_DIR / "daily_batches"
PRIORITY_SEAT_LIST_PATH = ROOT / "data" / "seat_analysis" / "generated" / "priority_seat_list.csv"
SEAT_NOTE_COVERAGE_PATH = ROOT / "data" / "seat_analysis" / "manual" / "reports" / "seat_note_coverage_report.csv"

PROGRESS_BY_STATE_PATH = MANUAL_REPORTS_DIR / "manual_demographic_progress_by_state.csv"
PROGRESS_BY_CONSTITUENCY_PATH = MANUAL_REPORTS_DIR / "manual_demographic_progress_by_constituency.csv"
PROGRESS_BY_VARIABLE_PATH = MANUAL_REPORTS_DIR / "manual_demographic_progress_by_variable.csv"

GEOJSON_PATH = ROOT / "frontend" / "public" / "geo" / "india_constituencies.geojson"
DELIMITATION_PATH = ROOT / "data" / "reference" / "lok_sabha_district_summary_delimitation.csv"
COMPLETION_WORKLIST_PATH = MANUAL_REPORTS_DIR / "master_seat_completion_worklist.csv"
COMPLETION_BY_STATE_PATH = MANUAL_REPORTS_DIR / "master_seat_completion_by_state.csv"
COMPLETION_CHECKLIST_MD_PATH = MANUAL_REPORTS_DIR / "master_seat_completion_checklist.md"

COMPLETION_CORE_FIELDS = [
    "urban_pct",
    "literacy_rate",
    "female_literacy_pct",
    "male_literacy_pct",
    "sc_pct",
    "st_pct",
    "religion_hindu_pct",
    "religion_muslim_pct",
    "religion_christian_pct",
    "religion_sikh_pct",
    "population_density",
    "sex_ratio",
]

MAJOR_STATE_KEYS = {
    "MAHARASHTRA",
    "UTTAR PRADESH",
    "WEST BENGAL",
    "BIHAR",
    "ODISHA",
    "RAJASTHAN",
    "TAMIL NADU",
    "KARNATAKA",
    "ANDHRA PRADESH",
    "MADHYA PRADESH",
    "NCT OF DELHI",
}

CORE_FIELDS = [
    "urban_pct",
    "literacy_rate",
    "sc_pct",
    "st_pct",
    "religion_hindu_pct",
    "religion_muslim_pct",
    "religion_christian_pct",
    "religion_sikh_pct",
    "population_density",
    "sex_ratio",
]

DAILY_BATCH_SIZE = 50

LOW_COVERAGE_THRESHOLD = 0.75

ALLOWED_VARIABLES = [
    "urban_pct",
    "literacy_rate",
    "female_literacy_pct",
    "male_literacy_pct",
    "sc_pct",
    "st_pct",
    "religion_hindu_pct",
    "religion_muslim_pct",
    "religion_christian_pct",
    "religion_sikh_pct",
    "population_density",
    "sex_ratio",
    "electricity_pct",
    "lpg_pct",
    "improved_sanitation_pct",
    "mobile_phone_pct",
    "bank_account_pct",
    "wealth_index_mean",
    "fertility_rate",
]

PERCENTAGE_VARIABLES = {
    "urban_pct",
    "literacy_rate",
    "female_literacy_pct",
    "male_literacy_pct",
    "sc_pct",
    "st_pct",
    "religion_hindu_pct",
    "religion_muslim_pct",
    "religion_christian_pct",
    "religion_sikh_pct",
    "electricity_pct",
    "lpg_pct",
    "improved_sanitation_pct",
    "mobile_phone_pct",
    "bank_account_pct",
}

PROXY_GEOGRAPHY_LEVELS = {
    "district_weighted_estimate",
    "state_average_proxy",
}

ALLOWED_CONFIDENCE = {"high", "medium", "low"}

ALLOWED_GEOGRAPHY_LEVELS = {
    "constituency",
    "district",
    "subdistrict",
    "municipal",
    "district_weighted_estimate",
    "state_average_proxy",
}

# Manual variable -> generated NFHS-5 master column
VARIABLE_TO_NFHS5 = {
    "urban_pct": "urban_pct_nfhs5",
    "female_literacy_pct": "female_literacy_pct_nfhs5",
    "male_literacy_pct": "male_literacy_pct_nfhs5",
    "electricity_pct": "electricity_pct_nfhs5",
    "lpg_pct": "lpg_pct_nfhs5",
    "improved_sanitation_pct": "improved_sanitation_pct_nfhs5",
    "mobile_phone_pct": "mobile_phone_pct_nfhs5",
    "bank_account_pct": "bank_account_pct_nfhs5",
    "wealth_index_mean": "wealth_index_mean_nfhs5",
    "fertility_rate": "fertility_rate_nfhs5",
}

MANUAL_ONLY_VARIABLES = set(ALLOWED_VARIABLES) - set(VARIABLE_TO_NFHS5.keys())

TEMPLATE_COLUMNS = [
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
    "override_allowed",
]

SOURCE_META_SUFFIXES = ("_source", "_source_year", "_method", "_confidence")


def ensure_dirs() -> None:
    for path in (MANUAL_DIR, MANUAL_REPORTS_DIR, PROCESSED_DIR, FRONTEND_DATA_DIR, DAILY_BATCHES_DIR):
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


def non_empty_text(value: object) -> bool:
    cleaned = nan_to_none(value)
    return cleaned is not None and str(cleaned).strip() != ""


def to_float(value: object) -> float | None:
    cleaned = nan_to_none(value)
    if cleaned is None:
        return None
    try:
        return float(cleaned)
    except (TypeError, ValueError):
        return None


def load_constituency_lookup() -> dict[str, dict[str, str]]:
    import json

    if not CONSTITUENCIES_JSON_PATH.exists():
        master = pd.read_csv(MASTER_PATH)
        lookup: dict[str, dict[str, str]] = {}
        for _, row in master.iterrows():
            key = lookup_key(str(row["state_key"]), str(row["constituency_key"]))
            lookup[key] = {
                "state": str(row["state"]),
                "constituency": str(row["constituency"]),
                "state_key": str(row["state_key"]),
                "constituency_key": str(row["constituency_key"]),
            }
        return lookup

    records = json.loads(CONSTITUENCIES_JSON_PATH.read_text(encoding="utf-8"))
    lookup = {}
    for row in records:
        key = lookup_key(str(row["state_key"]), str(row["constituency_key"]))
        lookup[key] = {
            "state": str(row["state"]),
            "constituency": str(row["constituency"]),
            "state_key": str(row["state_key"]),
            "constituency_key": str(row["constituency_key"]),
        }
    return lookup


def generated_value_for_variable(row: pd.Series, variable: str) -> float | None:
    nfhs_col = VARIABLE_TO_NFHS5.get(variable)
    if nfhs_col:
        return to_float(row.get(nfhs_col))
    return to_float(row.get(variable))


def constituency_needs_manual_template(row: pd.Series) -> bool:
    coverage = to_float(row.get("nfhs5_coverage_share"))
    has_any = any(generated_value_for_variable(row, var) is not None for var in ALLOWED_VARIABLES)
    if not has_any:
        return True
    if coverage is None or coverage <= 0:
        return True
    if coverage < LOW_COVERAGE_THRESHOLD:
        return True
    return False


def clean_delimitation_constituency_name(name: object) -> str:
    text = str(name).strip()
    text = re.sub(r"\s*\([^)]*\)", "", text)
    text = re.split(r",\s*\d+-", text)[0]
    text = re.sub(r"\s+\d+-.*", "", text)
    return text.strip()


def data_quality_label_from_row(row: pd.Series) -> str:
    coverage = to_float(row.get("nfhs5_coverage_share"))
    has_demo = any(generated_value_for_variable(row, var) is not None for var in ALLOWED_VARIABLES)
    if not has_demo or coverage is None or coverage <= 0:
        return "election_only"
    if coverage >= 0.75:
        return "high"
    if coverage >= 0.5:
        return "medium"
    return "low"


def default_unit(variable: str) -> str:
    if variable in PERCENTAGE_VARIABLES:
        return "percent"
    if variable == "population_density":
        return "persons_per_sq_km"
    if variable == "sex_ratio":
        return "females_per_1000_males"
    if variable == "fertility_rate":
        return "births_per_woman"
    if variable == "wealth_index_mean":
        return "index"
    return ""
