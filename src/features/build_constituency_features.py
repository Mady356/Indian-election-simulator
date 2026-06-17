"""
Build the per-constituency feature table used by analysis & ML.

Run as:
    python -m src.features.build_constituency_features

Inputs:
    data/processed/<CANDIDATE_RESULTS_FILE>     (from src.data_io)
    data/processed/<WINNERS_FILE>

Output:
    data/processed/<CONSTITUENCY_FEATURES_FILE>

Columns produced:
    state, constituency, winning_party, <ALLIANCE_COL>, winner_vote_share,
    margin_votes, party_type, ideology, effective_num_parties, top2_margin_pct
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.config import ALLIANCE_COL
from src.data_io import (
    CONSTITUENCY_FEATURES_FILE,
    load_candidate_results,
    load_winners,
    save_csv,
)
from src.utils.election_metrics import (
    calculate_top2_margin,
    effective_number_of_parties,
)
from src.utils.validation import check_required_columns


def build_features() -> None:
    results = load_candidate_results()
    winners = load_winners()

    check_required_columns(results, ["state", "constituency", "vote_share", "rank"])
    check_required_columns(
        winners,
        ["state", "constituency", "party", ALLIANCE_COL,
         "vote_share", "margin_votes", "party_type", "ideology"],
    )

    # 1. Effective Number of Parties per constituency.
    enp = (
        results.groupby(["state", "constituency"])["vote_share"]
               .apply(effective_number_of_parties)
               .reset_index(name="effective_num_parties")
    )

    # 2. Top-2 vote-share margin (winner % minus runner-up %).
    margins = calculate_top2_margin(results)

    # 3. Pull the winner-side fields we care about.
    features = winners[[
        "state", "constituency",
        "party", ALLIANCE_COL,
        "vote_share", "margin_votes",
        "party_type", "ideology",
    ]].copy()

    # 4. Join everything on (state, constituency).
    features = (
        features.merge(enp, on=["state", "constituency"], how="left")
                .merge(margins, on=["state", "constituency"], how="left")
                .rename(columns={
                    "party": "winning_party",
                    "vote_share": "winner_vote_share",
                })
    )

    save_csv(features, CONSTITUENCY_FEATURES_FILE)

    print("\nFeature preview:")
    print(features.head(10).to_string(index=False))


if __name__ == "__main__":
    build_features()
