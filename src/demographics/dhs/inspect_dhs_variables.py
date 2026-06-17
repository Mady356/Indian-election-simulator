"""
Inspect extracted DHS Stata variables and build a feature dictionary.

Run as:
    python -m src.demographics.dhs.inspect_dhs_variables
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pyreadstat

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from src.config import DHS_EXTRACTED_DIR
from src.demographics.dhs.paths import FEATURE_DICTIONARY


def inspect_dta(path: Path) -> list[dict]:
    _, meta = pyreadstat.read_dta(str(path), metadataonly=True)
    rows = []
    for col in meta.column_names:
        label = meta.column_names_to_labels.get(col, "")
        value_labels = meta.variable_value_labels.get(col, {})
        sample_values = ""
        if value_labels:
            sample_values = "; ".join(f"{k}={v}" for k, v in list(value_labels.items())[:5])
        rows.append(
            {
                "source_file": path.name,
                "variable": col,
                "label": label,
                "value_labels_sample": sample_values,
                "n_value_labels": len(value_labels),
            }
        )
    return rows


def main() -> None:
    dta_files = sorted(DHS_EXTRACTED_DIR.glob("*.dta")) + sorted(DHS_EXTRACTED_DIR.glob("*.DTA"))
    if not dta_files:
        print(f"No extracted .dta files in {DHS_EXTRACTED_DIR}")
        print("Run: python -m src.demographics.dhs.extract_dhs_zips")
        return

    rows: list[dict] = []
    for path in dta_files:
        print(f"  Inspecting {path.name} ({path.stat().st_size / 1e6:.1f} MB)...")
        rows.extend(inspect_dta(path))

    df = pd.DataFrame(rows)
    FEATURE_DICTIONARY.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(FEATURE_DICTIONARY, index=False)
    print(f"\nSaved {len(df)} variable rows -> {FEATURE_DICTIONARY}")


if __name__ == "__main__":
    main()
