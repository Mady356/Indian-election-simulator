"""
Join Lok Sabha→Assembly and Assembly→District delimitation crosswalks.

This produces an approximate LS→District mapping based on assembly segment
counts, **not** GIS polygon overlap. Future work should replace
district_segment_share with population-weighted GIS intersection.

Run as:
    python -m src.reference.build_ls_district_crosswalk_from_delimitation

Outputs:
    data/reference/lok_sabha_district_crosswalk_delimitation.csv
    data/reference/lok_sabha_district_summary_delimitation.csv
    data/reference/manual_review/unmatched_ls_ac_segments.csv
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.reference.delimitation_normalize import join_ls_to_district
from src.reference.delimitation_paths import (
    ASSEMBLY_DISTRICT_CROSSWALK,
    LOK_SABHA_ASSEMBLY_CROSSWALK,
    LOK_SABHA_DISTRICT_CROSSWALK,
    LOK_SABHA_DISTRICT_SUMMARY,
    MANUAL_REVIEW_DIR,
    UNMATCHED_LS_AC,
)


def load_inputs() -> tuple[pd.DataFrame, pd.DataFrame]:
    if not ASSEMBLY_DISTRICT_CROSSWALK.exists() or not LOK_SABHA_ASSEMBLY_CROSSWALK.exists():
        print("ERROR: Missing crosswalk inputs. Run build_ls_ac_crosswalk first.")
        sys.exit(1)
    ac_dist = pd.read_csv(ASSEMBLY_DISTRICT_CROSSWALK)
    ls_ac = pd.read_csv(LOK_SABHA_ASSEMBLY_CROSSWALK)
    return ac_dist, ls_ac


def assign_district_roles(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        df["district_role"] = []
        return df

    out_rows: list[pd.DataFrame] = []
    group_cols = ["state", "lok_sabha_no", "lok_sabha_constituency"]
    for _, grp in df.groupby(group_cols, dropna=False):
        grp = grp.copy()
        known = grp[grp["district"].astype(str).str.strip().ne("")]
        if known.empty:
            grp["district_role"] = "unknown"
        else:
            counts = known.groupby("district").size()
            primary_district = counts.idxmax()
            grp["district_role"] = np.where(
                grp["district"].astype(str).str.strip().eq(""),
                "unknown",
                np.where(grp["district"].eq(primary_district), "primary", "secondary"),
            )
        out_rows.append(grp)
    return pd.concat(out_rows, ignore_index=True)


def build_summary(crosswalk: pd.DataFrame) -> pd.DataFrame:
    known = crosswalk[crosswalk["district"].astype(str).str.strip().ne("")].copy()
    if known.empty:
        return pd.DataFrame(
            columns=[
                "state",
                "lok_sabha_constituency",
                "district",
                "assembly_segments_in_district",
                "total_assembly_segments",
                "district_segment_share",
            ]
        )

    totals = (
        known.groupby(["state", "lok_sabha_constituency"], dropna=False)
        .size()
        .reset_index(name="total_assembly_segments")
    )
    counts = (
        known.groupby(["state", "lok_sabha_constituency", "district"], dropna=False)
        .size()
        .reset_index(name="assembly_segments_in_district")
    )
    summary = counts.merge(totals, on=["state", "lok_sabha_constituency"], how="left")
    summary["district_segment_share"] = (
        summary["assembly_segments_in_district"] / summary["total_assembly_segments"]
    ).round(4)
    return summary.sort_values(
        ["state", "lok_sabha_constituency", "district_segment_share"],
        ascending=[True, True, False],
    )


def print_validation(crosswalk: pd.DataFrame, summary: pd.DataFrame) -> None:
    print("\nValidation")
    total = len(crosswalk)
    by_number = (crosswalk["match_method"] == "by_number").sum()
    by_exact = (crosswalk["match_method"] == "by_exact_name").sum()
    by_fuzzy = (crosswalk["match_method"] == "by_fuzzy_name").sum()
    by_other = crosswalk["match_method"].isin(["by_substring", "by_prefix"]).sum()
    still_unmatched = (crosswalk["match_method"] == "unmatched").sum()

    ls_seats = crosswalk.drop_duplicates(subset=["state", "lok_sabha_no"]).shape[0]
    with_district = (
        crosswalk.groupby(["state", "lok_sabha_no"])["district"]
        .apply(lambda s: (s.astype(str).str.strip() != "").any())
        .sum()
    )
    zero_district = ls_seats - with_district if ls_seats else 0
    multi = summary.groupby(["state", "lok_sabha_constituency"]).size()
    multi_count = (multi > 1).sum()

    print(f"  Total LS-AC rows                 : {total}")
    print(f"  Matched by number                : {by_number}")
    print(f"  Matched by exact name            : {by_exact}")
    print(f"  Matched by fuzzy name            : {by_fuzzy}")
    print(f"  Matched by substring/prefix      : {by_other}")
    print(f"  Still unmatched                  : {still_unmatched}")
    print(f"  LS seats in crosswalk            : {ls_seats}")
    print(f"  LS seats with >=1 district       : {with_district}")
    print(f"  LS seats with 0 districts        : {zero_district}")
    print(f"  LS seats spanning >1 district    : {multi_count}")

    remaining = crosswalk[crosswalk["match_method"] == "unmatched"]
    if remaining.empty:
        return

    print("\n  Top 50 remaining unmatched rows:")
    for _, row in remaining.head(50).iterrows():
        print(
            f"    {row['state']:18s} LS {row['lok_sabha_no']!s:>3} "
            f"{str(row['lok_sabha_constituency'])[:22]:22s} "
            f"AC {str(row['assembly_no']):>4} "
            f"{str(row['assembly_constituency'])[:24]:24s} "
            f"reason={row.get('notes', row.get('match_detail', ''))}"
        )


def main() -> None:
    print(
        "Building Lok Sabha→District crosswalk from delimitation order.\n"
        "  NOTE: Approximate mapping via assembly segment counts — not GIS overlap."
    )
    ac_dist, ls_ac = load_inputs()
    merged = join_ls_to_district(ls_ac, ac_dist)
    crosswalk = assign_district_roles(merged)

    out_cols = [
        "state",
        "lok_sabha_no",
        "lok_sabha_constituency",
        "assembly_no",
        "assembly_constituency",
        "district",
        "district_role",
        "match_method",
        "mapping_confidence",
        "matched_assembly_no",
        "matched_assembly_constituency",
        "source",
        "notes",
    ]
    for col in out_cols:
        if col not in crosswalk.columns:
            crosswalk[col] = ""
    crosswalk = crosswalk[out_cols]

    summary = build_summary(crosswalk)
    unmatched = crosswalk[crosswalk["match_method"] == "unmatched"]

    LOK_SABHA_DISTRICT_CROSSWALK.parent.mkdir(parents=True, exist_ok=True)
    MANUAL_REVIEW_DIR.mkdir(parents=True, exist_ok=True)
    crosswalk.to_csv(LOK_SABHA_DISTRICT_CROSSWALK, index=False)
    summary.to_csv(LOK_SABHA_DISTRICT_SUMMARY, index=False)
    unmatched.to_csv(UNMATCHED_LS_AC, index=False)

    print(f"Saved: {LOK_SABHA_DISTRICT_CROSSWALK} ({len(crosswalk)} rows)")
    print(f"Saved: {LOK_SABHA_DISTRICT_SUMMARY} ({len(summary)} rows)")
    print(f"Saved: {UNMATCHED_LS_AC} ({len(unmatched)} rows)")
    print_validation(crosswalk, summary)


if __name__ == "__main__":
    main()
