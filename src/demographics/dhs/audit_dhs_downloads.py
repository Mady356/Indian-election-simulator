"""
Audit DHS / NFHS microdata zips in data/raw/dhs_downloads/.

Run as:
    python -m src.demographics.dhs.audit_dhs_downloads
"""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from src.config import DEMOGRAPHICS_OUTPUTS_DIR, DHS_DOWNLOADS_DIR
from src.demographics.dhs.filename_parser import parse_dhs_filename

OUTPUT_FILE = DEMOGRAPHICS_OUTPUTS_DIR / "dhs_downloads_audit.csv"
INVENTORY_FILE = DHS_DOWNLOADS_DIR / "dhs_file_inventory.csv"
ARCHIVE_SUFFIXES = {".zip", ".crdownload"}


def _list_zip_members(path: Path) -> tuple[str, str]:
    if path.suffix.lower() != ".zip":
        return "", "not a zip archive"
    try:
        with zipfile.ZipFile(path) as zf:
            names = [
                n
                for n in zf.namelist()
                if not n.endswith("/")
                and Path(n).suffix.lower() in {".dta", ".dat", ".sav", ".sas7bdat", ".shp", ".dbf"}
            ]
        return ", ".join(sorted(names)), ""
    except zipfile.BadZipFile:
        return "", "bad or incomplete zip"
    except OSError as exc:
        return "", str(exc)


def audit_download(path: Path) -> dict:
    info = parse_dhs_filename(path.name)
    inner_files, zip_error = _list_zip_members(path)
    download_status = "complete"
    if path.suffix.lower() == ".crdownload":
        download_status = "in_progress"
    elif zip_error == "bad or incomplete zip":
        download_status = "incomplete"

    return {
        "filename": path.name,
        "geo_code": info.geo_code,
        "state": info.state,
        "survey": info.survey,
        "survey_version_code": info.version_code,
        "dataset_type_code": info.dataset_type_code,
        "dataset_type": info.dataset_type,
        "file_format_code": info.file_format_code,
        "file_format": info.file_format,
        "inner_data_files": inner_files,
        "size_mb": round(path.stat().st_size / (1024 * 1024), 2),
        "download_status": download_status,
        "parse_ok": info.parse_ok,
        "parse_note": info.parse_note or zip_error,
        "path": str(path),
    }


def main() -> None:
    DEMOGRAPHICS_OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    downloads = sorted(
        [p for p in DHS_DOWNLOADS_DIR.iterdir() if p.is_file() and p.suffix.lower() in ARCHIVE_SUFFIXES],
        key=lambda p: p.name.lower(),
    )
    if not downloads:
        print(f"No DHS downloads found in {DHS_DOWNLOADS_DIR}")
        return

    df = pd.DataFrame([audit_download(p) for p in downloads])
    df.to_csv(OUTPUT_FILE, index=False)
    df.to_csv(INVENTORY_FILE, index=False)

    print("DHS downloads audit")
    print(f"  Source : {DHS_DOWNLOADS_DIR}")
    print(f"  Files  : {len(df)}")
    print(f"  DT zips: {(df['file_format_code'] == 'DT').sum()}")
    print(f"Saved: {OUTPUT_FILE}")
    print(f"Saved: {INVENTORY_FILE}")


if __name__ == "__main__":
    main()
