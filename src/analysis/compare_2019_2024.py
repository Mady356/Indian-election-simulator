import pandas as pd
from pathlib import Path

DATABASE_DIR = Path("data/database")
OUTPUT_DIR = Path("data/outputs")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


RESULTS_2019_PATH = DATABASE_DIR / "results_table_2019.parquet"
RESULTS_2024_PATH = DATABASE_DIR / "results_table_2024.parquet"
UNMATCHED_PATH = OUTPUT_DIR / "unmatched_constituencies_2019_2024.csv"


# Constituency names drift across ECI files because of spelling changes,
# delimitation-style seat renames, state/UT reorganisations, and dropped
# reservation suffixes. These aliases map older IDs onto the 2024 analytical
# key used by the comparison layer.
CONSTITUENCY_ID_ALIASES = {
    "ANDHRA_PRADESH__ANAKAPALLI": "ANDHRA_PRADESH__ANAKAPALLE",
    "ANDHRA_PRADESH__ANANTAPUR": "ANDHRA_PRADESH__ANANTHAPUR",
    "ANDHRA_PRADESH__ARUKU": "ANDHRA_PRADESH__ARAKU",
    "ANDHRA_PRADESH__KURNOOL": "ANDHRA_PRADESH__KURNOOLU",
    "ANDHRA_PRADESH__NARASARAOPET": "ANDHRA_PRADESH__NARSARAOPET",
    "ANDHRA_PRADESH__TIRUPATI": "ANDHRA_PRADESH__THIRUPATHI",
    "ASSAM__AUTONOMOUS_DISTRICT": "ASSAM__DIPHU",
    "ASSAM__GAUHATI": "ASSAM__GUWAHATI",
    "ASSAM__KALIABOR": "ASSAM__KAZIRANGA",
    "ASSAM__MANGALDOI": "ASSAM__DARRANG-UDALGURI",
    "ASSAM__NOWGONG": "ASSAM__NAGAON",
    "ASSAM__TEZPUR": "ASSAM__SONITPUR",
    "BIHAR__GAYA_(SC)": "BIHAR__GAYA",
    "BIHAR__GOPALGANJ_(SC)": "BIHAR__GOPALGANJ",
    "BIHAR__HAJIPUR_(SC)": "BIHAR__HAJIPUR",
    "BIHAR__JAMUI_(SC)": "BIHAR__JAMUI",
    "BIHAR__PATALIPUTRA": "BIHAR__PATLIPUTRA",
    "BIHAR__SAMASTIPUR_(SC)": "BIHAR__SAMASTIPUR",
    "BIHAR__SASARAM_(SC)": "BIHAR__SASARAM",
    "CHHATTISGARH__SARGUJA": "CHHATTISGARH__SURGUJA",
    "DADRA_&_NAGAR_HAVELI__DADRA_AND_NAGAR_HAVELI":
        "DADRA_&_NAGAR_HAVELI_AND_DAMAN_&_DIU__DADAR_&_NAGAR_HAVELI",
    "DAMAN_&_DIU__DAMAN_&_DIU":
        "DADRA_&_NAGAR_HAVELI_AND_DAMAN_&_DIU__DAMAN_&_DIU",
    "JAMMU_&_KASHMIR__ANANTNAG": "JAMMU_AND_KASHMIR__ANANTNAG-RAJOURI",
    "JAMMU_&_KASHMIR__BARAMULLA": "JAMMU_AND_KASHMIR__BARAMULLA",
    "JAMMU_&_KASHMIR__JAMMU": "JAMMU_AND_KASHMIR__JAMMU",
    "JAMMU_&_KASHMIR__LADAKH": "LADAKH__LADAKH",
    "JAMMU_&_KASHMIR__SRINAGAR": "JAMMU_AND_KASHMIR__SRINAGAR",
    "JAMMU_&_KASHMIR__UDHAMPUR": "JAMMU_AND_KASHMIR__UDHAMPUR",
    "JHARKHAND__PALAMAU": "JHARKHAND__PALAMU",
    "MAHARASHTRA__AHMADNAGAR": "MAHARASHTRA__AHMEDNAGAR",
    "MAHARASHTRA__BHANDARA_-_GONDIYA": "MAHARASHTRA__BHANDARA_GONDIYA",
    "MAHARASHTRA__GADCHIROLI-CHIMUR": "MAHARASHTRA__GADCHIROLI_-_CHIMUR",
    "MAHARASHTRA__HATKANANGLE": "MAHARASHTRA__HATKANANGALE",
    "MAHARASHTRA__RATNAGIRI_-_SINDHUDURG":
        "MAHARASHTRA__RATNAGIRI-_SINDHUDURG",
    "MAHARASHTRA__YAVATMAL-WASHIM": "MAHARASHTRA__YAVATMAL-_WASHIM",
    "NCT_OF_DELHI__NORTH_EAST_DELHI": "NCT_OF_DELHI__NORTH-EAST_DELHI",
    "NCT_OF_DELHI__NORTH_WEST_DELHI": "NCT_OF_DELHI__NORTH-WEST_DELHI",
    "RAJASTHAN__BIKANER_(SC)": "RAJASTHAN__BIKANER",
    "TAMIL_NADU__THIRUVALLUR": "TAMIL_NADU__TIRUVALLUR",
    "TELANGANA__SECUNDRABAD": "TELANGANA__SECUNDERABAD",
    "UTTAR_PRADESH__BAHRAICH": "UTTAR_PRADESH__BAHARAICH",
    "UTTARAKHAND__HARDWAR": "UTTARAKHAND__HARIDWAR",
    "WEST_BENGAL__ARAMBAGH": "WEST_BENGAL__ARAMBAG",
    "WEST_BENGAL__BARDHAMAN_DURGAPUR": "WEST_BENGAL__BARDHAMAN-DURGAPUR",
    "WEST_BENGAL__BARRACKPORE": "WEST_BENGAL__BARRACKPUR",
    "WEST_BENGAL__COOCH_BEHAR": "WEST_BENGAL__COOCHBEHAR",
    "WEST_BENGAL__SRERAMPUR": "WEST_BENGAL__SREERAMPUR",
}


def load_results():
    results_2019 = pd.read_parquet(RESULTS_2019_PATH)
    results_2024 = pd.read_parquet(RESULTS_2024_PATH)

    return results_2019, results_2024


def add_comparison_key(df):
    out = df.copy()
    out["source_constituency_id"] = out["constituency_id"]
    out["constituency_id"] = (
        out["constituency_id"]
        .map(CONSTITUENCY_ID_ALIASES)
        .fillna(out["constituency_id"])
    )
    return out


def build_unmatched_constituencies(results_2019, results_2024):
    winners_2019 = results_2019[results_2019["winner"] == True].copy()
    winners_2024 = results_2024[results_2024["winner"] == True].copy()

    ids_2019 = set(winners_2019["constituency_id"])
    ids_2024 = set(winners_2024["constituency_id"])

    unmatched_2019 = winners_2019[
        ~winners_2019["constituency_id"].isin(ids_2024)
    ].copy()
    unmatched_2019["comparison_year"] = 2019
    unmatched_2019["reason"] = "No matching 2024 constituency_id"

    unmatched_2024 = winners_2024[
        ~winners_2024["constituency_id"].isin(ids_2019)
    ].copy()
    unmatched_2024["comparison_year"] = 2024
    unmatched_2024["reason"] = "No matching 2019 constituency_id"

    keep_cols = [
        "comparison_year",
        "state",
        "source_constituency_id",
        "constituency_id",
        "constituency",
        "party_id",
        "candidate",
        "reason",
    ]

    return pd.concat(
        [unmatched_2019, unmatched_2024],
        ignore_index=True,
    )[[c for c in keep_cols if c in unmatched_2019.columns or c in unmatched_2024.columns]]


def build_winner_comparison(results_2019, results_2024):

    winners_2019 = results_2019[
        results_2019["winner"] == True
    ][
        [
            "state",
            "source_constituency_id",
            "constituency_id",
            "constituency",
            "party_id",
            "candidate",
            "vote_share",
        ]
    ].copy()

    winners_2024 = results_2024[
        results_2024["winner"] == True
    ][
        [
            "state",
            "source_constituency_id",
            "constituency_id",
            "constituency",
            "party_id",
            "candidate",
            "vote_share",
        ]
    ].copy()

    winners_2019 = winners_2019.rename(
        columns={
            "party_id": "party_2019",
            "candidate": "winner_2019",
            "vote_share": "vote_share_2019",
            "source_constituency_id": "constituency_id_2019",
            "state": "state_2019",
            "constituency": "constituency_2019",
        }
    )

    winners_2024 = winners_2024.rename(
        columns={
            "party_id": "party_2024",
            "candidate": "winner_2024",
            "vote_share": "vote_share_2024",
            "source_constituency_id": "constituency_id_2024",
            "state": "state_2024",
            "constituency": "constituency_2024",
        }
    )

    comparison = winners_2019.merge(
        winners_2024,
        on="constituency_id",
        how="inner",
    )

    comparison["state"] = comparison["state_2024"].fillna(
        comparison["state_2019"]
    )
    comparison["constituency"] = comparison["constituency_2024"].fillna(
        comparison["constituency_2019"]
    )

    comparison["seat_flipped"] = (
        comparison["party_2019"]
        != comparison["party_2024"]
    )

    return comparison


def build_party_swing_table(results_2019, results_2024):

    party_votes_2019 = results_2019[
        [
            "state",
            "source_constituency_id",
            "constituency_id",
            "party_id",
            "vote_share",
        ]
    ].copy()

    party_votes_2024 = results_2024[
        [
            "state",
            "source_constituency_id",
            "constituency_id",
            "party_id",
            "vote_share",
        ]
    ].copy()

    party_votes_2019 = party_votes_2019.rename(
        columns={
            "vote_share": "vote_share_2019",
            "source_constituency_id": "constituency_id_2019",
            "state": "state_2019",
        }
    )

    party_votes_2024 = party_votes_2024.rename(
        columns={
            "vote_share": "vote_share_2024",
            "source_constituency_id": "constituency_id_2024",
            "state": "state_2024",
        }
    )

    swings = party_votes_2019.merge(
        party_votes_2024,
        on=[
            "constituency_id",
            "party_id",
        ],
        how="outer",
    )

    swings["vote_share_2019"] = (
        swings["vote_share_2019"]
        .fillna(0)
    )

    swings["vote_share_2024"] = (
        swings["vote_share_2024"]
        .fillna(0)
    )

    swings["swing"] = (
        swings["vote_share_2024"]
        - swings["vote_share_2019"]
    )

    swings["state"] = swings["state_2024"].fillna(swings["state_2019"])

    return swings


def build_state_swing_summary(swings):

    state_summary = (
        swings.groupby(
            ["state", "party_id"]
        )["swing"]
        .mean()
        .reset_index()
    )

    return state_summary.sort_values(
        ["state", "swing"],
        ascending=[True, False]
    )


def main():

    print("\nLoading data...")

    results_2019, results_2024 = load_results()
    results_2019 = add_comparison_key(results_2019)
    results_2024 = add_comparison_key(results_2024)

    print("2019 rows:", len(results_2019))
    print("2024 rows:", len(results_2024))

    # -----------------------------------
    # WINNER COMPARISON
    # -----------------------------------

    print("\nBuilding winner comparison...")

    winner_comparison = build_winner_comparison(
        results_2019,
        results_2024,
    )

    # -----------------------------------
    # PARTY SWINGS
    # -----------------------------------

    print("Building party swing table...")

    swings = build_party_swing_table(
        results_2019,
        results_2024,
    )

    # -----------------------------------
    # STATE SUMMARY
    # -----------------------------------

    print("Building state swing summary...")

    state_summary = build_state_swing_summary(swings)

    unmatched = build_unmatched_constituencies(
        results_2019,
        results_2024,
    )

    # -----------------------------------
    # SAVE
    # -----------------------------------

    winner_comparison.to_csv(
        OUTPUT_DIR / "winner_comparison_2019_2024.csv",
        index=False,
    )

    swings.to_csv(
        OUTPUT_DIR / "party_swings_2019_2024.csv",
        index=False,
    )

    state_summary.to_csv(
        OUTPUT_DIR / "state_swing_summary_2019_2024.csv",
        index=False,
    )

    unmatched.to_csv(
        UNMATCHED_PATH,
        index=False,
    )

    # -----------------------------------
    # PRINT SUMMARY
    # -----------------------------------

    print("\n-----------------------------------")
    print("SEAT FLIPS")
    print("-----------------------------------")

    total_flips = winner_comparison["seat_flipped"].sum()

    print("Total seat flips:", total_flips)
    print("Matched constituencies:", len(winner_comparison))
    print("Unmatched constituency rows:", len(unmatched))

    print("\nTop party-to-party flips:")

    print(
        winner_comparison[
            winner_comparison["seat_flipped"]
        ]
        .groupby(
            ["party_2019", "party_2024"]
        )
        .size()
        .sort_values(ascending=False)
        .head(20)
    )

    print("\n-----------------------------------")
    print("BIGGEST POSITIVE SWINGS")
    print("-----------------------------------")

    print(
        swings.sort_values(
            "swing",
            ascending=False
        )[
            [
                "state",
                "constituency_id",
                "party_id",
                "vote_share_2019",
                "vote_share_2024",
                "swing",
            ]
        ]
        .head(20)
    )

    print("\n-----------------------------------")
    print("BIGGEST NEGATIVE SWINGS")
    print("-----------------------------------")

    print(
        swings.sort_values(
            "swing"
        )[
            [
                "state",
                "constituency_id",
                "party_id",
                "vote_share_2019",
                "vote_share_2024",
                "swing",
            ]
        ]
        .head(20)
    )

    print("\n-----------------------------------")
    print("FILES SAVED")
    print("-----------------------------------")

    print("winner_comparison_2019_2024.csv")
    print("party_swings_2019_2024.csv")
    print("state_swing_summary_2019_2024.csv")


if __name__ == "__main__":
    main()
