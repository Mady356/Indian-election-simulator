"""
Build delimitation district → Census 2011 district alias table.

Resolves spelling differences between the 2008 delimitation order district
labels (used in lok_sabha_district_summary_delimitation.csv) and Census 2011
district names used by NFHS / demographic panels.

Run as:
    python -m src.reference.build_delimitation_census_district_alias

Output:
    data/reference/delimitation_census_district_alias.csv
    data/reference/manual_review/delimitation_district_alias_unmatched.csv
"""

from __future__ import annotations

import sys
import warnings
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.config import DEMOGRAPHICS_PROCESSED_DIR, REFERENCE_DIR
from src.reference.delimitation_utils import normalize_key
from src.demographics.nfhs.panel_utils import SURVEY_NFHS5, prepare_district_panel
from src.demographics.nfhs.paths import NFHS_DISTRICT_FEATURES
from src.reference.delimitation_district_aliases import (
    NCT_PLACEHOLDER_DISTRICTS,
    FUZZY_MEDIUM,
    canonical_district_key,
    census_state_for_delimitation,
    confidence_from_score,
    fuzzy_best_match,
    nfhs4_state_for_census,
    nfhs5_state_for_census,
    resolve_nfhs_district_name,
)
from src.reference.delimitation_paths import LOK_SABHA_DISTRICT_SUMMARY, MANUAL_REVIEW_DIR

ALIAS_OUTPUT = REFERENCE_DIR / "delimitation_census_district_alias.csv"
UNMATCHED_OUTPUT = MANUAL_REVIEW_DIR / "delimitation_district_alias_unmatched.csv"
CENSUS_DISTRICT_PATH = DEMOGRAPHICS_PROCESSED_DIR / "census_district_demographics_2011.csv"

ALIAS_COLUMNS = [
    "delimitation_state",
    "delimitation_district",
    "delimitation_district_key",
    "census_state",
    "census_district",
    "census_district_code",
    "census_district_key",
    "nfhs_district",
    "nfhs4_state",
    "nfhs5_state",
    "nfhs_state",
    "match_method",
    "match_score",
    "confidence",
    "aggregate_share",
    "notes",
]


def load_nfhs_district_lookup() -> pd.DataFrame:
    if not NFHS_DISTRICT_FEATURES.exists():
        return pd.DataFrame(columns=["state", "district", "state_key", "district_key"])
    raw = pd.read_csv(NFHS_DISTRICT_FEATURES)
    panel = prepare_district_panel(raw)
    return panel[panel["survey"] == SURVEY_NFHS5][["state", "district", "state_key", "district_key"]]


def build_alias_table(
    delim_pairs: pd.DataFrame,
    census: pd.DataFrame,
    nfhs_lookup: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    census_sub = census[["state_2011", "district", "district_code_2011"]].drop_duplicates()
    census_sub["census_district_key"] = census_sub["district"].map(normalize_key)

    rows: list[dict] = []
    unmatched: list[dict] = []

    for _, pair in delim_pairs.iterrows():
        delim_state = str(pair["state"]).strip()
        delim_district = str(pair["district"]).strip()
        delim_key = normalize_key(delim_district)
        census_state = census_state_for_delimitation(delim_state)

        state_census = census_sub[census_sub["state_2011"] == census_state].copy()
        if state_census.empty:
            unmatched.append(
                {
                    "delimitation_state": delim_state,
                    "delimitation_district": delim_district,
                    "reason": f"no_census_state:{census_state}",
                }
            )
            continue

        # NCT placeholder: delimitation uses "Delhi" for all of NCT
        if delim_key in NCT_PLACEHOLDER_DISTRICTS and census_state == "NCT OF DELHI":
            n = len(state_census)
            share = 1.0 / n if n else 1.0
            for _, crow in state_census.iterrows():
                nfhs_district = resolve_nfhs_district_name(
                    nfhs_lookup, census_state, str(crow["district"])
                )
                nfhs4_state = nfhs4_state_for_census(census_state, str(crow["district"]))
                nfhs5_state = nfhs5_state_for_census(census_state, str(crow["district"]))
                rows.append(
                    {
                        "delimitation_state": delim_state,
                        "delimitation_district": delim_district,
                        "delimitation_district_key": delim_key,
                        "census_state": census_state,
                        "census_district": crow["district"],
                        "census_district_code": crow["district_code_2011"],
                        "census_district_key": crow["census_district_key"],
                        "nfhs_district": nfhs_district,
                        "nfhs4_state": nfhs4_state,
                        "nfhs5_state": nfhs5_state,
                        "nfhs_state": nfhs5_state,
                        "match_method": "nct_expansion",
                        "match_score": 1.0,
                        "confidence": "high",
                        "aggregate_share": share,
                        "notes": "Delimitation NCT placeholder expanded to all census districts",
                    }
                )
            continue

        candidate_keys = {
            str(r["census_district_key"]): str(r["district"])
            for _, r in state_census.iterrows()
        }
        query_key = canonical_district_key(delim_district)

        method = "exact"
        score = 1.0
        census_district: str | None = None

        if query_key in candidate_keys:
            census_district = candidate_keys[query_key]
        else:
            census_district, score = fuzzy_best_match(query_key, candidate_keys)
            if census_district and score >= FUZZY_MEDIUM:
                method = "alias" if query_key != delim_key else "fuzzy"
            else:
                census_district = None

        if census_district is None:
            unmatched.append(
                {
                    "delimitation_state": delim_state,
                    "delimitation_district": delim_district,
                    "reason": f"no_match_best_score:{score:.3f}",
                    "best_candidate": max(candidate_keys, key=lambda k: score) if candidate_keys else "",
                }
            )
            continue

        crow = state_census[state_census["district"] == census_district].iloc[0]
        census_district_name = str(crow["district"])
        nfhs5_state = nfhs5_state_for_census(census_state, census_district_name)
        nfhs_district = resolve_nfhs_district_name(
            nfhs_lookup, census_state, census_district_name, nfhs_state=nfhs5_state
        )
        conf = confidence_from_score(method, score)

        rows.append(
            {
                "delimitation_state": delim_state,
                "delimitation_district": delim_district,
                "delimitation_district_key": delim_key,
                "census_state": census_state,
                "census_district": census_district,
                "census_district_code": crow["district_code_2011"],
                "census_district_key": crow["census_district_key"],
                "nfhs_district": nfhs_district,
                "nfhs4_state": nfhs4_state_for_census(census_state, census_district_name),
                "nfhs5_state": nfhs5_state,
                "nfhs_state": nfhs5_state,
                "match_method": method,
                "match_score": round(score, 4),
                "confidence": conf,
                "aggregate_share": 1.0,
                "notes": "",
            }
        )

    alias_df = pd.DataFrame(rows)
    if not alias_df.empty:
        alias_df = alias_df[ALIAS_COLUMNS]
    unmatched_df = pd.DataFrame(unmatched)
    return alias_df, unmatched_df


def print_summary(alias_df: pd.DataFrame, unmatched_df: pd.DataFrame, delim_count: int) -> None:
    print("\nAlias table summary")
    print(f"  Delimitation district pairs : {delim_count}")
    print(f"  Alias rows                  : {len(alias_df)}")
    print(f"  Unmatched pairs             : {len(unmatched_df)}")

    if not alias_df.empty:
        mapped_pairs = alias_df.groupby(
            ["delimitation_state", "delimitation_district"]
        ).ngroups
        print(f"  Delimitation pairs mapped   : {mapped_pairs}")
        print("\n  By match_method:")
        for method, n in alias_df["match_method"].value_counts().items():
            print(f"    {method:20s} {n}")
        print("\n  By confidence:")
        for conf, n in alias_df["confidence"].value_counts().items():
            print(f"    {conf:8s} {n}")

    if not unmatched_df.empty:
        warnings.warn(f"{len(unmatched_df)} delimitation districts could not be mapped to census.")


def main() -> None:
    print("Building delimitation → census district alias table...")

    if not LOK_SABHA_DISTRICT_SUMMARY.exists():
        raise FileNotFoundError(f"Missing: {LOK_SABHA_DISTRICT_SUMMARY}")
    if not CENSUS_DISTRICT_PATH.exists():
        raise FileNotFoundError(f"Missing: {CENSUS_DISTRICT_PATH}")

    delim = pd.read_csv(LOK_SABHA_DISTRICT_SUMMARY)
    delim_pairs = delim[["state", "district"]].drop_duplicates()
    census = pd.read_csv(CENSUS_DISTRICT_PATH)
    nfhs_lookup = load_nfhs_district_lookup()

    alias_df, unmatched_df = build_alias_table(delim_pairs, census, nfhs_lookup)

    REFERENCE_DIR.mkdir(parents=True, exist_ok=True)
    MANUAL_REVIEW_DIR.mkdir(parents=True, exist_ok=True)
    alias_df.to_csv(ALIAS_OUTPUT, index=False)
    unmatched_df.to_csv(UNMATCHED_OUTPUT, index=False)

    print(f"\nSaved: {ALIAS_OUTPUT} ({len(alias_df)} rows)")
    if not unmatched_df.empty:
        print(f"Saved: {UNMATCHED_OUTPUT} ({len(unmatched_df)} rows)")

    print_summary(alias_df, unmatched_df, len(delim_pairs))


if __name__ == "__main__":
    main()
