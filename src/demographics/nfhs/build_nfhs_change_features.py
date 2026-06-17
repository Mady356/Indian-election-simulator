"""
Build NFHS-4 → NFHS-5 district change features from the district panel.

Run as:
    python -m src.demographics.nfhs.build_nfhs_change_features
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from src.demographics.nfhs.panel_utils import (
    PANEL_FEATURE_COLUMNS,
    build_district_change_features,
    load_nfhs_district_features,
    prepare_district_panel,
)
from src.demographics.nfhs.paths import NFHS_DISTRICT_CHANGE, NFHS_DISTRICT_PANEL


def load_panel() -> pd.DataFrame:
    if NFHS_DISTRICT_PANEL.exists():
        return pd.read_csv(NFHS_DISTRICT_PANEL)
    raw = load_nfhs_district_features()
    return prepare_district_panel(raw)


def print_summary(changes: pd.DataFrame) -> None:
    print("\nDistrict change summary")
    print(f"  Rows                         : {len(changes)}")
    both = changes["has_nfhs4"] & changes["has_nfhs5"]
    print(f"  Both rounds present          : {both.sum()}")
    print(f"  NFHS-4 only                  : {(changes['has_nfhs4'] & ~changes['has_nfhs5']).sum()}")
    print(f"  NFHS-5 only                  : {(~changes['has_nfhs4'] & changes['has_nfhs5']).sum()}")
    if "change_quality_flag" in changes.columns:
        print("\n  change_quality_flag:")
        for flag, n in changes["change_quality_flag"].value_counts().items():
            print(f"    {flag:8s} {n}")
    if both.any():
        print("\n  Change features available (both rounds):")
        subset = changes.loc[both]
        for col in PANEL_FEATURE_COLUMNS:
            change_col = f"{col}_change"
            if change_col in subset.columns:
                avail = subset[change_col].notna().mean() * 100
                print(f"    {change_col:40s} {avail:5.1f}%")


def main() -> None:
    print("Building NFHS district change features...")
    panel = load_panel()
    changes = build_district_change_features(panel)

    NFHS_DISTRICT_CHANGE.parent.mkdir(parents=True, exist_ok=True)
    changes.to_csv(NFHS_DISTRICT_CHANGE, index=False)
    print(f"\nSaved: {NFHS_DISTRICT_CHANGE} ({len(changes)} rows)")
    print_summary(changes)


if __name__ == "__main__":
    main()
