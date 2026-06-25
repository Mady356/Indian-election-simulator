"""Build Census 2011 district-level religion table."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import numpy as np
import pandas as pd

from src.demographics.census.common import (
    CENSUS_DISTRICT_RELIGION_PATH,
    CENSUS_SOURCE_NAME,
    PROCESSED_DISTRICT_CENSUS_PATH,
    assign_post_2011_state,
    ensure_dirs,
    find_c01_religion_files,
    normalize_key,
)

RELIGION_OUTPUT_COLUMNS = [
    "state",
    "district",
    "state_key",
    "district_key",
    "total_population",
    "hindu_population",
    "muslim_population",
    "christian_population",
    "sikh_population",
    "religion_hindu_pct",
    "religion_muslim_pct",
    "religion_christian_pct",
    "religion_sikh_pct",
    "source_name",
    "source_year",
    "source_file",
]

STATE_CODE_FROM_FILENAME = re.compile(r"DDW(\d{2})C-01", re.IGNORECASE)


def _ratio(numerator: pd.Series, denominator: pd.Series, multiplier: float = 100.0) -> pd.Series:
    numerator = pd.to_numeric(numerator, errors="coerce")
    denominator = pd.to_numeric(denominator, errors="coerce")
    return np.where(denominator > 0, numerator / denominator * multiplier, np.nan)


def _normalize_code(value: object, width: int) -> str:
    text = str(value).strip()
    if text.lower() in {"", "nan", "none"}:
        return ""
    if text.endswith(".0"):
        text = text[:-2]
    return text.zfill(width)


def _is_district_total_row(row: pd.Series) -> bool:
    district_code = _normalize_code(row.get("col_2"), 3)
    tehsil_code = _normalize_code(row.get("col_3"), 5)
    town_code = _normalize_code(row.get("col_4"), 6)
    area_type = str(row.get("col_6", "")).strip()
    if not district_code or district_code == "000":
        return False
    if tehsil_code not in {"", "00000"}:
        return False
    if town_code not in {"", "000000"}:
        return False
    return area_type == "Total"


def parse_ddw_religion(path: Path) -> pd.DataFrame:
    """Parse a state-level DDWxxC-01 MDDS file, keeping district totals only."""
    raw = pd.read_excel(path, header=None)
    rows = raw.iloc[7:].copy()
    rows.columns = [f"col_{idx}" for idx in range(len(rows.columns))]

    filename_state_code = ""
    match = STATE_CODE_FROM_FILENAME.search(path.name)
    if match:
        filename_state_code = match.group(1)

    records: list[dict[str, object]] = []
    for _, row in rows.iterrows():
        if not _is_district_total_row(row):
            continue

        state_code = _normalize_code(row.get("col_1"), 2) or filename_state_code
        district_code = _normalize_code(row.get("col_2"), 3)
        total = pd.to_numeric(row.get("col_7"), errors="coerce")
        hindu = pd.to_numeric(row.get("col_10"), errors="coerce")
        muslim = pd.to_numeric(row.get("col_13"), errors="coerce")
        christian = pd.to_numeric(row.get("col_16"), errors="coerce")
        sikh = pd.to_numeric(row.get("col_19"), errors="coerce")
        if pd.isna(total):
            continue

        records.append(
            {
                "state_code": state_code,
                "district_code": district_code,
                "total_population": total,
                "hindu_population": hindu,
                "muslim_population": muslim,
                "christian_population": christian,
                "sikh_population": sikh,
                "source_file": path.name,
            }
        )

    if not records:
        return pd.DataFrame()

    out = pd.DataFrame(records)
    out["religion_hindu_pct"] = _ratio(out["hindu_population"], out["total_population"])
    out["religion_muslim_pct"] = _ratio(out["muslim_population"], out["total_population"])
    out["religion_christian_pct"] = _ratio(out["christian_population"], out["total_population"])
    out["religion_sikh_pct"] = _ratio(out["sikh_population"], out["total_population"])
    return out


def attach_district_names(religion: pd.DataFrame, processed: pd.DataFrame) -> pd.DataFrame:
    if religion.empty or processed.empty:
        return pd.DataFrame(columns=RELIGION_OUTPUT_COLUMNS)

    lookup = processed.drop_duplicates(["state_code_2011", "district_code_2011"]).copy()
    lookup["state_code_2011"] = lookup["state_code_2011"].astype(str).str.zfill(2)
    lookup["district_code_2011"] = lookup["district_code_2011"].astype(str).str.zfill(3)

    religion = religion.copy()
    religion["state_code"] = religion["state_code"].astype(str).str.zfill(2)
    religion["district_code"] = religion["district_code"].astype(str).str.zfill(3)

    merged = religion.merge(
        lookup,
        left_on=["state_code", "district_code"],
        right_on=["state_code_2011", "district_code_2011"],
        how="left",
    )

    rows: list[dict[str, object]] = []
    for _, row in merged.iterrows():
        state_2011 = str(row.get("state_2011", ""))
        district = str(row.get("district", ""))
        if not district:
            continue
        state = assign_post_2011_state(state_2011, district)
        rows.append(
            {
                "state": state.title(),
                "district": district.title(),
                "state_key": state,
                "district_key": normalize_key(district),
                "total_population": row.get("total_population"),
                "hindu_population": row.get("hindu_population"),
                "muslim_population": row.get("muslim_population"),
                "christian_population": row.get("christian_population"),
                "sikh_population": row.get("sikh_population"),
                "religion_hindu_pct": row.get("religion_hindu_pct"),
                "religion_muslim_pct": row.get("religion_muslim_pct"),
                "religion_christian_pct": row.get("religion_christian_pct"),
                "religion_sikh_pct": row.get("religion_sikh_pct"),
                "source_name": CENSUS_SOURCE_NAME,
                "source_year": 2011,
                "source_file": row.get("source_file", ""),
            }
        )

    output = pd.DataFrame(rows)
    if output.empty:
        return output
    return output.drop_duplicates(["state_key", "district_key"], keep="first")


def build_census_district_religion() -> pd.DataFrame:
    ensure_dirs()
    processed = pd.read_csv(PROCESSED_DISTRICT_CENSUS_PATH) if PROCESSED_DISTRICT_CENSUS_PATH.exists() else pd.DataFrame()
    religion_files = find_c01_religion_files()

    if not religion_files:
        print("No state-level C-01 religion files found (DDWxxC-01, excluding DDW00C-01).")
        print(f"  Expected under: data/demographics/census/raw/religion/")
        print("  Run: python -m src.demographics.census.download_c01_religion_files")
        output = pd.DataFrame(columns=RELIGION_OUTPUT_COLUMNS)
        output.to_csv(CENSUS_DISTRICT_RELIGION_PATH, index=False)
        return output

    frames: list[pd.DataFrame] = []
    for path in religion_files:
        print(f"Parsing religion file: {path}")
        parsed = parse_ddw_religion(path)
        if parsed.empty:
            print(f"  No district-level rows in {path.name}")
            continue
        named = attach_district_names(parsed, processed)
        print(f"  District religion rows: {len(named)}")
        if not named.empty:
            frames.append(named)

    if frames:
        output = pd.concat(frames, ignore_index=True)
        output = output.drop_duplicates(["state_key", "district_key"], keep="first")
        output = output.sort_values(["state_key", "district_key"]).reset_index(drop=True)
    else:
        print("District-level religion rows not found in uploaded C-01 files.")
        output = pd.DataFrame(columns=RELIGION_OUTPUT_COLUMNS)

    output.to_csv(CENSUS_DISTRICT_RELIGION_PATH, index=False)
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    output = build_census_district_religion()
    print(f"Wrote {len(output)} district religion rows to {CENSUS_DISTRICT_RELIGION_PATH}")


if __name__ == "__main__":
    main()
