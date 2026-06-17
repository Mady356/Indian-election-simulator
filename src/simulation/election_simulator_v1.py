import pandas as pd
from pathlib import Path

DATABASE_DIR = Path("data/database")
OUTPUT_DIR = Path("data/outputs")
SCENARIO_DIR = Path("data/scenarios")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

BASE_YEAR = 2024

RESULTS_PATH = DATABASE_DIR / f"results_table_{BASE_YEAR}.parquet"
ALLIANCE_PATH = DATABASE_DIR / "party_alliance_by_year.csv"
VOLATILITY_PATH = OUTPUT_DIR / "constituency_volatility_2019_2024.csv"
SCENARIO_PATH = SCENARIO_DIR / "sim_v1_state_party_swings.csv"


def load_state_party_swings(path=SCENARIO_PATH):
    if not path.exists():
        raise FileNotFoundError(
            f"Scenario file not found: {path}. "
            "Create a CSV with columns: state, party_id, swing."
        )

    swings = pd.read_csv(path)
    required = {"state", "party_id", "swing"}
    missing = required - set(swings.columns)

    if missing:
        raise ValueError(
            f"Scenario file {path} is missing columns: {sorted(missing)}"
        )

    swings = swings.copy()
    swings["state"] = swings["state"].astype(str).str.strip()
    swings["party_id"] = swings["party_id"].astype(str).str.strip()
    swings["swing"] = pd.to_numeric(swings["swing"], errors="raise")

    duplicate_keys = swings.duplicated(["state", "party_id"], keep=False)
    if duplicate_keys.any():
        duplicates = swings.loc[duplicate_keys, ["state", "party_id"]]
        raise ValueError(
            "Scenario file has duplicate state/party swing rows: "
            f"{duplicates.to_dict(orient='records')}"
        )

    return {
        (row.state, row.party_id): row.swing
        for row in swings.itertuples(index=False)
    }


def apply_zero_sum_swing(group, state_party_swings):
    # pandas >= 3.0 drops the grouping columns from `group`, so recover
    # (state, constituency_id) from group.name (the groupby key tuple) and
    # re-attach them as columns so downstream code can keep treating them
    # as plain columns.
    state, constituency_id = group.name

    group = group.copy()
    group["state"] = state
    group["constituency_id"] = constituency_id

    # Vectorised swing lookup — faster and avoids the row-wise apply that
    # triggered the KeyError under pandas 3.0.
    group["swing"] = group["party_id"].map(
        lambda p: state_party_swings.get((state, p), 0.0)
    )

    group["sim_vote_share_raw"] = (
        group["vote_share"] + group["swing"]
    ).clip(lower=0)

    total = group["sim_vote_share_raw"].sum()

    if total > 0:
        group["sim_vote_share"] = (
            group["sim_vote_share_raw"] / total * 100
        )
    else:
        group["sim_vote_share"] = group["sim_vote_share_raw"]

    group["sim_rank"] = group["sim_vote_share"].rank(
        method="first",
        ascending=False,
    )

    return group


def load_data():
    results = pd.read_parquet(RESULTS_PATH)
    alliances = pd.read_csv(ALLIANCE_PATH)
    state_party_swings = load_state_party_swings()

    volatility = None
    if VOLATILITY_PATH.exists():
        volatility = pd.read_csv(VOLATILITY_PATH)

    return results, alliances, volatility, state_party_swings


def add_alliances(df, alliances):
    alliances = alliances[
        alliances["election_year"] == BASE_YEAR
    ][["party_id", "alliance"]].copy()

    return df.merge(
        alliances,
        on="party_id",
        how="left",
    )


def simulate(results, state_party_swings):
    simulated = (
        results.groupby(
            ["state", "constituency_id"],
            group_keys=False,
        )
        .apply(apply_zero_sum_swing, state_party_swings=state_party_swings)
    )

    winners = simulated[simulated["sim_rank"] == 1].copy()

    return simulated, winners


def build_actual_winners(results):
    actual = results[results["winner"] == True].copy()

    return actual[
        [
            "state",
            "constituency_id",
            "constituency",
            "candidate",
            "party_id",
            "vote_share",
        ]
    ].rename(
        columns={
            "candidate": "actual_winner",
            "party_id": "actual_party",
            "vote_share": "actual_vote_share",
        }
    )


def build_flip_report(actual_winners, simulated_winners):
    sim = simulated_winners[
        [
            "state",
            "constituency_id",
            "constituency",
            "candidate",
            "party_id",
            "sim_vote_share",
            "alliance",
        ]
    ].rename(
        columns={
            "candidate": "sim_winner",
            "party_id": "sim_party",
            "sim_vote_share": "sim_vote_share",
            "alliance": "sim_alliance",
        }
    )

    flips = actual_winners.merge(
        sim,
        on=["state", "constituency_id"],
        how="inner",
    )

    flips["flipped"] = flips["actual_party"] != flips["sim_party"]

    return flips.sort_values(
        ["flipped", "sim_vote_share"],
        ascending=[False, False],
    )


def build_national_projection(simulated_winners):
    party_projection = (
        simulated_winners.groupby("party_id")
        .size()
        .reset_index(name="seats")
        .sort_values("seats", ascending=False)
    )

    alliance_projection = (
        simulated_winners.groupby("alliance")
        .size()
        .reset_index(name="seats")
        .sort_values("seats", ascending=False)
    )

    return party_projection, alliance_projection


def build_state_projection(simulated_winners):
    return (
        simulated_winners.groupby(["state", "party_id"])
        .size()
        .reset_index(name="seats")
        .sort_values(["state", "seats"], ascending=[True, False])
    )


def build_battlegrounds(flip_report, volatility):
    battlegrounds = flip_report.copy()

    if volatility is not None and "volatility_score" in volatility.columns:
        keep_cols = [
            "constituency_id",
            "volatility_score",
            "top2_margin_pct",
            "effective_num_parties",
        ]

        keep_cols = [c for c in keep_cols if c in volatility.columns]

        battlegrounds = battlegrounds.merge(
            volatility[keep_cols].drop_duplicates(),
            on="constituency_id",
            how="left",
        )

        battlegrounds = battlegrounds.sort_values(
            ["flipped", "volatility_score"],
            ascending=[False, False],
        )

    return battlegrounds


def save_outputs(
    simulated,
    simulated_winners,
    flip_report,
    party_projection,
    alliance_projection,
    state_projection,
    battlegrounds,
):
    simulated.to_csv(
        OUTPUT_DIR / "sim_v1_full_results.csv",
        index=False,
    )

    simulated_winners.to_csv(
        OUTPUT_DIR / "sim_v1_winners.csv",
        index=False,
    )

    flip_report.to_csv(
        OUTPUT_DIR / "sim_v1_flip_report.csv",
        index=False,
    )

    party_projection.to_csv(
        OUTPUT_DIR / "sim_v1_party_projection.csv",
        index=False,
    )

    alliance_projection.to_csv(
        OUTPUT_DIR / "sim_v1_alliance_projection.csv",
        index=False,
    )

    state_projection.to_csv(
        OUTPUT_DIR / "sim_v1_state_projection.csv",
        index=False,
    )

    battlegrounds.to_csv(
        OUTPUT_DIR / "sim_v1_battlegrounds.csv",
        index=False,
    )


def main():
    results, alliances, volatility, state_party_swings = load_data()

    if "party_id" not in results.columns:
        raise ValueError("party_id missing. Run normalise_parties first.")

    if "constituency_id" not in results.columns:
        raise ValueError("constituency_id missing. Run constituency normalisation first.")

    results = add_alliances(results, alliances)

    simulated, simulated_winners = simulate(results, state_party_swings)

    actual_winners = build_actual_winners(results)

    flip_report = build_flip_report(
        actual_winners,
        simulated_winners,
    )

    party_projection, alliance_projection = build_national_projection(
        simulated_winners,
    )

    state_projection = build_state_projection(simulated_winners)

    battlegrounds = build_battlegrounds(
        flip_report,
        volatility,
    )

    save_outputs(
        simulated,
        simulated_winners,
        flip_report,
        party_projection,
        alliance_projection,
        state_projection,
        battlegrounds,
    )

    print("\nFull Simulator v1 complete.")
    print(f"\nScenario file: {SCENARIO_PATH}")
    print("\nAlliance projection:")
    print(alliance_projection)
    print("\nTop party projection:")
    print(party_projection.head(20))
    print("\nFlipped seats:", flip_report["flipped"].sum())
    print("\nTop battlegrounds:")
    cols = [
        "state",
        "constituency",
        "actual_party",
        "sim_party",
        "actual_vote_share",
        "sim_vote_share",
        "flipped",
        "volatility_score",
    ]
    cols = [c for c in cols if c in battlegrounds.columns]
    print(battlegrounds[cols].head(30))


if __name__ == "__main__":
    main()
