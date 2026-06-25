"""Build Census 2011 district-level core demographic table."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import numpy as np
import pandas as pd

from src.demographics.census.common import (
    CENSUS_DISTRICT_AREA_PATH,
    CENSUS_DISTRICT_CORE_PATH,
    CENSUS_SOURCE_NAME,
    PROCESSED_DISTRICT_CENSUS_PATH,
    assign_post_2011_state,
    ensure_dirs,
    find_raw_file,
    join_district_area,
    normalize_key,
)

CORE_COLUMN_MAP = {
    "state": ["state", "state_2011", "state_name"],
    "district": ["district", "district_name", "name"],
    "total_population": ["total_population", "population_total", "tot_p", "population"],
    "urban_population": ["urban_population", "urban_pop", "urban"],
    "rural_population": ["rural_population", "rural_pop", "rural"],
    "urban_pct": ["urban_pct", "urban_percent", "urban_percentage"],
    "literacy_rate": ["literacy_rate", "literacy_pct", "literacy"],
    "female_literacy_pct": ["female_literacy_pct", "female_literacy", "f_literacy"],
    "male_literacy_pct": ["male_literacy_pct", "male_literacy", "m_literacy"],
    "sc_population": ["sc_population", "sc_pop", "p_sc"],
    "st_population": ["st_population", "st_pop", "p_st"],
    "sc_pct": ["sc_pct", "sc_percent"],
    "st_pct": ["st_pct", "st_percent"],
    "area_sq_km": ["area_sq_km", "area", "area_in_sq_km"],
    "population_density": ["population_density", "density"],
    "sex_ratio": ["sex_ratio", "sex_ratio_females_per_1000_males"],
}


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out.columns = [re.sub(r"[^a-z0-9]+", "_", str(col).strip().lower()).strip("_") for col in out.columns]
    return out


def _pick_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    for candidate in candidates:
        if candidate in df.columns:
            return candidate
    return None


def _ratio(numerator: pd.Series, denominator: pd.Series, multiplier: float = 100.0) -> pd.Series:
    numerator = pd.to_numeric(numerator, errors="coerce")
    denominator = pd.to_numeric(denominator, errors="coerce")
    return np.where(denominator > 0, numerator / denominator * multiplier, np.nan)


def build_from_processed(processed: pd.DataFrame, source_file: str) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for _, row in processed.iterrows():
        state_2011 = str(row.get("state_2011", ""))
        district = str(row.get("district", ""))
        state = assign_post_2011_state(state_2011, district)
        total_pop = row.get("population_total")
        area = row.get("area_sq_km") if "area_sq_km" in processed.columns else np.nan
        density = row.get("population_density")
        if pd.isna(density) and pd.notna(area) and float(area) > 0 and pd.notna(total_pop):
            density = float(total_pop) / float(area)

        rows.append(
            {
                "state": state.title() if state else state,
                "district": district.title() if district else district,
                "state_key": state,
                "district_key": normalize_key(district),
                "total_population": total_pop,
                "urban_population": row.get("urban_population"),
                "rural_population": row.get("rural_population"),
                "urban_pct": row.get("urban_pct"),
                "literacy_rate": row.get("literacy_rate"),
                "female_literacy_pct": row.get("female_literacy"),
                "male_literacy_pct": row.get("male_literacy"),
                "sc_population": row.get("sc_population"),
                "st_population": row.get("st_population"),
                "sc_pct": row.get("sc_pct"),
                "st_pct": row.get("st_pct"),
                "area_sq_km": area,
                "population_density": density,
                "sex_ratio": row.get("sex_ratio"),
                "source_name": CENSUS_SOURCE_NAME,
                "source_year": 2011,
                "source_file": source_file,
            }
        )
    return pd.DataFrame(rows)


def build_from_raw_pca(path: Path) -> pd.DataFrame:
    raw = pd.read_excel(path, sheet_name="Data", engine="calamine")
    districts = raw[raw["Level"].astype(str).str.upper().eq("DISTRICT")].copy()
    total = districts[districts["TRU"].eq("Total")].copy()
    rural = districts[districts["TRU"].eq("Rural")][["State", "District", "TOT_P"]].rename(
        columns={"TOT_P": "rural_population"}
    )
    urban = districts[districts["TRU"].eq("Urban")][["State", "District", "TOT_P"]].rename(
        columns={"TOT_P": "urban_population"}
    )
    merged = total.merge(rural, on=["State", "District"], how="left").merge(
        urban, on=["State", "District"], how="left"
    )
    state_lookup = (
        raw[raw["Level"].astype(str).str.upper().eq("STATE")]
        .drop_duplicates("State")
        .set_index("State")["Name"]
    )
    merged["state_2011"] = merged["State"].map(state_lookup).map(lambda value: str(value).strip().upper())
    merged["district"] = merged["Name"].map(lambda value: str(value).strip().upper())
    merged["population_total"] = merged["TOT_P"]
    merged["sc_population"] = merged["P_SC"]
    merged["st_population"] = merged["P_ST"]
    merged["literates_total"] = merged["P_LIT"]
    merged["male_literates"] = merged["M_LIT"]
    merged["female_literates"] = merged["F_LIT"]
    merged["male_population"] = merged["TOT_M"]
    merged["female_population"] = merged["TOT_F"]
    denom = merged["population_total"]
    merged["urban_pct"] = _ratio(merged["urban_population"], denom)
    merged["sc_pct"] = _ratio(merged["sc_population"], denom)
    merged["st_pct"] = _ratio(merged["st_population"], denom)
    merged["sex_ratio"] = _ratio(merged["female_population"], merged["male_population"], 1000.0)
    merged["literacy_rate"] = _ratio(merged["literates_total"], denom)
    merged["male_literacy"] = _ratio(merged["male_literates"], merged["male_population"])
    merged["female_literacy"] = _ratio(merged["female_literates"], merged["female_population"])
    return build_from_processed(merged, str(path.name))


def build_census_district_core() -> pd.DataFrame:
    ensure_dirs()
    if PROCESSED_DISTRICT_CENSUS_PATH.exists():
        print(f"Building district core from processed file: {PROCESSED_DISTRICT_CENSUS_PATH}")
        processed = pd.read_csv(PROCESSED_DISTRICT_CENSUS_PATH)
        output = build_from_processed(processed, PROCESSED_DISTRICT_CENSUS_PATH.name)
    else:
        raw_path = find_raw_file("India State District Population")
        if raw_path is None:
            raise FileNotFoundError(
                "No Census 2011 district PCA file found. Place files under data/demographics/census/raw/ "
                "or run src.demographics.clean_census_district_2011 first."
            )
        print(f"Building district core from raw PCA: {raw_path}")
        output = build_from_raw_pca(raw_path)

    output = output.sort_values(["state_key", "district_key"]).reset_index(drop=True)
    if CENSUS_DISTRICT_AREA_PATH.exists():
        area_table = pd.read_csv(CENSUS_DISTRICT_AREA_PATH)
        output = join_district_area(output, area_table)
    output.to_csv(CENSUS_DISTRICT_CORE_PATH, index=False)
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    output = build_census_district_core()
    print(f"Wrote {len(output)} district rows to {CENSUS_DISTRICT_CORE_PATH}")
    missing_density = int(output["population_density"].isna().sum())
    if missing_density:
        print(f"  Note: {missing_density} districts missing area/density (not in PCA workbook)")


if __name__ == "__main__":
    main()
