"""
Extract tables and page text from CSDS-Lokniti PDF reports.

Run:
    python -m src.postpoll.extract_csds_tables
"""

from __future__ import annotations

import csv
import re
from pathlib import Path

import pandas as pd

from src.postpoll.csds_manifest import (
    BEHAVIOUR_ANALYSIS_DIR,
    EXTRACTED_DIR,
    REPORTS_DIR,
    STUDIES,
    resolve_report_path,
)

MANUAL_REVIEW_PATH = REPORTS_DIR / "manual_extraction_needed.csv"
MANUAL_REVIEW_COLUMNS = [
    "year",
    "poll_type",
    "page",
    "reason",
    "suggested_action",
]


def _study_prefix(year: int, poll_type: str) -> str:
    return f"{year}_{poll_type}"


def _clean_cell(value: object) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    text = re.sub(r"\s+", " ", text)
    return text


def _table_to_dataframe(table: list[list[object | None]]) -> pd.DataFrame:
    if not table:
        return pd.DataFrame()
    max_cols = max(len(row) for row in table)
    normalized = []
    for row in table:
        cells = [_clean_cell(cell) for cell in row]
        if len(cells) < max_cols:
            cells.extend([""] * (max_cols - len(cells)))
        normalized.append(cells)
    if not normalized:
        return pd.DataFrame()
    header = normalized[0]
    if all(not cell for cell in header):
        header = [f"col_{i}" for i in range(max_cols)]
    else:
        header = [cell or f"col_{i}" for i, cell in enumerate(header)]
    data = normalized[1:] if len(normalized) > 1 else []
    return pd.DataFrame(data, columns=header)


def _is_meaningful_table(df: pd.DataFrame) -> bool:
    if df.empty:
        return False
    non_empty = df.astype(str).replace("", pd.NA).dropna(how="all")
    if non_empty.empty:
        return False
    if non_empty.shape[0] < 2 and non_empty.shape[1] < 2:
        return False
    return True


def extract_study_pdf(
    year: int,
    poll_type: str,
    report_path: Path,
) -> tuple[int, list[dict[str, object]]]:
    prefix = _study_prefix(year, poll_type)
    text_path = EXTRACTED_DIR / f"{prefix}_text.txt"
    manual_rows: list[dict[str, object]] = []
    table_count = 0

    if not report_path.exists():
        manual_rows.append(
            {
                "year": year,
                "poll_type": poll_type,
                "page": "",
                "reason": "raw report PDF missing",
                "suggested_action": (
                    f"Add report PDF under data/behaviour-analysis/ "
                    f"(expected: {report_path})"
                ),
            }
        )
        return 0, manual_rows

    try:
        import pdfplumber
    except ImportError:
        manual_rows.append(
            {
                "year": year,
                "poll_type": poll_type,
                "page": "",
                "reason": "pdfplumber not installed",
                "suggested_action": "pip install pdfplumber and rerun extraction",
            }
        )
        return 0, manual_rows

    page_texts: list[str] = []
    try:
        with pdfplumber.open(report_path) as pdf:
            for page_idx, page in enumerate(pdf.pages, start=1):
                text = page.extract_text() or ""
                if text.strip():
                    page_texts.append(f"=== PAGE {page_idx} ===\n{text.strip()}\n")

                try:
                    tables = page.extract_tables() or []
                except Exception as exc:
                    manual_rows.append(
                        {
                            "year": year,
                            "poll_type": poll_type,
                            "page": page_idx,
                            "reason": f"table extraction error: {exc}",
                            "suggested_action": "manual table transcription",
                        }
                    )
                    continue

                for table in tables:
                    df = _table_to_dataframe(table)
                    if not _is_meaningful_table(df):
                        continue
                    table_count += 1
                    out_path = EXTRACTED_DIR / f"{prefix}_table_{table_count:03d}.csv"
                    df.to_csv(out_path, index=False, quoting=csv.QUOTE_MINIMAL)
    except Exception as exc:
        manual_rows.append(
            {
                "year": year,
                "poll_type": poll_type,
                "page": "",
                "reason": f"PDF open/read failed: {exc}",
                "suggested_action": "verify PDF integrity or transcribe manually",
            }
        )
        return table_count, manual_rows

    text_path.write_text("\n".join(page_texts), encoding="utf-8")

    if table_count == 0:
        manual_rows.append(
            {
                "year": year,
                "poll_type": poll_type,
                "page": "",
                "reason": "no tables detected by pdfplumber",
                "suggested_action": "inspect PDF layout; transcribe voter-group tables manually",
            }
        )

    return table_count, manual_rows


def extract_all() -> tuple[int, pd.DataFrame, int]:
    EXTRACTED_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    total_tables = 0
    manual_rows: list[dict[str, object]] = []
    files_found = 0

    for study in STUDIES:
        report_path = resolve_report_path(study)
        if report_path.exists():
            files_found += 1
        count, review = extract_study_pdf(
            int(study["year"]),
            str(study["poll_type"]),
            report_path,
        )
        total_tables += count
        manual_rows.extend(review)

    review_df = pd.DataFrame(manual_rows, columns=MANUAL_REVIEW_COLUMNS)
    review_df.to_csv(MANUAL_REVIEW_PATH, index=False)
    return total_tables, review_df, files_found


def main() -> None:
    total_tables, review_df, files_found = extract_all()

    print("CSDS table extraction")
    print(f"  Report PDFs found: {files_found}/{len(STUDIES)}")
    print(f"  Tables extracted: {total_tables}")
    print(f"  Source directory: {BEHAVIOUR_ANALYSIS_DIR}")
    print(f"  Extracted output: {EXTRACTED_DIR}")
    print(f"  Manual review items: {len(review_df)}")
    print(f"  Manual review file: {MANUAL_REVIEW_PATH}")
    if files_found == 0:
        print(
            "  No report PDFs found under data/behaviour-analysis/ "
            "post-poll/ or pre-poll/."
        )


if __name__ == "__main__":
    main()
