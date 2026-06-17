"""
NFHS-4 numeric district code (sdist) → district name crosswalk helpers.

NFHS-4 microdata stores districts as within-state numeric codes without value
labels. We resolve names by:

1. Census 2011 rank: sdist *n* → *n*th district when census districts are
   sorted by official district_code within the state.
2. Name match to NFHS-5 district labels (exact / fuzzy normalized key).
3. Feature-vector Hungarian matching within state as fallback.
"""

from __future__ import annotations

import re
import warnings
from typing import Iterable

import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment

from src.demographics.nfhs.panel_utils import (
    SURVEY_NFHS4,
    SURVEY_NFHS5,
    is_numeric_district,
    normalize_key,
    title_case_label,
)
from src.demographics.nfhs.state_maps import NFHS4_TO_CENSUS_STATE, nfhs5_state_label

MATCH_FEATURES: tuple[str, ...] = (
    "electricity_pct",
    "urban_pct",
    "improved_sanitation_pct",
    "lpg_pct",
    "mobile_phone_pct",
)

FEATURE_COST_HIGH = 12.0
FEATURE_COST_MEDIUM = 25.0
VALIDATION_COST_HIGH = 15.0


def feature_cost(row_a: pd.Series, row_b: pd.Series, features: Iterable[str] = MATCH_FEATURES) -> float:
    diffs: list[float] = []
    for feat in features:
        a, b = row_a.get(feat), row_b.get(feat)
        if pd.notna(a) and pd.notna(b):
            diffs.append(abs(float(a) - float(b)))
    return float(np.mean(diffs)) if diffs else np.nan


def fuzzy_district_match(census_key: str, nfhs5_keys: dict[str, str]) -> str | None:
    compact = census_key.replace(" ", "")
    for dk, name in nfhs5_keys.items():
        dk_compact = dk.replace(" ", "")
        if compact == dk_compact or compact in dk_compact or dk_compact in compact:
            return name
    return None


def hungarian_nfhs5_map(
    nfhs4_state: str,
    district_features: pd.DataFrame,
) -> dict[str, tuple[str, float]]:
    nfhs5_state = nfhs5_state_label(nfhs4_state)
    d4 = district_features[
        (district_features["survey"] == SURVEY_NFHS4) & (district_features["state"] == nfhs4_state)
    ]
    d5 = district_features[
        (district_features["survey"] == SURVEY_NFHS5) & (district_features["state"] == nfhs5_state)
    ]
    if d4.empty or d5.empty:
        return {}

    n4, n5 = len(d4), len(d5)
    cost = np.full((n4, n5), 1e6)
    for i in range(n4):
        for j in range(n5):
            cost[i, j] = feature_cost(d4.iloc[i], d5.iloc[j])

    row_idx, col_idx = linear_sum_assignment(cost)
    out: dict[str, tuple[str, float]] = {}
    for i, j in zip(row_idx, col_idx):
        code = str(d4.iloc[i]["district"])
        out[code] = (str(d5.iloc[j]["district"]), float(cost[i, j]))
    return out


def build_nfhs4_crosswalk(
    district_features: pd.DataFrame,
    census_districts: pd.DataFrame,
) -> pd.DataFrame:
    """
    Build sdist code → resolved district name crosswalk for all NFHS-4 rows.
    """
    nfhs4 = district_features[district_features["survey"] == SURVEY_NFHS4].copy()
    if nfhs4.empty:
        warnings.warn("No NFHS-4 rows in district features.")
        return pd.DataFrame()

    rows: list[dict] = []

    for nfhs4_state, census_state in NFHS4_TO_CENSUS_STATE.items():
        state_rows = nfhs4[nfhs4["state"] == nfhs4_state].copy()
        if state_rows.empty:
            continue

        state_rows["sdist_code"] = pd.to_numeric(state_rows["district"], errors="coerce")

        census_state_rows = census_districts[census_districts["state_2011"] == census_state].sort_values(
            "district_code_2011"
        )
        census_state_rows = census_state_rows.reset_index(drop=True)
        census_state_rows["sdist_rank"] = np.arange(1, len(census_state_rows) + 1)

        rank_map = state_rows.merge(
            census_state_rows[["sdist_rank", "district"]],
            left_on="sdist_code",
            right_on="sdist_rank",
            how="left",
            suffixes=("", "_census"),
        ).rename(columns={"district_census": "census_district"})

        nfhs5_state = nfhs5_state_label(nfhs4_state)
        nfhs5 = district_features[
            (district_features["survey"] == SURVEY_NFHS5) & (district_features["state"] == nfhs5_state)
        ]
        nfhs5_keys = {normalize_key(d): d for d in nfhs5["district"].astype(str)}

        feature_map = hungarian_nfhs5_map(nfhs4_state, district_features)

        for _, row in rank_map.iterrows():
            sdist_code = int(row["sdist_code"]) if pd.notna(row["sdist_code"]) else None
            census_name = row.get("census_district")
            resolved_name: str | None = None
            method = "unmapped"
            match_cost = np.nan
            confidence = "low"

            if pd.notna(census_name):
                census_key = normalize_key(census_name)
                if census_key in nfhs5_keys:
                    resolved_name = nfhs5_keys[census_key]
                    method = "census_rank_nfhs5"
                    nfhs5_row = nfhs5[nfhs5["district"] == resolved_name].iloc[0]
                    match_cost = feature_cost(row, nfhs5_row)
                    confidence = "high" if match_cost < VALIDATION_COST_HIGH else "medium"
                else:
                    fuzzy = fuzzy_district_match(census_key, nfhs5_keys)
                    if fuzzy:
                        resolved_name = fuzzy
                        method = "census_rank_fuzzy_nfhs5"
                        confidence = "medium"
                    else:
                        resolved_name = title_case_label(str(census_name))
                        method = "census_rank"
                        confidence = "medium"

            code_str = str(sdist_code) if sdist_code is not None else str(row["district"])
            if resolved_name is None and code_str in feature_map:
                resolved_name, match_cost = feature_map[code_str]
                method = "feature_match"
                if match_cost < FEATURE_COST_HIGH:
                    confidence = "high"
                elif match_cost < FEATURE_COST_MEDIUM:
                    confidence = "medium"
                else:
                    confidence = "low"

            rows.append(
                {
                    "state": title_case_label(nfhs4_state),
                    "nfhs4_state_raw": nfhs4_state,
                    "sdist_code": sdist_code,
                    "district_code_nfhs4": code_str,
                    "census_district": census_name if pd.notna(census_name) else "",
                    "district_resolved": resolved_name or "",
                    "nfhs5_state": nfhs5_state,
                    "mapping_method": method,
                    "match_cost": match_cost,
                    "confidence": confidence,
                    "state_key": normalize_key(nfhs4_state),
                    "district_key_resolved": normalize_key(resolved_name) if resolved_name else "",
                }
            )

    crosswalk = pd.DataFrame(rows)
    mapped = crosswalk["district_resolved"].astype(str).str.len().gt(0).sum()
    if mapped < len(crosswalk):
        warnings.warn(
            f"NFHS-4 crosswalk: {mapped}/{len(crosswalk)} codes resolved to district names. "
            f"{len(crosswalk) - mapped} remain unmapped (often states missing NFHS-5 district data)."
        )
    return crosswalk


def apply_crosswalk_to_nfhs4(panel: pd.DataFrame, crosswalk: pd.DataFrame) -> pd.DataFrame:
    """Replace numeric NFHS-4 district codes with resolved names where possible."""
    if panel.empty or crosswalk.empty:
        return panel

    out = panel.copy()
    out["nfhs4_sdist_code"] = np.nan
    out["district_name_source"] = ""

    nfhs4_mask = out["survey"] == SURVEY_NFHS4
    if not nfhs4_mask.any():
        return out

    cw = crosswalk.copy()
    cw["sdist_code"] = pd.to_numeric(cw["sdist_code"], errors="coerce")
    cw_lookup = cw.set_index(["state_key", "sdist_code"])

    for idx, row in out[nfhs4_mask].iterrows():
        district_str = str(row["district"]).strip()
        if not is_numeric_district(district_str):
            out.at[idx, "district_name_source"] = "state_file_census_name"
            continue

        code = pd.to_numeric(district_str, errors="coerce")
        out.at[idx, "nfhs4_sdist_code"] = code
        key = (row["state_key"], code)
        if key not in cw_lookup.index:
            out.at[idx, "district_name_source"] = "numeric_code_unmapped"
            continue

        hit = cw_lookup.loc[key]
        if isinstance(hit, pd.DataFrame):
            hit = hit.iloc[0]

        resolved = str(hit["district_resolved"]).strip()
        if not resolved:
            out.at[idx, "district_name_source"] = "numeric_code_unmapped"
            continue

        out.at[idx, "state"] = title_case_label(nfhs5_state_label(str(row["state"])))
        out.at[idx, "state_key"] = normalize_key(out.at[idx, "state"])
        out.at[idx, "district"] = resolved
        out.at[idx, "district_key"] = normalize_key(resolved)
        out.at[idx, "district_panel_id"] = (
            f"{out.at[idx, 'state_key']}__{normalize_key(resolved)}__{SURVEY_NFHS4}"
        )
        out.at[idx, "district_name_source"] = str(hit["mapping_method"])

    return out
