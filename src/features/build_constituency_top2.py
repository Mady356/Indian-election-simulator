"""
Build a per-constituency table that contains only the top-2 candidates by rank.

Run as:
    python -m src.features.build_constituency_top2

Used by:
    * Margin / two-horse-race style analyses.
    * Simulators that re-run only the contest between the leading pair.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.data_io import (
    CONSTITUENCY_TOP2_FILE,
    load_candidate_results,
    save_csv,
)
from src.utils.validation import check_required_columns


def build_top2() -> None:
    results = load_candidate_results()
    check_required_columns(results, ["state", "constituency", "rank"])

    # Sort then groupby+head(2) is the simplest way to keep the top-2 within
    # each constituency while preserving all original columns.
    results = results.sort_values(["state", "constituency", "rank"])
    top2 = (
        results.groupby(["state", "constituency"])
               .head(2)
               .copy()
    )

    save_csv(top2, CONSTITUENCY_TOP2_FILE)
    print("\nFirst 10 rows:")
    print(top2.head(10).to_string(index=False))


if __name__ == "__main__":
    build_top2()
