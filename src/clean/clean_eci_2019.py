"""
Read raw ECI Excel files for the active election and emit tidy CSVs to data/processed/.

Run as:
    python -m src.clean.clean_eci_2019

This loader targets the ECI 2024 file *format*. The output filenames are
derived from `ELECTION_YEAR` / `ELECTION_TYPE` in `src.config` so the same
loader works for any election year published in the same format. When a year
ships in a substantially different layout, add a sibling loader rather than
overloading this one.

Why a dedicated cleaner:
    The ECI .xls files have banner rows, merged-cell sub-headers, and (worst)
    a malformed OLE compound-document layout that breaks the default `xlrd`
    engine in pandas. This script reads with `calamine`, auto-detects the
    real header row, normalises column names, and derives rank / vote-share /
    margin per constituency.
"""

import re
import sys
from pathlib import Path

import pandas as pd

# Make the script runnable both as a module (`python -m src.clean.clean_eci_2019`)
# and as a plain script (`python src/clean/clean_eci_2024.py`).
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.config import ELECTION_YEAR, RAW_YEAR_DIR
from src.data_io import (
    CANDIDATE_RESULTS_FILE,
    CONSTITUENCY_SUMMARY_FILE,
    PARTIES_FILE,
    save_csv,
)


# --- Column-name normalisation ---

def clean_col(col: object) -> str:
    """Make a column name snake_case-and-safe: lower, underscores, alnum only."""
    name = str(col).strip()
    name = re.sub(r"\s+", "_", name)
    name = name.lower()
    name = re.sub(r"[^a-z0-9_]", "", name)
    return name


# --- Header-row detection ---

HEADER_KEYWORDS = {
    "state", "party", "name", "candidate", "constituency",
    "sr", "type", "abbreviation", "symbol", "pc",
    "votes", "category", "gender",
}


def detect_header_row(raw: pd.DataFrame, max_scan: int = 15) -> int:
    """
    Find the first row in the raw sheet that looks like a real header.

    Heuristic (in order):
      1. >= 60% of cells are non-null (rules out top banner rows).
      2. Every non-null cell is a string (rules out data rows).
      3. At least one cell contains a known header keyword.

    Falls back to 0 if nothing in the first `max_scan` rows matches.
    """
    n_cols = raw.shape[1]
    for i in range(min(max_scan, len(raw))):
        row = raw.iloc[i]
        non_null = row.dropna()
        if len(non_null) < 0.6 * n_cols:
            continue
        if not all(isinstance(v, str) for v in non_null):
            continue
        joined = " ".join(non_null.astype(str)).lower()
        if any(k in joined for k in HEADER_KEYWORDS):
            return i
    return 0


# --- Sheet loader ---

def load_excel_file(path: Path) -> pd.DataFrame:
    print(f"\nLoading: {path.name}")

    # ECI .xls files are malformed for xlrd; calamine reads .xls and .xlsx alike.
    engine = "calamine"

    xls = pd.ExcelFile(path, engine=engine)
    print(f"  Sheets: {xls.sheet_names[:5]}{' ...' if len(xls.sheet_names) > 5 else ''}")

    raw = pd.read_excel(path, sheet_name=0, header=None, engine=engine)
    header_row = detect_header_row(raw)
    print(f"  Detected header at row {header_row}")

    df = pd.read_excel(path, sheet_name=0, header=header_row, engine=engine)
    df = df.dropna(how="all").dropna(axis=1, how="all")
    df.columns = [clean_col(c) for c in df.columns]
    return df


# --- Row cleaning ---

def remove_junk_rows(df: pd.DataFrame) -> pd.DataFrame:
    """Drop rows that are entirely empty. (We deliberately keep 'total' rows
    for now because they're useful for cross-checks and easy to filter later.)"""
    return df.dropna(how="all").reset_index(drop=True)


# --- Per-file standardisers ---

# Map of any header variant we've seen to the canonical name we use everywhere.
RESULTS_RENAME_MAP = {
    "state": "state",
    "state_name": "state",
    "pc_name": "constituency",
    "constituency": "constituency",
    "constituency_name": "constituency",
    "candidate": "candidate",
    "candidate_name": "candidate",
    "party": "party",
    "party_name": "party",
    "evm_votes": "evm_votes",
    "postal_votes": "postal_votes",
    "total_votes": "votes",
    "total": "votes",
    "votes": "votes",
}


def standardize_results(df: pd.DataFrame) -> pd.DataFrame:
    """Take the raw candidate-level sheet and turn it into the canonical
    long table with rank / vote_share / margin_votes per constituency."""
    df = remove_junk_rows(df)

    df = df.rename(columns={c: RESULTS_RENAME_MAP[c]
                            for c in df.columns if c in RESULTS_RENAME_MAP})

    df["year"] = ELECTION_YEAR

    # Normalise whitespace on text columns so "BJP " and "BJP" don't split.
    for col in ("state", "constituency", "candidate", "party"):
        if col in df.columns:
            df[col] = (
                df[col].astype(str)
                       .str.strip()
                       .str.replace(r"\s+", " ", regex=True)
            )

    # Coerce vote-count columns to numeric (strip commas, NaN-out "nan" strings).
    for col in ("votes", "evm_votes", "postal_votes"):
        if col in df.columns:
            df[col] = (
                df[col].astype(str)
                       .str.replace(",", "", regex=False)
                       .replace("nan", pd.NA)
            )
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Per-constituency rank, vote share and winner-vs-runnerup margin.
    if {"state", "constituency", "votes"}.issubset(df.columns):
        gb = df.groupby(["state", "constituency"])

        df["rank"] = gb["votes"].rank(method="first", ascending=False).astype("Int64")
        df["winner"] = df["rank"] == 1

        total_votes = gb["votes"].transform("sum")
        df["vote_share"] = df["votes"] / total_votes * 100

        df = df.sort_values(["state", "constituency", "rank"])
        df["next_votes"] = df.groupby(["state", "constituency"])["votes"].shift(-1)
        df["margin_votes"] = df["votes"] - df["next_votes"]
        # Only the winner has a meaningful margin against runner-up.
        df.loc[df["winner"] != True, "margin_votes"] = pd.NA

    return df


def standardize_party_file(df: pd.DataFrame) -> pd.DataFrame:
    df = remove_junk_rows(df)
    df["year"] = ELECTION_YEAR
    for col in df.columns:
        if df[col].dtype == "object":
            df[col] = (
                df[col].astype(str)
                       .str.strip()
                       .str.replace(r"\s+", " ", regex=True)
            )
    return df


def standardize_summary_file(df: pd.DataFrame) -> pd.DataFrame:
    """The Constituency Data Summary file is a per-constituency *report card*
    spanning 543 sheets — not a single tidy table. For now we just clean
    sheet 0 enough to dump it; a proper loader can come later."""
    df = remove_junk_rows(df)
    df["year"] = ELECTION_YEAR
    for col in df.columns:
        if df[col].dtype == "object":
            df[col] = (
                df[col].astype(str)
                       .str.strip()
                       .str.replace(r"\s+", " ", regex=True)
            )
    return df


# --- Entry point ---

def main() -> None:
    if not RAW_YEAR_DIR.exists():
        raise FileNotFoundError(
            f"Raw data dir for {ELECTION_YEAR} not found: {RAW_YEAR_DIR}. "
            f"Drop the ECI .xls / .xlsx files there and re-run."
        )

    files = sorted(list(RAW_YEAR_DIR.glob("*.xls")) + list(RAW_YEAR_DIR.glob("*.xlsx")))

    print(f"Loading raw {ELECTION_YEAR} files from {RAW_YEAR_DIR}:")
    for f in files:
        print(" -", f.name)

    for file in files:
        df = load_excel_file(file)
        name = file.stem.lower()

        # Route each raw file to the right cleaner and the right output name.
        if "detailed" in name or "result" in name:
            cleaned = standardize_results(df)
            out_name = CANDIDATE_RESULTS_FILE
        elif "party" in name or "parties" in name:
            cleaned = standardize_party_file(df)
            out_name = PARTIES_FILE
        elif "summary" in name or "constituency" in name:
            cleaned = standardize_summary_file(df)
            out_name = CONSTITUENCY_SUMMARY_FILE
        else:
            cleaned = remove_junk_rows(df)
            out_name = f"cleaned_{file.stem}.csv"

        save_csv(cleaned, out_name)


if __name__ == "__main__":
    main()
