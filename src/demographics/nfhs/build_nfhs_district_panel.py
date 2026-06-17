"""
Build district-level NFHS-4 / NFHS-5 panel from processed district features.

Run as:
    python -m src.demographics.nfhs.build_nfhs_district_panel
"""

from __future__ import annotations

import sys
import warnings
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from src.demographics.nfhs.crosswalk_utils import apply_crosswalk_to_nfhs4, build_nfhs4_crosswalk
from src.demographics.nfhs.panel_utils import (
    PANEL_FEATURE_COLUMNS,
    SURVEY_NFHS4,
    SURVEY_NFHS5,
    is_numeric_district,
    load_nfhs_district_features,
    prepare_district_panel,
)
from src.demographics.nfhs.paths import (
    CENSUS_DISTRICT_DEMOGRAPHICS,
    NFHS4_DISTRICT_CROSSWALK,
    NFHS_DISTRICT_PANEL,
    NHFS_RAW_DIR,
)


def warn_on_raw_sources() -> None:
    if NHFS_RAW_DIR.exists():
        raw_files = sorted(p.name for p in NHFS_RAW_DIR.iterdir() if p.is_file())
        if raw_files:
            print(f"  NHFS raw reference files ({NHFS_RAW_DIR.name}/): {', '.join(raw_files)}")
            print("  (Panel built from processed nfhs_district_features.csv, not raw microdata.)")
    else:
        warnings.warn(f"NHFS raw directory not found: {NHFS_RAW_DIR}")


def print_summary(panel) -> None:
    print("\nDistrict panel summary")
    print(f"  Rows                 : {len(panel)}")
    print(f"  NFHS-4 rows          : {(panel['survey'] == SURVEY_NFHS4).sum()}")
    print(f"  NFHS-5 rows          : {(panel['survey'] == SURVEY_NFHS5).sum()}")
    print(f"  States               : {panel['state'].nunique()}")
    print(f"  District keys        : {panel['district_key'].nunique()}")
    numeric = panel.loc[panel["survey"] == SURVEY_NFHS4, "nfhs4_sdist_code"].notna().sum()
    unmapped = (
        panel.loc[panel["survey"] == SURVEY_NFHS4, "district_name_source"] == "numeric_code_unmapped"
    ).sum()
    if unmapped:
        warnings.warn(f"{unmapped} NFHS-4 rows still use unresolved numeric district codes.")
    if numeric:
        print(f"  NFHS-4 sdist codes tracked : {int(numeric)}")
        print(f"  NFHS-4 unresolved codes    : {int(unmapped)}")
    print("\n  Missing share by feature:")
    for col in PANEL_FEATURE_COLUMNS:
        if col in panel.columns:
            print(f"    {col:32s} {panel[col].isna().mean() * 100:5.1f}%")


def main() -> None:
    print("Building NFHS district panel...")
    warn_on_raw_sources()

    raw = load_nfhs_district_features()
    panel = prepare_district_panel(raw)

    if CENSUS_DISTRICT_DEMOGRAPHICS.exists():
        if NFHS4_DISTRICT_CROSSWALK.exists():
            crosswalk = pd.read_csv(NFHS4_DISTRICT_CROSSWALK)
            print(f"  Loaded crosswalk: {NFHS4_DISTRICT_CROSSWALK.name}")
        else:
            print("  Building NFHS-4 district code crosswalk...")
            census = pd.read_csv(CENSUS_DISTRICT_DEMOGRAPHICS)
            crosswalk = build_nfhs4_crosswalk(raw, census)
            NFHS4_DISTRICT_CROSSWALK.parent.mkdir(parents=True, exist_ok=True)
            crosswalk.to_csv(NFHS4_DISTRICT_CROSSWALK, index=False)
            print(f"  Saved crosswalk: {NFHS4_DISTRICT_CROSSWALK}")
        panel = apply_crosswalk_to_nfhs4(panel, crosswalk)
    else:
        print(f"  WARNING: No census districts at {CENSUS_DISTRICT_DEMOGRAPHICS}; NFHS-4 codes not resolved.")

    NFHS_DISTRICT_PANEL.parent.mkdir(parents=True, exist_ok=True)
    panel.to_csv(NFHS_DISTRICT_PANEL, index=False)
    print(f"\nSaved: {NFHS_DISTRICT_PANEL} ({len(panel)} rows)")
    print_summary(panel)


if __name__ == "__main__":
    main()
