"""Load delimitation → census / NFHS district alias table for panel joins."""

from __future__ import annotations

import warnings
from functools import lru_cache
from pathlib import Path

import pandas as pd

from src.reference.delimitation_utils import normalize_key
from src.reference.delimitation_paths import DELIMITATION_CENSUS_DISTRICT_ALIAS


@lru_cache(maxsize=1)
def load_district_alias_table(path: str | None = None) -> pd.DataFrame:
    alias_path = Path(path) if path else DELIMITATION_CENSUS_DISTRICT_ALIAS
    if not alias_path.exists():
        warnings.warn(
            f"District alias table missing: {alias_path}. "
            "Run: python -m src.reference.build_delimitation_census_district_alias"
        )
        return pd.DataFrame()
    return pd.read_csv(alias_path)


def resolve_delimitation_district(
    delim_state: str,
    delim_district: str,
    alias_table: pd.DataFrame | None = None,
) -> list[dict]:
    """
  Return one or more target districts for a delimitation district label.

    Each dict: nfhs_district, census_district, nfhs4_state, nfhs5_state,
    aggregate_share, confidence
    """
    table = alias_table if alias_table is not None else load_district_alias_table()
    if table.empty:
        return [
            {
                "nfhs_district": delim_district.strip(),
                "census_district": delim_district.strip(),
                "nfhs4_state": delim_state.strip(),
                "nfhs5_state": delim_state.strip(),
                "aggregate_share": 1.0,
                "confidence": "low",
                "match_method": "passthrough",
            }
        ]

    state_key = normalize_key(delim_state)
    district_key = normalize_key(delim_district)
    hits = table[
        (table["delimitation_state"].map(normalize_key) == state_key)
        & (table["delimitation_district_key"] == district_key)
    ]
    if hits.empty:
        hits = table[
            (table["delimitation_state"].map(normalize_key) == state_key)
            & (table["delimitation_district"].map(normalize_key) == district_key)
        ]

    if hits.empty:
        warnings.warn(f"No alias for delimitation district: {delim_state} / {delim_district}")
        return [
            {
                "nfhs_district": delim_district.strip(),
                "census_district": delim_district.strip(),
                "nfhs4_state": delim_state.strip(),
                "nfhs5_state": delim_state.strip(),
                "aggregate_share": 1.0,
                "confidence": "low",
                "match_method": "unmatched",
            }
        ]

    out: list[dict] = []
    for _, row in hits.iterrows():
        nfhs_name = str(row.get("nfhs_district", "")).strip() or str(row["census_district"]).strip()
        nfhs4_state = str(row.get("nfhs4_state", row.get("nfhs_state", ""))).strip()
        nfhs5_state = str(row.get("nfhs5_state", row.get("nfhs_state", ""))).strip()
        out.append(
            {
                "nfhs_district": nfhs_name,
                "census_district": str(row["census_district"]).strip(),
                "nfhs4_state": nfhs4_state or delim_state.strip(),
                "nfhs5_state": nfhs5_state or delim_state.strip(),
                "aggregate_share": float(row.get("aggregate_share", 1.0)),
                "confidence": str(row.get("confidence", "medium")),
                "match_method": str(row.get("match_method", "")),
            }
        )
    return out
