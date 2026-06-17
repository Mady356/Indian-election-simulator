"""
Build a district-to-Lok Sabha constituency crosswalk (many-to-many).

This is a **temporary approximate mapping** based on name matching. Later,
replace with GIS overlap analysis:

    Lok Sabha constituency polygon × district polygon
    -> district_weight_in_constituency

Run as:
    python -m src.reference.build_district_constituency_crosswalk

Output:
    data/reference/district_constituency_crosswalk.csv

Columns include optional future GIS fields (left blank for now):
    district_weight_estimate, overlap_method, source
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.config import DATABASE_DIR, DEMOGRAPHICS_PROCESSED_DIR, ELECTION_TYPE, REFERENCE_DIR

CROSSWALK_PATH = REFERENCE_DIR / "district_constituency_crosswalk.csv"
CENSUS_DISTRICT_PATH = DEMOGRAPHICS_PROCESSED_DIR / "census_district_demographics_2011.csv"
NFHS_DISTRICT_PATH = DEMOGRAPHICS_PROCESSED_DIR / "nfhs_district_features.csv"

CROSSWALK_COLUMNS = [
    "election_type",
    "state",
    "constituency_id",
    "constituency",
    "district",
    "district_role",
    "mapping_confidence",
    "notes",
    "district_weight_estimate",
    "overlap_method",
    "source",
]

ELECTION_YEARS = (2019, 2024)


def normalize_name(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip().upper()
    text = text.replace("&", " AND ")
    text = re.sub(r"[^A-Z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def load_constituencies(year: int) -> pd.DataFrame:
    path = DATABASE_DIR / f"constituency_table_{year}.csv"
    if not path.exists():
        print(f"  SKIP {year}: missing {path.name}")
        return pd.DataFrame()
    df = pd.read_csv(path)
    required = {"constituency_id", "state", "constituency"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"{path.name} missing columns: {sorted(missing)}")
    df["election_year"] = year
    return df


def load_district_names() -> pd.DataFrame:
    """District names from Census 2011 processed table (preferred) or NFHS district features."""
    candidates = [
        CENSUS_DISTRICT_PATH,
        NFHS_DISTRICT_PATH,
    ]
    for path in candidates:
        if not path.exists():
            continue
        df = pd.read_csv(path)
        state_col = "state_2011" if "state_2011" in df.columns else "state"
        if state_col not in df.columns or "district" not in df.columns:
            continue
        out = df[[state_col, "district"]].drop_duplicates()
        out = out.rename(columns={state_col: "state"})
        out["state_norm"] = out["state"].map(normalize_name)
        out["district_norm"] = out["district"].map(normalize_name)
        out["source_table"] = path.name
        return out
    print("  WARNING: no district name table found — crosswalk will be template-only.")
    return pd.DataFrame(columns=["state", "district", "state_norm", "district_norm", "source_table"])


def match_districts_for_constituency(
    state_norm: str,
    constituency_norm: str,
    districts: pd.DataFrame,
) -> list[dict[str, object]]:
    """
    Return zero or more district mapping rows for one constituency.

    Supports many-to-many: multiple districts can match one constituency.
    """
    state_districts = districts[districts["state_norm"] == state_norm]
    if state_districts.empty:
        return [
            {
                "district": "",
                "district_role": "unknown",
                "mapping_confidence": "manual_needed",
                "notes": "No district list for this state — fill manually",
            }
        ]

    exact = state_districts[state_districts["district_norm"] == constituency_norm]
    if not exact.empty:
        return [
            {
                "district": row["district"],
                "district_role": "primary",
                "mapping_confidence": "high",
                "notes": "Exact constituency/district name match",
            }
            for _, row in exact.iterrows()
        ]

    contains_matches: list[dict[str, object]] = []
    for _, row in state_districts.iterrows():
        d_norm = row["district_norm"]
        if not d_norm:
            continue
        if d_norm in constituency_norm or constituency_norm in d_norm:
            role = "primary" if len(d_norm) >= len(constituency_norm) * 0.8 else "secondary"
            confidence = "medium"
            contains_matches.append(
                {
                    "district": row["district"],
                    "district_role": "partial" if role == "secondary" else "partial",
                    "mapping_confidence": confidence,
                    "notes": f"Name overlap: constituency='{constituency_norm}' district='{d_norm}'",
                }
            )

    if contains_matches:
        return contains_matches

    return [
        {
            "district": "",
            "district_role": "unknown",
            "mapping_confidence": "manual_needed",
            "notes": "No automatic match — requires manual district assignment or future GIS overlap",
        }
    ]


def build_crosswalk() -> pd.DataFrame:
    constituencies = pd.concat(
        [load_constituencies(y) for y in ELECTION_YEARS],
        ignore_index=True,
    )
    if constituencies.empty:
        print("ERROR: no constituency tables found under data/database/")
        return pd.DataFrame(columns=CROSSWALK_COLUMNS)

    districts = load_district_names()
    rows: list[dict[str, object]] = []

    for _, con in constituencies.iterrows():
        state_norm = normalize_name(con["state"])
        con_norm = normalize_name(con["constituency"])
        matches = match_districts_for_constituency(state_norm, con_norm, districts)

        for match in matches:
            rows.append(
                {
                    "election_type": ELECTION_TYPE,
                    "state": con["state"],
                    "constituency_id": con["constituency_id"],
                    "constituency": con["constituency"],
                    "district": match["district"],
                    "district_role": match["district_role"],
                    "mapping_confidence": match["mapping_confidence"],
                    "notes": match["notes"],
                    "district_weight_estimate": np.nan,
                    "overlap_method": "",
                    "source": f"constituency_table_{int(con['election_year'])}",
                }
            )

    df = pd.DataFrame(rows)
    for col in CROSSWALK_COLUMNS:
        if col not in df.columns:
            df[col] = np.nan
    return df[CROSSWALK_COLUMNS]


def print_validation(df: pd.DataFrame) -> None:
    if df.empty:
        print("  No crosswalk rows produced.")
        return

    con_ids = df["constituency_id"].nunique()
    mapped = df[df["district"].astype(str).str.strip() != ""]["constituency_id"].nunique()
    manual = df[df["mapping_confidence"] == "manual_needed"]["constituency_id"].nunique()

    print("\nValidation")
    print(f"  Crosswalk rows (many-to-many): {len(df)}")
    print(f"  Unique constituencies       : {con_ids}")
    print(f"  Mapped to >=1 district      : {mapped} ({mapped / con_ids * 100:.1f}%)")
    print(f"  Needing manual mapping      : {manual} ({manual / con_ids * 100:.1f}%)")

    unmapped = df[df["mapping_confidence"] == "manual_needed"].groupby("state").size()
    if not unmapped.empty:
        print("\n  Top states with manual_needed constituencies:")
        for state, count in unmapped.sort_values(ascending=False).head(10).items():
            print(f"    {state:30s} {count}")

    multi = df[df["district"].astype(str).str.strip() != ""].groupby("constituency_id").size()
    multi_count = (multi > 1).sum()
    print(f"\n  Constituencies with >1 district row: {multi_count}")


def main() -> None:
    print("Building district-to-constituency crosswalk...")
    print(
        "  NOTE: This is a temporary name-based mapping. "
        "Future GIS overlap should compute district_weight_in_constituency."
    )

    df = build_crosswalk()
    REFERENCE_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(CROSSWALK_PATH, index=False)
    print(f"\nSaved: {CROSSWALK_PATH} ({len(df)} rows)")
    print_validation(df)


if __name__ == "__main__":
    main()
