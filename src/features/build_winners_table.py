"""
Build the one-row-per-constituency winners table, enriched with party metadata.

Run as:
    python -m src.features.build_winners_table

Inputs:
    data/processed/<CANDIDATE_RESULTS_FILE>     (from src.data_io)
    data/processed/<PARTY_METADATA_FILE>

Outputs:
    data/processed/<WINNERS_FILE>

This is the foundational lookup the analysis/simulation layers read from.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.config import ALLIANCE_COL
from src.data_io import (
    WINNERS_FILE,
    load_candidate_results,
    load_party_metadata,
    save_csv,
)
from src.utils.validation import (
    check_expected_winners,
    check_no_duplicate_winners,
    check_required_columns,
)


def build_winners() -> None:
    results = load_candidate_results()
    party_meta = load_party_metadata()

    check_required_columns(
        results,
        ["state", "constituency", "party", "candidate", "winner", "margin_votes", "vote_share"],
    )

    winners = results[results["winner"] == True].copy()

    # Attach party metadata (alliance, ideology, …) so downstream code doesn't
    # need to re-join every single time.
    winners = winners.merge(
        party_meta[["party", "party_type", ALLIANCE_COL, "ideology", "region"]],
        on="party",
        how="left",
    )

    check_expected_winners(winners)
    check_no_duplicate_winners(winners)

    save_csv(winners, WINNERS_FILE)

    print("\nSeat count by alliance:")
    print(winners[ALLIANCE_COL].value_counts().to_string())

    print("\nTop parties by seats:")
    print(winners["party"].value_counts().head(15).to_string())

    print("\nClosest races (smallest margin_votes):")
    cols = ["state", "constituency", "candidate", "party", "margin_votes", "vote_share"]
    print(winners.sort_values("margin_votes")[cols].head(15).to_string(index=False))


if __name__ == "__main__":
    build_winners()
