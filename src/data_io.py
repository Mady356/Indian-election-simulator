"""
Reusable load/save helpers wired to the paths in `src.config`.

Every other module should go through this file when reading or writing data so
that filenames (and the choice of processed/ vs outputs/ vs database/) live in
one place. All canonical filenames are derived from `ACTIVE_YEAR` and
`ELECTION_TYPE` — change the year in config.py and these constants follow.
"""

from pathlib import Path

import pandas as pd

from src.config import (
    ACTIVE_YEAR,
    DATABASE_DIR,
    ELECTION_TYPE,
    OUTPUTS_DIR,
    PROCESSED_DIR,
)


# -----------------------------------------------------------------------------
# Canonical filenames for the processed tables
#
# Every output is year-stamped with `ACTIVE_YEAR` so flipping years in
# `src.config` can never overwrite a prior year's tables. There is therefore
# no need to delete old files when re-running for a different year.
# -----------------------------------------------------------------------------

# Cleaned ECI inputs.
CANDIDATE_RESULTS_FILE = f"eci_{ACTIVE_YEAR}_candidate_results.csv"
PARTIES_FILE = f"eci_{ACTIVE_YEAR}_parties.csv"
CONSTITUENCY_SUMMARY_FILE = f"eci_{ACTIVE_YEAR}_constituency_summary.csv"

# Party-side derived tables.
PARTY_COUNTS_FILE = f"party_counts_audit_{ACTIVE_YEAR}.csv"
PARTY_METADATA_FILE = f"party_metadata_{ACTIVE_YEAR}.csv"

# Constituency-side derived tables.
WINNERS_FILE = f"{ELECTION_TYPE}_{ACTIVE_YEAR}_winners.csv"
CONSTITUENCY_FEATURES_FILE = f"constituency_features_{ACTIVE_YEAR}.csv"
CONSTITUENCY_TOP2_FILE = f"constituency_top2_{ACTIVE_YEAR}.csv"

# Analysis outputs (single-year reports).
VOTE_SEAT_DISTORTION_FILE = f"vote_vs_seat_share_{ACTIVE_YEAR}.csv"
CONSTITUENCY_NEIGHBORS_FILE = f"constituency_nearest_neighbors_{ACTIVE_YEAR}.csv"
SEAT_FLIP_REPORT_FILE = f"seat_flip_report_{ACTIVE_YEAR}.csv"
STATE_SWING_SENSITIVITY_FILE = f"state_swing_sensitivity_{ACTIVE_YEAR}.csv"

# Simulation outputs.
SIMULATED_WINNERS_FILE = f"simulated_winners_{ACTIVE_YEAR}.csv"
STATE_SIMULATED_WINNERS_FILE = f"state_simulated_winners_{ACTIVE_YEAR}.csv"
ZERO_SUM_RESULTS_FILE = f"zero_sum_simulated_results_{ACTIVE_YEAR}.csv"
ZERO_SUM_WINNERS_FILE = f"zero_sum_simulated_winners_{ACTIVE_YEAR}.csv"


# -----------------------------------------------------------------------------
# Loaders
# -----------------------------------------------------------------------------

def load_candidate_results() -> pd.DataFrame:
    """Long candidate-level table: one row per (state, constituency, candidate)."""
    return pd.read_csv(PROCESSED_DIR / CANDIDATE_RESULTS_FILE)


def load_party_metadata() -> pd.DataFrame:
    """party -> party_type / alliance / ideology / region lookup for ACTIVE_YEAR."""
    return pd.read_csv(PROCESSED_DIR / PARTY_METADATA_FILE)


def load_winners() -> pd.DataFrame:
    """One row per constituency = winning candidate enriched with party metadata."""
    return pd.read_csv(PROCESSED_DIR / WINNERS_FILE)


def load_constituency_features() -> pd.DataFrame:
    """One row per constituency with model-ready numeric features (ENP, margin, etc.)."""
    return pd.read_csv(PROCESSED_DIR / CONSTITUENCY_FEATURES_FILE)


# -----------------------------------------------------------------------------
# Savers
# -----------------------------------------------------------------------------

def _resolve_base(outputs: bool) -> Path:
    return OUTPUTS_DIR if outputs else PROCESSED_DIR


def save_csv(df: pd.DataFrame, filename: str, *, outputs: bool = False) -> Path:
    """
    Save `df` to processed/ (default) or outputs/ when outputs=True.

    Use outputs=True for report-style artefacts (tables you'd paste into a
    write-up) and the default for intermediate data the pipeline depends on.
    """
    path = _resolve_base(outputs) / filename
    df.to_csv(path, index=False)
    print(f"Saved CSV: {path}  ({df.shape[0]} rows x {df.shape[1]} cols)")
    return path


def save_parquet(df: pd.DataFrame, filename: str, *, outputs: bool = False) -> Path:
    """Same as save_csv but writes Parquet (smaller, typed, faster reload)."""
    path = _resolve_base(outputs) / filename
    df.to_parquet(path, index=False)
    print(f"Saved Parquet: {path}  ({df.shape[0]} rows x {df.shape[1]} cols)")
    return path


def save_table(df: pd.DataFrame, name: str) -> tuple[Path, Path]:
    """
    Write a database table to DATABASE_DIR as both CSV and Parquet.

    `name` should be a bare table name (no extension, no year suffix); the
    active election year is appended automatically so 2019 / 2014 tables can
    later coexist with the 2024 ones.
    """
    stem = f"{name}_{ACTIVE_YEAR}"
    csv_path = DATABASE_DIR / f"{stem}.csv"
    parquet_path = DATABASE_DIR / f"{stem}.parquet"

    df.to_csv(csv_path, index=False)
    df.to_parquet(parquet_path, index=False)

    print(f"Saved table '{name}' "
          f"({df.shape[0]} rows x {df.shape[1]} cols) "
          f"-> {csv_path.name}, {parquet_path.name}")
    return csv_path, parquet_path


def load_table(name: str) -> pd.DataFrame:
    """Load a database table written by save_table (Parquet preferred)."""
    return pd.read_parquet(DATABASE_DIR / f"{name}_{ACTIVE_YEAR}.parquet")
