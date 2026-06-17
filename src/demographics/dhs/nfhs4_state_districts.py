"""
Build NFHS-4 district features from state-level HR/IR files with census district names.

National IAHR42FL stores districts as numeric sdist codes. State extracts use the
same codes but are processed per state and mapped to Census 2011 district names.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from src.demographics.dhs.feature_utils import (
    aggregate_hh_features,
    aggregate_ir_features,
    find_column,
    read_metadata,
    resolve_dta_path,
)
from src.demographics.dhs.paths import DISTRICT_FEATURE_COLUMNS, SURVEY_VERSIONS
from src.demographics.dhs_filename_parser import INDIA_GEO_CODES
from src.demographics.nfhs.state_maps import NFHS4_TO_CENSUS_STATE
from src.reference.delimitation_utils import normalize_key


def _census_state_for_nfhs_label(nfhs_state: str, census_states: set[str]) -> str | None:
    """Resolve NFHS hv024 state label to census state_2011."""
    direct = nfhs_state.strip().upper()
    if direct in census_states:
        return direct
    mapped = NFHS4_TO_CENSUS_STATE.get(nfhs_state.strip())
    if mapped and mapped in census_states:
        return mapped
    for census_state in census_states:
        if normalize_key(census_state) == normalize_key(nfhs_state):
            return census_state
    return None


def _sdist_to_census_name(
    sdist_code: int,
    census_state: str,
    census_by_state: dict[str, pd.DataFrame],
) -> str:
    state_df = census_by_state.get(census_state)
    if state_df is None or state_df.empty:
        return str(sdist_code)
    ranked = state_df.sort_values("district_code_2011").reset_index(drop=True)
    if 1 <= sdist_code <= len(ranked):
        return str(ranked.iloc[sdist_code - 1]["district"])
    return str(sdist_code)


def _nfhs_state_from_file_prefix(prefix: str) -> str | None:
    """Map DHS file prefix (e.g. AP) to NFHS-4 state label."""
    return INDIA_GEO_CODES.get(prefix.upper())


def build_nfhs4_state_district_features(
    extracted_dir: Path,
    census_districts: pd.DataFrame,
) -> pd.DataFrame:
    """Aggregate state-level NFHS-4 HR/IR files with named districts."""
    census_sub = census_districts[["state_2011", "district", "district_code_2011"]].drop_duplicates()
    census_by_state = {
        state: grp.copy() for state, grp in census_sub.groupby("state_2011")
    }
    census_states = set(census_by_state)

    hr_files = sorted(
        p
        for p in extracted_dir.glob("*HR42FL*")
        if p.suffix.lower() == ".dta" and not p.name.upper().startswith("IAHR42")
    )

    frames: list[pd.DataFrame] = []
    for hr_path in hr_files:
        prefix = hr_path.name.upper()[:2]
        nfhs_state = _nfhs_state_from_file_prefix(prefix)
        if not nfhs_state:
            print(f"  SKIP {hr_path.name}: unknown prefix {prefix}")
            continue
        census_state = _census_state_for_nfhs_label(nfhs_state, census_states)
        if census_state is None:
            print(f"  SKIP {hr_path.name}: no census state for {nfhs_state}")
            continue

        ir_stem = f"{prefix}IR42FL"
        ir_path = resolve_dta_path(extracted_dir, ir_stem)

        try:
            hh_df, _ = aggregate_hh_features(hr_path, ["sdist", "hv024"])
        except (ValueError, OSError) as exc:
            print(f"  SKIP {hr_path.name}: {exc}")
            continue

        hh_df["state"] = nfhs_state
        hh_df["sdist_code"] = pd.to_numeric(hh_df["sdist"], errors="coerce")

        named_districts: list[str] = []
        for _, row in hh_df.iterrows():
            code = int(row["sdist_code"]) if pd.notna(row["sdist_code"]) else 0
            named_districts.append(_sdist_to_census_name(code, census_state, census_by_state))
        hh_df["district"] = named_districts
        hh_df["survey"] = SURVEY_VERSIONS["42"]["survey"]
        hh_df["survey_year"] = SURVEY_VERSIONS["42"]["survey_year"]

        if ir_path:
            ir_meta = read_metadata(ir_path)
            ir_state_col = find_column(ir_meta, ["v024"], ["state"])
            if ir_state_col and "sdist" in ir_meta.column_names:
                ir_df, _ = aggregate_ir_features(ir_path, ["sdist", ir_state_col])
                ir_df = ir_df.rename(columns={"sdist": "sdist_code"})
                ir_df["state"] = nfhs_state
                ir_named: list[str] = []
                for _, row in ir_df.iterrows():
                    code = int(pd.to_numeric(row["sdist_code"], errors="coerce"))
                    ir_named.append(_sdist_to_census_name(code, census_state, census_by_state))
                ir_df["district"] = ir_named
                ir_cols = [c for c in ir_df.columns if c not in hh_df.columns or c in {"state", "district"}]
                hh_df = hh_df.merge(ir_df[ir_cols], on=["state", "district"], how="left")

        frames.append(hh_df)
        print(f"  {hr_path.name}: {len(hh_df)} district rows")

    if not frames:
        return pd.DataFrame(columns=DISTRICT_FEATURE_COLUMNS)

    out = pd.concat(frames, ignore_index=True)
    cols = [c for c in DISTRICT_FEATURE_COLUMNS if c in out.columns]
    for col in DISTRICT_FEATURE_COLUMNS:
        if col not in out.columns:
            out[col] = np.nan
    return out[DISTRICT_FEATURE_COLUMNS]
