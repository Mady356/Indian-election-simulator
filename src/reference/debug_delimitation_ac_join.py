"""
Diagnose and improve LS-AC -> district join quality.

Run as:
    python -m src.reference.debug_delimitation_ac_join

Loads raw parsed crosswalks (does not overwrite them), writes normalized
copies and unmatched join diagnostics.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.reference.delimitation_normalize import (
    build_ac_lookups,
    diagnose_row,
    join_ls_to_district,
    match_ls_row,
    prepare_ac_table,
    prepare_ls_table,
)
from src.reference.delimitation_paths import (
    ASSEMBLY_DISTRICT_CROSSWALK,
    ASSEMBLY_DISTRICT_CROSSWALK_NORMALIZED,
    LOK_SABHA_ASSEMBLY_CROSSWALK,
    LOK_SABHA_ASSEMBLY_CROSSWALK_NORMALIZED,
    MANUAL_REVIEW_DIR,
    UNMATCHED_LS_AC_JOIN_DIAGNOSTICS,
)


def build_diagnostics(ls: pd.DataFrame, ac: pd.DataFrame) -> pd.DataFrame:
    lookups = build_ac_lookups(ac)
    rows: list[dict[str, object]] = []

    for row in ls.itertuples(index=False):
        row_series = pd.Series(row._asdict())
        state_key = str(row_series.get("state_key", ""))
        diag = diagnose_row(row_series, lookups.get(state_key))
        matched = match_ls_row(row_series, lookups.get(state_key))

        record = {
            "state": row_series.get("state"),
            "lok_sabha_no": row_series.get("lok_sabha_no"),
            "lok_sabha_constituency": row_series.get("lok_sabha_constituency"),
            "assembly_no": row_series.get("assembly_no"),
            "assembly_constituency": row_series.get("assembly_constituency"),
            "ac_short_name": row_series.get("ac_short_name"),
            "assembly_constituency_normalized": row_series.get(
                "assembly_constituency_normalized"
            ),
            **diag,
            "resolved_district": matched.get("district", ""),
            "resolved_match_method": matched.get("match_method", ""),
            "resolved_mapping_confidence": matched.get("mapping_confidence", ""),
            "resolved_match_detail": matched.get("match_detail", ""),
        }
        rows.append(record)

    diag_df = pd.DataFrame(rows)
    unmatched = diag_df[diag_df["resolved_match_method"] == "unmatched"].copy()
    if not unmatched.empty:
        unmatched["manual_review"] = True
    else:
        unmatched["manual_review"] = pd.Series(dtype=bool)
    diag_df["manual_review"] = diag_df["resolved_match_method"] == "unmatched"
    return diag_df


def print_validation(diag_df: pd.DataFrame, joined: pd.DataFrame) -> None:
    total = len(joined)
    by_number = (joined["match_method"] == "by_number").sum()
    by_exact = joined["match_method"] == "by_exact_name"
    by_fuzzy = joined["match_method"] == "by_fuzzy_name"
    by_substring = joined["match_method"] == "by_substring"
    by_prefix = joined["match_method"] == "by_prefix"
    by_exact_name = by_exact.sum()
    by_fuzzy_name = by_fuzzy.sum()
    by_name_other = (by_substring | by_prefix).sum()
    still_unmatched = (joined["match_method"] == "unmatched").sum()

    ls_seats = joined.drop_duplicates(subset=["state", "lok_sabha_no"]).shape[0]
    with_district = (
        joined.groupby(["state", "lok_sabha_no"])["district"]
        .apply(lambda s: (s.astype(str).str.strip() != "").any())
        .sum()
    )
    zero_district = ls_seats - with_district

    print("\nValidation")
    print(f"  Total LS-AC rows                 : {total}")
    print(f"  Matched by number                : {by_number}")
    print(f"  Matched by exact name            : {by_exact_name}")
    print(f"  Matched by fuzzy name            : {by_fuzzy_name}")
    print(f"  Matched by substring/prefix      : {by_name_other}")
    print(f"  Still unmatched                  : {still_unmatched}")
    print(f"  LS seats with zero district match: {zero_district}")

    remaining = joined[joined["match_method"] == "unmatched"].copy()
    if remaining.empty:
        return

    print("\n  Top 50 remaining unmatched rows:")
    show_cols = [
        "state",
        "lok_sabha_no",
        "lok_sabha_constituency",
        "assembly_no",
        "assembly_constituency",
        "match_detail",
    ]
    for _, row in remaining.head(50).iterrows():
        print(
            f"    {row['state']:18s} LS {row['lok_sabha_no']!s:>3} "
            f"{str(row['lok_sabha_constituency'])[:22]:22s} "
            f"AC {str(row['assembly_no']):>4} "
            f"{str(row['assembly_constituency'])[:24]:24s} "
            f"reason={row.get('match_detail', '')}"
        )


def main() -> None:
    if not ASSEMBLY_DISTRICT_CROSSWALK.exists() or not LOK_SABHA_ASSEMBLY_CROSSWALK.exists():
        print("ERROR: Missing crosswalk inputs. Run build_ls_ac_crosswalk first.")
        sys.exit(1)

    print("Loading raw parsed crosswalks...")
    ac_raw = pd.read_csv(ASSEMBLY_DISTRICT_CROSSWALK)
    ls_raw = pd.read_csv(LOK_SABHA_ASSEMBLY_CROSSWALK)

    ac = prepare_ac_table(ac_raw)
    ls = prepare_ls_table(ls_raw)

    MANUAL_REVIEW_DIR.mkdir(parents=True, exist_ok=True)
    ASSEMBLY_DISTRICT_CROSSWALK_NORMALIZED.parent.mkdir(parents=True, exist_ok=True)

    ac.to_csv(ASSEMBLY_DISTRICT_CROSSWALK_NORMALIZED, index=False)
    ls.to_csv(LOK_SABHA_ASSEMBLY_CROSSWALK_NORMALIZED, index=False)
    print(f"Saved: {ASSEMBLY_DISTRICT_CROSSWALK_NORMALIZED}")
    print(f"Saved: {LOK_SABHA_ASSEMBLY_CROSSWALK_NORMALIZED}")

    print("Building join diagnostics...")
    diag_df = build_diagnostics(ls, ac)
    unmatched_diag = diag_df[diag_df["manual_review"]].copy()
    unmatched_diag.to_csv(UNMATCHED_LS_AC_JOIN_DIAGNOSTICS, index=False)
    print(f"Saved: {UNMATCHED_LS_AC_JOIN_DIAGNOSTICS} ({len(unmatched_diag)} rows)")

    joined = join_ls_to_district(ls_raw, ac_raw)
    print_validation(diag_df, joined)


if __name__ == "__main__":
    main()
