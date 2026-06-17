"""
Build NFHS-4 sdist code → district name crosswalk.

Uses Census 2011 district ordering within state, validated against NFHS-5
district labels where available, with feature-matching fallback.

Run as:
    python -m src.demographics.nfhs.build_nfhs4_district_crosswalk
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from src.demographics.nfhs.crosswalk_utils import build_nfhs4_crosswalk
from src.demographics.nfhs.panel_utils import load_nfhs_district_features
from src.demographics.nfhs.paths import CENSUS_DISTRICT_DEMOGRAPHICS, NFHS4_DISTRICT_CROSSWALK


def main() -> None:
    print("Building NFHS-4 district code crosswalk...")

    district_features = load_nfhs_district_features()
    if not CENSUS_DISTRICT_DEMOGRAPHICS.exists():
        raise FileNotFoundError(
            f"Missing census districts: {CENSUS_DISTRICT_DEMOGRAPHICS}\n"
            "Run: python -m src.demographics.clean_census_district_2011"
        )

    census = pd.read_csv(CENSUS_DISTRICT_DEMOGRAPHICS)
    crosswalk = build_nfhs4_crosswalk(district_features, census)

    NFHS4_DISTRICT_CROSSWALK.parent.mkdir(parents=True, exist_ok=True)
    crosswalk.to_csv(NFHS4_DISTRICT_CROSSWALK, index=False)
    print(f"\nSaved: {NFHS4_DISTRICT_CROSSWALK} ({len(crosswalk)} rows)")

    print("\nCrosswalk summary")
    print(f"  Resolved to name     : {(crosswalk['district_resolved'].astype(str).str.len() > 0).sum()}")
    print(f"  High confidence      : {(crosswalk['confidence'] == 'high').sum()}")
    print(f"  Medium confidence    : {(crosswalk['confidence'] == 'medium').sum()}")
    print(f"  Low / unmapped       : {(crosswalk['confidence'] == 'low').sum()}")
    print("\n  By mapping method:")
    for method, n in crosswalk["mapping_method"].value_counts().items():
        print(f"    {method:28s} {n}")


if __name__ == "__main__":
    main()
