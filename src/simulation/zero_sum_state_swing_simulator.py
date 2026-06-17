"""
Per-(state, party) swing simulator that renormalises each constituency to 100%.

Run as:
    python -m src.simulation.zero_sum_state_swing_simulator

Why "zero sum":
    state_swing_simulator just adds the swing to each party's share. If BJP
    gains 2 points, the total share in that seat becomes 102 — i.e. votes are
    invented from nowhere. This script instead clips to >= 0 and rescales the
    per-constituency total back to 100, so any party gaining share necessarily
    takes it from someone else.

Outputs (year-stamped via src.data_io):
    data/processed/<ZERO_SUM_RESULTS_FILE>   full candidate rows w/ sim_*
    data/processed/<ZERO_SUM_WINNERS_FILE>   just the simulated winners
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.data_io import (
    ZERO_SUM_RESULTS_FILE,
    ZERO_SUM_WINNERS_FILE,
    load_candidate_results,
    save_csv,
)


STATE_SWINGS = {
    ("Uttar Pradesh", "BJP"): -2.0,
    ("Uttar Pradesh", "SP"):  +2.0,

    ("Maharashtra", "BJP"):    -1.5,
    ("Maharashtra", "INC"):    +1.0,
    ("Maharashtra", "SHSUBT"): +0.5,
}


def apply_zero_sum_swing(group: pd.DataFrame) -> pd.DataFrame:
    """Apply per-(state, party) swing within one constituency and renormalise."""
    # pandas >= 3.0 drops the groupby keys from `group`, so recover state from
    # group.name, which is the (state, constituency) tuple.
    state, _constituency = group.name

    group = group.copy()
    group["raw_swing"] = group["party"].map(
        lambda p: STATE_SWINGS.get((state, p), 0.0)
    )
    group["sim_vote_share"] = (group["vote_share"] + group["raw_swing"]).clip(lower=0)

    total = float(group["sim_vote_share"].sum())
    if total > 0:
        group["sim_vote_share"] = group["sim_vote_share"] / total * 100

    group["sim_rank"] = group["sim_vote_share"].rank(method="first", ascending=False)
    return group


def main() -> None:
    results = load_candidate_results()

    simulated = (
        results.groupby(["state", "constituency"])
               .apply(apply_zero_sum_swing)
               # Bring grouping cols back as real columns (they're on the index after apply).
               .reset_index(level=["state", "constituency"])
               .reset_index(drop=True)
    )

    simulated_winners = simulated[simulated["sim_rank"] == 1].copy()

    save_csv(simulated, ZERO_SUM_RESULTS_FILE)
    save_csv(simulated_winners, ZERO_SUM_WINNERS_FILE)

    print("\nSimulated seat counts (top 20):")
    print(simulated_winners["party"].value_counts().head(20).to_string())

    # Seats where the *party* changed (winner != True means the previous
    # winning row is no longer rank 1).
    flipped = simulated_winners[simulated_winners["winner"] != True]
    print(f"\nChanged seats: {len(flipped)}")
    if not flipped.empty:
        print(flipped[["state", "constituency", "candidate", "party",
                       "sim_vote_share"]].to_string(index=False))


if __name__ == "__main__":
    main()
