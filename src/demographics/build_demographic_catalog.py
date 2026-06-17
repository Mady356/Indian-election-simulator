"""
Export the in-code demographic catalog to CSV files under data/demographics/catalog/.

Run as:
    python -m src.demographics.build_demographic_catalog

Outputs:
    data/demographics/catalog/demographic_variables_master.csv
    data/demographics/catalog/demographic_sources_master.csv
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.config import DEMOGRAPHICS_CATALOG_DIR, DEMOGRAPHICS_DIR
from src.demographics.demographic_catalog import (
    DEMOGRAPHIC_SOURCES,
    DEMOGRAPHIC_VARIABLES,
)


def ensure_folders() -> None:
    """Create the demographic warehouse tree if it does not exist yet."""
    subdirs = (
        DEMOGRAPHICS_DIR / "catalog",
        DEMOGRAPHICS_DIR / "raw" / "census_2011",
        DEMOGRAPHICS_DIR / "raw" / "nfhs",
        DEMOGRAPHICS_DIR / "raw" / "mospi",
        DEMOGRAPHICS_DIR / "raw" / "rbi",
        DEMOGRAPHICS_DIR / "processed",
        DEMOGRAPHICS_DIR / "outputs",
    )
    for folder in subdirs:
        folder.mkdir(parents=True, exist_ok=True)


def main() -> None:
    ensure_folders()

    variables_df = pd.DataFrame(DEMOGRAPHIC_VARIABLES)
    sources_df = pd.DataFrame(DEMOGRAPHIC_SOURCES)

    variables_path = DEMOGRAPHICS_CATALOG_DIR / "demographic_variables_master.csv"
    sources_path = DEMOGRAPHICS_CATALOG_DIR / "demographic_sources_master.csv"

    variables_df.to_csv(variables_path, index=False)
    sources_df.to_csv(sources_path, index=False)

    print("Demographic catalog exported.")
    print(f"  Variables ({len(variables_df)} rows): {variables_path}")
    print(f"  Sources   ({len(sources_df)} rows): {sources_path}")
    print()
    print("Next: upload raw files, then run:")
    print("  python -m src.demographics.audit_demographic_coverage")


if __name__ == "__main__":
    main()
