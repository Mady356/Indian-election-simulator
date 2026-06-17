"""
Build a district-level demographic master table from NFHS and Census sources.

Merges existing processed NFHS district/state features with Census 2011 district
rows when available. Does not impute missing values.

Run as:
    python -m src.demographics.build_district_master_table

Output:
    data/demographics/processed/district_master_table.csv
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.config import DEMOGRAPHICS_PROCESSED_DIR
from src.demographics.dhs.paths import (
    DISTRICT_MASTER_COLUMNS,
    DISTRICT_MASTER_TABLE,
    NFHS_DISTRICT_FEATURES,
    NFHS_STATE_FEATURES,
)

CENSUS_STATE_PATH = DEMOGRAPHICS_PROCESSED_DIR / "census_state_demographics_2011.csv"
CENSUS_DISTRICT_PATH = DEMOGRAPHICS_PROCESSED_DIR / "census_district_demographics_2011.csv"

NFHS_METRIC_COLUMNS = [
    "fertility_rate",
    "electricity_pct",
    "improved_sanitation_pct",
    "lpg_pct",
    "mobile_phone_pct",
    "bank_account_pct",
    "women_secondary_edu_pct",
    "female_literacy_pct",
    "male_literacy_pct",
    "wealth_index_mean",
    "urban_pct",
]


def normalize_key(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip().upper()
    text = re.sub(r"[^A-Z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def make_district_id(state: object, district: object) -> str:
    state_key = normalize_key(state).replace(" ", "_")
    district_key = normalize_key(district).replace(" ", "_")
    if not state_key or not district_key:
        return ""
    return f"{state_key}__{district_key}"


def title_case_label(value: object) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip().title()


def load_nfhs_district() -> pd.DataFrame:
    if not NFHS_DISTRICT_FEATURES.exists():
        print(f"  Missing: {NFHS_DISTRICT_FEATURES}")
        return pd.DataFrame(columns=DISTRICT_MASTER_COLUMNS)
    df = pd.read_csv(NFHS_DISTRICT_FEATURES)
    if df.empty:
        return df
    df["state"] = df["state"].map(title_case_label)
    df["district"] = df["district"].astype(str).str.strip()
    df["district_id"] = df.apply(lambda r: make_district_id(r["state"], r["district"]), axis=1)
    return df


def load_census_district() -> pd.DataFrame:
    if not CENSUS_DISTRICT_PATH.exists():
        print(f"  Missing (optional): {CENSUS_DISTRICT_PATH}")
        return pd.DataFrame()
    df = pd.read_csv(CENSUS_DISTRICT_PATH)
    df["state"] = df["state_2011"].map(title_case_label)
    df["district"] = df["district"].map(title_case_label)
    df["district_id"] = df.apply(lambda r: make_district_id(r["state"], r["district"]), axis=1)
    rename = {
        "female_literacy": "female_literacy_pct",
        "male_literacy": "male_literacy_pct",
        "literacy_rate": "literacy_rate_pct",
        "urban_pct": "census_urban_pct",
    }
    return df.rename(columns=rename)


def enrich_from_census(master: pd.DataFrame, census: pd.DataFrame) -> pd.DataFrame:
    """Fill NFHS gaps with Census district literacy/urban only when NFHS is missing."""
    if census.empty or master.empty:
        return master

    census_sub = census[
        [
            c
            for c in (
                "district_id",
                "female_literacy_pct",
                "male_literacy_pct",
                "census_urban_pct",
            )
            if c in census.columns
        ]
    ].rename(
        columns={
            "female_literacy_pct": "_census_female_literacy",
            "male_literacy_pct": "_census_male_literacy",
            "census_urban_pct": "_census_urban",
        }
    )
    merged = master.merge(census_sub, on="district_id", how="left")

    if "_census_female_literacy" in merged.columns:
        merged["female_literacy_pct"] = merged["female_literacy_pct"].where(
            merged["female_literacy_pct"].notna(), merged["_census_female_literacy"]
        )
    if "_census_male_literacy" in merged.columns:
        merged["male_literacy_pct"] = merged["male_literacy_pct"].where(
            merged["male_literacy_pct"].notna(), merged["_census_male_literacy"]
        )
    if "_census_urban" in merged.columns:
        merged["urban_pct"] = merged["urban_pct"].where(
            merged["urban_pct"].notna(), merged["_census_urban"]
        )

    drop_cols = [c for c in merged.columns if c.startswith("_census_")]
    return merged.drop(columns=drop_cols)


def build_master_table() -> pd.DataFrame:
    nfhs = load_nfhs_district()
    census = load_census_district()

    if nfhs.empty:
        print("  No NFHS district features — writing empty template.")
        return pd.DataFrame(columns=DISTRICT_MASTER_COLUMNS)

    keep = [c for c in DISTRICT_MASTER_COLUMNS if c in nfhs.columns]
    master = nfhs[keep].copy()
    for col in DISTRICT_MASTER_COLUMNS:
        if col not in master.columns:
            master[col] = np.nan

    master = enrich_from_census(master, census)
    master = master[DISTRICT_MASTER_COLUMNS]
    master = master.drop_duplicates(subset=["district_id", "survey"], keep="last")
    master = master.sort_values(["state", "district", "survey_year"])
    return master


def print_validation(df: pd.DataFrame) -> None:
    print("\nValidation")
    print(f"  District rows          : {len(df)}")
    print(f"  Unique district_id     : {df['district_id'].nunique() if not df.empty else 0}")
    print(f"  Surveys                : {df['survey'].dropna().unique().tolist() if not df.empty else []}")

    if df.empty:
        return

    print("\n  Missing share by demographic variable:")
    for col in NFHS_METRIC_COLUMNS:
        if col in df.columns:
            pct = df[col].isna().mean() * 100
            print(f"    {col:30s} {pct:5.1f}%")


def main() -> None:
    print("Building district master table...")
    if NFHS_STATE_FEATURES.exists():
        state_df = pd.read_csv(NFHS_STATE_FEATURES)
        print(f"  Loaded state features: {len(state_df)} rows (reference only)")
    else:
        print(f"  Missing (optional): {NFHS_STATE_FEATURES}")

    if CENSUS_STATE_PATH.exists():
        print(f"  Loaded census state: {CENSUS_STATE_PATH.name}")
    else:
        print(f"  Missing (optional): {CENSUS_STATE_PATH}")

    df = build_master_table()
    DISTRICT_MASTER_TABLE.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(DISTRICT_MASTER_TABLE, index=False)
    print(f"\nSaved: {DISTRICT_MASTER_TABLE} ({len(df)} rows)")
    print_validation(df)


if __name__ == "__main__":
    main()
