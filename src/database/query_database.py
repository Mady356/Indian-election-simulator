"""
Convenience queries against the database snapshot built by `database_layer`.

Run as:
    python -m src.database.query_database

All table reads go through `src.data_io.load_table`, which resolves the
year-stamped filename from `ELECTION_YEAR` in config — so this module never
needs to know the on-disk filename.
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.config import ALLIANCE_COL, CLOSE_MARGIN_THRESHOLD
from src.data_io import load_table


def closest_wins(party: str | None = None, n: int = 20) -> pd.DataFrame:
    """The closest contests, optionally filtered to one winning party."""
    constituencies = load_table("constituency_table")
    if party is not None:
        constituencies = constituencies[constituencies["winning_party"] == party]
    return constituencies.sort_values("top2_margin_pct").head(n)


def most_fragmented(n: int = 20) -> pd.DataFrame:
    """Constituencies with the highest effective number of parties."""
    constituencies = load_table("constituency_table")
    return constituencies.sort_values("effective_num_parties", ascending=False).head(n)


def seats_by_state_and_party() -> pd.DataFrame:
    """Long table: state x party -> seat count, sorted within each state."""
    results = load_table("results_table")
    winners = results[results["winner"] == True]
    return (
        winners.groupby(["state", "party"])
               .size()
               .reset_index(name="seats")
               .sort_values(["state", "seats"], ascending=[True, False])
    )


def vulnerable_seats(party: str, margin_threshold: float = CLOSE_MARGIN_THRESHOLD) -> pd.DataFrame:
    """Seats held by `party` whose top-2 vote-share margin is below the threshold."""
    constituencies = load_table("constituency_table")
    return (
        constituencies[
            (constituencies["winning_party"] == party)
            & (constituencies["top2_margin_pct"] <= margin_threshold)
        ]
        .sort_values("top2_margin_pct")
    )


def alliance_seat_counts() -> pd.DataFrame:
    """Seat counts grouped by alliance (using the year-stamped alliance column)."""
    constituencies = load_table("constituency_table")
    return (
        constituencies.groupby(ALLIANCE_COL)
                      .size()
                      .reset_index(name="seats")
                      .sort_values("seats", ascending=False)
    )


def main() -> None:
    print("\nClosest BJP wins:")
    print(closest_wins("BJP", 20).to_string(index=False))

    print("\nMost fragmented constituencies:")
    print(most_fragmented(20).to_string(index=False))

    print(f"\nVulnerable INC seats (margin < {CLOSE_MARGIN_THRESHOLD}%):")
    print(vulnerable_seats("INC").to_string(index=False))

    print("\nSeat counts by alliance:")
    print(alliance_seat_counts().to_string(index=False))


if __name__ == "__main__":
    main()
