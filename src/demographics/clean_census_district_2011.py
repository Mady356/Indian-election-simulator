"""
Clean Census 2011 district-level PCA population data.

Run as:
    venv/bin/python -m src.demographics.clean_census_district_2011

Reads:
    India State District Population 2011.xlsx

Writes:
    data/demographics/processed/census_district_demographics_2011.csv
    data/demographics/processed/census_state_from_districts_2011.csv
    data/demographics/processed/state_demographics_master.csv

This cleaner uses district PCA rows to create a proper post-2011 state/UT
rollup for Telangana and Ladakh. It only writes variables that this workbook
actually supports; religion, detailed age, NFHS, and density remain separate
inputs.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.config import DEMOGRAPHICS_PROCESSED_DIR, LEGACY_CENSUS_2011_DIRS
from src.demographics.demographic_catalog import STATE_DEMOGRAPHICS_MASTER_COLUMNS


RAW_FILE_PATTERN = "India State District Population"
DISTRICT_OUT = DEMOGRAPHICS_PROCESSED_DIR / "census_district_demographics_2011.csv"
STATE_FROM_DISTRICTS_OUT = DEMOGRAPHICS_PROCESSED_DIR / "census_state_from_districts_2011.csv"
STATE_MASTER_OUT = DEMOGRAPHICS_PROCESSED_DIR / "state_demographics_master.csv"

RAW_EXTENSIONS = {".xlsx", ".xls", ".csv"}

TELANGANA_DISTRICTS = {
    "ADILABAD",
    "NIZAMABAD",
    "KARIMNAGAR",
    "MEDAK",
    "HYDERABAD",
    "RANGAREDDY",
    "MAHBUBNAGAR",
    "NALGONDA",
    "WARANGAL",
    "KHAMMAM",
}

LADAKH_DISTRICTS = {
    "LEH(LADAKH)",
    "KARGIL",
}

PCA_STATE_COLUMNS = [
    "state",
    "census_state_code",
    "population_total",
    "urban_pct",
    "rural_pct",
    "sc_pct",
    "st_pct",
    "sex_ratio",
    "literacy_rate",
    "male_literacy",
    "female_literacy",
]

PCA_ONLY_COLUMNS = [
    "population_total",
    "urban_pct",
    "rural_pct",
    "sc_pct",
    "st_pct",
    "sex_ratio",
    "literacy_rate",
    "male_literacy",
    "female_literacy",
]

SPLIT_STATES = {"ANDHRA PRADESH", "TELANGANA", "JAMMU & KASHMIR", "LADAKH"}
SPLIT_UNSUPPORTED_COLUMNS = [
    "hindu_pct",
    "muslim_pct",
    "christian_pct",
    "sikh_pct",
    "buddhist_pct",
    "jain_pct",
    "youth_pct",
    "working_age_pct",
    "elderly_pct",
]


def clean_name(value: object) -> str:
    if pd.isna(value):
        return ""
    name = str(value).strip().upper()
    name = re.sub(r"\s+", " ", name)
    return name


def find_raw_file() -> Path | None:
    needle = RAW_FILE_PATTERN.lower()
    for root in LEGACY_CENSUS_2011_DIRS:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if path.is_file() and path.suffix.lower() in RAW_EXTENSIONS:
                if needle in path.name.lower():
                    return path
    return None


def ratio(numerator: pd.Series, denominator: pd.Series, multiplier: float = 100.0) -> pd.Series:
    numerator = pd.to_numeric(numerator, errors="coerce")
    denominator = pd.to_numeric(denominator, errors="coerce")
    return np.where(denominator > 0, numerator / denominator * multiplier, np.nan)


def load_pca(path: Path) -> pd.DataFrame:
    return pd.read_excel(path, sheet_name="Data", engine="calamine")


def build_district_table(raw: pd.DataFrame) -> pd.DataFrame:
    districts = raw[raw["Level"].astype(str).str.upper().eq("DISTRICT")].copy()

    total = districts[districts["TRU"].eq("Total")].copy()
    rural = districts[districts["TRU"].eq("Rural")][
        ["State", "District", "TOT_P", "No_HH"]
    ].rename(columns={"TOT_P": "rural_population", "No_HH": "rural_households"})
    urban = districts[districts["TRU"].eq("Urban")][
        ["State", "District", "TOT_P", "No_HH"]
    ].rename(columns={"TOT_P": "urban_population", "No_HH": "urban_households"})

    out = total.merge(rural, on=["State", "District"], how="left")
    out = out.merge(urban, on=["State", "District"], how="left")

    result = pd.DataFrame(
        {
            "state_code_2011": out["State"],
            "district_code_2011": out["District"],
            "state_2011": out.groupby("State")["Name"].transform("first"),
            "district": out["Name"],
            "population_total": out["TOT_P"],
            "male_population": out["TOT_M"],
            "female_population": out["TOT_F"],
            "households": out["No_HH"],
            "rural_population": out["rural_population"],
            "urban_population": out["urban_population"],
            "rural_households": out["rural_households"],
            "urban_households": out["urban_households"],
            "sc_population": out["P_SC"],
            "st_population": out["P_ST"],
            "literates_total": out["P_LIT"],
            "male_literates": out["M_LIT"],
            "female_literates": out["F_LIT"],
            "age_0_6_population": out["P_06"],
            "workers_total": out["TOT_WORK_P"],
            "main_workers_total": out["MAINWORK_P"],
            "marginal_workers_total": out["MARGWORK_P"],
            "non_workers_total": out["NON_WORK_P"],
        }
    )

    result["state_2011"] = result["state_code_2011"].map(
        raw[raw["Level"].eq("STATE")].drop_duplicates("State").set_index("State")["Name"]
    )
    result["state_2011"] = result["state_2011"].map(clean_name)
    result["district"] = result["district"].map(clean_name)

    denom = result["population_total"]
    result["urban_pct"] = ratio(result["urban_population"], denom)
    result["rural_pct"] = ratio(result["rural_population"], denom)
    result["sc_pct"] = ratio(result["sc_population"], denom)
    result["st_pct"] = ratio(result["st_population"], denom)
    result["sex_ratio"] = ratio(result["female_population"], result["male_population"], 1000.0)
    result["literacy_rate"] = ratio(result["literates_total"], denom)
    result["male_literacy"] = ratio(result["male_literates"], result["male_population"])
    result["female_literacy"] = ratio(result["female_literates"], result["female_population"])
    result["child_0_6_pct"] = ratio(result["age_0_6_population"], denom)
    result["worker_pct"] = ratio(result["workers_total"], denom)
    result["main_worker_pct"] = ratio(result["main_workers_total"], denom)
    result["marginal_worker_pct"] = ratio(result["marginal_workers_total"], denom)
    result["non_worker_pct"] = ratio(result["non_workers_total"], denom)
    result["source_year"] = 2011
    result["geography_level"] = "district"

    return result.sort_values(["state_code_2011", "district_code_2011"]).reset_index(drop=True)


def assign_post_2011_state(row: pd.Series) -> str:
    state = row["state_2011"]
    district = row["district"]

    if state == "ANDHRA PRADESH":
        if district in TELANGANA_DISTRICTS:
            return "TELANGANA"
        return "ANDHRA PRADESH"

    if state == "JAMMU & KASHMIR":
        if district in LADAKH_DISTRICTS:
            return "LADAKH"
        return "JAMMU & KASHMIR"

    return state


def aggregate_group(group: pd.DataFrame) -> pd.Series:
    pop = group["population_total"].sum()
    male = group["male_population"].sum()
    female = group["female_population"].sum()

    return pd.Series(
        {
            "census_state_code": (
                group["state_code_2011"].iloc[0]
                if group["state_code_2011"].nunique() == 1
                else np.nan
            ),
            "district_count_2011": group["district_code_2011"].nunique(),
            "population_total": pop,
            "urban_pct": group["urban_population"].sum() / pop * 100 if pop else np.nan,
            "rural_pct": group["rural_population"].sum() / pop * 100 if pop else np.nan,
            "sc_pct": group["sc_population"].sum() / pop * 100 if pop else np.nan,
            "st_pct": group["st_population"].sum() / pop * 100 if pop else np.nan,
            "sex_ratio": female / male * 1000 if male else np.nan,
            "literacy_rate": group["literates_total"].sum() / pop * 100 if pop else np.nan,
            "male_literacy": group["male_literates"].sum() / male * 100 if male else np.nan,
            "female_literacy": group["female_literates"].sum() / female * 100 if female else np.nan,
            "child_0_6_pct": group["age_0_6_population"].sum() / pop * 100 if pop else np.nan,
            "worker_pct": group["workers_total"].sum() / pop * 100 if pop else np.nan,
            "main_worker_pct": group["main_workers_total"].sum() / pop * 100 if pop else np.nan,
            "marginal_worker_pct": group["marginal_workers_total"].sum() / pop * 100 if pop else np.nan,
            "non_worker_pct": group["non_workers_total"].sum() / pop * 100 if pop else np.nan,
            "source_year": 2011,
            "geography_level": "state_from_districts",
        }
    )


def build_state_from_districts(districts: pd.DataFrame) -> pd.DataFrame:
    out = districts.copy()
    out["state"] = out.apply(assign_post_2011_state, axis=1)

    state = (
        out.groupby("state", as_index=False)
        .apply(aggregate_group, include_groups=False)
        .reset_index(drop=True)
    )
    return state.sort_values("state").reset_index(drop=True)


def update_state_master(state_from_districts: pd.DataFrame) -> pd.DataFrame:
    if STATE_MASTER_OUT.exists():
        master = pd.read_csv(STATE_MASTER_OUT)
    else:
        master = pd.DataFrame(columns=STATE_DEMOGRAPHICS_MASTER_COLUMNS)

    update_cols = ["state", *PCA_ONLY_COLUMNS, "census_state_code"]
    updates = state_from_districts[[c for c in update_cols if c in state_from_districts.columns]].copy()

    merged = master.merge(updates, on="state", how="outer", suffixes=("", "_district"))

    for col in [c for c in update_cols if c != "state"]:
        district_col = f"{col}_district"
        if district_col not in merged.columns:
            continue
        if col in merged.columns:
            merged[col] = merged[district_col].combine_first(merged[col])
        else:
            merged[col] = merged[district_col]
        merged = merged.drop(columns=[district_col])

    # Existing Andhra/J&K religion and age columns came from undivided 2011
    # state geography. Once split rows are introduced, blank these columns for
    # affected states until district-level religion/age cleaners fill them.
    split_mask = merged["state"].isin(SPLIT_STATES)
    for col in SPLIT_UNSUPPORTED_COLUMNS:
        if col in merged.columns:
            merged.loc[split_mask, col] = np.nan

    for col in STATE_DEMOGRAPHICS_MASTER_COLUMNS:
        if col not in merged.columns:
            merged[col] = np.nan

    merged = merged[STATE_DEMOGRAPHICS_MASTER_COLUMNS].sort_values("state").reset_index(drop=True)
    merged.to_csv(STATE_MASTER_OUT, index=False)
    return merged


def print_validation(districts: pd.DataFrame, state_from_districts: pd.DataFrame, master: pd.DataFrame) -> None:
    print("\nValidation")
    print(f"  District rows: {len(districts)}")
    print(f"  State/UT rows from districts: {len(state_from_districts)}")
    print(f"  State master rows: {len(master)}")
    print()
    print("Post-2011 split rows:")
    show_cols = [
        "state",
        "district_count_2011",
        "population_total",
        "urban_pct",
        "sc_pct",
        "st_pct",
        "literacy_rate",
    ]
    print(
        state_from_districts[
            state_from_districts["state"].isin(SPLIT_STATES)
        ][show_cols].to_string(index=False)
    )
    print()
    print("Rows in master with unavailable split-sensitive columns cleared:")
    cols = ["state", "population_total", "urban_pct", "hindu_pct", "muslim_pct", "youth_pct"]
    print(master[master["state"].isin(SPLIT_STATES)][cols].to_string(index=False))


def main() -> None:
    print("Census 2011 district PCA cleaner")
    raw_path = find_raw_file()
    if raw_path is None:
        raise FileNotFoundError(
            "Could not find India State District Population 2011 workbook under "
            "the configured Census raw folders."
        )

    print(f"  Reading: {raw_path}")
    raw = load_pca(raw_path)

    DEMOGRAPHICS_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    districts = build_district_table(raw)
    state_from_districts = build_state_from_districts(districts)
    master = update_state_master(state_from_districts)

    districts.to_csv(DISTRICT_OUT, index=False)
    state_from_districts.to_csv(STATE_FROM_DISTRICTS_OUT, index=False)

    print(f"Saved: {DISTRICT_OUT} ({len(districts)} rows)")
    print(f"Saved: {STATE_FROM_DISTRICTS_OUT} ({len(state_from_districts)} rows)")
    print(f"Updated: {STATE_MASTER_OUT} ({len(master)} rows)")

    print_validation(districts, state_from_districts, master)


if __name__ == "__main__":
    main()
