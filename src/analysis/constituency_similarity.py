"""
Nearest-neighbour analysis over constituency_features.

Run as:
    python -m src.analysis.constituency_similarity

Idea:
    Two constituencies are "similar" if their (winner_vote_share, top2_margin_pct,
    effective_num_parties, margin_votes) vectors are close. We standardise the
    four numeric features so they all carry equal weight, then use sklearn's
    NearestNeighbors to find the k closest constituencies to each one.

Output:
    data/processed/<CONSTITUENCY_NEIGHBORS_FILE>  (year-stamped via src.data_io)
        columns: state, constituency, neighbor_state, neighbor_constituency, distance
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.data_io import (
    CONSTITUENCY_NEIGHBORS_FILE,
    load_constituency_features,
    save_csv,
)
from src.utils.validation import check_required_columns


FEATURE_COLS = [
    "winner_vote_share",
    "top2_margin_pct",
    "effective_num_parties",
    "margin_votes",
]
N_NEIGHBORS = 5  # we'll request k+1 from sklearn and drop the self-match


def build_similarity(features: pd.DataFrame, n_neighbors: int = N_NEIGHBORS) -> pd.DataFrame:
    check_required_columns(features, ["state", "constituency", *FEATURE_COLS])

    # Drop rows missing any of the features we need. We could impute later, but
    # for now keeping it simple avoids the question of how to fill margin_votes.
    feat = features.dropna(subset=FEATURE_COLS).reset_index(drop=True)
    print(f"Building NN index over {len(feat)} constituencies "
          f"(dropped {len(features) - len(feat)} with NaNs).")

    X = feat[FEATURE_COLS].values
    X_scaled = StandardScaler().fit_transform(X)

    # k+1 because the closest point to each row is the row itself (distance 0).
    nn = NearestNeighbors(n_neighbors=n_neighbors + 1, algorithm="auto")
    nn.fit(X_scaled)
    distances, indices = nn.kneighbors(X_scaled)

    rows = []
    for i in range(len(feat)):
        # Skip column 0 (self). Columns 1..k are the actual neighbours.
        for j in range(1, n_neighbors + 1):
            rows.append({
                "state": feat.loc[i, "state"],
                "constituency": feat.loc[i, "constituency"],
                "neighbor_state": feat.loc[indices[i, j], "state"],
                "neighbor_constituency": feat.loc[indices[i, j], "constituency"],
                "distance": float(distances[i, j]),
            })

    return pd.DataFrame(rows)


def main() -> None:
    features = load_constituency_features()
    neighbors = build_similarity(features)
    save_csv(neighbors, CONSTITUENCY_NEIGHBORS_FILE)

    # A few human-readable examples so the output is easy to sanity-check.
    examples = [
        ("Kerala", "Wayanad"),
        ("Uttar Pradesh", "Varanasi"),
        ("Maharashtra", "Mumbai North West"),
        ("Tamil Nadu", "Chennai South"),
    ]
    print("\nExample neighbours:")
    for state, constituency in examples:
        sample = neighbors[
            (neighbors["state"] == state)
            & (neighbors["constituency"] == constituency)
        ]
        if sample.empty:
            print(f"  (no rows for {state} / {constituency})")
            continue
        print(f"\n  {state} / {constituency}")
        print(sample[["neighbor_state", "neighbor_constituency", "distance"]]
              .to_string(index=False))


if __name__ == "__main__":
    main()
