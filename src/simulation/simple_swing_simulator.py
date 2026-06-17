"""
Uniform per-party swing simulator (the simplest possible model).

Run as:
    python -m src.simulation.simple_swing_simulator

Idea:
    Pick a percentage-point swing for each party (positive = gain, negative
    = lose). Apply it to every candidate of that party in every constituency,
    re-rank, and pick the new winner.

Caveats:
    This model is *not* zero-sum — the per-constituency total vote share will
    no longer sum to 100. Use it for quick "what if" exploration; for more
    rigorous comparisons use zero_sum_state_swing_simulator.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.data_io import SIMULATED_WINNERS_FILE, load_candidate_results, save_csv


# Edit these to explore different scenarios.
SWINGS = {
    "BJP":  2.0,
    "INC": -1.0,
    "SP":   1.0,
}


def main() -> None:
    results = load_candidate_results()

    # Vectorised swing application; faster and clearer than a row-wise apply.
    results = results.copy()
    results["swing"] = results["party"].map(SWINGS).fillna(0.0)
    results["sim_vote_share"] = (results["vote_share"] + results["swing"]).clip(lower=0)

    # Re-rank candidates within each constituency by simulated share.
    results["sim_rank"] = (
        results.groupby(["state", "constituency"])["sim_vote_share"]
               .rank(method="first", ascending=False)
    )

    simulated_winners = results[results["sim_rank"] == 1].copy()

    save_csv(simulated_winners, SIMULATED_WINNERS_FILE)

    print("\nApplied swings:")
    for party, swing in SWINGS.items():
        print(f"  {party}: {swing:+.2f}%")

    print("\nSimulated seat counts (top 20):")
    print(simulated_winners["party"].value_counts().head(20).to_string())


if __name__ == "__main__":
    main()
