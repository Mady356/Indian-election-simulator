"""
Build the state-level election + demographic analysis spine.

Run as:
    venv/bin/python -m src.analysis.build_state_election_demographic_analysis

Writes:
    data/outputs/state_election_demographic_analysis.csv
    data/outputs/state_party_swing_analysis.csv

This is the bridge between the current Lok Sabha analytical outputs and the
state demographic warehouse. It intentionally stays at state level: the
current demographic master is state-level, so constituency-level demographic
claims should wait for district/GIS allocation.
"""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd


OUTPUT_DIR = Path("data/outputs")
DATABASE_DIR = Path("data/database")
DEMOGRAPHICS_PROCESSED_DIR = Path("data/demographics/processed")

WINNER_COMPARISON_PATH = OUTPUT_DIR / "winner_comparison_2019_2024.csv"
VOLATILITY_PATH = OUTPUT_DIR / "constituency_volatility_2019_2024.csv"
PARTY_SWINGS_PATH = OUTPUT_DIR / "party_swings_2019_2024.csv"
ALLIANCE_PATH = DATABASE_DIR / "party_alliance_by_year.csv"
STATE_DEMOGRAPHICS_PATH = DEMOGRAPHICS_PROCESSED_DIR / "state_demographics_master.csv"

STATE_OUT_PATH = OUTPUT_DIR / "state_election_demographic_analysis.csv"
STATE_PARTY_OUT_PATH = OUTPUT_DIR / "state_party_swing_analysis.csv"

KEY_PARTIES = ["BJP", "INC"]


def normalise_state_name(value: object) -> str:
    """Return a comparison key that handles common Census/ECI naming drift."""
    if pd.isna(value):
        return ""
    name = str(value).strip().upper()
    name = name.replace(" AND ", " & ")
    name = re.sub(r"\s+", " ", name)
    name = name.replace("JAMMU & KASHMIR", "JAMMU & KASHMIR")
    name = name.replace("NCT OF DELHI", "NCT OF DELHI")
    return name


def load_inputs() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    winner_comparison = pd.read_csv(WINNER_COMPARISON_PATH)
    volatility = pd.read_csv(VOLATILITY_PATH)
    party_swings = pd.read_csv(PARTY_SWINGS_PATH)
    alliances = pd.read_csv(ALLIANCE_PATH)
    demographics = pd.read_csv(STATE_DEMOGRAPHICS_PATH)
    return winner_comparison, volatility, party_swings, alliances, demographics


def weighted_average(group: pd.DataFrame, column: str, weight_col: str) -> float:
    values = pd.to_numeric(group[column], errors="coerce")
    weights = pd.to_numeric(group[weight_col], errors="coerce")
    mask = values.notna() & weights.notna() & (weights > 0)
    if not mask.any():
        return np.nan
    return np.average(values[mask], weights=weights[mask])


def build_demographic_lookup(demographics: pd.DataFrame) -> pd.DataFrame:
    """
    Make a state-keyed demographic lookup and explicitly tag imperfect matches.

    Census 2011 geography predates Telangana, Ladakh, and the merged
    Dadra/Nagar Haveli + Daman/Diu UT. Exact state matches remain exact; legacy
    rows are tagged so downstream analysis can filter them.
    """
    demo = demographics.copy()
    demo["state_key"] = demo["state"].map(normalise_state_name)
    demo["demographic_state_source"] = demo["state"]
    demo["demography_match_status"] = "exact"

    rows = [demo]

    # 2024 election geography combines two Census 2011 UT rows.
    dnh_dd_keys = {"DADRA & NAGAR HAVELI", "DAMAN & DIU"}
    dnh_dd = demo[demo["state_key"].isin(dnh_dd_keys)].copy()
    if not dnh_dd.empty:
        composite = {
            "state": "DADRA & NAGAR HAVELI AND DAMAN & DIU",
            "state_key": "DADRA & NAGAR HAVELI & DAMAN & DIU",
            "demographic_state_source": "DADRA & NAGAR HAVELI + DAMAN & DIU",
            "demography_match_status": "composite_weighted_2011",
        }
        numeric_cols = [
            c
            for c in dnh_dd.columns
            if c not in {"state", "state_key", "demographic_state_source", "demography_match_status"}
            and pd.api.types.is_numeric_dtype(dnh_dd[c])
        ]
        for col in numeric_cols:
            if col == "population_total":
                composite[col] = dnh_dd[col].sum(min_count=1)
            elif col.endswith("_code"):
                composite[col] = np.nan
            else:
                composite[col] = weighted_average(dnh_dd, col, "population_total")
        rows.append(pd.DataFrame([composite]))

    # 2011 Census predates these political/geographic splits. Only create
    # legacy aliases when an exact row is not already present from a district
    # rollup cleaner.
    legacy_aliases = {
        "JAMMU & KASHMIR": "JAMMU & KASHMIR",
        "LADAKH": "JAMMU & KASHMIR",
    }
    legacy_rows = []
    exact_keys = set(demo["state_key"])
    for election_key, census_key in legacy_aliases.items():
        if election_key in exact_keys:
            continue
        base = demo[demo["state_key"] == census_key]
        if base.empty:
            continue
        row = base.iloc[0].copy()
        row["state_key"] = election_key
        row["demographic_state_source"] = f"{census_key} (Census 2011 geography)"
        row["demography_match_status"] = "legacy_2011_geography"
        legacy_rows.append(row)
    if legacy_rows:
        rows.append(pd.DataFrame(legacy_rows))

    out = pd.concat(rows, ignore_index=True)
    out = out.drop_duplicates("state_key", keep="last")
    return out


def add_alliance_columns(winners: pd.DataFrame, alliances: pd.DataFrame) -> pd.DataFrame:
    out = winners.copy()

    for year in (2019, 2024):
        mapping = (
            alliances[alliances["election_year"] == year][["party_id", "alliance"]]
            .drop_duplicates("party_id")
            .rename(
                columns={
                    "party_id": f"party_{year}",
                    "alliance": f"alliance_{year}",
                }
            )
        )
        out = out.merge(mapping, on=f"party_{year}", how="left")
        out[f"alliance_{year}"] = out[f"alliance_{year}"].fillna("UNKNOWN")

    out["alliance_flipped"] = out["alliance_2019"] != out["alliance_2024"]
    return out


def most_common(series: pd.Series) -> str:
    counts = series.dropna().value_counts()
    if counts.empty:
        return ""
    return counts.index[0]


def build_state_outcomes(winners: pd.DataFrame, volatility: pd.DataFrame) -> pd.DataFrame:
    state = (
        winners.groupby("state", as_index=False)
        .agg(
            seats=("constituency_id", "count"),
            seat_flips=("seat_flipped", "sum"),
            alliance_flips=("alliance_flipped", "sum"),
            avg_winner_vote_share_2019=("vote_share_2019", "mean"),
            avg_winner_vote_share_2024=("vote_share_2024", "mean"),
            leading_party_2019=("party_2019", most_common),
            leading_party_2024=("party_2024", most_common),
            leading_alliance_2019=("alliance_2019", most_common),
            leading_alliance_2024=("alliance_2024", most_common),
        )
    )

    state["flip_rate"] = state["seat_flips"] / state["seats"] * 100
    state["alliance_flip_rate"] = state["alliance_flips"] / state["seats"] * 100
    state["avg_winner_vote_share_change"] = (
        state["avg_winner_vote_share_2024"] - state["avg_winner_vote_share_2019"]
    )

    party_2019 = (
        winners.groupby(["state", "party_2019"]).size().reset_index(name="seats_2019")
    )
    party_2024 = (
        winners.groupby(["state", "party_2024"]).size().reset_index(name="seats_2024")
    )

    for party in KEY_PARTIES:
        s2019 = (
            party_2019[party_2019["party_2019"] == party][["state", "seats_2019"]]
            .rename(columns={"seats_2019": f"{party.lower()}_seats_2019"})
        )
        s2024 = (
            party_2024[party_2024["party_2024"] == party][["state", "seats_2024"]]
            .rename(columns={"seats_2024": f"{party.lower()}_seats_2024"})
        )
        state = state.merge(s2019, on="state", how="left")
        state = state.merge(s2024, on="state", how="left")
        state[f"{party.lower()}_seats_2019"] = state[f"{party.lower()}_seats_2019"].fillna(0).astype(int)
        state[f"{party.lower()}_seats_2024"] = state[f"{party.lower()}_seats_2024"].fillna(0).astype(int)
        state[f"{party.lower()}_seat_change"] = (
            state[f"{party.lower()}_seats_2024"] - state[f"{party.lower()}_seats_2019"]
        )

    vol = (
        volatility.groupby("state", as_index=False)
        .agg(
            avg_top2_margin_pct=("top2_margin_pct", "mean"),
            median_top2_margin_pct=("top2_margin_pct", "median"),
            close_seats_5pct=("top2_margin_pct", lambda s: int((s <= 5).sum())),
            avg_effective_num_parties=("effective_num_parties", "mean"),
            avg_volatility_score=("volatility_score", "mean"),
            max_volatility_score=("volatility_score", "max"),
        )
    )
    state = state.merge(vol, on="state", how="left")
    state["close_seat_rate_5pct"] = state["close_seats_5pct"] / state["seats"] * 100
    state["state_key"] = state["state"].map(normalise_state_name)
    return state


def build_state_party_swings(
    party_swings: pd.DataFrame,
    winners: pd.DataFrame,
    alliances: pd.DataFrame,
) -> pd.DataFrame:
    swing = (
        party_swings.groupby(["state", "party_id"], as_index=False)
        .agg(
            avg_vote_share_2019=("vote_share_2019", "mean"),
            avg_vote_share_2024=("vote_share_2024", "mean"),
            avg_swing=("swing", "mean"),
            max_swing=("swing", "max"),
            min_swing=("swing", "min"),
            constituencies_seen=("constituency_id", "nunique"),
        )
    )

    seats_2019 = (
        winners.groupby(["state", "party_2019"]).size().reset_index(name="seats_2019")
        .rename(columns={"party_2019": "party_id"})
    )
    seats_2024 = (
        winners.groupby(["state", "party_2024"]).size().reset_index(name="seats_2024")
        .rename(columns={"party_2024": "party_id"})
    )

    swing = swing.merge(seats_2019, on=["state", "party_id"], how="left")
    swing = swing.merge(seats_2024, on=["state", "party_id"], how="left")
    swing["seats_2019"] = swing["seats_2019"].fillna(0).astype(int)
    swing["seats_2024"] = swing["seats_2024"].fillna(0).astype(int)
    swing["seat_change"] = swing["seats_2024"] - swing["seats_2019"]

    alliance_2024 = (
        alliances[alliances["election_year"] == 2024][["party_id", "alliance"]]
        .drop_duplicates("party_id")
        .rename(columns={"alliance": "alliance_2024"})
    )
    swing = swing.merge(alliance_2024, on="party_id", how="left")
    swing["alliance_2024"] = swing["alliance_2024"].fillna("UNKNOWN")
    return swing.sort_values(["state", "seats_2024", "avg_swing"], ascending=[True, False, False])


def add_key_party_swing_columns(state: pd.DataFrame, state_party: pd.DataFrame) -> pd.DataFrame:
    out = state.copy()
    for party in KEY_PARTIES:
        party_state = state_party[state_party["party_id"] == party][
            ["state", "avg_swing", "avg_vote_share_2019", "avg_vote_share_2024"]
        ].rename(
            columns={
                "avg_swing": f"{party.lower()}_avg_swing",
                "avg_vote_share_2019": f"{party.lower()}_avg_vote_share_2019",
                "avg_vote_share_2024": f"{party.lower()}_avg_vote_share_2024",
            }
        )
        out = out.merge(party_state, on="state", how="left")
    return out


def main() -> None:
    winners, volatility, party_swings, alliances, demographics = load_inputs()
    winners = add_alliance_columns(winners, alliances)

    state = build_state_outcomes(winners, volatility)
    state_party = build_state_party_swings(party_swings, winners, alliances)
    state = add_key_party_swing_columns(state, state_party)

    demo_lookup = build_demographic_lookup(demographics)
    state = state.merge(
        demo_lookup.drop(columns=["state"], errors="ignore"),
        on="state_key",
        how="left",
    )
    state["demography_match_status"] = state["demography_match_status"].fillna("no_state_demographic_match")

    preferred_order = [
        "state",
        "state_key",
        "demography_match_status",
        "demographic_state_source",
        "seats",
        "seat_flips",
        "flip_rate",
        "alliance_flips",
        "alliance_flip_rate",
        "close_seats_5pct",
        "close_seat_rate_5pct",
        "avg_top2_margin_pct",
        "avg_effective_num_parties",
        "avg_volatility_score",
        "leading_party_2019",
        "leading_party_2024",
        "leading_alliance_2019",
        "leading_alliance_2024",
        "bjp_seats_2019",
        "bjp_seats_2024",
        "bjp_seat_change",
        "bjp_avg_swing",
        "inc_seats_2019",
        "inc_seats_2024",
        "inc_seat_change",
        "inc_avg_swing",
    ]
    preferred_order = [c for c in preferred_order if c in state.columns]
    remaining = [c for c in state.columns if c not in preferred_order]
    state = state[preferred_order + remaining].sort_values("state").reset_index(drop=True)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    state.to_csv(STATE_OUT_PATH, index=False)
    state_party.to_csv(STATE_PARTY_OUT_PATH, index=False)

    print("Saved state election-demographic analysis:")
    print(f"  {STATE_OUT_PATH} ({state.shape[0]} rows x {state.shape[1]} cols)")
    print(f"  {STATE_PARTY_OUT_PATH} ({state_party.shape[0]} rows x {state_party.shape[1]} cols)")
    print()
    print("Demography match status:")
    print(state["demography_match_status"].value_counts().to_string())
    print()
    print("States without exact demographic matches:")
    cols = ["state", "demography_match_status", "demographic_state_source"]
    print(state[state["demography_match_status"] != "exact"][cols].to_string(index=False))


if __name__ == "__main__":
    main()
