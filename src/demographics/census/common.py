"""Shared paths and helpers for Census 2011 constituency autofill."""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd

from src.config import DEMOGRAPHICS_PROCESSED_DIR, LEGACY_CENSUS_2011_DIRS, REFERENCE_DIR
from src.demographics.manual.common import (
    COMPLETION_CORE_FIELDS,
    COMPLETION_WORKLIST_PATH,
    CONSTITUENCIES_JSON_PATH,
    DELIMITATION_PATH,
    GEOJSON_PATH,
    MANUAL_CSV_PATH,
    MASTER_WITH_MANUAL_PATH,
    clean_delimitation_constituency_name,
    generated_value_for_variable,
    lookup_key,
    nan_to_none,
    normalize_key,
    to_float,
)

ROOT = Path(__file__).resolve().parents[3]
CENSUS_DIR = ROOT / "data" / "demographics" / "census"
CENSUS_RAW_DIR = CENSUS_DIR / "raw"
CENSUS_RELIGION_RAW_DIR = CENSUS_RAW_DIR / "religion"
CENSUS_REPORTS_DIR = CENSUS_DIR / "reports"
MANUAL_DIR = ROOT / "data" / "demographics" / "manual"
MANUAL_REPORTS_DIR = MANUAL_DIR / "reports"

CENSUS_DISTRICT_CORE_PATH = CENSUS_DIR / "census_2011_district_core.csv"
CENSUS_DISTRICT_AREA_PATH = CENSUS_DIR / "census_2011_district_area.csv"
CENSUS_DISTRICT_RELIGION_PATH = CENSUS_DIR / "census_2011_district_religion.csv"
C01_RELIGION_MANIFEST_PATH = CENSUS_REPORTS_DIR / "c01_religion_download_manifest.csv"
C01_RELIGION_MISSING_PRIORITY_PATH = CENSUS_REPORTS_DIR / "c01_religion_missing_priority_states.csv"
AUTOFILL_CANDIDATES_PATH = CENSUS_DIR / "constituency_census_autofill_candidates.csv"
MANUAL_AUTOFILL_CANDIDATES_PATH = MANUAL_DIR / "manual_constituency_demographics_autofill_candidates.csv"
ALIAS_REPAIR_REPORT_PATH = MANUAL_REPORTS_DIR / "completion_worklist_alias_repair_report.csv"
CLEANED_WORKLIST_PATH = MANUAL_REPORTS_DIR / "master_seat_completion_worklist_cleaned.csv"
FINAL_543_UNIVERSE_PATH = MANUAL_REPORTS_DIR / "final_543_seat_universe.csv"
NON_543_EXCLUDE_PATH = MANUAL_REPORTS_DIR / "non_543_records_to_exclude.csv"
SKIPPED_DIAGNOSTICS_PATH = CENSUS_REPORTS_DIR / "skipped_autofill_seats_diagnostics.csv"
SKIPPED_DIAGNOSTICS_MD_PATH = CENSUS_REPORTS_DIR / "skipped_autofill_seats_markdown.md"
DELIMITATION_CENSUS_ALIAS_PATH = REFERENCE_DIR / "delimitation_census_district_alias.csv"
PROCESSED_DISTRICT_CENSUS_PATH = DEMOGRAPHICS_PROCESSED_DIR / "census_district_demographics_2011.csv"

CENSUS_SOURCE_NAME = "Census 2011"
CENSUS_SOURCE_YEAR = "2011"
CENSUS_SOURCE_URL = "https://censusindia.gov.in/census.website/data/population-finder"

RAW_EXTENSIONS = {".xlsx", ".xls", ".csv"}

TELANGANA_DISTRICTS = {
    "ADILABAD", "NIZAMABAD", "KARIMNAGAR", "MEDAK", "HYDERABAD", "RANGAREDDY",
    "RANGAREDDI", "MAHBUBNAGAR", "NALGONDA", "WARANGAL", "KHAMMAM",
}
LADAKH_DISTRICTS = {"LEH(LADAKH)", "LEH", "KARGIL"}

STATE_ALIASES: dict[str, str] = {
    "ORISSA": "ODISHA",
    "DELHI": "NCT OF DELHI",
    "NCT OF DELHI": "NCT OF DELHI",
    "ANDAMAN AND NICOBAR": "ANDAMAN & NICOBAR ISLANDS",
    "ANDAMAN AND NICOBAR ISLANDS": "ANDAMAN & NICOBAR ISLANDS",
    "DADRA AND NAGAR HAVELI": "DADRA & NAGAR HAVELI",
    "DADAR AND NAGAR HAVELI": "DADRA & NAGAR HAVELI",
    "DADRA & NAGAR HAVELI": "DADRA & NAGAR HAVELI",
    "DAMAN AND DIU": "DAMAN & DIU",
    "DAMAN & DIU": "DAMAN & DIU",
    "PONDICHERRY": "PUDUCHERRY",
    "UTTARANCHAL": "UTTARAKHAND",
}

CONSTITUENCY_ALIASES: dict[tuple[str, str], tuple[str, str]] = {
    ("ASSAM", "GAUHATI"): ("ASSAM", "GUWAHATI"),
    ("ASSAM", "NOWGONG"): ("ASSAM", "NAGAON"),
    ("ASSAM", "MANGALDOI"): ("ASSAM", "DARRANG-UDALGURI"),
    ("ASSAM", "TEZPUR"): ("ASSAM", "SONITPUR"),
    ("ASSAM", "KALIABOR"): ("ASSAM", "KAZIRANGA"),
    ("BIHAR", "PATALIPUTRA"): ("BIHAR", "PATLIPUTRA"),
    ("UTTAR PRADESH", "BAHRAICH"): ("UTTAR PRADESH", "BAHARAICH"),
    ("TAMIL NADU", "KANYAKUMARI"): ("TAMIL NADU", "KANNIYAKUMARI"),
    ("ANDHRA PRADESH", "THIRUPATHI"): ("ANDHRA PRADESH", "TIRUPATI"),
    ("ANDHRA PRADESH", "NARSARAOPET"): ("ANDHRA PRADESH", "NARASARAOPET"),
    ("ANDHRA PRADESH", "ANANTAPURAMU"): ("ANDHRA PRADESH", "ANANTHAPUR"),
    ("ANDHRA PRADESH", "ANANTAPUR"): ("ANDHRA PRADESH", "ANANTHAPUR"),
    ("ANDHRA PRADESH", "KURNOOL"): ("ANDHRA PRADESH", "KURNOOLU"),
    ("TELANGANA", "BHUVANAGIRI"): ("TELANGANA", "BHONGIR"),
    ("PUNJAB", "FIROZEPUR"): ("PUNJAB", "FIROZPUR"),
    ("DADRA & NAGAR HAVELI", "DADAR & NAGAR HAVELI"): ("DADRA & NAGAR HAVELI", "DADRA & NAGAR HAVELI"),
    ("ANDAMAN AND NICOBAR", "ANDAMAN AND NICOBAR ISLANDS"): (
        "ANDAMAN & NICOBAR ISLANDS",
        "ANDAMAN NICOBAR ISLANDS",
    ),
}

AUTOFILL_TARGET_CATEGORIES = {
    "election_only_needs_demographics",
    "partial_demographics_missing_core_fields",
    "low_coverage_needs_review",
}

MANUAL_ENTRY_COLUMNS = [
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

VARIABLE_UNITS = {
    "urban_pct": "percent",
    "literacy_rate": "percent",
    "female_literacy_pct": "percent",
    "male_literacy_pct": "percent",
    "sc_pct": "percent",
    "st_pct": "percent",
    "religion_hindu_pct": "percent",
    "religion_muslim_pct": "percent",
    "religion_christian_pct": "percent",
    "religion_sikh_pct": "percent",
    "population_density": "persons_per_sq_km",
    "sex_ratio": "females_per_1000_males",
}


def ensure_dirs() -> None:
    for path in (CENSUS_DIR, CENSUS_RAW_DIR, CENSUS_RELIGION_RAW_DIR, CENSUS_REPORTS_DIR, MANUAL_REPORTS_DIR):
        path.mkdir(parents=True, exist_ok=True)


def census_raw_roots() -> list[Path]:
    roots = [CENSUS_RAW_DIR, CENSUS_RELIGION_RAW_DIR, *LEGACY_CENSUS_2011_DIRS]
    return [path for path in roots if path.exists()]


def find_c01_religion_files() -> list[Path]:
    """Return state-level DDWxxC-01 religion files, excluding all-India DDW00C-01."""
    import re

    pattern = re.compile(r"DDW(\d{2})C-01", re.IGNORECASE)
    found: dict[str, Path] = {}
    for root in census_raw_roots():
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in RAW_EXTENSIONS:
                continue
            match = pattern.search(path.name)
            if not match or match.group(1) == "00":
                continue
            found[path.name.upper()] = path
    return sorted(found.values(), key=lambda p: p.name)


def find_raw_file(pattern: str) -> Path | None:
    needle = pattern.lower()
    for root in census_raw_roots():
        for path in root.rglob("*"):
            if path.is_file() and path.suffix.lower() in RAW_EXTENSIONS and needle in path.name.lower():
                return path
    return None


def canonical_state_key(state_key: object) -> str:
    key = normalize_key(state_key)
    return STATE_ALIASES.get(key, key)


def canonical_constituency_keys(state_key: object, constituency_key: object) -> tuple[str, str]:
    state = canonical_state_key(state_key)
    constituency = normalize_key(constituency_key)
    alias = CONSTITUENCY_ALIASES.get((state, constituency))
    if alias:
        return alias[0], alias[1]
    return state, constituency


def canonical_seat_key(state_key: object, constituency_key: object) -> str:
    state, constituency = canonical_constituency_keys(state_key, constituency_key)
    return lookup_key(state, constituency)


def assign_post_2011_state(state_2011: str, district: str) -> str:
    state = normalize_key(state_2011)
    district = normalize_key(district)
    if state == "ANDHRA PRADESH" and district in TELANGANA_DISTRICTS:
        return "TELANGANA"
    if state == "JAMMU & KASHMIR" and district in LADAKH_DISTRICTS:
        return "LADAKH"
    return state


def weighted_average(values: pd.Series, weights: pd.Series) -> float | None:
    values = pd.to_numeric(values, errors="coerce")
    weights = pd.to_numeric(weights, errors="coerce")
    mask = values.notna() & weights.notna() & (weights > 0)
    if not mask.any():
        return None
    total_weight = weights[mask].sum()
    if total_weight <= 0:
        return None
    return float((values[mask] * weights[mask]).sum() / total_weight)


def field_already_present(master_row: pd.Series, variable: str) -> bool:
    return generated_value_for_variable(master_row, variable) is not None


def names_similar(left: str, right: str) -> bool:
    if left == right:
        return True
    if not left or not right:
        return False
    if left in right or right in left:
        return min(len(left), len(right)) >= 5
    prefix = min(len(left), len(right), 6)
    return left[:prefix] == right[:prefix] and prefix >= 5


def compact_key_part(value: object) -> str:
    text = normalize_key(value)
    for token in ("AND", "THE", "LOK SABHA"):
        text = text.replace(token, " ")
    return re.sub(r"\s+", " ", text).strip()


def load_geojson_seats() -> dict[str, dict[str, str]]:
    import json

    if not GEOJSON_PATH.exists():
        return {}
    payload = json.loads(GEOJSON_PATH.read_text(encoding="utf-8"))
    seats: dict[str, dict[str, str]] = {}
    for feature in payload.get("features", []):
        props = feature.get("properties", {})
        state = str(props.get("st_name", "")).strip()
        constituency = str(props.get("pc_name", "")).strip()
        if not state or not constituency:
            continue
        state_key = canonical_state_key(state)
        constituency_key = normalize_key(constituency)
        key = lookup_key(state_key, constituency_key)
        seats[key] = {
            "state": state,
            "constituency": constituency,
            "state_key": state_key,
            "constituency_key": constituency_key,
        }
    return seats


def load_frontend_seats() -> dict[str, dict[str, object]]:
    import json

    if not CONSTITUENCIES_JSON_PATH.exists():
        return {}
    records = json.loads(CONSTITUENCIES_JSON_PATH.read_text(encoding="utf-8"))
    seats: dict[str, dict[str, object]] = {}
    for row in records:
        state_key = str(row.get("state_key", "")).strip()
        constituency_key = str(row.get("constituency_key", "")).strip()
        key = lookup_key(canonical_state_key(state_key), normalize_key(constituency_key))
        seats[key] = row
    return seats


def closest_name_match(
    state_key: str,
    constituency_key: str,
    candidates: dict[str, dict[str, str]],
) -> str:
    state_norm = canonical_state_key(state_key)
    pc_norm = compact_key_part(constituency_key)
    best = ""
    for key, meta in candidates.items():
        if canonical_state_key(meta.get("state_key", "")) != state_norm:
            continue
        candidate_pc = compact_key_part(meta.get("constituency_key", ""))
        if names_similar(pc_norm, candidate_pc):
            return f"{meta.get('state')} / {meta.get('constituency')}"
        if not best:
            best = f"{meta.get('state')} / {meta.get('constituency')}"
    return best


def join_district_area(core: pd.DataFrame, area_table: pd.DataFrame) -> pd.DataFrame:
    if area_table.empty:
        return core
    merged = core.merge(
        area_table[["state_key", "district_key", "area_sq_km"]],
        on=["state_key", "district_key"],
        how="left",
        suffixes=("", "_area"),
    )
    if "area_sq_km_area" in merged.columns:
        merged["area_sq_km"] = merged["area_sq_km"].combine_first(merged["area_sq_km_area"])
        merged = merged.drop(columns=["area_sq_km_area"])
    pop = pd.to_numeric(merged["total_population"], errors="coerce")
    area = pd.to_numeric(merged["area_sq_km"], errors="coerce")
    density = merged.get("population_density")
    if density is None:
        merged["population_density"] = np.where(area > 0, pop / area, np.nan)
    else:
        merged["population_density"] = pd.to_numeric(density, errors="coerce")
        merged.loc[merged["population_density"].isna() & area.gt(0), "population_density"] = (
            pop / area
        ).loc[merged["population_density"].isna() & area.gt(0)]
    return merged
