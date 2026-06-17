"""
Shared helpers for weighted NFHS aggregation from Stata microdata.

Privacy: functions read microdata in memory only; callers must write aggregated
outputs. Never export row-level records.
"""

from __future__ import annotations

import re
import warnings
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pyreadstat

from src.demographics.dhs.paths import INVENTORY_CANDIDATES

IMPROVED_TOILET_CODES = {10, 11, 12, 13, 14, 15, 21, 22}
LPG_FUEL_CODE = 2
LITERATE_CODES = {1, 2}
SECONDARY_PLUS_V106 = {2, 3}
SECONDARY_PLUS_V149 = {4, 5}

HH_INDICATOR_SPECS: dict[str, dict[str, Any]] = {
    "electricity_pct": {
        "candidates": ["hv206"],
        "keywords": ["electricity"],
        "yes_values": {1},
    },
    "mobile_phone_pct": {
        "candidates": ["hv243a", "sh47k", "hv221"],
        "keywords": ["mobile telephone", "mobile phone", "telephone"],
        "yes_values": {1},
    },
    "bank_account_pct": {
        "candidates": ["hv247"],
        "keywords": ["bank account", "post office account"],
        "yes_values": {1},
    },
    "internet_pct": {
        "candidates": [],
        "keywords": ["internet", "broadband", "wifi"],
        "yes_values": {1},
    },
    "improved_sanitation_pct": {
        "candidates": ["hv205"],
        "keywords": ["toilet facility", "sanitation"],
        "derived": "improved_toilet",
    },
    "lpg_pct": {
        "candidates": ["hv226"],
        "keywords": ["cooking fuel", "lpg"],
        "derived": "lpg_fuel",
    },
    "urban_pct": {
        "candidates": ["hv025"],
        "keywords": ["type of place", "urban"],
        "yes_values": {1},
    },
    "wealth_index_mean": {
        "candidates": ["hv271", "hv270"],
        "keywords": ["wealth index factor score", "wealth index"],
        "aggregate": "mean",
    },
}

IR_SPECS: dict[str, dict[str, Any]] = {
    "female_literacy_pct": {
        "candidates": ["v155", "s119", "v108"],
        "keywords": ["literacy", "read and write", "can read"],
        "yes_values": {1, 2},
        "yes_values_s119": {1},
    },
    "women_secondary_edu_pct": {
        "candidates": ["v106", "v149"],
        "keywords": ["secondary", "educational attainment", "highest educational"],
        "yes_values_v106": SECONDARY_PLUS_V106,
        "yes_values_v149": SECONDARY_PLUS_V149,
    },
    "fertility_rate": {
        "candidates": ["v201"],
        "keywords": ["children ever born", "fertility"],
        "derived": "tfr",
    },
}

MR_SPECS: dict[str, dict[str, Any]] = {
    "male_literacy_pct": {
        "candidates": ["mv155"],
        "keywords": ["literacy"],
        "yes_values": LITERATE_CODES,
    },
}


def load_inventory() -> pd.DataFrame:
    """Load DHS file inventory; fall back to audit CSV."""
    for path in INVENTORY_CANDIDATES:
        if path.exists():
            df = pd.read_csv(path)
            if "parse_ok" not in df.columns and "filename" in df.columns:
                from src.demographics.dhs.filename_parser import parse_dhs_filename

                parsed = df["filename"].map(parse_dhs_filename)
                df["parse_ok"] = [p.parse_ok for p in parsed]
                df["file_format_code"] = [p.file_format_code for p in parsed]
            return df
    raise FileNotFoundError(
        "No DHS inventory found. Run: python -m src.demographics.dhs.audit_dhs_downloads"
    )


def read_metadata(path: Path) -> pyreadstat.metadata_container:
    _, meta = pyreadstat.read_dta(str(path), metadataonly=True)
    return meta


def find_column(
    meta: pyreadstat.metadata_container,
    candidates: list[str],
    keywords: list[str],
) -> str | None:
    """Resolve a column by exact name then keyword search on labels."""
    names = {c.lower(): c for c in meta.column_names}
    for cand in candidates:
        if cand.lower() in names:
            return names[cand.lower()]
    kw = [k.lower() for k in keywords]
    for col in meta.column_names:
        label = (meta.column_names_to_labels.get(col) or "").lower()
        if any(k in label for k in kw):
            return col
    return None


def normalize_weight(series: pd.Series) -> pd.Series:
    """DHS weights are stored with 6 implied decimals."""
    w = pd.to_numeric(series, errors="coerce")
    if w.dropna().empty:
        return w
    if w.dropna().max() > 1_000:
        w = w / 1_000_000
    return w


def clean_state_label(raw: str | float) -> str:
    if raw is None or (isinstance(raw, float) and np.isnan(raw)):
        return ""
    text = str(raw).strip()
    text = re.sub(r"^\[[^\]]+\]\s*", "", text, flags=re.IGNORECASE)
    return text.title()


def state_labels_from_meta(meta: pyreadstat.metadata_container, col: str) -> dict:
    return meta.variable_value_labels.get(col, {})


def weighted_pct(
    values: pd.Series,
    weights: pd.Series,
    yes_values: set,
) -> float:
    mask = values.notna() & weights.notna() & (weights > 0)
    if not mask.any():
        return np.nan
    yes = mask & values.isin(yes_values)
    return float(weights.loc[yes].sum() / weights.loc[mask].sum() * 100)


def weighted_mean(values: pd.Series, weights: pd.Series) -> float:
    mask = values.notna() & weights.notna() & (weights > 0)
    if not mask.any():
        return np.nan
    return float((values.loc[mask] * weights.loc[mask]).sum() / weights.loc[mask].sum())


def resolve_dta_path(extracted_dir: Path, stem: str) -> Path | None:
    for ext in (".dta", ".DTA"):
        path = extracted_dir / f"{stem}{ext}"
        if path.exists():
            return path
        path = extracted_dir / f"{stem.upper()}{ext}"
        if path.exists():
            return path
    matches = list(extracted_dir.glob(f"{stem}*.dta")) + list(
        extracted_dir.glob(f"{stem}*.DTA")
    )
    return matches[0] if matches else None


def compute_tfr(
    df: pd.DataFrame,
    weight_col: str,
    age_col: str = "v012",
) -> float:
    """
    Estimate total fertility rate from birth history (simplified DHS method).

    Uses births in the three years before interview by five-year age groups.
    Falls back to weighted mean children ever born for women 15-49 if birth
    history columns are unavailable.
    """
    ages = pd.to_numeric(df[age_col], errors="coerce")
    women = df[(ages >= 15) & (ages <= 49)].copy()
    if women.empty:
        return np.nan

    ww = normalize_weight(women[weight_col])
    w_ages = pd.to_numeric(women[age_col], errors="coerce")
    icmc = pd.to_numeric(women.get("v008"), errors="coerce")

    birth_cols = [c for c in women.columns if re.match(r"^b3_\d{2}$", c.lower())]
    if birth_cols and icmc.notna().any():
        asfr: dict[int, float] = {}
        for age in range(15, 50):
            grp = women[w_ages == age]
            if grp.empty:
                asfr[age] = 0.0
                continue
            gw = normalize_weight(grp[weight_col])
            recent = 0.0
            icmc_grp = pd.to_numeric(grp["v008"], errors="coerce")
            for bc in birth_cols:
                bdates = pd.to_numeric(grp[bc], errors="coerce")
                recent += gw[(bdates.notna()) & (icmc_grp - bdates <= 36)].sum()
            person_years = gw.sum()
            asfr[age] = recent / person_years if person_years > 0 else 0.0
        return float(sum(asfr.values()))

    if "v201" in women.columns:
        ceb = pd.to_numeric(women["v201"], errors="coerce")
        mask = ceb.notna() & ww.notna() & (ww > 0)
        if mask.any():
            return float((ceb.loc[mask] * ww.loc[mask]).sum() / ww.loc[mask].sum())
    return np.nan


def derive_hh_indicators(df: pd.DataFrame, meta: pyreadstat.metadata_container) -> dict:
    """Return derived boolean/numeric columns for household indicators."""
    out: dict[str, pd.Series] = {}
    toilet_col = find_column(meta, ["hv205"], ["toilet facility"])
    if toilet_col:
        vals = pd.to_numeric(df[toilet_col], errors="coerce")
        series = vals.isin(IMPROVED_TOILET_CODES).astype(float)
        series[vals.isna()] = np.nan
        out["improved_toilet"] = series

    fuel_col = find_column(meta, ["hv226", "sh37"], ["cooking fuel", "main cooking fuel"])
    if fuel_col:
        vals = pd.to_numeric(df[fuel_col], errors="coerce")
        if fuel_col.lower() == "sh37":
            series = (vals == 8).astype(float)
        else:
            series = (vals == LPG_FUEL_CODE).astype(float)
        series[vals.isna()] = np.nan
        out["lpg_fuel"] = series
    elif "sh38h" in df.columns:
        vals = pd.to_numeric(df["sh38h"], errors="coerce")
        series = (vals == 1).astype(float)
        series[vals.isna()] = np.nan
        out["lpg_fuel"] = series
    return out


def aggregate_hh_features(
    hr_path: Path,
    group_cols: list[str],
) -> tuple[pd.DataFrame, dict[str, str | None]]:
    meta = read_metadata(hr_path)
    state_col = find_column(meta, ["hv024"], ["state"])
    weight_col = find_column(meta, ["hv005", "hv005s"], ["household weight"])
    if not state_col or not weight_col:
        raise ValueError(f"Missing state/weight in {hr_path.name}")

    usecols = list({state_col, weight_col, *group_cols})
    for spec in HH_INDICATOR_SPECS.values():
        usecols.extend(spec.get("candidates", []))
    usecols.extend(["sh37", "sh38h"])
    usecols = list(dict.fromkeys(c for c in usecols if c in meta.column_names))

    df, meta = pyreadstat.read_dta(str(hr_path), usecols=usecols)
    derived = derive_hh_indicators(df, meta)
    for name, series in derived.items():
        df[name] = series

    df["_w"] = normalize_weight(df[weight_col])
    mapping: dict[str, str | None] = {}

    rows = []
    for keys, grp in df.groupby(group_cols, dropna=False):
        if not isinstance(keys, tuple):
            keys = (keys,)
        row = dict(zip(group_cols, keys))
        row["household_count"] = len(grp)

        for feat, spec in HH_INDICATOR_SPECS.items():
            col = find_column(meta, spec.get("candidates", []), spec.get("keywords", []))
            mapping[feat] = col
            if spec.get("derived"):
                dcol = spec["derived"]
                if dcol in grp.columns:
                    row[feat] = weighted_pct(grp[dcol], grp["_w"], {1.0})
                else:
                    row[feat] = np.nan
            elif spec.get("aggregate") == "mean" and col:
                row[feat] = weighted_mean(pd.to_numeric(grp[col], errors="coerce"), grp["_w"])
            elif col:
                row[feat] = weighted_pct(
                    pd.to_numeric(grp[col], errors="coerce"),
                    grp["_w"],
                    spec.get("yes_values", {1}),
                )
            else:
                row[feat] = np.nan
        rows.append(row)

    return pd.DataFrame(rows), mapping


def aggregate_ir_features(
    ir_path: Path,
    group_cols: list[str],
) -> tuple[pd.DataFrame, dict[str, str | None]]:
    meta = read_metadata(ir_path)
    state_col = find_column(meta, ["v024"], ["state"])
    weight_col = find_column(meta, ["v005", "v005s"], ["women's weight", "weight"])
    if not state_col or not weight_col:
        raise ValueError(f"Missing state/weight in {ir_path.name}")

    usecols = [state_col, weight_col, "v012", "v008", *group_cols]
    for spec in IR_SPECS.values():
        usecols.extend(spec.get("candidates", []))
    usecols.extend(c for c in meta.column_names if re.match(r"^b3_\d{2}$", c.lower()))
    usecols = list(dict.fromkeys(c for c in usecols if c in meta.column_names))

    df, meta = pyreadstat.read_dta(str(ir_path), usecols=usecols)
    df["_w"] = normalize_weight(df[weight_col])
    mapping: dict[str, str | None] = {}
    rows = []

    for keys, grp in df.groupby(group_cols, dropna=False):
        if not isinstance(keys, tuple):
            keys = (keys,)
        row = dict(zip(group_cols, keys))

        for feat, spec in IR_SPECS.items():
            if spec.get("derived") == "tfr":
                row[feat] = compute_tfr(grp, weight_col)
                mapping[feat] = "birth_history_b3_*"
                continue

            col = find_column(meta, spec.get("candidates", []), spec.get("keywords", []))
            mapping[feat] = col
            if feat == "women_secondary_edu_pct":
                if col == "v106":
                    yes = spec["yes_values_v106"]
                elif col == "v149":
                    yes = spec["yes_values_v149"]
                else:
                    yes = SECONDARY_PLUS_V149
                row[feat] = weighted_pct(pd.to_numeric(grp[col], errors="coerce"), grp["_w"], yes) if col else np.nan
            elif feat == "female_literacy_pct" and col:
                if col == "s119":
                    yes = spec.get("yes_values_s119", {1})
                else:
                    yes = spec.get("yes_values", LITERATE_CODES)
                row[feat] = weighted_pct(pd.to_numeric(grp[col], errors="coerce"), grp["_w"], yes)
            elif col:
                row[feat] = weighted_pct(
                    pd.to_numeric(grp[col], errors="coerce"),
                    grp["_w"],
                    spec.get("yes_values", {1}),
                )
            else:
                row[feat] = np.nan
        rows.append(row)

    return pd.DataFrame(rows), mapping


def aggregate_mr_features(
    mr_path: Path,
    group_cols: list[str],
) -> tuple[pd.DataFrame, dict[str, str | None]]:
    meta = read_metadata(mr_path)
    state_col = find_column(meta, ["mv024"], ["state"])
    weight_col = find_column(meta, ["mv005"], ["men's weight", "weight"])
    if not state_col or not weight_col:
        return pd.DataFrame(columns=group_cols), {}

    usecols = [state_col, weight_col]
    for spec in MR_SPECS.values():
        usecols.extend(spec.get("candidates", []))
    usecols = list(dict.fromkeys(c for c in usecols if c in meta.column_names))

    df, meta = pyreadstat.read_dta(str(mr_path), usecols=usecols)
    df["_w"] = normalize_weight(df[weight_col])
    mapping: dict[str, str | None] = {}
    rows = []

    for keys, grp in df.groupby(group_cols, dropna=False):
        if not isinstance(keys, tuple):
            keys = (keys,)
        row = dict(zip(group_cols, keys))
        for feat, spec in MR_SPECS.items():
            col = find_column(meta, spec.get("candidates", []), spec.get("keywords", []))
            mapping[feat] = col
            row[feat] = (
                weighted_pct(pd.to_numeric(grp[col], errors="coerce"), grp["_w"], spec.get("yes_values", {1}))
                if col
                else np.nan
            )
        rows.append(row)

    return pd.DataFrame(rows), mapping


def count_persons(pr_path: Path, group_cols: list[str]) -> pd.DataFrame:
    meta = read_metadata(pr_path)
    state_col = find_column(meta, ["hv024"], ["state"])
    if not state_col:
        return pd.DataFrame(columns=[*group_cols, "person_count"])

    usecols = list(dict.fromkeys([*group_cols, state_col]))
    usecols = [c for c in usecols if c in meta.column_names]
    df, _ = pyreadstat.read_dta(str(pr_path), usecols=usecols)
    counts = df.groupby(group_cols, dropna=False).size().reset_index(name="person_count")
    return counts


def find_district_column(meta: pyreadstat.metadata_container) -> tuple[str | None, list[str]]:
    """Return best district column and candidate list for diagnostics."""
    candidates = []
    preferred = {"sdist", "ssdist", "shdist", "district", "dhsregna"}
    for col in meta.column_names:
        label = (meta.column_names_to_labels.get(col) or "").lower()
        if col.lower() in preferred or label == "district" or label.startswith("district "):
            candidates.append(col)
    return (candidates[0] if candidates else None, candidates)


def print_missing_warnings(mapping: dict[str, str | None], prefix: str = "") -> list[str]:
    missing = [k for k, v in mapping.items() if v is None]
    for feat in missing:
        warnings.warn(f"{prefix}Variable not found for {feat}; leaving NA")
    return missing
