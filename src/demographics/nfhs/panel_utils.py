"""
Shared helpers for NFHS district / constituency demographic panels.
"""

from __future__ import annotations

import re
import warnings
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

from src.demographics.nfhs.district_alias import load_district_alias_table, resolve_delimitation_district
from src.reference.ap_telangana_bifurcation import NFHS5_STATE_TELANGANA, pair_district_key, pair_state_key
from src.demographics.nfhs.paths import NFHS_DISTRICT_FEATURES
from src.demographics.nfhs.state_maps import NFHS4_TO_NFHS5_STATE, nfhs5_state_label
from src.reference.delimitation_district_aliases import (
    census_state_for_delimitation,
    nfhs4_state_for_census,
    nfhs5_state_for_census,
)

SURVEY_NFHS4 = "NFHS-4"
SURVEY_NFHS5 = "NFHS-5"

# Canonical years for annualized change (per project spec).
NFHS4_CANONICAL_YEAR = 2016
NFHS5_CANONICAL_YEAR = 2021
YEARS_BETWEEN_SURVEYS = NFHS5_CANONICAL_YEAR - NFHS4_CANONICAL_YEAR

MIN_HOUSEHOLD_COUNT_HIGH = 30

PANEL_FEATURE_COLUMNS = [
    "fertility_rate",
    "electricity_pct",
    "improved_sanitation_pct",
    "lpg_pct",
    "mobile_phone_pct",
    "bank_account_pct",
    "women_secondary_edu_pct",
    "female_literacy_pct",
    "male_literacy_pct",
    "wealth_index_mean",
    "urban_pct",
]

COUNT_COLUMNS = ["household_count", "person_count"]

DISTRICT_PANEL_COLUMNS = [
    "state",
    "district",
    "survey",
    "survey_year",
    *PANEL_FEATURE_COLUMNS,
    *COUNT_COLUMNS,
    "state_key",
    "district_key",
    "district_panel_id",
]

CHANGE_FEATURE_SUFFIXES = [f"{c}_change" for c in PANEL_FEATURE_COLUMNS]
ANNUAL_CHANGE_SUFFIXES = [f"{c}_annual_change" for c in PANEL_FEATURE_COLUMNS]


def normalize_key(value: object) -> str:
    """Normalize geographic names for joins."""
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return ""
    text = str(value).strip().upper()
    text = text.replace("&", " AND ")
    text = re.sub(r"[–—\-/]", " ", text)
    text = re.sub(r"[^A-Z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def title_case_label(value: object) -> str:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return ""
    text = str(value).strip()
    text = re.sub(r"\s+", " ", text)
    if text.isupper() and len(text) > 3:
        return text.title()
    return text


def make_district_keys(state: object, district: object) -> tuple[str, str, str, str]:
    state_label = title_case_label(state)
    district_label = str(district).strip() if pd.notna(district) else ""
    state_key = normalize_key(state_label)
    district_key = normalize_key(district_label)
    return state_label, district_label, state_key, district_key


def canonical_survey_year(survey: str, survey_year: object) -> int:
    if survey == SURVEY_NFHS4:
        return NFHS4_CANONICAL_YEAR
    if survey == SURVEY_NFHS5:
        return NFHS5_CANONICAL_YEAR
    try:
        return int(survey_year)
    except (TypeError, ValueError):
        return int(np.nan)


def load_nfhs_district_features(path: Path | None = None) -> pd.DataFrame:
    source = path or NFHS_DISTRICT_FEATURES
    if not source.exists():
        raise FileNotFoundError(
            f"Missing NFHS district features: {source}\n"
            "Run: python -m src.demographics.dhs.build_nfhs_district_features"
        )
    df = pd.read_csv(source)
    if df.empty:
        warnings.warn(f"NFHS district features file is empty: {source}")
    return df


def prepare_district_panel(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize district feature rows into panel schema."""
    if df.empty:
        return pd.DataFrame(columns=DISTRICT_PANEL_COLUMNS)

    out = df.copy()
    out["state"] = out["state"].map(title_case_label)
    out["district"] = out["district"].astype(str).str.strip()

    keyed = out.apply(
        lambda r: pd.Series(
            make_district_keys(r["state"], r["district"]),
            index=["state", "district", "state_key", "district_key"],
        ),
        axis=1,
    )
    out[["state", "district", "state_key", "district_key"]] = keyed
    out["district_panel_id"] = out.apply(
        lambda r: f"{r['state_key']}__{r['district_key']}__{r['survey']}"
        if r["state_key"] and r["district_key"]
        else "",
        axis=1,
    )

    for col in PANEL_FEATURE_COLUMNS + COUNT_COLUMNS:
        if col not in out.columns:
            out[col] = np.nan
            warnings.warn(f"Column missing from NFHS district features: {col}")

    out = out[DISTRICT_PANEL_COLUMNS]
    out = out.drop_duplicates(subset=["state_key", "district_key", "survey"], keep="last")
    out = out.sort_values(["state", "district", "survey"])
    return out


def is_numeric_district(district: str) -> bool:
    return bool(re.fullmatch(r"\d+", str(district).strip()))


def assess_change_quality(
    row_nfhs4: pd.Series | None,
    row_nfhs5: pd.Series | None,
    feature_cols: Iterable[str] = PANEL_FEATURE_COLUMNS,
) -> str:
    if row_nfhs4 is None or row_nfhs5 is None:
        return "low"

    hh4 = pd.to_numeric(row_nfhs4.get("household_count"), errors="coerce")
    hh5 = pd.to_numeric(row_nfhs5.get("household_count"), errors="coerce")
    reasonable_hh = (
        (pd.isna(hh4) or hh4 >= MIN_HOUSEHOLD_COUNT_HIGH)
        and (pd.isna(hh5) or hh5 >= MIN_HOUSEHOLD_COUNT_HIGH)
    )

    missing4 = sum(pd.isna(row_nfhs4.get(c)) for c in feature_cols)
    missing5 = sum(pd.isna(row_nfhs5.get(c)) for c in feature_cols)
    any_missing = (missing4 + missing5) > 0

    if reasonable_hh and not any_missing:
        return "high"
    if reasonable_hh and any_missing:
        return "medium"
    return "low"


def compute_change_row(
    base: dict,
    val4: pd.Series | None,
    val5: pd.Series | None,
) -> dict:
    row = dict(base)
    row["has_nfhs4"] = val4 is not None
    row["has_nfhs5"] = val5 is not None
    row["household_count_nfhs4"] = val4["household_count"] if val4 is not None else np.nan
    row["household_count_nfhs5"] = val5["household_count"] if val5 is not None else np.nan
    row["change_quality_flag"] = assess_change_quality(val4, val5)

    for feat in PANEL_FEATURE_COLUMNS:
        v4 = val4[feat] if val4 is not None else np.nan
        v5 = val5[feat] if val5 is not None else np.nan
        if pd.notna(v4) and pd.notna(v5):
            delta = float(v5) - float(v4)
            row[f"{feat}_change"] = delta
            row[f"{feat}_annual_change"] = delta / YEARS_BETWEEN_SURVEYS
        else:
            row[f"{feat}_change"] = np.nan
            row[f"{feat}_annual_change"] = np.nan

    return row


def join_state_key(state: str, survey: str, district_key: str = "") -> str:
    """Normalize state keys so NFHS-4 / NFHS-5 rows align for change joins."""
    if district_key:
        return pair_state_key(state, survey, district_key)
    if survey == SURVEY_NFHS4 and state in NFHS4_TO_NFHS5_STATE:
        return normalize_key(nfhs5_state_label(state))
    return normalize_key(state)


def build_district_change_features(panel: pd.DataFrame) -> pd.DataFrame:
    """Pair NFHS-4 and NFHS-5 rows on join_state_key + district_key."""
    if panel.empty:
        return pd.DataFrame()

    panel = panel.copy()
    panel["join_state_key"] = panel.apply(
        lambda r: join_state_key(str(r["state"]), str(r["survey"]), str(r["district_key"])),
        axis=1,
    )
    panel["pair_district_key"] = panel["district_key"].map(pair_district_key)

    still_numeric = (
        (panel["survey"] == SURVEY_NFHS4)
        & panel["district"].map(is_numeric_district)
    ).sum()
    if still_numeric:
        warnings.warn(
            f"{still_numeric} NFHS-4 rows still have numeric district codes after crosswalk."
        )

    nfhs4 = panel[panel["survey"] == SURVEY_NFHS4].set_index(["join_state_key", "pair_district_key"])
    nfhs5 = panel[panel["survey"] == SURVEY_NFHS5].set_index(["join_state_key", "pair_district_key"])

    all_keys = sorted(set(nfhs4.index) | set(nfhs5.index))
    rows: list[dict] = []
    for state_key, district_key in all_keys:
        val4 = nfhs4.loc[(state_key, district_key)] if (state_key, district_key) in nfhs4.index else None
        val5 = nfhs5.loc[(state_key, district_key)] if (state_key, district_key) in nfhs5.index else None
        if isinstance(val4, pd.DataFrame):
            val4 = val4.iloc[0]
        if isinstance(val5, pd.DataFrame):
            val5 = val5.iloc[0]

        base = {
            "state": val5["state"] if val5 is not None else (val4["state"] if val4 is not None else ""),
            "district": val5["district"] if val5 is not None else (val4["district"] if val4 is not None else ""),
            "state_key": state_key,
            "district_key": district_key,
        }
        rows.append(compute_change_row(base, val4, val5))

    out = pd.DataFrame(rows)
    col_order = [
        "state",
        "district",
        "state_key",
        "district_key",
        "has_nfhs4",
        "has_nfhs5",
        *CHANGE_FEATURE_SUFFIXES,
        *ANNUAL_CHANGE_SUFFIXES,
        "household_count_nfhs4",
        "household_count_nfhs5",
        "change_quality_flag",
    ]
    return out[[c for c in col_order if c in out.columns]]


def candidate_state_keys(delim_state: str, survey: str | None = None) -> list[str]:
    """State keys to try when joining delimitation labels to NFHS panels."""
    keys = [normalize_key(delim_state)]
    census_state = census_state_for_delimitation(delim_state)
    keys.append(normalize_key(census_state))
    keys.append(normalize_key(nfhs5_state_for_census(census_state)))
    keys.append(join_state_key(delim_state, SURVEY_NFHS4))
    keys.append(join_state_key(delim_state, SURVEY_NFHS5))
    if survey == SURVEY_NFHS4:
        keys.append(normalize_key(nfhs4_state_for_census(census_state)))
    elif survey == SURVEY_NFHS5:
        keys.append(normalize_key(nfhs5_state_for_census(census_state)))
    return list(dict.fromkeys(k for k in keys if k))


def lookup_district_features(
    district_panel: pd.DataFrame,
    state_key: str,
    district_name: str,
    survey: str,
    state_keys: list[str] | None = None,
) -> pd.Series | None:
    district_key = normalize_key(district_name)
    keys_to_try = state_keys or [state_key]
    for sk in keys_to_try:
        mask = (
            (district_panel["state_key"] == sk)
            & (district_panel["district_key"] == district_key)
            & (district_panel["survey"] == survey)
        )
        hits = district_panel.loc[mask]
        if not hits.empty:
            return hits.iloc[0]

    if survey == SURVEY_NFHS4:
        for sk in keys_to_try:
            for _, prow in district_panel[
                (district_panel["survey"] == SURVEY_NFHS4)
                & (district_panel["district_key"] == district_key)
            ].iterrows():
                jsk = join_state_key(str(prow["state"]), SURVEY_NFHS4)
                if jsk == sk or normalize_key(str(prow["state"])) == sk:
                    return prow
    return None


def lookup_district_features_flexible(
    district_panel: pd.DataFrame,
    delim_state: str,
    district_name: str,
    survey: str,
    nfhs_state: str | None = None,
) -> pd.Series | None:
    if nfhs_state:
        state_keys = candidate_state_keys(nfhs_state, survey)
        primary_key = state_keys[0] if state_keys else normalize_key(nfhs_state)
    else:
        state_keys = candidate_state_keys(delim_state, survey)
        primary_key = state_keys[0] if state_keys else normalize_key(delim_state)
    return lookup_district_features(
        district_panel, primary_key, district_name, survey, state_keys=state_keys
    )


def aggregate_constituency_survey(
    crosswalk: pd.DataFrame,
    district_panel: pd.DataFrame,
    survey: str,
    alias_table: pd.DataFrame | None = None,
) -> pd.DataFrame:
    rows: list[dict] = []
    group_cols = ["state", "lok_sabha_constituency"]
    if alias_table is None:
        alias_table = load_district_alias_table()

    for (state, constituency), grp in crosswalk.groupby(group_cols, dropna=False):
        state_label = title_case_label(state)
        weights = grp["district_segment_share"].astype(float)
        weight_sum = weights.sum()
        if weight_sum <= 0:
            warnings.warn(
                f"Skipping {state} / {constituency}: district_segment_share sums to {weight_sum}"
            )
            continue

        if not np.isclose(weight_sum, 1.0, atol=0.02):
            weights = weights / weight_sum
            weight_normalized = True
        else:
            weight_normalized = False

        districts_used: list[str] = []
        districts_missing: list[str] = []
        effective_weights: list[float] = []
        district_rows: list[pd.Series] = []
        used_nfhs4_proxy = False

        for _, seg in grp.iterrows():
            delim_district = str(seg["district"]).strip()
            seg_w = float(seg["district_segment_share"])
            if weight_normalized:
                seg_w = seg_w / weight_sum

            targets = resolve_delimitation_district(state_label, delim_district, alias_table)
            segment_matched = False
            for target in targets:
                lookup_name = str(target["nfhs_district"]).strip()
                eff_w = seg_w * float(target["aggregate_share"])
                nfhs_state = (
                    str(target.get("nfhs4_state", "")).strip()
                    if survey == SURVEY_NFHS4
                    else str(target.get("nfhs5_state", "")).strip()
                ) or None
                row = lookup_district_features_flexible(
                    district_panel,
                    state_label,
                    lookup_name,
                    survey,
                    nfhs_state=nfhs_state,
                )
                if row is None and target.get("census_district"):
                    row = lookup_district_features_flexible(
                        district_panel,
                        state_label,
                        str(target["census_district"]),
                        survey,
                        nfhs_state=nfhs_state,
                    )
                # When NFHS-5 district rows are missing, fall back to NFHS-4 features.
                row_proxy = False
                if row is None and survey == SURVEY_NFHS5:
                    nfhs4_state = str(target.get("nfhs4_state", "")).strip()
                    fallback_names = [
                        lookup_name,
                        str(target.get("census_district", "")).strip(),
                    ]
                    for fallback_name in fallback_names:
                        if not fallback_name or not nfhs4_state:
                            continue
                        row = lookup_district_features_flexible(
                            district_panel,
                            state_label,
                            fallback_name,
                            SURVEY_NFHS4,
                            nfhs_state=nfhs4_state,
                        )
                        if row is not None:
                            break
                if row is None:
                    continue
                if survey == SURVEY_NFHS5 and str(row.get("survey", "")) == SURVEY_NFHS4:
                    row_proxy = True
                    used_nfhs4_proxy = True
                segment_matched = True
                proxy_tag = " (NFHS-4 proxy)" if row_proxy else ""
                label = f"{delim_district}→{lookup_name}{proxy_tag}"
                districts_used.append(label)
                effective_weights.append(eff_w)
                district_rows.append(row)

            if not segment_matched:
                districts_missing.append(delim_district)

        coverage_share = float(sum(effective_weights))
        record: dict = {
            "state": state_label,
            "lok_sabha_constituency": str(constituency).strip(),
            "survey": survey,
            "survey_year": (
                NFHS4_CANONICAL_YEAR if survey == SURVEY_NFHS4 else NFHS5_CANONICAL_YEAR
            ),
            "districts_used": "; ".join(districts_used),
            "districts_missing": "; ".join(districts_missing),
            "coverage_share": coverage_share,
            "aggregation_method": "weighted_district_segment_share",
        }
        if weight_normalized:
            record["aggregation_method"] = "weighted_district_segment_share_normalized"
        if not alias_table.empty:
            record["aggregation_method"] += "_with_delimitation_alias"
        if used_nfhs4_proxy:
            record["aggregation_method"] += "_nfhs4_proxy"

        if not district_rows:
            warnings.warn(
                f"No NFHS district data for {state_label} / {constituency} ({survey}); "
                f"missing districts: {districts_missing}"
            )
            for feat in PANEL_FEATURE_COLUMNS + COUNT_COLUMNS:
                record[feat] = np.nan
            rows.append(record)
            continue

        eff_w = np.array(effective_weights, dtype=float)
        if eff_w.sum() > 0:
            eff_w = eff_w / eff_w.sum()

        for feat in PANEL_FEATURE_COLUMNS:
            vals = []
            ws = []
            for row, w in zip(district_rows, eff_w):
                v = row.get(feat)
                if pd.notna(v):
                    vals.append(float(v))
                    ws.append(w)
            if vals and ws and sum(ws) > 0:
                record[feat] = float(np.average(vals, weights=ws))
            else:
                record[feat] = np.nan

        for count_col in COUNT_COLUMNS:
            total = 0.0
            seen = False
            for row, w in zip(district_rows, eff_w):
                v = pd.to_numeric(row.get(count_col), errors="coerce")
                if pd.notna(v):
                    total += float(v) * w
                    seen = True
            record[count_col] = total if seen else np.nan

        if coverage_share < 0.85:
            warnings.warn(
                f"Low coverage ({coverage_share:.2f}) for {state_label} / {constituency} ({survey})"
            )

        rows.append(record)

    if not rows:
        return pd.DataFrame()

    out = pd.DataFrame(rows)
    col_order = [
        "state",
        "lok_sabha_constituency",
        "survey",
        "survey_year",
        *PANEL_FEATURE_COLUMNS,
        *COUNT_COLUMNS,
        "districts_used",
        "districts_missing",
        "coverage_share",
        "aggregation_method",
    ]
    return out[[c for c in col_order if c in out.columns]]


def build_constituency_change_features(constituency_panel: pd.DataFrame) -> pd.DataFrame:
    if constituency_panel.empty:
        return pd.DataFrame()

    nfhs4 = constituency_panel[constituency_panel["survey"] == SURVEY_NFHS4].set_index(
        ["state", "lok_sabha_constituency"]
    )
    nfhs5 = constituency_panel[constituency_panel["survey"] == SURVEY_NFHS5].set_index(
        ["state", "lok_sabha_constituency"]
    )
    all_keys = sorted(set(nfhs4.index) | set(nfhs5.index))
    rows: list[dict] = []

    for key in all_keys:
        val4 = nfhs4.loc[key] if key in nfhs4.index else None
        val5 = nfhs5.loc[key] if key in nfhs5.index else None
        if isinstance(val4, pd.DataFrame):
            val4 = val4.iloc[0]
        if isinstance(val5, pd.DataFrame):
            val5 = val5.iloc[0]

        base = {
            "state": key[0],
            "lok_sabha_constituency": key[1],
        }
        row = compute_change_row(base, val4, val5)
        row["coverage_share_nfhs4"] = val4["coverage_share"] if val4 is not None else np.nan
        row["coverage_share_nfhs5"] = val5["coverage_share"] if val5 is not None else np.nan
        rows.append(row)

    out = pd.DataFrame(rows)
    col_order = [
        "state",
        "lok_sabha_constituency",
        "has_nfhs4",
        "has_nfhs5",
        "coverage_share_nfhs4",
        "coverage_share_nfhs5",
        *CHANGE_FEATURE_SUFFIXES,
        *ANNUAL_CHANGE_SUFFIXES,
        "change_quality_flag",
    ]
    return out[[c for c in col_order if c in out.columns]]


def missing_share_by_feature(df: pd.DataFrame, features: Iterable[str]) -> dict[str, float]:
    if df.empty:
        return {f: 1.0 for f in features}
    return {f: float(df[f].isna().mean()) if f in df.columns else 1.0 for f in features}
