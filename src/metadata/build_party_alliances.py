"""
Build the long-format (party_id, election_year, alliance) lookup table.

Run as:
    python -m src.metadata.build_party_alliances

Input:
    data/database/party_master.csv   (produced by normalise_parties)

Output:
    data/database/party_alliance_by_year.csv

PARTY_ALLIANCE_MAP below is the only place in the project where year-specific
alliance assumptions live. The output table is *always cross-year*, so its
filename is not year-stamped — every year of alliances coexists as separate
rows keyed by `election_year`.
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.config import DATABASE_DIR


PARTY_MASTER_PATH = DATABASE_DIR / "party_master.csv"
OUT_PATH = DATABASE_DIR / "party_alliance_by_year.csv"


# Year-specific alliance assignments. Add/update years here as you expand.
# Keep this dict as the only source of "which party was in which alliance".
PARTY_ALLIANCE_MAP = {
    2024: {
        "BJP": "NDA",
        "INC": "INDIA",
        "SP": "INDIA",
        "DMK": "INDIA",
        "AITC": "INDIA",
        "AAP": "INDIA",
        "CPIM": "INDIA",
        "CPI": "INDIA",
        "RJD": "INDIA",
        "SHSUBT": "INDIA",
        "NCPSP": "INDIA",

        "JDU": "NDA",
        "TDP": "NDA",
        "SHS": "NDA",
        "NCP": "NDA",

        "YSRCP": "OTHER",
        "BJD": "OTHER",
        "BSP": "OTHER",
        "IND": "OTHER",
        "NOTA": "NONE",
    },
    2019: {
        "BJP": "NDA",
        "INC": "UPA",
        "DMK": "UPA",
        "NCP": "UPA",
        "RJD": "UPA",
        "JMM": "UPA",
        "IUML": "UPA",
        "JDS": "UPA",

        "JDU": "NDA",
        "SHS": "NDA",
        "AIADMK": "NDA",
        "LJP": "NDA",

        "AITC": "OTHER",
        "SP": "OTHER",
        "BSP": "OTHER",
        "YSRCP": "OTHER",
        "TDP": "OTHER",
        "BJD": "OTHER",
        "AAP": "OTHER",
        "CPIM": "OTHER",
        "CPI": "OTHER",
        "IND": "OTHER",
        "NOTA": "NONE",
    },
}


def load_party_master() -> pd.DataFrame:
    if not PARTY_MASTER_PATH.exists():
        raise FileNotFoundError(
            f"{PARTY_MASTER_PATH} not found. Run "
            "`python -m src.normalisation.normalise_parties` first."
        )
    return pd.read_csv(PARTY_MASTER_PATH)


def build_party_alliance_table(party_master: pd.DataFrame) -> pd.DataFrame:
    """One row per (party_id, election_year) with the alliance for that year."""
    rows = []
    unique_parties = sorted(party_master["party_id"].dropna().unique())

    for year, alliance_map in PARTY_ALLIANCE_MAP.items():
        for party_id in unique_parties:
            rows.append({
                "party_id": party_id,
                "election_year": year,
                "alliance": alliance_map.get(party_id, "UNKNOWN"),
            })
    return pd.DataFrame(rows)


def main() -> None:
    party_master = load_party_master()
    alliance_table = build_party_alliance_table(party_master)
    alliance_table.to_csv(OUT_PATH, index=False)

    print(f"Saved: {OUT_PATH}")
    print()
    print("Alliance counts by year:")
    print(
        alliance_table.groupby(["election_year", "alliance"])
                      .size()
                      .reset_index(name="party_count")
                      .to_string(index=False)
    )
    print()
    unknown = (
        alliance_table[alliance_table["alliance"] == "UNKNOWN"]
        .sort_values(["election_year", "party_id"])
    )
    print(f"UNKNOWN rows (curate these next): {len(unknown)}")
    print(unknown.head(20).to_string(index=False))


if __name__ == "__main__":
    main()
