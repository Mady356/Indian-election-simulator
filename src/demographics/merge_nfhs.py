"""
Placeholder: merge NFHS-5 indicators into state_demographics_master.csv.

Run as:
    python -m src.demographics.merge_nfhs

NFHS adds recent household/health indicators (internet, bank accounts, fertility,
sanitation) that Census 2011 does not cover. This script does not fabricate data;
it only checks whether NFHS raw/processed files exist and explains next steps.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.config import DEMOGRAPHICS_PROCESSED_DIR, DEMOGRAPHICS_RAW_NFHS
from src.demographics.audit_demographic_coverage import (
    list_raw_files,
    list_processed_files,
    processed_column_ready,
)
from src.demographics.demographic_catalog import DEMOGRAPHIC_VARIABLES, SOURCE_NFHS_5


STATE_MASTER = DEMOGRAPHICS_PROCESSED_DIR / "state_demographics_master.csv"
NFHS_COLUMNS = [
    v["processed_column"]
    for v in DEMOGRAPHIC_VARIABLES
    if v["source"] == SOURCE_NFHS_5
]


def main() -> None:
    print("NFHS merge (placeholder)")
    print(f"  NFHS raw folder : {DEMOGRAPHICS_RAW_NFHS}")
    print(f"  Target master   : {STATE_MASTER}")
    print()

    raw_files = list_raw_files(DEMOGRAPHICS_RAW_NFHS)
    if raw_files:
        print(f"  Raw NFHS files found ({len(raw_files)}):")
        for p in raw_files:
            print(f"    - {p.name}")
    else:
        print("  No NFHS raw files yet.")
        print(f"  Upload NFHS state tables to: {DEMOGRAPHICS_RAW_NFHS}")

    print()
    processed_files = list_processed_files()
    print("  NFHS columns in catalog vs processed:")
    for col in NFHS_COLUMNS:
        ready = processed_column_ready(col, processed_files)
        print(f"    {'[OK]' if ready else '[--]'} {col}")

    print()
    print("  Planned workflow (not implemented yet):")
    print("    1. Clean NFHS state indicator file(s) -> processed/nfhs_state_indicators.csv")
    print("    2. Map NFHS state names to `nfhs_state_code` in state_demographics_master")
    print("    3. Left-join NFHS columns into state_demographics_master.csv")
    print()
    print("  No merge performed — no synthetic values written.")


if __name__ == "__main__":
    main()
