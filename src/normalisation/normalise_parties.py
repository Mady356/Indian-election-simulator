"""
Normalise raw party names into stable `party_id`s and write a party master.

Run as:
    python -m src.normalisation.normalise_parties

Inputs (from data/database/, written by `src.database.database_layer`):
    results_table_<ACTIVE_YEAR>.parquet

Outputs (data/database/):
    results_table_<ACTIVE_YEAR>.{csv,parquet}    augmented with party_id columns
    party_master.csv                              dedup'd (party_id, party_clean, party_raw)

Year-agnostic: every path resolves through `src.config.ACTIVE_YEAR` so this
script reads/writes the *current* active year's tables only.
"""

import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.config import ACTIVE_YEAR, DATABASE_DIR


RESULTS_STEM = f"results_table_{ACTIVE_YEAR}"
RESULTS_PARQUET = DATABASE_DIR / f"{RESULTS_STEM}.parquet"
RESULTS_CSV = DATABASE_DIR / f"{RESULTS_STEM}.csv"
PARTY_MASTER_PATH = DATABASE_DIR / "party_master.csv"


# Maps anything we've seen in raw ECI data to the canonical `party_id` we use
# everywhere downstream. Add aliases as you encounter them in new years.
KNOWN_PARTY_ALIASES = {
    "BJP": "BJP", "BHARATIYA JANATA PARTY": "BJP",
    "INC": "INC", "INDIAN NATIONAL CONGRESS": "INC",
    "BSP": "BSP", "BAHUJAN SAMAJ PARTY": "BSP",
    "SP": "SP",   "SAMAJWADI PARTY": "SP",
    "AAP": "AAP", "AAM AADMI PARTY": "AAP",
    "AITC": "AITC", "ALL INDIA TRINAMOOL CONGRESS": "AITC",
    "DMK": "DMK", "DRAVIDA MUNNETRA KAZHAGAM": "DMK",
    "TDP": "TDP", "TELUGU DESAM PARTY": "TDP",
    "YSRCP": "YSRCP", "YSR CONGRESS PARTY": "YSRCP",
    "JD(U)": "JDU", "JDU": "JDU", "JANATA DAL (UNITED)": "JDU",
    "RJD": "RJD", "RASHTRIYA JANATA DAL": "RJD",
    "SHS": "SHS", "SHIV SENA": "SHS",
    "SHSUBT": "SHSUBT",
    "SHIV SENA (UDDHAV BALASAHEB THACKERAY)": "SHSUBT",
    "NCP": "NCP", "NATIONALIST CONGRESS PARTY": "NCP",
    "NCPSP": "NCPSP",
    "NATIONALIST CONGRESS PARTY – SHARADCHANDRA PAWAR": "NCPSP",
    "NATIONALIST CONGRESS PARTY - SHARADCHANDRA PAWAR": "NCPSP",
    "CPI": "CPI", "COMMUNIST PARTY OF INDIA": "CPI",
    "CPI(M)": "CPIM", "CPIM": "CPIM",
    "COMMUNIST PARTY OF INDIA (MARXIST)": "CPIM",
    "IND": "IND", "INDEPENDENT": "IND",
    "NOTA": "NOTA",
}


def clean_text(value: object) -> str:
    if pd.isna(value):
        return ""
    value = str(value).strip().upper()
    value = re.sub(r"\s+", " ", value)
    value = value.replace("\u2019", "'").replace("\u2013", "-")
    return value


def slugify(value: object) -> str:
    value = clean_text(value)
    value = re.sub(r"[^A-Z0-9]+", "_", value)
    return value.strip("_")


def normalise_party(party_raw: object) -> str:
    party_clean = clean_text(party_raw)

    if party_clean in KNOWN_PARTY_ALIASES:
        return KNOWN_PARTY_ALIASES[party_clean]

    # ECI usually already gives clean abbreviations like BJP, INC, AIFB, etc.
    if len(party_clean) <= 15 and " " not in party_clean:
        return party_clean

    return "PARTY_" + slugify(party_clean)[:40]


def main() -> None:
    if not RESULTS_PARQUET.exists():
        raise FileNotFoundError(
            f"{RESULTS_PARQUET} not found. Run `python -m src.database.database_layer` "
            f"first (with ACTIVE_YEAR={ACTIVE_YEAR} in src/config.py)."
        )

    print(f"Reading {RESULTS_PARQUET.name}")
    results = pd.read_parquet(RESULTS_PARQUET)

    results["party_raw"] = results["party"]
    results["party_clean"] = results["party"].apply(clean_text)
    results["party_id"] = results["party"].apply(normalise_party)

    party_master = (
        results[["party_id", "party_clean", "party_raw"]]
        .drop_duplicates()
        .sort_values(["party_id", "party_clean"])
    )

    results.to_parquet(RESULTS_PARQUET, index=False)
    results.to_csv(RESULTS_CSV, index=False)
    party_master.to_csv(PARTY_MASTER_PATH, index=False)

    print(f"Party normalisation complete for {ACTIVE_YEAR}.")
    print(f"  Augmented: {RESULTS_PARQUET.name}, {RESULTS_CSV.name}")
    print(f"  Saved:     {PARTY_MASTER_PATH.name} "
          f"({len(party_master)} unique (party_id, party_clean) rows)")
    print()
    print(party_master.head(20).to_string(index=False))


if __name__ == "__main__":
    main()
