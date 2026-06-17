"""
Diagnose NFHS-5 household-records (HR) to GE shapefile cluster joins.

NFHS-5 HR cluster IDs (hv001) often differ from GE DHSCLUST encoding — e.g.
HR 1001 vs GE 10001. This script inspects candidate keys, tests transform
strategies, and writes join success rates for choosing the correct mapping.

Run as:
    python -m src.demographics.dhs.debug_nfhs5_ge_join

Output:
    data/demographics/processed/nfhs5_ge_join_diagnostics.csv
"""

from __future__ import annotations

import sys
from collections.abc import Callable
from pathlib import Path

import numpy as np
import pandas as pd
import pyreadstat
import shapefile

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from src.config import DHS_EXTRACTED_DIR
from src.demographics.dhs.feature_utils import find_column, read_metadata, resolve_dta_path
from src.demographics.dhs.paths import (
    GE_SHAPEFILE_STEMS,
    NATIONAL_FILESETS,
    NFHS5_GE_JOIN_DIAGNOSTICS,
)

HR_KEY_CANDIDATES = ("hv001", "hv021", "hv024", "hv023")
GE_ID_CANDIDATES = ("DHSCLUST", "CLUSTID", "CLUSTER", "DHSID")


def load_ge_table(extracted_dir: Path) -> tuple[pd.DataFrame, str]:
    """Load the first available NFHS-5 GE shapefile as a flat attribute table."""
    for stem in GE_SHAPEFILE_STEMS:
        shp_dir = extracted_dir / f"ge_{stem}"
        shp = shp_dir / f"{stem}.shp"
        if not shp.exists():
            continue
        sf = shapefile.Reader(str(shp))
        fields = [f[0] for f in sf.fields[1:]]
        rows = [dict(zip(fields, rec)) for rec in sf.records()]
        ge = pd.DataFrame(rows)
        ge["source_shapefile"] = stem
        return ge, stem
    raise FileNotFoundError(
        "No GE shapefile found under "
        f"{extracted_dir}/ge_<stem>/. Run extract_dhs_zips and build_dhs_geospatial_layer first."
    )


def load_hr_keys(hr_path: Path) -> tuple[pd.DataFrame, pyreadstat.metadata_container]:
    """Load one row per cluster with candidate join keys from NFHS-5 HR."""
    meta = read_metadata(hr_path)
    usecols = [c for c in HR_KEY_CANDIDATES if c in meta.column_names]
    if not usecols:
        raise ValueError(f"No HR key columns found in {hr_path.name}")

    df, meta = pyreadstat.read_dta(str(hr_path), usecols=usecols)
    df = df.drop_duplicates(subset=[usecols[0]])
    return df, meta


def numeric_stats(series: pd.Series) -> dict[str, object]:
    s = pd.to_numeric(series, errors="coerce").dropna()
    if s.empty:
        return {"min": np.nan, "max": np.nan, "unique": 0, "sample": []}
    sample = sorted(s.unique().tolist())[:8]
    return {
        "min": int(s.min()),
        "max": int(s.max()),
        "unique": int(s.nunique()),
        "sample": sample,
    }


def print_key_report(label: str, stats: dict[str, object]) -> None:
    print(f"  {label}:")
    print(f"    min={stats['min']} max={stats['max']} unique={stats['unique']}")
    print(f"    sample={stats['sample']}")


def build_strategies(
    hr_col: str,
    ge_col: str,
) -> list[tuple[str, Callable[[pd.Series], pd.Series], str]]:
    """Return (name, transform, description) tuples for HR-side keys."""
    return [
        ("raw", lambda s: pd.to_numeric(s, errors="coerce"), "Use HR key unchanged"),
        (
            "hr_times_10",
            lambda s: pd.to_numeric(s, errors="coerce") * 10,
            "HR key * 10 (pad cluster to GE width)",
        ),
        (
            "hr_times_10_plus_1",
            lambda s: pd.to_numeric(s, errors="coerce") * 10 + 1,
            "HR key * 10 + 1 (GE often ends in 1)",
        ),
        (
            "hr_as_string",
            lambda s: pd.to_numeric(s, errors="coerce").astype("Int64").astype(str),
            "HR key cast to string",
        ),
        (
            "ge_floor_div_10",
            lambda s: pd.to_numeric(s, errors="coerce"),
            "Match GE floor(key/10) to HR (transform applied on GE side)",
        ),
    ]


def evaluate_join(
    hr: pd.DataFrame,
    ge: pd.DataFrame,
    hr_col: str,
    ge_col: str,
    strategy: str,
    hr_transform: Callable[[pd.Series], pd.Series],
    ge_transform: Callable[[pd.Series], pd.Series] | None = None,
) -> dict[str, object]:
    hr_keys = hr_transform(hr[hr_col])
    ge_keys = ge_transform(ge[ge_col]) if ge_transform else pd.to_numeric(ge[ge_col], errors="coerce")

    hr_df = pd.DataFrame({"hr_key": hr_keys}).dropna()
    ge_df = pd.DataFrame({"ge_key": ge_keys}).dropna()

    if strategy == "hr_as_string":
        hr_df["hr_key"] = hr_df["hr_key"].astype(str)
        ge_df["ge_key"] = ge_df["ge_key"].astype("Int64").astype(str)
    else:
        hr_df["hr_key"] = pd.to_numeric(hr_df["hr_key"], errors="coerce")
        ge_df["ge_key"] = pd.to_numeric(ge_df["ge_key"], errors="coerce")
        hr_df = hr_df.dropna()
        ge_df = ge_df.dropna()

    ge_set = set(ge_df["ge_key"].tolist())
    hr_set = set(hr_df["hr_key"].tolist())
    matched = hr_set & ge_set
    hr_total = len(hr_set)
    match_rate = len(matched) / hr_total if hr_total else 0.0

    return {
        "strategy": strategy,
        "hr_key_column": hr_col,
        "ge_key_column": ge_col,
        "hr_unique_count": hr_total,
        "ge_unique_count": len(ge_set),
        "matched_clusters": len(matched),
        "match_rate_pct": round(match_rate * 100, 2),
        "hr_key_min": int(hr_df["hr_key"].min()) if hr_total and strategy != "hr_as_string" else "",
        "hr_key_max": int(hr_df["hr_key"].max()) if hr_total and strategy != "hr_as_string" else "",
        "ge_key_min": int(ge_df["ge_key"].min()) if len(ge_set) and strategy != "hr_as_string" else "",
        "ge_key_max": int(ge_df["ge_key"].max()) if len(ge_set) and strategy != "hr_as_string" else "",
        "hr_key_sample": sorted(list(hr_set))[:5],
        "ge_key_sample": sorted(list(ge_set))[:5],
        "notes": "",
    }


def evaluate_ge_div10_join(hr: pd.DataFrame, ge: pd.DataFrame, hr_col: str, ge_col: str) -> dict[str, object]:
    """GE key floor(/10) matched to raw HR key — fixes 10001 -> 1001 pattern."""
    hr_keys = pd.to_numeric(hr[hr_col], errors="coerce").dropna().astype(int)
    ge_keys = pd.to_numeric(ge[ge_col], errors="coerce").dropna()
    ge_mapped = (ge_keys // 10).astype(int)

    hr_set = set(hr_keys.tolist())
    ge_set = set(ge_mapped.tolist())
    matched = hr_set & ge_set
    hr_total = len(hr_set)
    match_rate = len(matched) / hr_total if hr_total else 0.0

    return {
        "strategy": "ge_floor_div_10",
        "hr_key_column": hr_col,
        "ge_key_column": ge_col,
        "hr_unique_count": hr_total,
        "ge_unique_count": len(ge_set),
        "matched_clusters": len(matched),
        "match_rate_pct": round(match_rate * 100, 2),
        "hr_key_min": int(hr_keys.min()) if hr_total else "",
        "hr_key_max": int(hr_keys.max()) if hr_total else "",
        "ge_key_min": int(ge_keys.min()) if len(ge_keys) else "",
        "ge_key_max": int(ge_keys.max()) if len(ge_keys) else "",
        "hr_key_sample": sorted(list(hr_set))[:5],
        "ge_key_sample": sorted(list(ge_set))[:5],
        "notes": "Transform GE DHSCLUST with floor(key/10) before joining to HR",
    }


def evaluate_ge_remove_trailing_digit(
    hr: pd.DataFrame, ge: pd.DataFrame, hr_col: str, ge_col: str
) -> dict[str, object]:
    """GE key with last digit removed: (key - key%10)/10 or key // 10."""
    return evaluate_ge_div10_join(hr, ge, hr_col, ge_col) | {
        "strategy": "ge_remove_trailing_digit",
        "notes": "Remove trailing digit from GE key (integer division by 10)",
    }


def evaluate_state_prefix_join(
    hr: pd.DataFrame,
    ge: pd.DataFrame,
    hr_state_col: str,
    hr_cluster_col: str,
    ge_state_col: str,
    ge_cluster_col: str,
    multiplier: int,
) -> dict[str, object]:
    """Composite key: state_code * multiplier + cluster."""
    hr_state = pd.to_numeric(hr[hr_state_col], errors="coerce")
    hr_cluster = pd.to_numeric(hr[hr_cluster_col], errors="coerce")
    hr_composite = hr_state * multiplier + hr_cluster

    ge_cluster = pd.to_numeric(ge[ge_cluster_col], errors="coerce")
    hr_set = set(hr_composite.dropna().astype(int).tolist())
    ge_set = set(ge_cluster.dropna().astype(int).tolist())
    matched = hr_set & ge_set
    hr_total = len(hr_set)
    match_rate = len(matched) / hr_total if hr_total else 0.0

    return {
        "strategy": f"state_prefix_hv024_x{multiplier}_plus_hv001",
        "hr_key_column": f"{hr_state_col}+{hr_cluster_col}",
        "ge_key_column": ge_cluster_col,
        "hr_unique_count": hr_total,
        "ge_unique_count": len(ge_set),
        "matched_clusters": len(matched),
        "match_rate_pct": round(match_rate * 100, 2),
        "hr_key_min": int(hr_composite.min()) if hr_total else "",
        "hr_key_max": int(hr_composite.max()) if hr_total else "",
        "ge_key_min": int(ge_cluster.min()) if len(ge_set) else "",
        "ge_key_max": int(ge_cluster.max()) if len(ge_set) else "",
        "hr_key_sample": sorted(list(hr_set))[:5],
        "ge_key_sample": sorted(list(ge_set))[:5],
        "notes": f"Composite HR key = {hr_state_col} * {multiplier} + {hr_cluster_col}",
    }


def run_diagnostics(hr_path: Path, ge: pd.DataFrame) -> pd.DataFrame:
    hr, meta = load_hr_keys(hr_path)

    print("\n=== NFHS-5 HR key inspection ===")
    for col in HR_KEY_CANDIDATES:
        if col in hr.columns:
            print_key_report(col, numeric_stats(hr[col]))
            label = meta.column_names_to_labels.get(col, "")
            if label:
                print(f"    label: {label}")

    ge_id_col = next((c for c in GE_ID_CANDIDATES if c in ge.columns), None)
    if ge_id_col is None:
        ge_id_col = "DHSCLUST" if "DHSCLUST" in ge.columns else ge.columns[0]

    print("\n=== GE shapefile columns ===")
    print(f"  shapefile: {ge['source_shapefile'].iloc[0]}")
    print(f"  columns: {list(ge.columns)}")
    print_key_report(ge_id_col, numeric_stats(ge[ge_id_col]))
    for col in ("ADM1NAME", "DHSREGNA", "DHSYEAR", "URBAN_RURA"):
        if col in ge.columns:
            print(f"  {col} unique={ge[col].nunique()} sample={ge[col].dropna().unique()[:3].tolist()}")

    hr_cluster_col = "hv001" if "hv001" in hr.columns else hr.columns[0]
    rows: list[dict[str, object]] = []

    for strategy, transform, note in build_strategies(hr_cluster_col, ge_id_col):
        row = evaluate_join(hr, ge, hr_cluster_col, ge_id_col, strategy, transform)
        row["notes"] = note
        rows.append(row)

    rows.append(evaluate_ge_div10_join(hr, ge, hr_cluster_col, ge_id_col))
    rows.append(evaluate_ge_remove_trailing_digit(hr, ge, hr_cluster_col, ge_id_col))

    if "hv021" in hr.columns:
        row = evaluate_join(
            hr,
            ge,
            "hv021",
            ge_id_col,
            "hv021_raw",
            lambda s: pd.to_numeric(s, errors="coerce"),
        )
        row["notes"] = "Alternate PSU/cluster column hv021"
        rows.append(row)

    if "hv024" in hr.columns and "hv001" in hr.columns:
        for mult in (1000, 10000, 100000):
            rows.append(
                evaluate_state_prefix_join(
                    hr, ge, "hv024", "hv001", "ADM1NAME", ge_id_col, mult
                )
            )

    # hv001 * 10 matched to raw GE (inverse of ge_floor_div_10)
    row = evaluate_join(
        hr,
        ge,
        hr_cluster_col,
        ge_id_col,
        "hr_times_10_vs_raw_ge",
        lambda s: pd.to_numeric(s, errors="coerce") * 10,
    )
    row["notes"] = "HR hv001 * 10 joined to raw GE DHSCLUST"
    rows.append(row)

    diag = pd.DataFrame(rows).sort_values("match_rate_pct", ascending=False).reset_index(drop=True)
    return diag


def main() -> None:
    hr_stem = NATIONAL_FILESETS["52"]["HR"]
    hr_path = resolve_dta_path(DHS_EXTRACTED_DIR, hr_stem)
    if not hr_path or not hr_path.exists():
        print(f"ERROR: NFHS-5 HR file not found ({hr_stem}.dta).")
        print(f"  Expected under: {DHS_EXTRACTED_DIR}")
        print("  Run: python -m src.demographics.dhs.extract_dhs_zips")
        sys.exit(1)

    print(f"Loading HR: {hr_path.name}")
    ge, stem = load_ge_table(DHS_EXTRACTED_DIR)
    print(f"Loading GE: {stem} ({len(ge)} clusters)")

    diag = run_diagnostics(hr_path, ge)

    NFHS5_GE_JOIN_DIAGNOSTICS.parent.mkdir(parents=True, exist_ok=True)
    diag.to_csv(NFHS5_GE_JOIN_DIAGNOSTICS, index=False)

    best = diag.iloc[0]
    print("\n=== Join strategy ranking (top 5) ===")
    for _, row in diag.head(5).iterrows():
        print(
            f"  {row['match_rate_pct']:6.2f}%  {row['strategy']:30s}  "
            f"hr={row['hr_key_column']} ge={row['ge_key_column']}"
        )

    print(f"\nBest strategy: {best['strategy']} ({best['match_rate_pct']}% match)")
    print(f"  HR column: {best['hr_key_column']}, GE column: {best['ge_key_column']}")
    print(f"  Notes: {best['notes']}")
    print(f"\nSaved: {NFHS5_GE_JOIN_DIAGNOSTICS}")


if __name__ == "__main__":
    main()
