"""
Compare each party's national vote share against its seat share.

Run as:
    python -m src.analysis.vote_seat_distortion

Output:
    data/processed/<VOTE_SEAT_DISTORTION_FILE>  (year-stamped via src.data_io)
        columns: party, vote_share_pct, seat_share_pct, seats, representation_gap

The `representation_gap` column (seat_share - vote_share) is the headline
metric: positive => party benefits from FPTP, negative => party is punished.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.data_io import (
    VOTE_SEAT_DISTORTION_FILE,
    load_candidate_results,
    load_winners,
    save_csv,
)
from src.utils.election_metrics import calculate_vote_seat_distortion


def main() -> None:
    results = load_candidate_results()
    winners = load_winners()

    combined = calculate_vote_seat_distortion(results, winners)
    save_csv(combined, VOTE_SEAT_DISTORTION_FILE)

    display_cols = ["party", "vote_share_pct", "seat_share_pct",
                    "representation_gap", "seats"]

    print("\nVote share vs seat share (top 15 by vote share):")
    print(combined[display_cols].head(15).round(2).to_string(index=False))

    print("\nMost over-represented (gap > 0):")
    print(
        combined.sort_values("representation_gap", ascending=False)
                [display_cols]
                .head(10).round(2)
                .to_string(index=False)
    )

    print("\nMost under-represented (gap < 0):")
    print(
        combined.sort_values("representation_gap")
                [display_cols]
                .head(10).round(2)
                .to_string(index=False)
    )


if __name__ == "__main__":
    main()
