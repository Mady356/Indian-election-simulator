"""
Per-(state, party) swing simulator.

Run as:
    python -m src.simulation.state_swing_simulator

Like simple_swing_simulator but the swing is keyed by (state, party) instead of
just party. This lets you model state-specific dynamics (e.g. BJP -2 in UP but
+1 in Karnataka).

Output:
    data/processed/state_simulated_winners.csv
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.config import ALLIANCE_COL
from src.data_io import STATE_SIMULATED_WINNERS_FILE, load_candidate_results, save_csv


STATE_SWINGS = {
    ("Uttar Pradesh", "BJP"): -2.0,
    ("Uttar Pradesh", "SP"):  +2.0,

    ("Maharashtra", "BJP"):    -1.5,
    ("Maharashtra", "INC"):    +1.0,
    ("Maharashtra", "SHSUBT"): +1.0,

    ("Tamil Nadu", "DMK"): +1.0,
    ("Tamil Nadu", "BJP"): +1.0,
}


def main() -> None:
    results = load_candidate_results().copy()

    # Vectorised swing lookup via a MultiIndex map.
    keys = list(zip(results["state"], results["party"]))
    results["swing"] = [STATE_SWINGS.get(k, 0.0) for k in keys]

    results["sim_vote_share"] = (results["vote_share"] + results["swing"]).clip(lower=0)
    results["sim_rank"] = (
        results.groupby(["state", "constituency"])["sim_vote_share"]
               .rank(method="first", ascending=False)
    )

    simulated_winners = results[results["sim_rank"] == 1].copy()

    save_csv(simulated_winners, STATE_SIMULATED_WINNERS_FILE)

    print("\nApplied (state, party) swings:")
    for (state, party), swing in STATE_SWINGS.items():
        print(f"  {state:20s} {party:8s}  {swing:+.2f}%")

    print("\nSimulated seat counts (top 20):")
    print(simulated_winners["party"].value_counts().head(20).to_string())

    if ALLIANCE_COL in simulated_winners.columns:
        print("\nSimulated alliance counts:")
        print(simulated_winners[ALLIANCE_COL].value_counts().to_string())


if __name__ == "__main__":
    main()
