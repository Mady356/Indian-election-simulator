"""
Validate NFHS panel outputs and write a quality report.

Also builds constituency change features if not already present.

Run as:
    python -m src.demographics.nfhs.validate_nfhs_panel
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from src.demographics.nfhs.panel_utils import (
    PANEL_FEATURE_COLUMNS,
    SURVEY_NFHS4,
    SURVEY_NFHS5,
    build_constituency_change_features,
    missing_share_by_feature,
)
from src.demographics.nfhs.paths import (
    CONSTITUENCY_DEMOGRAPHIC_CHANGE,
    CONSTITUENCY_DEMOGRAPHIC_PANEL,
    NFHS_DISTRICT_CHANGE,
    NFHS_DISTRICT_PANEL,
    NFHS_PANEL_QUALITY_REPORT,
)


def load_csv(path: Path, label: str) -> pd.DataFrame:
    if not path.exists():
        print(f"  WARNING: missing {label}: {path}")
        return pd.DataFrame()
    return pd.read_csv(path)


def dataset_report(name: str, df: pd.DataFrame, entity_cols: dict[str, str]) -> dict:
    if df.empty:
        return {
            "dataset_name": name,
            "row_count": 0,
            "states_covered": 0,
            "districts_covered": 0,
            "constituencies_covered": 0,
            "features_available": "",
            "missing_share_by_feature": "{}",
            "both_rounds_available_count": 0,
            "low_quality_count": 0,
            "notes": "dataset missing or empty",
        }

    missing = missing_share_by_feature(df, PANEL_FEATURE_COLUMNS)
    top_missing = sorted(missing.items(), key=lambda x: x[1], reverse=True)[:5]

    both_rounds = 0
    low_quality = 0
    notes_parts: list[str] = []

    if "has_nfhs4" in df.columns and "has_nfhs5" in df.columns:
        both_rounds = int((df["has_nfhs4"] & df["has_nfhs5"]).sum())
        only_one = int(((df["has_nfhs4"] ^ df["has_nfhs5"]).sum()))
        if only_one:
            notes_parts.append(f"{only_one} rows with only one survey round")
    if "change_quality_flag" in df.columns:
        low_quality = int((df["change_quality_flag"] == "low").sum())
    if "coverage_share" in df.columns:
        low_cov = int((df["coverage_share"] < 0.85).sum())
        if low_cov:
            notes_parts.append(f"{low_cov} rows with coverage_share < 0.85")

    if top_missing:
        notes_parts.append(
            "top missing: "
            + ", ".join(f"{k}={v:.0%}" for k, v in top_missing[:3])
        )

    districts = 0
    if entity_cols.get("district"):
        districts = df[entity_cols["district"]].nunique()

    constituencies = 0
    if entity_cols.get("constituency"):
        constituencies = df.groupby(["state", entity_cols["constituency"]]).ngroups

    return {
        "dataset_name": name,
        "row_count": len(df),
        "states_covered": df["state"].nunique() if "state" in df.columns else 0,
        "districts_covered": districts,
        "constituencies_covered": constituencies,
        "features_available": ", ".join(c for c in PANEL_FEATURE_COLUMNS if c in df.columns),
        "missing_share_by_feature": json.dumps({k: round(v, 4) for k, v in missing.items()}),
        "both_rounds_available_count": both_rounds,
        "low_quality_count": low_quality,
        "notes": "; ".join(notes_parts) if notes_parts else "ok",
    }


def print_validation_summary(
    district_panel: pd.DataFrame,
    district_change: pd.DataFrame,
    constituency_panel: pd.DataFrame,
    constituency_change: pd.DataFrame,
) -> None:
    print("\n" + "=" * 60)
    print("NFHS panel validation")
    print("=" * 60)
    print(f"  District panel rows           : {len(district_panel)}")
    print(f"  District change rows          : {len(district_change)}")
    print(f"  Constituency panel rows       : {len(constituency_panel)}")
    print(f"  Constituency change rows      : {len(constituency_change)}")

    if not district_panel.empty:
        print("\n  District panel — missing share (top features):")
        miss = missing_share_by_feature(district_panel, PANEL_FEATURE_COLUMNS)
        for feat, share in sorted(miss.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"    {feat:32s} {share * 100:5.1f}%")

    if not district_change.empty and {"has_nfhs4", "has_nfhs5"}.issubset(district_change.columns):
        both = district_change["has_nfhs4"] & district_change["has_nfhs5"]
        print(f"\n  Districts with both NFHS rounds: {both.sum()}")

    if not constituency_panel.empty and "coverage_share" in constituency_panel.columns:
        low = constituency_panel.nsmallest(10, "coverage_share")
        print("\n  Top low-coverage constituencies:")
        for _, r in low.iterrows():
            print(
                f"    {r['state']} / {r['lok_sabha_constituency']} "
                f"({r.get('survey', '?')}): {r['coverage_share']:.2f}"
            )

    if not constituency_change.empty and "change_quality_flag" in constituency_change.columns:
        low_q = constituency_change[constituency_change["change_quality_flag"] == "low"]
        print(f"\n  Low-quality constituency changes : {len(low_q)}")


def main() -> None:
    print("Validating NFHS panel outputs...")

    district_panel = load_csv(NFHS_DISTRICT_PANEL, "district panel")
    district_change = load_csv(NFHS_DISTRICT_CHANGE, "district change")
    constituency_panel = load_csv(CONSTITUENCY_DEMOGRAPHIC_PANEL, "constituency panel")

    if constituency_panel.empty:
        print("  Run build_constituency_demographic_panel first.")
    elif not CONSTITUENCY_DEMOGRAPHIC_CHANGE.exists():
        print("  Building constituency change features...")
        constituency_change = build_constituency_change_features(constituency_panel)
        CONSTITUENCY_DEMOGRAPHIC_CHANGE.parent.mkdir(parents=True, exist_ok=True)
        constituency_change.to_csv(CONSTITUENCY_DEMOGRAPHIC_CHANGE, index=False)
        print(f"  Saved: {CONSTITUENCY_DEMOGRAPHIC_CHANGE}")
    else:
        constituency_change = load_csv(CONSTITUENCY_DEMOGRAPHIC_CHANGE, "constituency change")

    reports = [
        dataset_report("nfhs_district_panel", district_panel, {"district": "district"}),
        dataset_report("nfhs_district_change_features", district_change, {"district": "district"}),
        dataset_report(
            "constituency_demographic_panel",
            constituency_panel,
            {"constituency": "lok_sabha_constituency"},
        ),
        dataset_report(
            "constituency_demographic_change_features",
            constituency_change,
            {"constituency": "lok_sabha_constituency"},
        ),
    ]

    report_df = pd.DataFrame(reports)
    NFHS_PANEL_QUALITY_REPORT.parent.mkdir(parents=True, exist_ok=True)
    report_df.to_csv(NFHS_PANEL_QUALITY_REPORT, index=False)
    print(f"\nSaved: {NFHS_PANEL_QUALITY_REPORT}")

    print_validation_summary(
        district_panel, district_change, constituency_panel, constituency_change
    )


if __name__ == "__main__":
    main()
