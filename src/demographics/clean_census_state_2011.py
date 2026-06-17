"""
Clean Census 2011 state-level tables from manually uploaded raw Excel files.

Run as:
    python -m src.demographics.clean_census_state_2011

Reads (searched under data/demographics/raw/ and legacy folders):
    * India State Population 2011.xlsx  — population, urban/rural, SC/ST, sex ratio
    * DDW00C-01 MDDS.XLS                 — religion (wide layout)
    * PCA_AY_2011_Revised.xlsx           — SC/ST cross-check, youth share

Writes:
    data/demographics/processed/census_state_demographics_2011.csv
    data/demographics/processed/state_demographics_master.csv  (merged, no fake values)
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.config import (
    DEMOGRAPHICS_PROCESSED_DIR,
    DEMOGRAPHICS_RAW_DIR,
    LEGACY_CENSUS_2011_DIRS,
)
from src.demographics.demographic_catalog import STATE_DEMOGRAPHICS_MASTER_COLUMNS


# -----------------------------------------------------------------------------
# Paths
# -----------------------------------------------------------------------------

CENSUS_STATE_OUT = DEMOGRAPHICS_PROCESSED_DIR / "census_state_demographics_2011.csv"
STATE_MASTER_OUT = DEMOGRAPHICS_PROCESSED_DIR / "state_demographics_master.csv"

RAW_EXTENSIONS = {".xlsx", ".xls", ".csv"}

# Religion file: "Persons" columns (0-based) from Census C-01 layout.
RELIGION_PERSON_COLS = {
    "total": 7,
    "hindu": 10,
    "muslim": 13,
    "christian": 16,
    "sikh": 19,
    "buddhist": 22,
    "jain": 25,
}

CENSUS_OUTPUT_COLUMNS = [
    "state",
    "population_total",
    "population_density",
    "urban_pct",
    "rural_pct",
    "hindu_pct",
    "muslim_pct",
    "christian_pct",
    "sikh_pct",
    "buddhist_pct",
    "jain_pct",
    "sc_pct",
    "st_pct",
    "sex_ratio",
    "literacy_rate",
    "male_literacy",
    "female_literacy",
    "youth_pct",
    "working_age_pct",
    "elderly_pct",
    "source_year",
    "geography_level",
]


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

def _raw_search_roots() -> list[Path]:
    roots = [DEMOGRAPHICS_RAW_DIR, *LEGACY_CENSUS_2011_DIRS]
    return [r for r in roots if r.exists()]


def find_file(pattern: str) -> Path | None:
    """
    Find the first file under demographic raw roots whose name contains
    `pattern` (case-insensitive). Searches nested folders.
    """
    needle = pattern.lower()
    for root in _raw_search_roots():
        for path in root.rglob("*"):
            if path.is_file() and path.suffix.lower() in RAW_EXTENSIONS:
                if needle in path.name.lower():
                    return path
    return None


def clean_state_name(value: object) -> str:
    """Normalise Census state labels for merging across tables."""
    if pd.isna(value):
        return ""
    name = str(value).strip().upper()
    name = re.sub(r"^STATE\s*-\s*", "", name, flags=re.IGNORECASE)
    name = re.sub(r"\s+", " ", name)
    # Drop trailing parenthetical codes: "JAMMU & KASHMIR (01)" -> "JAMMU & KASHMIR"
    name = re.sub(r"\s*\(\d+\)\s*$", "", name).strip()
    return name


def safe_read_excel(path: Path, sheet_name=0, header=0) -> pd.DataFrame | None:
    """Read Excel with calamine; return None and print on failure."""
    try:
        return pd.read_excel(path, sheet_name=sheet_name, header=header, engine="calamine")
    except Exception as exc:
        print(f"  [WARN] Could not read {path.name}: {exc}")
        return None


def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Lowercase, strip, replace spaces with underscores."""
    out = df.copy()
    out.columns = [
        re.sub(r"[^a-z0-9]+", "_", str(c).strip().lower()).strip("_")
        for c in out.columns
    ]
    return out


def _find_column(df: pd.DataFrame, keywords: list[str], exclude: list[str] | None = None) -> str | None:
    """Pick first column whose normalised name matches all keywords and no excludes."""
    exclude = exclude or []
    for col in df.columns:
        name = str(col).lower()
        if all(k in name for k in keywords) and not any(e in name for e in exclude):
            return col
    return None


def _to_numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series.astype(str).str.replace(",", "", regex=False), errors="coerce")


def _warn_missing(label: str, detail: str) -> None:
    print(f"  [WARN] {label}: {detail}")


def _diagnose_df(df: pd.DataFrame | None, label: str) -> None:
    if df is None or df.empty:
        print(f"  [DEBUG] {label}: empty")
        return
    print(f"  [DEBUG] {label} shape={df.shape}")
    print(f"  [DEBUG] columns: {list(df.columns)[:20]}")
    print(df.head(5).to_string())


# -----------------------------------------------------------------------------
# Population
# -----------------------------------------------------------------------------

def clean_population_file(path: Path | None) -> pd.DataFrame:
    """
    Extract state-level population, urban/rural %, sex ratio from PCA-style
    'India State Population 2011.xlsx' (Level=STATE, TRU=Total/Rural/Urban).
    """
    empty = pd.DataFrame(columns=["state"] + CENSUS_OUTPUT_COLUMNS[1:-2])
    if path is None:
        _warn_missing("population", "file not found (expected name contains 'India State Population')")
        return empty

    print(f"\n--- Population: {path.name} ---")
    xl = pd.ExcelFile(path, engine="calamine")
    print(f"  Sheets: {xl.sheet_names}")

    df = safe_read_excel(path, sheet_name="Data" if "Data" in xl.sheet_names else 0, header=0)
    if df is None:
        return empty

    df = standardize_columns(df)

    if "level" not in df.columns or "name" not in df.columns:
        _warn_missing("population", "expected Level/Name columns not found")
        _diagnose_df(df, "population")
        return empty

    state_rows = df[df["level"].astype(str).str.upper() == "STATE"].copy()
    if state_rows.empty:
        _warn_missing("population", "no Level=STATE rows")
        _diagnose_df(df, "population")
        return empty

    # Total population + SC/ST + sex ratio from TRU=Total rows.
    total = state_rows[state_rows["tru"].astype(str).str.upper() == "TOTAL"].copy()
    total["state"] = total["name"].map(clean_state_name)

    out = pd.DataFrame({"state": total["state"]})

    if "tot_p" in total.columns:
        out["population_total"] = _to_numeric(total["tot_p"])
    else:
        col = _find_column(total, ["tot", "p"]) or _find_column(total, ["population"])
        out["population_total"] = _to_numeric(total[col]) if col else np.nan
        if col is None:
            _warn_missing("population_total", "column not found")

    # Literacy (available in the same PCA state extract).
    if "tot_p" in total.columns and "p_lit" in total.columns:
        tp = _to_numeric(total["tot_p"])
        out["literacy_rate"] = np.where(tp > 0, _to_numeric(total["p_lit"]) / tp * 100, np.nan)
    if "tot_m" in total.columns and "m_lit" in total.columns:
        tm = _to_numeric(total["tot_m"])
        out["male_literacy"] = np.where(tm > 0, _to_numeric(total["m_lit"]) / tm * 100, np.nan)
    if "tot_f" in total.columns and "f_lit" in total.columns:
        tf = _to_numeric(total["tot_f"])
        out["female_literacy"] = np.where(tf > 0, _to_numeric(total["f_lit"]) / tf * 100, np.nan)

    # Sex ratio: females per 1000 males (standard Census definition).
    if "tot_m" in total.columns and "tot_f" in total.columns:
        m = _to_numeric(total["tot_m"])
        f = _to_numeric(total["tot_f"])
        out["sex_ratio"] = np.where(m > 0, f / m * 1000, np.nan)
    else:
        out["sex_ratio"] = np.nan
        _warn_missing("sex_ratio", "TOT_M / TOT_F columns not found")

    # SC/ST % from same rows (also filled in PCA; population file is authoritative here).
    if "tot_p" in total.columns and "p_sc" in total.columns:
        tp = _to_numeric(total["tot_p"])
        out["sc_pct"] = np.where(tp > 0, _to_numeric(total["p_sc"]) / tp * 100, np.nan)
    else:
        out["sc_pct"] = np.nan

    if "tot_p" in total.columns and "p_st" in total.columns:
        tp = _to_numeric(total["tot_p"])
        out["st_pct"] = np.where(tp > 0, _to_numeric(total["p_st"]) / tp * 100, np.nan)
    else:
        out["st_pct"] = np.nan

    # Urban / rural % from separate TRU rows per state.
    def _tru_pop(tru_label: str) -> pd.DataFrame:
        chunk = state_rows[state_rows["tru"].astype(str).str.upper() == tru_label].copy()
        chunk["state"] = chunk["name"].map(clean_state_name)
        pop = _to_numeric(chunk["tot_p"]) if "tot_p" in chunk.columns else np.nan
        return pd.DataFrame({"state": chunk["state"], f"{tru_label.lower()}_pop": pop})

    urban_df = _tru_pop("URBAN")
    rural_df = _tru_pop("RURAL")
    out = out.merge(urban_df, on="state", how="left")
    out = out.merge(rural_df, on="state", how="left")
    denom = out["population_total"]
    out["urban_pct"] = np.where(denom > 0, out["urban_pop"] / denom * 100, np.nan)
    out["rural_pct"] = np.where(denom > 0, out["rural_pop"] / denom * 100, np.nan)
    out = out.drop(columns=["urban_pop", "rural_pop"], errors="ignore")

    # Population density is not in this PCA extract.
    out["population_density"] = np.nan
    _warn_missing(
        "population_density",
        "not in India State Population file — add a table with area or compute from district data",
    )

    print(f"  Parsed {len(out)} states from population file.")
    return out


# -----------------------------------------------------------------------------
# Religion
# -----------------------------------------------------------------------------

def clean_religion_file(path: Path | None) -> pd.DataFrame:
    """Parse DDW00C-01 MDDS.XLS (C-01) state-level religion counts -> percentages."""
    cols = [
        "state",
        "hindu_pct",
        "muslim_pct",
        "christian_pct",
        "sikh_pct",
        "buddhist_pct",
        "jain_pct",
    ]
    empty = pd.DataFrame(columns=cols)
    if path is None:
        _warn_missing("religion", "file not found (expected DDW00C or religion in name)")
        return empty

    print(f"\n--- Religion: {path.name} ---")
    xl = pd.ExcelFile(path, engine="calamine")
    print(f"  Sheets: {xl.sheet_names}")

    raw = safe_read_excel(path, sheet_name=0, header=None)
    if raw is None:
        return empty

    # Data starts around row 7; state rows: dist=000, tehsil=00000, Total/Rural/Urban=Total.
    data = raw.iloc[7:].copy()
    data.columns = list(range(data.shape[1]))

    def _col_str(series, idx):
        return series.iloc[:, idx].astype(str).str.strip()

    mask = (
        _col_str(data, 2).eq("000")
        & _col_str(data, 3).eq("00000")
        & _col_str(data, 6).str.lower().eq("total")
        & ~_col_str(data, 1).eq("00")
    )
    states = data[mask].copy()
    if states.empty:
        _warn_missing("religion", "no state-level rows detected; trying wide-format fallback")
        return _clean_religion_wide_fallback(path)

    rows = []
    for _, row in states.iterrows():
        state = clean_state_name(row[5])
        if not state or state == "INDIA":
            continue
        try:
            total = float(row[RELIGION_PERSON_COLS["total"]])
        except (TypeError, ValueError):
            continue
        if not total or total <= 0:
            continue
        rec = {"state": state}
        for religion, col_idx in RELIGION_PERSON_COLS.items():
            if religion == "total":
                continue
            try:
                val = float(row[col_idx])
            except (TypeError, ValueError):
                val = np.nan
            rec[f"{religion}_pct"] = (val / total * 100) if pd.notna(val) else np.nan
        rows.append(rec)

    out = pd.DataFrame(rows)
    if out.empty:
        _warn_missing("religion", "parsing produced zero rows")
        _diagnose_df(states.iloc[:, :12], "religion raw slice")
        return empty

    print(f"  Parsed {len(out)} states from religion file.")
    return out


def _clean_religion_wide_fallback(path: Path) -> pd.DataFrame:
    """Attempt religion wide format with standard column names."""
    df = safe_read_excel(path, header=0)
    if df is None:
        return pd.DataFrame()
    df = standardize_columns(df)
    state_col = _find_column(df, ["state"]) or _find_column(df, ["area", "name"])
    if not state_col:
        _diagnose_df(df, "religion wide fallback")
        return pd.DataFrame()
    out = pd.DataFrame({"state": df[state_col].map(clean_state_name)})
    for religion in ("hindu", "muslim", "christian", "sikh", "buddhist", "jain"):
        col = _find_column(df, [religion])
        out[f"{religion}_pct"] = _to_numeric(df[col]) if col else np.nan
    return out.drop_duplicates(subset=["state"])


# -----------------------------------------------------------------------------
# PCA / age
# -----------------------------------------------------------------------------

def clean_pca_age_file(path: Path | None) -> pd.DataFrame:
    """
    PCA_AY file: adolescent/youth tabulation.
    Extract youth_pct from 'Youth (15-24)' / 'All Ages'.
    SC/ST cross-check from 'All Ages' row (optional; population file is primary).
    """
    empty = pd.DataFrame(
        columns=["state", "sc_pct", "st_pct", "youth_pct", "working_age_pct", "elderly_pct"]
    )
    if path is None:
        _warn_missing("PCA/age", "file not found (expected PCA_AY)")
        return empty

    print(f"\n--- PCA / age: {path.name} ---")
    xl = pd.ExcelFile(path, engine="calamine")
    print(f"  Sheets: {xl.sheet_names}")

    raw = safe_read_excel(path, sheet_name=0, header=None)
    if raw is None:
        return empty

    data = raw.iloc[7:].copy()
    data.columns = list(range(data.shape[1]))

    def _s(idx):
        return data.iloc[:, idx].astype(str).str.strip()

    base_mask = _s(2).eq("000") & _s(4).str.lower().eq("total") & ~_s(1).eq("00")

    def _state_name(row):
        return clean_state_name(row[3])

    # All Ages row for SC/ST and youth denominator.
    all_ages = data[base_mask & _s(5).str.lower().str.contains("all ages", na=False)]
    youth_rows = data[base_mask & _s(5).str.lower().str.contains("youth", na=False)]

    records: dict[str, dict] = {}

    for _, row in all_ages.iterrows():
        state = _state_name(row)
        if not state:
            continue
        try:
            total = float(row[6])
            sc = float(row[9])
            st = float(row[12])
        except (TypeError, ValueError):
            continue
        rec = records.setdefault(state, {"state": state})
        if total > 0:
            rec["sc_pct_pca"] = sc / total * 100
            rec["st_pct_pca"] = st / total * 100
            rec["pop_all_ages"] = total

    for _, row in youth_rows.iterrows():
        state = _state_name(row)
        if not state:
            continue
        try:
            youth_pop = float(row[6])
        except (TypeError, ValueError):
            continue
        rec = records.setdefault(state, {"state": state})
        rec["youth_pop"] = youth_pop

    rows = []
    for state, rec in records.items():
        row = {"state": state}
        pop = rec.get("pop_all_ages")
        youth = rec.get("youth_pop")
        if pop and youth:
            row["youth_pct"] = youth / pop * 100
        else:
            row["youth_pct"] = np.nan
        # Keep PCA SC/ST only as fallback (merged later; population wins).
        row["sc_pct"] = rec.get("sc_pct_pca", np.nan)
        row["st_pct"] = rec.get("st_pct_pca", np.nan)
        row["working_age_pct"] = np.nan
        row["elderly_pct"] = np.nan
        rows.append(row)

    out = pd.DataFrame(rows)
    if out.empty:
        _warn_missing("PCA/age", "no state rows parsed")
        _diagnose_df(data[base_mask].head(10), "PCA filtered")
        return empty

    _warn_missing(
        "working_age_pct / elderly_pct",
        "PCA_AY file only has youth bands (10-14, 15-19, 20-24, Youth 15-24) — not 15-59 or 60+",
    )
    print(f"  Parsed {len(out)} states from PCA file.")
    return out


# -----------------------------------------------------------------------------
# Merge, save, validate
# -----------------------------------------------------------------------------

def merge_census_tables(
    population: pd.DataFrame,
    religion: pd.DataFrame,
    pca: pd.DataFrame,
) -> pd.DataFrame:
    """Outer-merge on state; coalesce SC/ST from population then PCA."""
    merged = population
    if not religion.empty:
        merged = merged.merge(religion, on="state", how="outer", suffixes=("", "_rel"))
    if not pca.empty:
        merged = merged.merge(pca, on="state", how="outer", suffixes=("", "_pca"))

    # If religion added duplicate columns, keep left.
    for col in CENSUS_OUTPUT_COLUMNS[1:-2]:
        if col not in merged.columns:
            merged[col] = np.nan

    # Prefer population SC/ST over PCA when both exist.
    for pct in ("sc_pct", "st_pct"):
        pca_col = f"{pct}_pca"
        if pca_col in merged.columns:
            merged[pct] = merged[pct].combine_first(merged[pca_col])
            merged = merged.drop(columns=[pca_col])

    merged["source_year"] = 2011
    merged["geography_level"] = "state"
    merged = merged.sort_values("state").reset_index(drop=True)

    keep = [c for c in CENSUS_OUTPUT_COLUMNS if c in merged.columns]
    return merged[keep]


def save_output(df: pd.DataFrame) -> None:
    DEMOGRAPHICS_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(CENSUS_STATE_OUT, index=False)
    print(f"\nSaved: {CENSUS_STATE_OUT}  ({len(df)} rows)")


def update_state_master(census: pd.DataFrame) -> None:
    """
    Merge Census columns into state_demographics_master.csv.
    Preserves existing columns (e.g. future NFHS); does not invent values.
    """
    if STATE_MASTER_OUT.exists():
        master = pd.read_csv(STATE_MASTER_OUT)
    else:
        master = pd.DataFrame(columns=STATE_DEMOGRAPHICS_MASTER_COLUMNS)

    census_cols = [c for c in census.columns if c != "state"]
    merged = master.merge(census, on="state", how="outer", suffixes= ("", "_census"))

    # For overlapping columns, prefer newly cleaned Census values where present.
    for col in census_cols:
        census_only = f"{col}_census"
        if census_only in merged.columns:
            if col in merged.columns:
                merged[col] = merged[census_only].combine_first(merged[col])
            else:
                merged[col] = merged[census_only]
            merged = merged.drop(columns=[census_only])

    # Ensure full schema (empty columns for not-yet-built fields).
    for col in STATE_DEMOGRAPHICS_MASTER_COLUMNS:
        if col not in merged.columns:
            merged[col] = np.nan

    merged = merged[STATE_DEMOGRAPHICS_MASTER_COLUMNS]
    merged.to_csv(STATE_MASTER_OUT, index=False)
    print(f"Saved: {STATE_MASTER_OUT}  ({len(merged)} rows, headers preserved)")


def print_validation(df: pd.DataFrame) -> None:
    print("\n--- Validation ---")
    print(f"  States in output: {len(df)}")

    metric_cols = [c for c in CENSUS_OUTPUT_COLUMNS if c not in ("state", "source_year", "geography_level")]
    print("\n  Missing values by column:")
    for col in metric_cols:
        if col not in df.columns:
            print(f"    {col:22s}  MISSING COLUMN")
            continue
        n_missing = int(df[col].isna().sum())
        print(f"    {col:22s}  {n_missing:3d} / {len(df)} empty")

    populated = [c for c in metric_cols if c in df.columns and df[c].notna().any()]
    empty = [c for c in metric_cols if c not in populated]
    print(f"\n  Populated columns ({len(populated)}): {', '.join(populated)}")
    print(f"  Still empty ({len(empty)}): {', '.join(empty) or '(none)'}")

    show_cols = ["state", "population_total", "urban_pct", "hindu_pct", "muslim_pct", "sc_pct", "youth_pct"]
    show_cols = [c for c in show_cols if c in df.columns]
    print("\n  Sample rows:")
    print(df[show_cols].head(8).to_string(index=False))


def main() -> None:
    print("Census 2011 state cleaner")
    print(f"  Searching under: {DEMOGRAPHICS_RAW_DIR} (+ legacy folders)")

    pop_path = find_file("India State Population")
    rel_path = find_file("DDW00C") or find_file("MDDS")
    pca_path = find_file("PCA_AY")

    print("\nFiles located:")
    print(f"  Population : {pop_path or 'NOT FOUND'}")
    print(f"  Religion   : {rel_path or 'NOT FOUND'}")
    print(f"  PCA/age    : {pca_path or 'NOT FOUND'}")

    population = clean_population_file(pop_path)
    religion = clean_religion_file(rel_path)
    pca = clean_pca_age_file(pca_path)

    census = merge_census_tables(population, religion, pca)
    save_output(census)
    update_state_master(census)
    print_validation(census)

    print("\nNext: python -m src.demographics.audit_demographic_coverage")


if __name__ == "__main__":
    main()
