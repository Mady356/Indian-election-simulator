"""
Extract Stata (.dta) files from DHS DT zips.

Run as:
    python -m src.demographics.dhs.extract_dhs_zips
"""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from src.config import DHS_EXTRACTED_DIR
from src.demographics.dhs.feature_utils import load_inventory


def extract_stata_from_zip(zip_path: Path, out_dir: Path) -> list[Path]:
    extracted: list[Path] = []
    with zipfile.ZipFile(zip_path) as zf:
        for name in zf.namelist():
            if name.endswith("/"):
                continue
            if Path(name).suffix.lower() != ".dta":
                continue
            target = out_dir / Path(name).name
            if target.exists():
                extracted.append(target)
                continue
            with zf.open(name) as src, open(target, "wb") as dst:
                dst.write(src.read())
            extracted.append(target)
    return extracted


def main() -> None:
    DHS_EXTRACTED_DIR.mkdir(parents=True, exist_ok=True)
    inventory = load_inventory()
    dt_files = inventory[(inventory["parse_ok"] == True) & (inventory["file_format_code"] == "DT")]  # noqa: E712

    all_extracted: list[Path] = []
    for _, row in dt_files.iterrows():
        zip_path = Path(row["path"])
        if not zip_path.exists():
            print(f"  SKIP missing: {zip_path.name}")
            continue
        paths = extract_stata_from_zip(zip_path, DHS_EXTRACTED_DIR)
        all_extracted.extend(paths)
        print(f"  {zip_path.name} -> {[p.name for p in paths]}")

    print()
    print(f"Extracted {len(all_extracted)} Stata files to {DHS_EXTRACTED_DIR}")


if __name__ == "__main__":
    main()
