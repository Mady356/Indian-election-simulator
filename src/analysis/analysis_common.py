"""Shared helpers for constituency-level election + demographic analysis."""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data"
OUTPUT_DIR = DATA_DIR / "outputs"
PROCESSED_DIR = DATA_DIR / "processed"
DATABASE_DIR = DATA_DIR / "database"
ELECTIONS_PROCESSED_DIR = DATA_DIR / "elections" / "processed"
DEMOGRAPHICS_DIR = DATA_DIR / "demographics" / "processed"
REFERENCE_DIR = DATA_DIR / "reference"
ANALYSIS_DIR = DATA_DIR / "analysis"

ELECTION_SEARCH_DIRS = [
    OUTPUT_DIR,
    PROCESSED_DIR,
    ELECTIONS_PROCESSED_DIR,
    DATABASE_DIR,
]

NFHS5_LEVEL_COLUMNS = [
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

CHANGE_COLUMNS = [
    "fertility_rate_change",
    "electricity_pct_change",
    "improved_sanitation_pct_change",
    "lpg_pct_change",
    "mobile_phone_pct_change",
    "bank_account_pct_change",
    "women_secondary_edu_pct_change",
    "female_literacy_pct_change",
    "male_literacy_pct_change",
    "wealth_index_mean_change",
    "urban_pct_change",
]

TARGET_COLUMNS = [
    "bjp_swing_2019_2024",
    "inc_swing_2019_2024",
    "turnout_change",
    "margin_change",
]

FEATURE_COLUMNS = NFHS5_LEVEL_COLUMNS + CHANGE_COLUMNS

# Map election constituency keys onto delimitation-style demographic keys.
CONSTITUENCY_KEY_ALIASES = {
    "MAHABUBABAD": "MAHABUBABAD",
    "MAHBUBNAGAR": "MAHBUBNAGAR",
    "SECUNDERABAD": "SECUNDERABAD",
    "RANGA REDDY": "CHEVELLA",  # not used directly; keep for future aliases
}


def normalise_state_key(value: object) -> str:
    if pd.isna(value):
        return ""
    name = str(value).strip().upper()
    name = name.replace(" AND ", " & ")
    name = re.sub(r"\s+", " ", name)
    return name


def normalise_constituency_key(value: object) -> str:
    if pd.isna(value):
        return ""
    name = str(value).strip().upper()
    name = re.sub(r"\s*\((SC|ST|GEN)\)\s*", " ", name)
    name = re.sub(r"[^A-Z0-9]+", " ", name)
    name = re.sub(r"\s+", " ", name).strip()
    return CONSTITUENCY_KEY_ALIASES.get(name, name)


def add_join_keys(df: pd.DataFrame, state_col: str, constituency_col: str) -> pd.DataFrame:
    out = df.copy()
    out["state_key"] = out[state_col].map(normalise_state_key)
    out["constituency_key"] = out[constituency_col].map(normalise_constituency_key)
    return out


def discover_file(
    label: str,
    patterns: list[str],
    search_dirs: list[Path] | None = None,
) -> Path:
    """Pick the first matching file from likely project folders."""
    bases = search_dirs or ELECTION_SEARCH_DIRS
    checked: list[str] = []
    for base in bases:
        if not base.exists():
            continue
        for pattern in patterns:
            matches = sorted(base.glob(pattern))
            checked.append(f"{base}/{pattern}")
            if matches:
                selected = matches[0]
                print(f"Selected {label}: {selected}")
                return selected
    raise FileNotFoundError(
        f"Could not find {label}. Checked patterns: {', '.join(checked)}"
    )


def demographic_lookup_keys(state_key: str, constituency_key: str) -> list[tuple[str, str]]:
    """Return join keys to try when matching election rows to demographics."""
    keys = [(state_key, constituency_key)]
    if state_key == "TELANGANA":
        keys.append(("ANDHRA PRADESH", constituency_key))
    return keys


def lookup_row_by_keys(
    table: pd.DataFrame,
    state_key: str,
    constituency_key: str,
) -> pd.Series | None:
    for sk, ck in demographic_lookup_keys(state_key, constituency_key):
        match = table[(table["state_key"] == sk) & (table["constituency_key"] == ck)]
        if not match.empty:
            return match.iloc[0]
    return None
