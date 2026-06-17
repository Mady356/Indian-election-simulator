"""
Build state-level NFHS-4 and NFHS-5 aggregated features.

Run as:
    python -m src.demographics.dhs.build_nfhs_state_features
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from src.config import DHS_EXTRACTED_DIR
from src.demographics.dhs.feature_utils import (
    aggregate_hh_features,
    aggregate_ir_features,
    aggregate_mr_features,
    clean_state_label,
    count_persons,
    print_missing_warnings,
    read_metadata,
    resolve_dta_path,
    state_labels_from_meta,
)
from src.demographics.dhs.paths import (
    NATIONAL_FILESETS,
    NFHS_STATE_FEATURES,
    STATE_FEATURE_COLUMNS,
    SURVEY_VERSIONS,
    TREND_COLUMNS,
)


def build_survey_features(version: str) -> tuple[pd.DataFrame, dict]:
    stems = NATIONAL_FILESETS[version]
    hr = resolve_dta_path(DHS_EXTRACTED_DIR, stems["HR"])
    ir = resolve_dta_path(DHS_EXTRACTED_DIR, stems["IR"])
    pr = resolve_dta_path(DHS_EXTRACTED_DIR, stems["PR"])
    mr = resolve_dta_path(DHS_EXTRACTED_DIR, stems.get("MR", ""))

    if not hr or not ir:
        raise FileNotFoundError(f"Missing national HR/IR for version {version}")

    meta = read_metadata(hr)
    state_col = "hv024"
    hh_df, hh_map = aggregate_hh_features(hr, [state_col])
    ir_df, ir_map = aggregate_ir_features(ir, ["v024"])
    ir_df = ir_df.rename(columns={"v024": state_col})
    mr_df = pd.DataFrame()
    mr_map: dict = {}
    if mr and mr.exists():
        mr_df, mr_map = aggregate_mr_features(mr, ["mv024"])
        mr_df = mr_df.rename(columns={"mv024": state_col})

    pr_df = count_persons(pr, [state_col]) if pr and pr.exists() else pd.DataFrame()

    out = hh_df.copy()
    out = out.merge(ir_df, on=state_col, how="left")
    if not mr_df.empty:
        out = out.merge(mr_df, on=state_col, how="left")
    if not pr_df.empty:
        out = out.merge(pr_df, on=state_col, how="left")

    labels = state_labels_from_meta(meta, state_col)
    out["state"] = out[state_col].map(labels).map(clean_state_label)
    info = SURVEY_VERSIONS[version]
    out["survey"] = info["survey"]
    out["survey_year"] = info["survey_year"]

    mapping = {**hh_map, **ir_map, **mr_map}
    return out, mapping


def add_trends(df: pd.DataFrame) -> pd.DataFrame:
    nfhs4 = df[df["survey"] == "NFHS-4"].set_index("state")
    nfhs5 = df[df["survey"] == "NFHS-5"].set_index("state")
    trend = nfhs5.join(nfhs4, lsuffix="_5", rsuffix="_4", how="outer")

    pairs = [
        ("internet_growth_nfhs4_to_nfhs5", "internet_pct_5", "internet_pct_4"),
        ("electricity_growth_nfhs4_to_nfhs5", "electricity_pct_5", "electricity_pct_4"),
        ("sanitation_growth_nfhs4_to_nfhs5", "improved_sanitation_pct_5", "improved_sanitation_pct_4"),
        ("fertility_decline_nfhs4_to_nfhs5", "fertility_rate_4", "fertility_rate_5"),
    ]
    trend_cols = {}
    for name, a, b in pairs:
        if a in trend.columns and b in trend.columns:
            trend_cols[name] = trend[a] - trend[b]

    trend_df = pd.DataFrame(trend_cols).reset_index()
    return df.merge(trend_df, on="state", how="left")


def print_validation(df: pd.DataFrame, mappings: dict[str, dict]) -> None:
    print("\nValidation")
    print(f"  States covered     : {df['state'].nunique()}")
    print(f"  Survey rounds      : {df['survey'].unique().tolist()}")
    feature_cols = [c for c in STATE_FEATURE_COLUMNS if c not in ("survey", "survey_year", "state")]
    missing = df[feature_cols].isna().mean().sort_values(ascending=False)
    print("\n  Missing share by feature:")
    for col, pct in missing.items():
        print(f"    {col:30s} {pct*100:5.1f}%")

    print("\n  Variable mappings:")
    for version, mp in mappings.items():
        print(f"    NFHS version {version}:")
        for feat, col in sorted(mp.items()):
            print(f"      {feat:30s} -> {col or 'NOT FOUND'}")


def main() -> None:
    frames = []
    all_maps: dict[str, dict] = {}
    for version in ("52", "42"):
        print(f"Building NFHS-{4 if version=='42' else 5} state features...")
        try:
            frame, mapping = build_survey_features(version)
            frames.append(frame)
            all_maps[version] = mapping
            for v in mapping.values():
                if v is None:
                    continue
            print_missing_warnings(mapping, prefix=f"NFHS-{version} ")
        except FileNotFoundError as exc:
            print(f"  SKIP: {exc}")

    if not frames:
        print("No state features built. Extract Stata files first.")
        return

    df = pd.concat(frames, ignore_index=True)
    df = add_trends(df)

    extra = [c for c in TREND_COLUMNS if c in df.columns]
    out_cols = [c for c in STATE_FEATURE_COLUMNS if c in df.columns] + extra
    df = df[out_cols]

    NFHS_STATE_FEATURES.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(NFHS_STATE_FEATURES, index=False)
    print(f"\nSaved: {NFHS_STATE_FEATURES} ({len(df)} rows)")
    print_validation(df, all_maps)


if __name__ == "__main__":
    main()
