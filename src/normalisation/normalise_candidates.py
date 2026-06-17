"""
Normalise raw candidate names and stamp every row with a stable `candidate_election_id`.

Run as:
    python -m src.normalisation.normalise_candidates

Inputs (data/database/, written by `normalise_parties`):
    results_table_<ACTIVE_YEAR>.parquet      (must already contain `party_id`)

Outputs:
    results_table_<ACTIVE_YEAR>.{csv,parquet}    augmented with candidate id columns
    candidate_master.csv                          dedup'd candidate roster across years

`candidate_election_id` is shaped:
    CAND_<year>_<STATE>_<CONSTITUENCY>_<PARTY_ID>_<CANDIDATE_NAME>
so it is unique per (year, seat, candidate) and stable across pipeline reruns.
"""

import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.config import ACTIVE_YEAR, DATABASE_DIR


RESULTS_STEM = f"results_table_{ACTIVE_YEAR}"
RESULTS_PARQUET = DATABASE_DIR / f"{RESULTS_STEM}.parquet"
RESULTS_CSV = DATABASE_DIR / f"{RESULTS_STEM}.csv"
CANDIDATE_MASTER_PATH = DATABASE_DIR / "candidate_master.csv"


def clean_text(value: object) -> str:
    if pd.isna(value):
        return ""
    value = str(value).strip().upper()
    value = re.sub(r"\s+", " ", value)
    value = value.replace("\u2019", "'").replace("\u2013", "-")
    value = re.sub(r"[^A-Z0-9 .'\-]", "", value)
    return value


def slugify(value: object) -> str:
    value = clean_text(value)
    value = re.sub(r"[^A-Z0-9]+", "_", value)
    return value.strip("_")


def build_candidate_election_id(row: pd.Series) -> str:
    # Pull the year from the row when available (multi-year merges), otherwise
    # fall back to the active year — never to a literal "2024".
    year = str(row.get("election_year", ACTIVE_YEAR))
    state = slugify(row["state"])
    constituency = slugify(row["constituency"])
    party_id = slugify(row.get("party_id", row["party"]))
    candidate = slugify(row["candidate"])
    return f"CAND_{year}_{state}_{constituency}_{party_id}_{candidate}"


def main() -> None:
    if not RESULTS_PARQUET.exists():
        raise FileNotFoundError(
            f"{RESULTS_PARQUET} not found. Run `python -m src.database.database_layer` "
            f"then `python -m src.normalisation.normalise_parties` first."
        )

    print(f"Reading {RESULTS_PARQUET.name}")
    results = pd.read_parquet(RESULTS_PARQUET)

    if "party_id" not in results.columns:
        raise ValueError(
            "`party_id` not found in results table. "
            "Run `python -m src.normalisation.normalise_parties` first."
        )

    results["candidate_raw"] = results["candidate"]
    results["candidate_clean"] = results["candidate"].apply(clean_text)
    results["candidate_election_id"] = results.apply(build_candidate_election_id, axis=1)

    candidate_master = (
        results[[
            "candidate_election_id",
            "candidate_clean",
            "candidate_raw",
            "party_id",
            "state",
            "constituency",
            "election_year",
        ]]
        .drop_duplicates()
        .sort_values(["election_year", "state", "constituency", "party_id"])
    )

    results.to_parquet(RESULTS_PARQUET, index=False)
    results.to_csv(RESULTS_CSV, index=False)

    # candidate_master.csv is the canonical cross-year roster; we append (and
    # then de-duplicate) so multiple year-runs accumulate into one file.
    if CANDIDATE_MASTER_PATH.exists():
        prior = pd.read_csv(CANDIDATE_MASTER_PATH)
        candidate_master = (
            pd.concat([prior, candidate_master], ignore_index=True)
              .drop_duplicates()
              .sort_values(["election_year", "state", "constituency", "party_id"])
        )

    candidate_master.to_csv(CANDIDATE_MASTER_PATH, index=False)

    print(f"Candidate normalisation complete for {ACTIVE_YEAR}.")
    print(f"  Augmented: {RESULTS_PARQUET.name}, {RESULTS_CSV.name}")
    print(f"  Saved:     {CANDIDATE_MASTER_PATH.name} "
          f"({len(candidate_master)} rows across all loaded years)")
    print()
    print(candidate_master.head(20).to_string(index=False))


if __name__ == "__main__":
    main()
