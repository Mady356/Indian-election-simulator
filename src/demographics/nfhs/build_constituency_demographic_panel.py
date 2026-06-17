"""
Build constituency-level NFHS demographic panels via weighted district aggregation.

Run as:
    python -m src.demographics.nfhs.build_constituency_demographic_panel
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from src.demographics.nfhs.panel_utils import (
    SURVEY_NFHS4,
    SURVEY_NFHS5,
    aggregate_constituency_survey,
    build_constituency_change_features,
    load_nfhs_district_features,
    prepare_district_panel,
)
from src.demographics.nfhs.paths import (
    CONSTITUENCY_DEMOGRAPHIC_CHANGE,
    CONSTITUENCY_DEMOGRAPHIC_PANEL,
    LOK_SABHA_DISTRICT_SUMMARY,
    NFHS_DISTRICT_PANEL,
)


def load_district_panel() -> pd.DataFrame:
    if NFHS_DISTRICT_PANEL.exists():
        return pd.read_csv(NFHS_DISTRICT_PANEL)
    return prepare_district_panel(load_nfhs_district_features())


def load_crosswalk() -> pd.DataFrame:
    if not LOK_SABHA_DISTRICT_SUMMARY.exists():
        raise FileNotFoundError(
            f"Missing delimitation crosswalk: {LOK_SABHA_DISTRICT_SUMMARY}\n"
            "Run the delimitation reference pipeline first."
        )
    return pd.read_csv(LOK_SABHA_DISTRICT_SUMMARY)


def print_summary(panel: pd.DataFrame) -> None:
    print("\nConstituency panel summary")
    print(f"  Rows                 : {len(panel)}")
    for survey in (SURVEY_NFHS4, SURVEY_NFHS5):
        sub = panel[panel["survey"] == survey]
        print(f"  {survey} rows          : {len(sub)}")
    print(f"  Constituencies       : {panel.groupby(['state', 'lok_sabha_constituency']).ngroups}")
    if "coverage_share" in panel.columns:
        low = panel[panel["coverage_share"] < 0.85]
        print(f"  Low coverage (<85%)  : {len(low)}")
        if not low.empty:
            print("\n  Top low-coverage constituencies:")
            top = low.nsmallest(10, "coverage_share")
            for _, r in top.iterrows():
                print(
                    f"    {r['state']} / {r['lok_sabha_constituency']} "
                    f"({r['survey']}): {r['coverage_share']:.2f}"
                )


def main() -> None:
    print("Building constituency demographic panel...")
    crosswalk = load_crosswalk()
    district_panel = load_district_panel()

    frames = [
        aggregate_constituency_survey(crosswalk, district_panel, SURVEY_NFHS4),
        aggregate_constituency_survey(crosswalk, district_panel, SURVEY_NFHS5),
    ]
    panel = pd.concat(frames, ignore_index=True)

    CONSTITUENCY_DEMOGRAPHIC_PANEL.parent.mkdir(parents=True, exist_ok=True)
    panel.to_csv(CONSTITUENCY_DEMOGRAPHIC_PANEL, index=False)
    print(f"\nSaved: {CONSTITUENCY_DEMOGRAPHIC_PANEL} ({len(panel)} rows)")

    changes = build_constituency_change_features(panel)
    changes.to_csv(CONSTITUENCY_DEMOGRAPHIC_CHANGE, index=False)
    print(f"Saved: {CONSTITUENCY_DEMOGRAPHIC_CHANGE} ({len(changes)} rows)")

    print_summary(panel)


if __name__ == "__main__":
    main()
