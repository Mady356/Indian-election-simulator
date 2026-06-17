"""
Placeholder cleaner for Census 2011 state-level demographics.

Run as:
    python -m src.demographics.build_state_demographics_2011

Today:
    * Checks `data/raw/demographics/census_2011/` against the curated manifest.
    * Lists files you have uploaded and which manifest tables are still missing.
    * Does not parse Census Excel yet (each table has its own layout).

Later:
    * Emit `data/processed/state_demographics_2011.csv` (one row per state).
    * Then `district_demographics_2011.csv`; constituency demographics via
      district/GIS approximation after that.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.config import CENSUS_2011_DIR
from src.demographics.census_manifest import (
    CENSUS_2011_TABLES,
    expected_basename,
    find_uploaded_file,
)


def main() -> None:
    print("Census 2011 state-demographics builder (placeholder)")
    print(f"  Raw dir: {CENSUS_2011_DIR}")
    print()
    print("  Upload Census Excel files manually into that folder.")
    print("  Preferred names (see src/demographics/census_manifest.py):")
    for entry in CENSUS_2011_TABLES:
        print(f"    - {expected_basename(entry)}")
    print()

    CENSUS_2011_DIR.mkdir(parents=True, exist_ok=True)

    present = []
    missing = []
    for entry in CENSUS_2011_TABLES:
        path = find_uploaded_file(CENSUS_2011_DIR, entry)
        if path:
            present.append((entry, path))
        else:
            missing.append(entry)

    if present:
        print(f"  Found ({len(present)}):")
        for entry, path in present:
            size_kb = path.stat().st_size / 1024
            print(f"    [{entry['priority']:6s}] {path.name}  ({size_kb:,.1f} KB)")
    else:
        print("  No manifest-matched files found yet.")

    if missing:
        print()
        print(f"  Still expected ({len(missing)}):")
        for entry in missing:
            print(
                f"    [{entry['priority']:6s}] {entry['code']:10s}  "
                f"{expected_basename(entry)}  — {entry['description']}"
            )

    extra = [
        p.name
        for p in sorted(CENSUS_2011_DIR.iterdir())
        if p.is_file()
        and not any(find_uploaded_file(CENSUS_2011_DIR, e) == p for e in CENSUS_2011_TABLES)
    ]
    if extra:
        print()
        print(f"  Other files in folder ({len(extra)}) — kept as-is:")
        for name in extra:
            print(f"    - {name}")

    print()
    print("  Cleaning is table-specific and will be implemented once files are uploaded.")


if __name__ == "__main__":
    main()
