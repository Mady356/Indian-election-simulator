"""
Build the state-level demographic master table (placeholder).

Run as:
    python -m src.demographics.build_state_demographic_master

Output:
    data/demographics/processed/state_demographics_master.csv

This script creates an empty template (column headers only, zero data rows).
No values are invented. Once Census/NFHS cleaners exist, they will populate
this file column by column.
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.config import DEMOGRAPHICS_PROCESSED_DIR
from src.demographics.demographic_catalog import STATE_DEMOGRAPHICS_MASTER_COLUMNS


OUT_PATH = DEMOGRAPHICS_PROCESSED_DIR / "state_demographics_master.csv"


def main() -> None:
    DEMOGRAPHICS_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # Header-only template — no fake state rows or placeholder numbers.
    template = pd.DataFrame(columns=STATE_DEMOGRAPHICS_MASTER_COLUMNS)
    template.to_csv(OUT_PATH, index=False)

    print("State demographic master (template)")
    print(f"  Saved: {OUT_PATH}")
    print(f"  Rows  : 0  (headers only)")
    print(f"  Cols  : {len(STATE_DEMOGRAPHICS_MASTER_COLUMNS)}")
    print()
    print("  Raw Census/NFHS files still need table-specific cleaners before")
    print("  this master can be filled. Run the coverage audit to see gaps:")
    print("    python -m src.demographics.audit_demographic_coverage")


if __name__ == "__main__":
    main()
