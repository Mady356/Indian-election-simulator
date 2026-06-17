"""
Build the normalised "database" snapshot of the active election.

Run as:
    python -m src.database.database_layer

Reads the cleaned/processed CSVs through `src.data_io` and writes a set of
narrow analytical tables to `data/database/`, year-stamped with
`ACTIVE_YEAR` so multiple election snapshots can coexist.

Tables produced (suffixed with `_<ACTIVE_YEAR>`):
    results_table     : long candidate-level results, with constituency_id,
                        election_year, election_type
    candidate_table   : (candidate_id, candidate, party, state, constituency)
    party_table       : (party, candidate_count, party_type, alliance, ideology, region)
    alliance_table    : (election_year, party, alliance)
    constituency_table: (constituency_id, state, constituency, winner_*, features...)

`constituency_id` is a year-stable slug like ``UTTAR_PRADESH__VARANASI`` so
cross-year joins (e.g. `compare_2019_2024`) merge cleanly regardless of
whitespace/casing drift between ECI files.
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.config import ACTIVE_YEAR, ALLIANCE_COL, ELECTION_TYPE
from src.data_io import (
    load_candidate_results,
    load_constituency_features,
    load_party_metadata,
    load_winners,
    save_table,
)


# -----------------------------------------------------------------------------
# Shared key helpers
# -----------------------------------------------------------------------------

def make_constituency_id(state: pd.Series, constituency: pd.Series) -> pd.Series:
    """
    Build a year-stable slug for (state, constituency).

    Example: ("Uttar Pradesh", "Varanasi") -> "UTTAR_PRADESH__VARANASI".

    The double-underscore separator makes the boundary unambiguous even when
    a state name contains spaces. Used by every table that needs to join on a
    constituency across years.
    """
    return (
        state.astype(str).str.strip().str.upper().str.replace(" ", "_", regex=False)
        + "__"
        + constituency.astype(str).str.strip().str.upper().str.replace(" ", "_", regex=False)
    )


# -----------------------------------------------------------------------------
# Loading
# -----------------------------------------------------------------------------

def load_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Return (results, party_meta, winners, features) — the four inputs we need."""
    results = load_candidate_results()
    party_meta = load_party_metadata()
    winners = load_winners()
    features = load_constituency_features()
    return results, party_meta, winners, features


# -----------------------------------------------------------------------------
# Table builders
# -----------------------------------------------------------------------------

def build_results_table(results: pd.DataFrame) -> pd.DataFrame:
    """Long candidate-level fact table, tagged with election_year, election_type,
    and a year-stable `constituency_id` so cross-year joins work cleanly."""
    out = results.copy()
    out["election_year"] = ACTIVE_YEAR
    out["election_type"] = ELECTION_TYPE
    out["constituency_id"] = make_constituency_id(out["state"], out["constituency"])

    keep_cols = [
        "election_year", "election_type",
        "constituency_id", "state", "constituency",
        "candidate", "party",
        "votes", "vote_share", "rank", "winner", "margin_votes",
    ]
    return out[[c for c in keep_cols if c in out.columns]]


def build_party_table(party_meta: pd.DataFrame) -> pd.DataFrame:
    """One row per party with its metadata for the active election."""
    keep_cols = [
        "party", "candidate_count",
        "party_type", ALLIANCE_COL,
        "ideology", "region",
    ]
    keep_cols = [c for c in keep_cols if c in party_meta.columns]
    return party_meta[keep_cols].drop_duplicates()


def build_constituency_table(features: pd.DataFrame) -> pd.DataFrame:
    """One row per constituency with stable id + winner facts + numeric features."""
    out = features.copy()
    out["constituency_id"] = make_constituency_id(out["state"], out["constituency"])

    keep_cols = [
        "constituency_id", "state", "constituency",
        "winning_party", ALLIANCE_COL,
        "winner_vote_share", "top2_margin_pct",
        "effective_num_parties", "margin_votes",
        "party_type", "ideology",
    ]
    return out[[c for c in keep_cols if c in out.columns]].drop_duplicates()


def build_alliance_table(party_meta: pd.DataFrame) -> pd.DataFrame:
    """(election_year, party, alliance) — the long-format mapping you'll want
    once 2019/2014 are loaded next to 2024."""
    out = party_meta.copy()
    out["election_year"] = ACTIVE_YEAR

    keep_cols = ["election_year", "party", ALLIANCE_COL]
    return out[[c for c in keep_cols if c in out.columns]].drop_duplicates()


def build_candidate_table(results: pd.DataFrame) -> pd.DataFrame:
    """Lightweight candidate lookup keyed by a stable id."""
    out = results.copy()
    out["candidate_id"] = (
        out["candidate"].astype(str).str.upper().str.replace(" ", "_")
        + "__"
        + out["party"].astype(str).str.upper().str.replace(" ", "_")
    )
    keep_cols = ["candidate_id", "candidate", "party", "state", "constituency"]
    return out[[c for c in keep_cols if c in out.columns]].drop_duplicates()


# -----------------------------------------------------------------------------
# Entry point
# -----------------------------------------------------------------------------

def main() -> None:
    results, party_meta, winners, features = load_data()

    save_table(build_results_table(results), "results_table")
    save_table(build_candidate_table(results), "candidate_table")
    save_table(build_party_table(party_meta), "party_table")
    save_table(build_alliance_table(party_meta), "alliance_table")
    save_table(build_constituency_table(features), "constituency_table")

    print(f"\nDatabase layer built successfully for "
          f"{ELECTION_TYPE} {ACTIVE_YEAR}.")


if __name__ == "__main__":
    main()
