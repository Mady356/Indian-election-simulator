import pandas as pd
from pathlib import Path

OUTPUT_DIR = Path("data/outputs")
DATABASE_DIR = Path("data/database")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


WINNER_COMPARISON_PATH = OUTPUT_DIR / "winner_comparison_2019_2024.csv"
PARTY_SWINGS_PATH = OUTPUT_DIR / "party_swings_2019_2024.csv"
FEATURES_2024_PATH = DATABASE_DIR / "constituency_table_2024.parquet"

OUT_PATH = OUTPUT_DIR / "constituency_volatility_2019_2024.csv"


def load_data():
    winner_comparison = pd.read_csv(WINNER_COMPARISON_PATH)
    party_swings = pd.read_csv(PARTY_SWINGS_PATH)
    features_2024 = pd.read_parquet(FEATURES_2024_PATH)

    return winner_comparison, party_swings, features_2024


def build_party_swing_features(party_swings):
    swing_summary = (
        party_swings.groupby(["state", "constituency_id"])
        .agg(
            max_positive_swing=("swing", "max"),
            max_negative_swing=("swing", "min"),
            avg_abs_swing=("swing", lambda x: x.abs().mean()),
        )
        .reset_index()
    )

    swing_summary["swing_range"] = (
        swing_summary["max_positive_swing"]
        - swing_summary["max_negative_swing"]
    )

    return swing_summary


def build_volatility_table(winner_comparison, party_swings, features_2024):
    swing_features = build_party_swing_features(party_swings)

    volatility = winner_comparison.merge(
        swing_features,
        on=["state", "constituency_id"],
        how="left",
    )

    features_keep = [
        "constituency_id",
        "top2_margin_pct",
        "effective_num_parties",
        "winner_vote_share",
        "margin_votes",
    ]

    features_keep = [c for c in features_keep if c in features_2024.columns]

    volatility = volatility.merge(
        features_2024[features_keep],
        on="constituency_id",
        how="left",
    )

    volatility["winner_vote_share_change"] = (
        volatility["vote_share_2024"]
        - volatility["vote_share_2019"]
    )

    volatility["flip_score"] = volatility["seat_flipped"].astype(int) * 40

    volatility["close_margin_score"] = (
        20 - volatility["top2_margin_pct"].clip(upper=20)
    )

    volatility["fragmentation_score"] = (
        volatility["effective_num_parties"].fillna(0) * 5
    )

    volatility["swing_score"] = (
        volatility["avg_abs_swing"].fillna(0) * 2
    )

    volatility["volatility_score"] = (
        volatility["flip_score"]
        + volatility["close_margin_score"]
        + volatility["fragmentation_score"]
        + volatility["swing_score"]
    )

    volatility = volatility.sort_values(
        "volatility_score",
        ascending=False,
    )

    return volatility


def main():
    winner_comparison, party_swings, features_2024 = load_data()

    volatility = build_volatility_table(
        winner_comparison,
        party_swings,
        features_2024,
    )

    volatility.to_csv(OUT_PATH, index=False)

    print("Saved constituency volatility table:")
    print(OUT_PATH)
    print()

    print("Most volatile constituencies:")
    cols = [
        "state",
        "constituency",
        "party_2019",
        "party_2024",
        "seat_flipped",
        "top2_margin_pct",
        "effective_num_parties",
        "avg_abs_swing",
        "volatility_score",
    ]

    cols = [c for c in cols if c in volatility.columns]

    print(volatility[cols].head(30))


if __name__ == "__main__":
    main()
