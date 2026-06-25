"""Build Census 2011 district area table from A-01 or compatible raw files."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import pandas as pd

from src.demographics.census.common import (
    CENSUS_DISTRICT_AREA_PATH,
    CENSUS_SOURCE_NAME,
    assign_post_2011_state,
    census_raw_roots,
    ensure_dirs,
    find_raw_file,
    normalize_key,
)

RAW_EXTENSIONS = {".xlsx", ".xls", ".csv"}
AREA_FILE_PATTERNS = ("a01", "area", "population_households_area", "households_area")


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out.columns = [re.sub(r"[^a-z0-9]+", "_", str(col).strip().lower()).strip("_") for col in out.columns]
    return out


def _pick_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    for candidate in candidates:
        if candidate in df.columns:
            return candidate
    return None


def parse_area_table(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == ".csv":
        raw = pd.read_csv(path)
    else:
        xl = pd.ExcelFile(path, engine="calamine")
        sheet = "Data" if "Data" in xl.sheet_names else xl.sheet_names[0]
        raw = pd.read_excel(path, sheet_name=sheet, engine="calamine")

    df = _normalize_columns(raw)

    if "level" in df.columns:
        df = df[df["level"].astype(str).str.upper().eq("DISTRICT")]

    state_col = _pick_column(df, ["state_name", "state", "name_1", "stname"])
    district_col = _pick_column(df, ["district", "district_name", "name", "name_2"])
    area_col = _pick_column(df, ["area_in_sq_km", "area_sq_km", "area", "land_area_sq_km"])

    if state_col is None or district_col is None or area_col is None:
        print(f"  [WARN] Unmapped columns in {path.name}: {list(df.columns)[:20]}")
        return pd.DataFrame()

    rows: list[dict[str, object]] = []
    for _, row in df.iterrows():
        state_raw = str(row[state_col]).strip()
        district_raw = str(row[district_col]).strip()
        area = pd.to_numeric(row[area_col], errors="coerce")
        if pd.isna(area) or area <= 0:
            continue
        state_key = assign_post_2011_state(state_raw.upper(), district_raw.upper())
        rows.append(
            {
                "state": state_key.title(),
                "district": district_raw.title(),
                "state_key": state_key,
                "district_key": normalize_key(district_raw),
                "area_sq_km": float(area),
                "source_name": CENSUS_SOURCE_NAME,
                "source_year": 2011,
                "source_file": path.name,
            }
        )
    return pd.DataFrame(rows)


def find_area_files() -> list[Path]:
    found: list[Path] = []
    seen: set[str] = set()
    for pattern in AREA_FILE_PATTERNS:
        path = find_raw_file(pattern)
        if path is not None and path.name not in seen:
            found.append(path)
            seen.add(path.name)
    for root in census_raw_roots():
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in RAW_EXTENSIONS:
                continue
            name = path.name.lower()
            if any(token in name for token in AREA_FILE_PATTERNS) and path.name not in seen:
                found.append(path)
                seen.add(path.name)
    return found


def build_district_area_table() -> pd.DataFrame:
    ensure_dirs()
    files = find_area_files()
    frames: list[pd.DataFrame] = []
    for path in files:
        print(f"Parsing area file: {path}")
        parsed = parse_area_table(path)
        if not parsed.empty:
            frames.append(parsed)

    if frames:
        output = pd.concat(frames, ignore_index=True)
        output = output.drop_duplicates(["state_key", "district_key"], keep="first")
    else:
        print("No district area files found. Writing empty area table.")
        output = pd.DataFrame(
            columns=[
                "state",
                "district",
                "state_key",
                "district_key",
                "area_sq_km",
                "source_name",
                "source_year",
                "source_file",
            ]
        )

    output = output.sort_values(["state_key", "district_key"]).reset_index(drop=True)
    output.to_csv(CENSUS_DISTRICT_AREA_PATH, index=False)
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    output = build_district_area_table()
    print(f"Wrote {len(output)} district area rows to {CENSUS_DISTRICT_AREA_PATH}")


if __name__ == "__main__":
    main()
