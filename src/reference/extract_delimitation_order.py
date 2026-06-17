"""
Extract page-level text from the 2008 Delimitation Order PDF.

Run as:
    python -m src.reference.extract_delimitation_order

Output:
    data/reference/delimitation_raw_text.csv
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.reference.delimitation_paths import DELIMITATION_PDF, DELIMITATION_RAW_TEXT
from src.reference.delimitation_utils import extract_pdf_pages, pdf_page_count


def main() -> None:
    if not DELIMITATION_PDF.exists():
        print(f"ERROR: PDF not found at {DELIMITATION_PDF}")
        print("  Expected: data/raw/ls-as-mapping/DelimitationofParliamentaryAssemblyConstituenciesOrder-2008(English).pdf")
        sys.exit(1)

    pages = pdf_page_count()
    print(f"Extracting {pages} pages from {DELIMITATION_PDF.name}...")
    df = extract_pdf_pages()
    DELIMITATION_RAW_TEXT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(DELIMITATION_RAW_TEXT, index=False)
    print(f"Saved: {DELIMITATION_RAW_TEXT} ({len(df)} rows)")


if __name__ == "__main__":
    main()
