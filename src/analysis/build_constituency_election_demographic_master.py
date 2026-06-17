"""
Build a constituency-level master table combining 2019/2024 election results
with NFHS demographic levels and NFHS-4 to NFHS-5 changes.

Run:
    python -m src.analysis.build_constituency_election_demographic_master
"""

from __future__ import annotations

import pandas as pd

from src.analysis.analysis_common import (
    ANALYSIS_DIR,
    CHANGE_COLUMNS,
    DATABASE_DIR,
    DEMOGRAPHICS_DIR,
    NFHS5_LEVEL_COLUMNS,
    REFERENCE_DIR,
    add_join_keys,
    discover_file,
)

MASTER_PATH = ANALYSIS_DIR / "constituency_election_demographic_master.csv"

PANEL_SOURCE_COLUMNS = {
    "fertility_rate": "fertility_rate_nfhs5",
    "electricity_pct": "electricity_pct_nfhs5",
    "improved_sanitation_pct": "improved_sanitation_pct_nfhs5",
    "lpg_pct": "lpg_pct_nfhs5",
    "mobile_phone_pct": "mobile_phone_pct_nfhs5",
    "bank_account_pct": "bank_account_pct_nfhs5",
    "women_secondary_edu_pct": "women_secondary_edu_pct_nfhs5",
    "female_literacy_pct": "female_literacy_pct_nfhs5",
    "male_literacy_pct": "male_literacy_pct_nfhs5",
    "wealth_index_mean": "wealth_index_mean_nfhs5",
    "urban_pct": "urban_pct_nfhs5",
}


def load_election_inputs() -> tuple[
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
]:
    print("Discovering election input files...")
    winner_path = discover_file(
        "winner comparison (2019 vs 2024)",
        [
            "winner_comparison_2019_2024.csv",
            "*winner*comparison*2019*2024*.csv",
        ],
    )
    swings_path = discover_file(
        "party swings (2019 vs 2024)",
        [
            "party_swings_2019_2024.csv",
            "*party*swing*2019*2024*.csv",
        ],
    )

    tables_2019 = discover_file(
        "constituency features 2019",
        ["constituency_table_2019.parquet", "results_table_2019.parquet"],
    )
    tables_2024 = discover_file(
        "constituency features 2024",
        ["constituency_table_2024.parquet", "results_table_2024.parquet"],
    )

    top2_2019_path = discover_file(
        "constituency top-2 results 2019",
        ["constituency_top2_2019.csv", "*top2*2019*.csv"],
    )
    top2_2024_path = discover_file(
        "constituency top-2 results 2024",
        ["constituency_top2_2024.csv", "*top2*2024*.csv"],
    )

    winner_comparison = pd.read_csv(winner_path)
    party_swings = pd.read_csv(swings_path)

    if tables_2019.suffix == ".parquet":
        features_2019 = pd.read_parquet(tables_2019)
    else:
        features_2019 = pd.read_parquet(DATABASE_DIR / "constituency_table_2019.parquet")

    if tables_2024.suffix == ".parquet":
        features_2024 = pd.read_parquet(tables_2024)
    else:
        features_2024 = pd.read_parquet(DATABASE_DIR / "constituency_table_2024.parquet")

    top2_2019 = pd.read_csv(top2_2019_path)
    top2_2024 = pd.read_csv(top2_2024_path)

    return winner_comparison, party_swings, features_2019, features_2024, top2_2019, top2_2024


def pivot_party_swings(party_swings: pd.DataFrame, party_id: str) -> pd.DataFrame:
    subset = party_swings[party_swings["party_id"] == party_id].copy()
    prefix = party_id.lower()
    return subset[
        [
            "constituency_id",
            f"vote_share_2019",
            f"vote_share_2024",
            "swing",
        ]
    ].rename(
        columns={
            "vote_share_2019": f"{prefix}_vote_share_2019",
            "vote_share_2024": f"{prefix}_vote_share_2024",
            "swing": f"{prefix}_swing_2019_2024",
        }
    )


def build_turnout_lookup(top2: pd.DataFrame, year: int) -> pd.DataFrame:
    winners = top2[top2["winner"] == True].copy()  # noqa: E712
    winners = add_join_keys(winners, "state", "constituency")
    winners["turnout"] = pd.to_numeric(
        winners["over_total_electors_in_constituency"],
        errors="coerce",
    )
    return winners[["constituency_key", "state_key", "turnout"]].rename(
        columns={"turnout": f"turnout_{year}"}
    )


def build_election_spine(
    winner_comparison: pd.DataFrame,
    party_swings: pd.DataFrame,
    features_2019: pd.DataFrame,
    features_2024: pd.DataFrame,
    top2_2019: pd.DataFrame,
    top2_2024: pd.DataFrame,
) -> pd.DataFrame:
    base = winner_comparison.copy()
    base = add_join_keys(base, "state", "constituency")

    bjp = pivot_party_swings(party_swings, "BJP")
    inc = pivot_party_swings(party_swings, "INC")
    base = base.merge(bjp, on="constituency_id", how="left")
    base = base.merge(inc, on="constituency_id", how="left")

    margin_2019 = features_2019[["constituency_id", "top2_margin_pct"]].rename(
        columns={"top2_margin_pct": "margin_2019"}
    )
    margin_2024 = features_2024[["constituency_id", "top2_margin_pct"]].rename(
        columns={"top2_margin_pct": "margin_2024"}
    )
    base = base.merge(margin_2019, on="constituency_id", how="left")
    base = base.merge(margin_2024, on="constituency_id", how="left")

    turnout_2019 = build_turnout_lookup(top2_2019, 2019)
    turnout_2024 = build_turnout_lookup(top2_2024, 2024)
    base = base.merge(turnout_2019, on=["state_key", "constituency_key"], how="left")
    base = base.merge(turnout_2024, on=["state_key", "constituency_key"], how="left")

    master = pd.DataFrame(
        {
            "state": base["state"],
            "constituency": base["constituency"],
            "constituency_id": base["constituency_id"],
            "state_key": base["state_key"],
            "constituency_key": base["constituency_key"],
            "winner_2019": base["winner_2019"],
            "winner_2024": base["winner_2024"],
            "winner_party_2019": base["party_2019"],
            "winner_party_2024": base["party_2024"],
            "bjp_vote_share_2019": base["bjp_vote_share_2019"],
            "bjp_vote_share_2024": base["bjp_vote_share_2024"],
            "inc_vote_share_2019": base["inc_vote_share_2019"],
            "inc_vote_share_2024": base["inc_vote_share_2024"],
            "bjp_swing_2019_2024": base["bjp_swing_2019_2024"],
            "inc_swing_2019_2024": base["inc_swing_2019_2024"],
            "winner_changed": base["seat_flipped"],
            "margin_2019": base["margin_2019"],
            "margin_2024": base["margin_2024"],
            "turnout_2019": base["turnout_2019"],
            "turnout_2024": base["turnout_2024"],
        }
    )

    master["margin_change"] = master["margin_2024"] - master["margin_2019"]
    master["turnout_change"] = master["turnout_2024"] - master["turnout_2019"]
    return master


def expand_telangana_demo_keys(df: pd.DataFrame) -> pd.DataFrame:
    """Duplicate Andhra Pradesh delimitation rows under Telangana election keys."""
    ap_rows = df[df["state_key"] == "ANDHRA PRADESH"].copy()
    if ap_rows.empty:
        return df
    telangana_rows = ap_rows.copy()
    telangana_rows["state_key"] = "TELANGANA"
    combined = pd.concat([df, telangana_rows], ignore_index=True)
    return combined.drop_duplicates(["state_key", "constituency_key"], keep="first")


def prepare_nfhs5_lookup(panel: pd.DataFrame) -> pd.DataFrame:
    nfhs5 = panel[panel["survey"] == "NFHS-5"].copy()
    nfhs5 = add_join_keys(nfhs5, "state", "lok_sabha_constituency")
    nfhs5 = expand_telangana_demo_keys(nfhs5)

    rename_map = dict(PANEL_SOURCE_COLUMNS)
    rename_map.update(
        {
            "coverage_share": "nfhs5_coverage_share",
            "districts_used": "districts_used",
            "districts_missing": "districts_missing",
        }
    )
    keep_cols = ["state_key", "constituency_key", *rename_map.keys()]
    keep_cols = [c for c in keep_cols if c in nfhs5.columns]
    lookup = nfhs5[keep_cols].rename(columns=rename_map)
    return lookup


def prepare_change_lookup(change: pd.DataFrame) -> pd.DataFrame:
    change = add_join_keys(change, "state", "lok_sabha_constituency")
    change = expand_telangana_demo_keys(change)
    rename_map = {
        **{col: col for col in CHANGE_COLUMNS},
        "coverage_share_nfhs5": "change_coverage_share",
        "change_quality_flag": "change_quality_flag",
    }
    keep_cols = ["state_key", "constituency_key", *rename_map.keys()]
    keep_cols = [c for c in keep_cols if c in change.columns]
    return change[keep_cols].rename(columns=rename_map)


def attach_demographics(master: pd.DataFrame, panel: pd.DataFrame, change: pd.DataFrame) -> pd.DataFrame:
    panel_lookup = prepare_nfhs5_lookup(panel)
    change_lookup = prepare_change_lookup(change)

    out = master.merge(panel_lookup, on=["state_key", "constituency_key"], how="left")
    out = out.merge(change_lookup, on=["state_key", "constituency_key"], how="left", suffixes=("", "_change"))
    return out


def load_demographic_inputs() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    panel_path = DEMOGRAPHICS_DIR / "constituency_demographic_panel.csv"
    change_path = DEMOGRAPHICS_DIR / "constituency_demographic_change_features.csv"
    delimitation_path = REFERENCE_DIR / "lok_sabha_district_summary_delimitation.csv"

    print(f"Using demographic panel: {panel_path}")
    print(f"Using demographic change features: {change_path}")
    print(f"Using delimitation reference: {delimitation_path}")

    panel = pd.read_csv(panel_path)
    change = pd.read_csv(change_path)
    delimitation = pd.read_csv(delimitation_path)
    return panel, change, delimitation


def final_column_order() -> list[str]:
    return [
        "state",
        "constituency",
        "constituency_id",
        "state_key",
        "constituency_key",
        "winner_2019",
        "winner_2024",
        "winner_party_2019",
        "winner_party_2024",
        "bjp_vote_share_2019",
        "bjp_vote_share_2024",
        "inc_vote_share_2019",
        "inc_vote_share_2024",
        "bjp_swing_2019_2024",
        "inc_swing_2019_2024",
        "winner_changed",
        "margin_2019",
        "margin_2024",
        "margin_change",
        "turnout_2019",
        "turnout_2024",
        "turnout_change",
        *NFHS5_LEVEL_COLUMNS,
        *CHANGE_COLUMNS,
        "nfhs5_coverage_share",
        "change_coverage_share",
        "change_quality_flag",
        "districts_used",
        "districts_missing",
    ]


def main() -> None:
    (
        winner_comparison,
        party_swings,
        features_2019,
        features_2024,
        top2_2019,
        top2_2024,
    ) = load_election_inputs()
    panel, change, delimitation = load_demographic_inputs()

    master = build_election_spine(
        winner_comparison,
        party_swings,
        features_2019,
        features_2024,
        top2_2019,
        top2_2024,
    )
    master = attach_demographics(master, panel, change)

    columns = [c for c in final_column_order() if c in master.columns]
    master = master[columns].sort_values(["state", "constituency"]).reset_index(drop=True)

    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    master.to_csv(MASTER_PATH, index=False)

    delimitation_constituencies = delimitation[["state", "lok_sabha_constituency"]].drop_duplicates()
    nfhs5_rows = int(master[NFHS5_LEVEL_COLUMNS].notna().any(axis=1).sum())

    print()
    print("Saved constituency election-demographic master:")
    print(f"  {MASTER_PATH} ({master.shape[0]} rows x {master.shape[1]} cols)")
    print(f"  Election constituencies: {master['constituency_id'].nunique()}")
    print(f"  With NFHS-5 demographic levels: {nfhs5_rows}")
    print(f"  Delimitation reference constituencies: {len(delimitation_constituencies)}")
    print(f"  Valid BJP swing rows: {master['bjp_swing_2019_2024'].notna().sum()}")
    print(f"  Valid INC swing rows: {master['inc_swing_2019_2024'].notna().sum()}")


if __name__ == "__main__":
    main()
