"""
Parse Assembly→District (Table A) and Lok Sabha→Assembly (Table B) crosswalks
from extracted delimitation PDF text.

Run as:
    python -m src.reference.build_ls_ac_crosswalk

Requires:
    data/reference/delimitation_raw_text.csv  (from extract_delimitation_order)

Outputs:
    data/reference/assembly_constituency_district_crosswalk.csv
    data/reference/lok_sabha_assembly_crosswalk.csv
    data/reference/manual_review/delimitation_low_confidence_*.csv
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.reference.delimitation_paths import (
    ASSEMBLY_DISTRICT_CROSSWALK,
    DELIMITATION_RAW_TEXT,
    LOW_CONFIDENCE_ASSEMBLY,
    LOW_CONFIDENCE_LOK_SABHA,
    LOK_SABHA_ASSEMBLY_CROSSWALK,
    MANUAL_REVIEW_DIR,
)
from src.reference.delimitation_utils import (
    EXPECTED_AC_SEATS,
    EXPECTED_LS_SEATS,
    parse_delimitation_pages,
)


def print_validation(ac_df: pd.DataFrame, ls_df: pd.DataFrame) -> None:
    print("\nValidation")
    if ac_df.empty and ls_df.empty:
        print("  No rows parsed.")
        return

    states_ac = ac_df["state"].nunique() if not ac_df.empty else 0
    states_ls = ls_df["state"].nunique() if not ls_df.empty else 0
    ac_count = len(ac_df)
    ls_count = (
        ls_df.drop_duplicates(subset=["state", "lok_sabha_no"]).shape[0] if not ls_df.empty else 0
    )

    print(f"  States parsed (assembly)     : {states_ac}")
    print(f"  States parsed (lok sabha)    : {states_ls}")
    print(f"  Assembly constituencies      : {ac_count} (expected ~{EXPECTED_AC_SEATS})")
    print(f"  Lok Sabha constituencies     : {ls_count} (expected ~{EXPECTED_LS_SEATS})")

    if not ls_df.empty:
        low = ls_df[ls_df["parse_confidence"] != "high"]
        print(f"  LS rows not high confidence  : {len(low)}")
        print("\n  Top 30 low-confidence LS parses:")
        sample = low.head(30)
        for _, row in sample.iterrows():
            print(
                f"    {row['state']:20s} LS {row['lok_sabha_no']:3} "
                f"{row['lok_sabha_constituency'][:30]:30s} AC {row.get('assembly_no', '')} "
                f"conf={row['parse_confidence']}"
            )

    if not ac_df.empty:
        low_ac = ac_df[ac_df["parse_confidence"] != "high"]
        print(f"\n  Assembly rows not high confidence: {len(low_ac)}")
        print("  Top 30 low-confidence assembly parses:")
        for _, row in low_ac.head(30).iterrows():
            print(
                f"    {row['state']:20s} AC {row['assembly_no']:4} "
                f"{str(row['assembly_constituency'])[:28]:28s} conf={row['parse_confidence']}"
            )


def main() -> None:
    if not DELIMITATION_RAW_TEXT.exists():
        print(f"ERROR: {DELIMITATION_RAW_TEXT} not found.")
        print("  Run: python -m src.reference.extract_delimitation_order")
        sys.exit(1)

    print(f"Loading {DELIMITATION_RAW_TEXT.name}...")
    pages_df = pd.read_csv(DELIMITATION_RAW_TEXT)
    ac_df, ls_df = parse_delimitation_pages(pages_df)

    ASSEMBLY_DISTRICT_CROSSWALK.parent.mkdir(parents=True, exist_ok=True)
    MANUAL_REVIEW_DIR.mkdir(parents=True, exist_ok=True)

    ac_df.to_csv(ASSEMBLY_DISTRICT_CROSSWALK, index=False)
    ls_df.to_csv(LOK_SABHA_ASSEMBLY_CROSSWALK, index=False)

    if not ac_df.empty:
        ac_df[ac_df["parse_confidence"] != "high"].to_csv(LOW_CONFIDENCE_ASSEMBLY, index=False)
    if not ls_df.empty:
        ls_df[ls_df["parse_confidence"] != "high"].to_csv(LOW_CONFIDENCE_LOK_SABHA, index=False)

    print(f"Saved: {ASSEMBLY_DISTRICT_CROSSWALK} ({len(ac_df)} rows)")
    print(f"Saved: {LOK_SABHA_ASSEMBLY_CROSSWALK} ({len(ls_df)} rows)")
    if LOW_CONFIDENCE_ASSEMBLY.exists():
        print(f"Saved: {LOW_CONFIDENCE_ASSEMBLY}")
    if LOW_CONFIDENCE_LOK_SABHA.exists():
        print(f"Saved: {LOW_CONFIDENCE_LOK_SABHA}")

    print_validation(ac_df, ls_df)


if __name__ == "__main__":
    main()
