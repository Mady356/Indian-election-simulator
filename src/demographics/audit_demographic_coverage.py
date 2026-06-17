"""
Audit which demographic variables have raw and processed data on disk.

Run as:
    python -m src.demographics.audit_demographic_coverage

Reads:
    data/demographics/catalog/demographic_variables_master.csv

Scans:
    data/demographics/raw/{census_2011,nfhs,mospi,rbi}/
    data/demographics/processed/
    (plus legacy Census folders from config, e.g. data/raw/demographics-census-2011/)

Writes:
    data/demographics/outputs/demographic_coverage_report.csv
    data/demographics/outputs/missing_demographic_variables.csv
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.config import (
    DEMOGRAPHICS_CATALOG_DIR,
    DEMOGRAPHICS_OUTPUTS_DIR,
    DEMOGRAPHICS_PROCESSED_DIR,
    DEMOGRAPHICS_RAW_DIR,
    LEGACY_CENSUS_2011_DIRS,
)
from src.demographics.demographic_catalog import (
    SOURCE_CENSUS_2011,
    SOURCE_RAW_DIRS,
)


VARIABLES_MASTER = DEMOGRAPHICS_CATALOG_DIR / "demographic_variables_master.csv"
STATE_MASTER_FILE = DEMOGRAPHICS_PROCESSED_DIR / "state_demographics_master.csv"
CENSUS_STATE_FILE = DEMOGRAPHICS_PROCESSED_DIR / "census_state_demographics_2011.csv"
RAW_EXTENSIONS = {".xlsx", ".xls", ".csv", ".parquet", ".zip"}


def list_raw_files(*roots: Path) -> list[Path]:
    """All data files under the given roots, including nested subfolders."""
    found = []
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if path.is_file() and path.suffix.lower() in RAW_EXTENSIONS:
                found.append(path)
    return found


def raw_roots_for_source(source_id: str) -> list[Path]:
    """Warehouse raw dirs + legacy Census paths when source is Census."""
    dirs = []
    for sub in SOURCE_RAW_DIRS.get(source_id, ()):
        dirs.append(DEMOGRAPHICS_RAW_DIR / sub)
    if source_id == SOURCE_CENSUS_2011:
        dirs.extend(LEGACY_CENSUS_2011_DIRS)
    return dirs


def match_raw_file(expected: str, files: list[Path]) -> str | None:
    """Return matching filename if any file contains `expected` (case-insensitive)."""
    if not expected or not str(expected).strip():
        return None
    needle = str(expected).strip().lower()
    for path in files:
        if needle in path.name.lower():
            return path.name
    return None


def list_processed_files() -> list[Path]:
    if not DEMOGRAPHICS_PROCESSED_DIR.exists():
        return []
    return [
        p
        for p in DEMOGRAPHICS_PROCESSED_DIR.iterdir()
        if p.is_file() and p.suffix.lower() in {".csv", ".parquet"}
    ]


def processed_column_ready(column: str, processed_files: list[Path]) -> bool:
    """
    True if the column exists with at least one non-null value in:
      - state_demographics_master.csv, or
      - census_state_demographics_2011.csv, or
      - a dedicated processed file named after the column.
    """
    if not column:
        return False

    col_lower = column.lower()
    for path in processed_files:
        if col_lower in path.stem.lower():
            return True

    for table_path in (STATE_MASTER_FILE, CENSUS_STATE_FILE):
        if not table_path.exists():
            continue
        header = pd.read_csv(table_path, nrows=0)
        if column not in header.columns:
            continue
        series = pd.read_csv(table_path, usecols=[column])[column]
        if series.notna().any():
            return True

    return False


def audit_variables(df: pd.DataFrame) -> pd.DataFrame:
    """Add raw_file_found, processed_file_found, matched_raw_filename."""
    out = df.copy()

    # Pre-index raw files by source.
    source_files: dict[str, list[Path]] = {}
    for source in df["source"].unique():
        source_files[source] = list_raw_files(*raw_roots_for_source(source))

    processed_files = list_processed_files()

    matched_names = []
    raw_flags = []
    proc_flags = []

    for _, row in out.iterrows():
        files = source_files.get(row["source"], [])
        matched = match_raw_file(row.get("raw_file_expected", ""), files)
        matched_names.append(matched or "")
        raw_flags.append(matched is not None)

        proc_flags.append(
            processed_column_ready(row.get("processed_column", ""), processed_files)
        )

    out["matched_raw_filename"] = matched_names
    out["raw_file_found"] = raw_flags
    out["processed_file_found"] = proc_flags

    # Suggested status for the report (does not overwrite catalog master on disk).
    def _status(r):
        if r["processed_file_found"]:
            return "processed_available"
        if r["raw_file_found"]:
            return "raw_available"
        return r.get("status", "planned")

    out["coverage_status"] = out.apply(_status, axis=1)
    return out


def print_summary(report: pd.DataFrame) -> None:
    total = len(report)
    planned = int((report["coverage_status"] == "planned").sum())
    raw_ok = int(report["raw_file_found"].sum())
    proc_ok = int(report["processed_file_found"].sum())
    missing_raw = int((~report["raw_file_found"]).sum())
    missing_proc = int((~report["processed_file_found"]).sum())

    print()
    print("Coverage summary")
    print(f"  Total variables      : {total}")
    print(f"  Still planned        : {planned}")
    print(f"  Raw file matched     : {raw_ok}")
    print(f"  Processed available  : {proc_ok}")
    print(f"  Missing raw          : {missing_raw}")
    print(f"  Missing processed    : {missing_proc}")
    print()

    by_source = (
        report.groupby("source", as_index=False)
        .agg(
            total=("variable_id", "count"),
            raw_found=("raw_file_found", "sum"),
            processed_found=("processed_file_found", "sum"),
        )
    )
    print("By source:")
    print(by_source.to_string(index=False))
    print()

    if raw_ok:
        print("Variables with raw data (not yet processed):")
        pending = report[report["raw_file_found"] & ~report["processed_file_found"]]
        if pending.empty:
            print("  (none — all matched raw is already processed, or none matched)")
        else:
            for _, r in pending.head(15).iterrows():
                print(f"  - {r['variable_id']:28s}  {r['matched_raw_filename']}")
        if len(pending) > 15:
            print(f"  ... and {len(pending) - 15} more")


def main() -> None:
    if not VARIABLES_MASTER.exists():
        print(f"Catalog not found: {VARIABLES_MASTER}")
        print("Run: python -m src.demographics.build_demographic_catalog")
        return

    DEMOGRAPHICS_OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

    variables = pd.read_csv(VARIABLES_MASTER)
    report = audit_variables(variables)

    coverage_path = DEMOGRAPHICS_OUTPUTS_DIR / "demographic_coverage_report.csv"
    missing_path = DEMOGRAPHICS_OUTPUTS_DIR / "missing_demographic_variables.csv"

    report.to_csv(coverage_path, index=False)

    missing = report[~report["raw_file_found"] | ~report["processed_file_found"]].copy()
    missing.to_csv(missing_path, index=False)

    print("Demographic coverage audit")
    print(f"  Catalog : {VARIABLES_MASTER}")
    print(f"  Raw root: {DEMOGRAPHICS_RAW_DIR}")
    print(f"  Legacy Census dirs also scanned: {len(LEGACY_CENSUS_2011_DIRS)}")
    print_summary(report)

    print(f"Saved: {coverage_path}")
    print(f"Saved: {missing_path}  ({len(missing)} rows with gaps)")


if __name__ == "__main__":
    main()
