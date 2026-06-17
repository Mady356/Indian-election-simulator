"""
Tag every contesting party with structural metadata: type / alliance / ideology / region.

Run as:
    python -m src.metadata.build_party_metadata

Inputs:
    data/processed/<CANDIDATE_RESULTS_FILE>     (from src.data_io)

Outputs:
    data/processed/<PARTY_COUNTS_FILE>          (audit: party -> candidate_count)
    data/processed/<PARTY_METADATA_FILE>        (full metadata table)

PARTY_ALLIANCE_MAP is the only year-specific block in this file: it maps each
known party abbreviation to the alliance it belonged to in ELECTION_YEAR.
The rest of the metadata (party_type / ideology / region) is treated as
year-invariant.
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.config import ALLIANCE_COL
from src.data_io import (
    PARTY_COUNTS_FILE,
    PARTY_METADATA_FILE,
    load_candidate_results,
    save_csv,
)


# Year-invariant party facts. Update when you investigate a new party from the
# audit table.
PARTY_FACTS = {
    "BJP":        {"party_type": "national",    "ideology": "centre-right",          "region": "national"},
    "INC":        {"party_type": "national",    "ideology": "centre-left",           "region": "national"},
    "BSP":        {"party_type": "national",    "ideology": "bahujan_social_justice","region": "uttar_pradesh"},
    "SP":         {"party_type": "regional",    "ideology": "socialist",             "region": "uttar_pradesh"},
    "AITC":       {"party_type": "regional",    "ideology": "centre",                "region": "west_bengal"},
    "DMK":        {"party_type": "regional",    "ideology": "dravidian",             "region": "tamil_nadu"},
    "TDP":        {"party_type": "regional",    "ideology": "regional_centre",       "region": "andhra_pradesh"},
    "JD(U)":      {"party_type": "regional",    "ideology": "regional_centre",       "region": "bihar"},
    "YSRCP":      {"party_type": "regional",    "ideology": "regional_centre",       "region": "andhra_pradesh"},
    "SHS":        {"party_type": "regional",    "ideology": "marathi_regionalist",   "region": "maharashtra"},
    "SHSUBT":     {"party_type": "regional",    "ideology": "marathi_regionalist",   "region": "maharashtra"},
    "NCP":        {"party_type": "regional",    "ideology": "regional_centre",       "region": "maharashtra"},
    "NCPSP":      {"party_type": "regional",    "ideology": "regional_centre",       "region": "maharashtra"},
    "AAAP":       {"party_type": "national",    "ideology": "welfare_populist",      "region": "delhi_punjab"},
    "CPI":        {"party_type": "national",    "ideology": "far-left",              "region": "national"},
    "CPI(M)":     {"party_type": "national",    "ideology": "far-left",              "region": "national"},
    "RJD":        {"party_type": "regional",    "ideology": "social_justice",        "region": "bihar"},
    "BJD":        {"party_type": "regional",    "ideology": "regional_centre",       "region": "odisha"},
    "JMM":        {"party_type": "regional",    "ideology": "tribal_regional",       "region": "jharkhand"},
    "JD(S)":      {"party_type": "regional",    "ideology": "regional_centre",       "region": "karnataka"},
    "LJPRV":      {"party_type": "regional",    "ideology": "dalit_assertive",       "region": "bihar"},
    "IUML":       {"party_type": "regional",    "ideology": "muslim_minority",       "region": "kerala"},
    "JKN":        {"party_type": "regional",    "ideology": "regional_centre",       "region": "jammu_kashmir"},
    "VCK":        {"party_type": "regional",    "ideology": "dalit_assertive",       "region": "tamil_nadu"},
    "RLD":        {"party_type": "regional",    "ideology": "agrarian",              "region": "uttar_pradesh"},
    "AGP":        {"party_type": "regional",    "ideology": "regional_centre",       "region": "assam"},
    "UPPL":       {"party_type": "regional",    "ideology": "tribal_regional",       "region": "assam"},
    "HAMS":       {"party_type": "regional",    "ideology": "social_justice",        "region": "bihar"},
    "AJSUP":      {"party_type": "regional",    "ideology": "tribal_regional",       "region": "jharkhand"},
    "RSP":        {"party_type": "national",    "ideology": "far-left",              "region": "kerala"},
    "JnP":        {"party_type": "regional",    "ideology": "regional_centre",       "region": "andhra_pradesh"},
    "CPI(ML)(L)": {"party_type": "national",    "ideology": "far-left",              "region": "national"},
    "IND":        {"party_type": "independent", "ideology": "independent",           "region": "local"},
    "NOTA":       {"party_type": "nota",        "ideology": "none",                  "region": "none"},
}

# Year-specific: which alliance was each party in for ELECTION_YEAR?
# When you add 2019, add a separate dict and select on ELECTION_YEAR.
PARTY_ALLIANCE_MAP = {
    "BJP": "NDA",     "INC": "INDIA",   "BSP": "OTHER",  "SP": "INDIA",
    "AITC": "INDIA",  "DMK": "INDIA",   "TDP": "NDA",    "JD(U)": "NDA",
    "YSRCP": "OTHER", "SHS": "NDA",     "SHSUBT": "INDIA","NCP": "NDA",
    "NCPSP": "INDIA", "AAAP": "INDIA",  "CPI": "INDIA",  "CPI(M)": "INDIA",
    "RJD": "INDIA",   "BJD": "OTHER",   "JMM": "INDIA",  "JD(S)": "NDA",
    "LJPRV": "NDA",   "IUML": "INDIA",  "JKN": "INDIA",  "VCK": "INDIA",
    "RLD": "NDA",     "AGP": "NDA",     "UPPL": "NDA",   "HAMS": "NDA",
    "AJSUP": "NDA",   "RSP": "INDIA",   "JnP": "NDA",    "CPI(ML)(L)": "INDIA",
    "IND": "OTHER",   "NOTA": "NONE",
}


def build_party_counts(results: pd.DataFrame) -> pd.DataFrame:
    """How many candidates did each party field, across the country?"""
    counts = (
        results["party"]
        .value_counts(dropna=False)
        .reset_index()
    )
    counts.columns = ["party", "candidate_count"]
    return counts


def build_party_metadata(party_counts: pd.DataFrame) -> pd.DataFrame:
    """Attach year-invariant facts + the year-specific alliance to each party."""
    party_meta = party_counts.copy()

    # Defaults make it obvious which rows we *haven't* curated yet.
    party_meta["party_type"] = "unknown"
    party_meta[ALLIANCE_COL] = "OTHER"
    party_meta["ideology"] = "unknown"
    party_meta["region"] = "unknown"

    # Year-invariant facts.
    for party, facts in PARTY_FACTS.items():
        mask = party_meta["party"] == party
        for column, value in facts.items():
            party_meta.loc[mask, column] = value

    # Year-specific alliance assignment (column name comes from ALLIANCE_COL).
    for party, alliance in PARTY_ALLIANCE_MAP.items():
        party_meta.loc[party_meta["party"] == party, ALLIANCE_COL] = alliance

    return party_meta


def main() -> None:
    results = load_candidate_results()

    party_counts = build_party_counts(results)
    save_csv(party_counts, PARTY_COUNTS_FILE)

    party_meta = build_party_metadata(party_counts)
    save_csv(party_meta, PARTY_METADATA_FILE)

    print("\nTop parties:")
    print(party_meta.head(15).to_string(index=False))

    unknown = (
        party_meta[party_meta["party_type"] == "unknown"]
        .sort_values("candidate_count", ascending=False)
    )
    print(f"\nParties still untagged: {len(unknown)}")
    print(unknown.head(20).to_string(index=False))


if __name__ == "__main__":
    main()
