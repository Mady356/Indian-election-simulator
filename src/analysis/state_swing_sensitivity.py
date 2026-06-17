"""
Per-state summary of how sensitive seats are to a swing.

Run as:
    python -m src.analysis.state_swing_sensitivity

Inputs:
    data/processed/<CANDIDATE_RESULTS_FILE>     (from src.data_io)
    data/processed/<ZERO_SUM_RESULTS_FILE>      (produced by
        `src.simulation.zero_sum_state_swing_simulator`)

Output:
    data/processed/<STATE_SWING_SENSITIVITY_FILE>  (year-stamped via src.data_io)
        columns: state, total_seats, flipped_seats, close_seats,
                 avg_margin_votes, median_margin_votes, flip_rate_pct

A "close" seat is one where the winning margin (votes) is below
CLOSE_MARGIN_THRESHOLD percent of the winner's vote count.
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.config import CLOSE_MARGIN_THRESHOLD, PROCESSED_DIR
from src.data_io import (
    STATE_SWING_SENSITIVITY_FILE,
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

    actual_winners = actual[actual["winner"] == True].copy()
    sim_winners = simulated[simulated["sim_rank"] == 1].copy()

    merged = actual_winners.merge(
        sim_winners[["state", "constituency", "party"]],
        on=["state", "constituency"],
        suffixes=("_actual", "_sim"),
    )
    merged["flipped"] = merged["party_actual"] != merged["party_sim"]

    # `close_seat` is defined on the actual result, not the simulated one.
    merged["close_seat"] = (
        merged["margin_votes"] / merged["votes"] * 100
    ) < CLOSE_MARGIN_THRESHOLD

    state_summary = (
        merged.groupby("state")
              .agg(
                  total_seats=("constituency", "count"),
                  flipped_seats=("flipped", "sum"),
                  close_seats=("close_seat", "sum"),
                  avg_margin_votes=("margin_votes", "mean"),
                  median_margin_votes=("margin_votes", "median"),
              )
              .reset_index()
    )
    state_summary["flip_rate_pct"] = (
        state_summary["flipped_seats"] / state_summary["total_seats"] * 100
    )
    state_summary = state_summary.sort_values("flip_rate_pct", ascending=False)

    save_csv(state_summary, STATE_SWING_SENSITIVITY_FILE)

    print("\nMost swing-sensitive states:")
    print(state_summary.head(15).to_string(index=False))

    print("\nMost stable states:")
    print(state_summary.tail(15).to_string(index=False))


if __name__ == "__main__":
    main()
