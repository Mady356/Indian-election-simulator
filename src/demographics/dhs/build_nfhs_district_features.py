"""
Build district-level NFHS aggregated features (when district can be resolved).

District is not in standard NFHS recode files. This module attempts to join
household records to DHS geographic shapefiles via cluster IDs. If no district
column or join is possible, it prints candidate columns and writes an empty
or partial file with NA where needed.

Run as:
    python -m src.demographics.dhs.build_nfhs_district_features
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyreadstat
import shapefile

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from src.config import DHS_EXTRACTED_DIR
from src.demographics.dhs.feature_utils import (
    aggregate_hh_features,
    aggregate_ir_features,
    aggregate_mr_features,
    clean_state_label,
    count_persons,
    find_column,
    find_district_column,
    normalize_weight,
    read_metadata,
    resolve_dta_path,
    state_labels_from_meta,
    weighted_mean,
    weighted_pct,
    derive_hh_indicators,
)
from src.demographics.dhs.paths import (
    DISTRICT_FEATURE_COLUMNS,
    GE_SHAPEFILE_STEMS_NFHS4,
    GE_SHAPEFILE_STEMS_NFHS5,
    NATIONAL_FILESETS,
    NFHS_DISTRICT_FEATURES,
    SURVEY_VERSIONS,
)
from src.demographics.dhs.nfhs4_state_districts import build_nfhs4_state_district_features
from src.config import DEMOGRAPHICS_PROCESSED_DIR

CENSUS_DISTRICT_PATH = DEMOGRAPHICS_PROCESSED_DIR / "census_district_demographics_2011.csv"


def load_ge_lookup(extracted_dir: Path, stems: tuple[str, ...]) -> pd.DataFrame | None:
    for stem in stems:
        shp_dir = extracted_dir / f"ge_{stem}"
        shp = shp_dir / f"{stem}.shp"
        if not shp.exists():
            continue
        sf = shapefile.Reader(str(shp))
        fields = [f[0] for f in sf.fields[1:]]
        rows = [r for r in sf.records()]
        ge = pd.DataFrame(rows, columns=fields)
        ge["cluster_id"] = ge["DHSCLUST"].astype(int)
        ge["district"] = ge["DHSREGNA"].astype(str).str.strip()
        ge["state_or_region"] = ge["ADM1NAME"].astype(str).str.strip()
        ge["urban_rural"] = ge["URBAN_RURA"].astype(str).str.strip()
        cols = ["cluster_id", "district", "state_or_region", "urban_rural", "DHSYEAR"]
        if "ADM1DHS" in ge.columns:
            ge["state_code"] = pd.to_numeric(ge["ADM1DHS"], errors="coerce")
            cols.append("state_code")
        return ge[cols]
    return None


# ADM1NAME values where IAGE7AFL is authoritative over IAGE71FL cluster joins.
GE_FALLBACK_PRIORITY_STATES: frozenset[str] = frozenset({"TELANGANA"})

GE_ATTR_COLS = ("district", "state_or_region", "urban_rural", "DHSYEAR")


def _compute_best_ge_join(
    hr_path: Path,
    ge: pd.DataFrame,
) -> tuple[pd.DataFrame | None, list[str], float, str]:
    """Join HR clusters to a GE layer; return best strategy without rejecting low rates."""
    meta = read_metadata(hr_path)
    district_col, candidates = find_district_column(meta)
    if district_col:
        return None, candidates, 0.0, "microdata_district_column"

    cluster_col = find_column(meta, ["hv001", "hv021", "sh021"], ["psu", "cluster"])
    state_col = find_column(meta, ["hv024"], ["state"])
    weight_col = find_column(meta, ["hv005"], ["household weight"])
    if not cluster_col or not state_col or not weight_col:
        return None, candidates, 0.0, "missing_columns"

    usecols = [cluster_col, state_col, weight_col, "hv206", "hv243a", "hv247", "hv226", "hv205", "hv025", "hv271"]
    usecols = [c for c in usecols if c in meta.column_names]
    df, meta = pyreadstat.read_dta(str(hr_path), usecols=usecols)
    df = df.drop_duplicates(subset=[cluster_col])

    ge_join = ge.copy()
    ge_join["cluster_id_raw"] = ge_join["cluster_id"].astype(int)
    ge_join["cluster_id_div10"] = ge_join["cluster_id_raw"] // 10

    strategies: list[tuple[str, pd.DataFrame, float]] = []

    joined_raw = df.merge(ge_join, left_on=cluster_col, right_on="cluster_id_raw", how="left")
    strategies.append(("raw cluster_id", joined_raw, joined_raw["district"].notna().mean()))

    joined_div10 = df.merge(ge_join, left_on=cluster_col, right_on="cluster_id_div10", how="left")
    strategies.append(("GE DHSCLUST // 10", joined_div10, joined_div10["district"].notna().mean()))

    if state_col in df.columns:
        for mult in (1000, 10000):
            df_comp = df.copy()
            df_comp["_composite"] = (
                pd.to_numeric(df_comp[state_col], errors="coerce").astype("Int64") * mult
                + pd.to_numeric(df_comp[cluster_col], errors="coerce").astype("Int64")
            )
            joined_comp = df_comp.merge(
                ge_join, left_on="_composite", right_on="cluster_id_raw", how="left"
            )
            rate = joined_comp["district"].notna().mean()
            strategies.append((f"hv024*{mult}+hv001", joined_comp, rate))

        if "state_code" in ge_join.columns:
            ge_state = ge_join.dropna(subset=["state_code"]).copy()
            ge_state["state_code"] = ge_state["state_code"].astype(int)
            df_state = df.copy()
            df_state[state_col] = pd.to_numeric(df_state[state_col], errors="coerce").astype("Int64")
            joined_state = df_state.merge(
                ge_state,
                left_on=[state_col, cluster_col],
                right_on=["state_code", "cluster_id_div10"],
                how="left",
            )
            rate = joined_state["district"].notna().mean()
            strategies.append(("state+cluster//10", joined_state, rate))

    strategy, joined, match_rate = max(strategies, key=lambda x: x[2])
    joined = _dedupe_cluster_join(joined, cluster_col)
    match_rate = joined["district"].notna().mean()
    return joined, candidates, match_rate, strategy


def _dedupe_cluster_join(joined: pd.DataFrame, cluster_col: str) -> pd.DataFrame:
    """GE // 10 joins can be many-to-one; keep the best row per HR cluster."""
    if cluster_col not in joined.columns or joined.empty:
        return joined
    ranked = joined.copy()
    ranked["_has_district"] = ranked["district"].notna().astype(int)
    ge_state = ranked["state_or_region"].astype(str).str.upper()
    hr_code = pd.to_numeric(ranked.get("hv024"), errors="coerce")
    ranked["_state_score"] = ranked["_has_district"] * 10
    # NFHS-5 HR code 28 = undivided AP; prefer Telangana on 7AFL, coastal AP on 71FL.
    ranked.loc[(hr_code == 28) & (ge_state == "TELANGANA"), "_state_score"] += 5
    ranked.loc[(hr_code == 28) & (ge_state == "ANDHRA PRADESH"), "_state_score"] += 4
    ranked = ranked.sort_values([cluster_col, "_state_score"], ascending=[True, False])
    return ranked.drop_duplicates(subset=[cluster_col], keep="first").drop(
        columns=["_has_district", "_state_score"], errors="ignore"
    )


def _coalesce_ge_joins(
    primary: pd.DataFrame,
    fallback: pd.DataFrame,
    cluster_col: str,
) -> pd.DataFrame:
    """Fill unmatched clusters from a secondary GE layer (e.g. Telangana on IAGE7AFL)."""
    fb_cols = {col: f"{col}_fb" for col in GE_ATTR_COLS if col in fallback.columns}
    fb_sub = fallback[[cluster_col, *fb_cols.keys()]].rename(columns=fb_cols)
    out = primary.merge(fb_sub, on=cluster_col, how="left")

    for col, fb_col in fb_cols.items():
        missing = out[col].isna()
        out.loc[missing, col] = out.loc[missing, fb_col]

        if col in GE_ATTR_COLS and "state_or_region_fb" in out.columns:
            priority = (
                out["state_or_region_fb"].astype(str).str.upper().isin(GE_FALLBACK_PRIORITY_STATES)
                & out["district_fb"].notna()
            )
            out.loc[priority, col] = out.loc[priority, fb_col]

    drop_cols = [c for c in out.columns if c.endswith("_fb")]
    return out.drop(columns=drop_cols)


def attach_district_from_ge(
    hr_path: Path,
    ge: pd.DataFrame,
    *,
    min_match_rate: float = 0.40,
    label: str = "",
) -> tuple[pd.DataFrame | None, list[str]]:
    joined, candidates, match_rate, strategy = _compute_best_ge_join(hr_path, ge)
    if joined is None:
        return None, candidates

    prefix = f"{label} " if label else ""
    print(f"  {prefix}GE join ({strategy}): {match_rate*100:.1f}%")

    if match_rate < min_match_rate:
        print(f"  {prefix}Join rate below {min_match_rate*100:.0f}% threshold.")
        return None, candidates

    return joined, candidates


def hybrid_attach_district_from_ge(
    hr_path: Path,
    ge_primary: pd.DataFrame,
    ge_fallback: pd.DataFrame,
) -> tuple[pd.DataFrame | None, list[str]]:
    """
    Prefer the high-match NFHS-4-era GE layer, then fill gaps from NFHS-5 GPS.

    IAGE71FL matches ~90% nationally but misses Telangana; IAGE7AFL recovers
    Telangana and several other states at lower overall match rates.
    """
    primary, candidates, rate_primary, strat_primary = _compute_best_ge_join(hr_path, ge_primary)
    fallback, candidates_fb, rate_fallback, strat_fallback = _compute_best_ge_join(hr_path, ge_fallback)

    if primary is None and fallback is None:
        return None, candidates or candidates_fb

    if primary is None:
        print(f"  GE join fallback only ({strat_fallback}): {rate_fallback*100:.1f}%")
        if rate_fallback < 0.40:
            return None, candidates_fb
        return fallback, candidates_fb

    if fallback is None:
        print(f"  GE join ({strat_primary}): {rate_primary*100:.1f}%")
        if rate_primary < 0.40:
            return None, candidates
        return primary, candidates

    cluster_col = find_column(read_metadata(hr_path), ["hv001", "hv021"], ["psu", "cluster"]) or "hv001"
    combined = _coalesce_ge_joins(primary, fallback, cluster_col)
    combined_rate = combined["district"].notna().mean()
    filled = int((primary["district"].isna() & combined["district"].notna()).sum())
    print(
        f"  Hybrid GE join: {strat_primary}@{rate_primary*100:.1f}% + "
        f"{strat_fallback}@{rate_fallback*100:.1f}% → {combined_rate*100:.1f}% "
        f"(+{filled} clusters from fallback)"
    )
    if combined_rate < 0.40:
        print("  Hybrid join rate below 40% threshold.")
        return None, candidates
    return combined, candidates


def aggregate_district_frame(joined: pd.DataFrame, version: str) -> pd.DataFrame:
    derived = derive_hh_indicators(joined, read_metadata(resolve_dta_path(DHS_EXTRACTED_DIR, NATIONAL_FILESETS[version]["HR"])))
    for k, v in derived.items():
        joined[k] = v.values
    joined["_w"] = normalize_weight(joined["hv005"])

    rows = []
    for (state, district), grp in joined.groupby(["state_or_region", "district"], dropna=True):
        if not district or district.lower() == "nan":
            continue
        row = {
            "survey": SURVEY_VERSIONS[version]["survey"],
            "survey_year": SURVEY_VERSIONS[version]["survey_year"],
            "state": state,
            "district": district,
            "household_count": len(grp),
            "person_count": np.nan,
            "electricity_pct": weighted_pct(pd.to_numeric(grp["hv206"], errors="coerce"), grp["_w"], {1}),
            "mobile_phone_pct": weighted_pct(pd.to_numeric(grp["hv243a"], errors="coerce"), grp["_w"], {1}),
            "bank_account_pct": weighted_pct(pd.to_numeric(grp["hv247"], errors="coerce"), grp["_w"], {1}),
            "improved_sanitation_pct": weighted_pct(grp.get("improved_toilet", pd.Series(dtype=float)), grp["_w"], {1.0}),
            "lpg_pct": weighted_pct(grp.get("lpg_fuel", pd.Series(dtype=float)), grp["_w"], {1.0}),
            "urban_pct": weighted_pct(pd.to_numeric(grp["hv025"], errors="coerce"), grp["_w"], {1}),
            "wealth_index_mean": weighted_mean(pd.to_numeric(grp["hv271"], errors="coerce"), grp["_w"]),
            "internet_pct": np.nan,
            "women_secondary_edu_pct": np.nan,
            "female_literacy_pct": np.nan,
            "male_literacy_pct": np.nan,
            "fertility_rate": np.nan,
        }
        rows.append(row)
    return pd.DataFrame(rows)


def main() -> None:
    frames = []

    # NFHS-5: national HR + hybrid GE join (IAGE71FL primary, IAGE7AFL fallback for Telangana)
    ge71 = load_ge_lookup(DHS_EXTRACTED_DIR, ("IAGE71FL",))
    ge7a = load_ge_lookup(DHS_EXTRACTED_DIR, ("IAGE7AFL",))

    version = "52"
    stems = NATIONAL_FILESETS[version]
    hr = resolve_dta_path(DHS_EXTRACTED_DIR, stems["HR"])
    if hr:
        print(f"\nNFHS version {version}:")
        if ge71 is not None and ge7a is not None:
            joined, _ = hybrid_attach_district_from_ge(hr, ge71, ge7a)
        elif ge71 is not None:
            joined, _ = attach_district_from_ge(hr, ge71)
        elif ge7a is not None:
            joined, _ = attach_district_from_ge(hr, ge7a)
        else:
            joined = None
            print("No GE shapefile found. Extract IAGE71FL and IAGE7AFL first.")
        if joined is not None:
            frames.append(aggregate_district_frame(joined, version))
        else:
            print("  District features not built for NFHS-5.")
    else:
        print("SKIP version 52: HR file missing")

    # NFHS-4: state-level HR/IR with census district names (avoids numeric sdist codes)
    if CENSUS_DISTRICT_PATH.exists():
        print("\nNFHS version 42 (state-level extracts):")
        census = pd.read_csv(CENSUS_DISTRICT_PATH)
        nfhs4_state = build_nfhs4_state_district_features(DHS_EXTRACTED_DIR, census)
        if not nfhs4_state.empty:
            frames.append(nfhs4_state)
        else:
            print("  No state-level NFHS-4 district rows produced.")
    else:
        print(f"WARNING: Missing {CENSUS_DISTRICT_PATH} — skipping NFHS-4 state build.")

    NFHS_DISTRICT_FEATURES.parent.mkdir(parents=True, exist_ok=True)
    if frames:
        df = pd.concat(frames, ignore_index=True)
        cols = [c for c in DISTRICT_FEATURE_COLUMNS if c in df.columns]
        df = df[cols]
        df.to_csv(NFHS_DISTRICT_FEATURES, index=False)
        n_districts = df["district"].nunique() if "district" in df.columns else 0
        print(f"\nSaved: {NFHS_DISTRICT_FEATURES} ({len(df)} rows, {n_districts} districts)")
    else:
        pd.DataFrame(columns=DISTRICT_FEATURE_COLUMNS).to_csv(NFHS_DISTRICT_FEATURES, index=False)
        print(f"\nWrote empty district template: {NFHS_DISTRICT_FEATURES}")
        print("District could not be resolved — inspect variable dictionary and GE join keys.")


if __name__ == "__main__":
    main()
