"""
Compare actual winners vs simulated winners and list every seat that flipped.

Run as:
    python -m src.analysis.seat_flip_report

Input:
    data/processed/<CANDIDATE_RESULTS_FILE>     (from src.data_io)
    data/processed/<ZERO_SUM_RESULTS_FILE>

Output:
    data/processed/<SEAT_FLIP_REPORT_FILE>  (year-stamped via src.data_io)
        columns: state, constituency,
                 actual_winner, actual_party, actual_vote_share, actual_margin_votes,
                 sim_winner, sim_party, sim_vote_share, flipped
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.config import PROCESSED_DIR
from src.data_io import (
    SEAT_FLIP_REPORT_FILE,
    ZERO_SUM_RESULTS_FILE,
    load_candidate_results,
    save_csv,
)


def main() -> None:
    actual = load_candidate_results()

    sim_path = PROCESSED_DIR / ZERO_SUM_RESULTS_FILE
    if not sim_path.exists():
        raise FileNotFoundError(
            f"{sim_path} not found. Run "
            "`python -m src.simulation.zero_sum_state_swing_simulator` first."
        )
    simulated = pd.read_csv(sim_path)

    actual_winners = (
        actual[actual["winner"] == True]
        [["state", "constituency", "candidate", "party", "vote_share", "margin_votes"]]
        .rename(columns={
            "candidate": "actual_winner",
            "party": "actual_party",
            "vote_share": "actual_vote_share",
            "margin_votes": "actual_margin_votes",
        })
    )

    sim_winners = (
        simulated[simulated["sim_rank"] == 1]
        [["state", "constituency", "candidate", "party", "sim_vote_share"]]
        .rename(columns={
            "candidate": "sim_winner",
            "party": "sim_party",
        })
    )

    flips = actual_winners.merge(sim_winners, on=["state", "constituency"], how="inner")
    flips["flipped"] = flips["actual_party"] != flips["sim_party"]
    flips = flips.sort_values(
        ["flipped", "actual_margin_votes"],
        ascending=[False, True],
    )

    save_csv(flips, SEAT_FLIP_REPORT_FILE)

    print(f"\nTotal seats compared: {len(flips)}")
    print(f"Flipped seats       : {int(flips['flipped'].sum())}")

    print("\nFlips by (actual_party -> sim_party):")
    print(
        flips[flips["flipped"]]
        .groupby(["actual_party", "sim_party"]).size()
        .sort_values(ascending=False)
        .to_string()
    )

    print("\nClosest flipped seats:")
    cols = ["state", "constituency", "actual_winner", "actual_party",
            "sim_winner", "sim_party",
            "actual_margin_votes", "actual_vote_share", "sim_vote_share"]
    print(flips[flips["flipped"]][cols].head(15).to_string(index=False))


if __name__ == "__main__":
    main()
