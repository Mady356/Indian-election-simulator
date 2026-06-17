"""
Taxonomy-guided page search across CSDS PDF reports.

Run:
    python -m src.postpoll.taxonomy_guided_search
"""

from __future__ import annotations

import pandas as pd

from src.postpoll.csds_taxonomy import (
    PAGE_CANDIDATES_PATH,
    classify_table_type,
    ensure_taxonomy_dirs,
    iter_study_reports,
    load_taxonomy,
    recommended_action,
    score_page_keywords,
)

PAGE_CANDIDATE_COLUMNS = [
    "year",
    "poll_type",
    "source_file",
    "page",
    "candidate_score",
    "matched_group_types",
    "matched_keywords",
    "likely_table_type",
    "page_text_excerpt",
    "recommended_action",
]


def extract_pdf_pages(report_path, max_excerpt: int = 400) -> list[tuple[int, str]]:
    try:
        import pdfplumber
    except ImportError as exc:
        raise RuntimeError("pdfplumber is required. pip install pdfplumber") from exc

    pages: list[tuple[int, str]] = []
    with pdfplumber.open(report_path) as pdf:
        for idx, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            pages.append((idx, text))
    return pages


def search_report(
    year: int,
    poll_type: str,
    source_file: str,
    report_path,
    taxonomy: dict,
    max_excerpt: int = 400,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for page_num, text in extract_pdf_pages(report_path):
        if not text.strip():
            continue
        score, group_types, keywords = score_page_keywords(text, taxonomy)
        table_type = classify_table_type(text, poll_type, taxonomy)
        action = recommended_action(score, table_type)
        if action == "ignore" and score < 3:
            continue
        rows.append(
            {
                "year": year,
                "poll_type": poll_type,
                "source_file": source_file,
                "page": page_num,
                "candidate_score": score,
                "matched_group_types": ";".join(group_types),
                "matched_keywords": ";".join(keywords[:25]),
                "likely_table_type": table_type,
                "page_text_excerpt": text.strip().replace("\n", " ")[:max_excerpt],
                "recommended_action": action,
            }
        )
    return rows


def run_search() -> pd.DataFrame:
    ensure_taxonomy_dirs()
    taxonomy = load_taxonomy()
    all_rows: list[dict[str, object]] = []

    for study in iter_study_reports():
        rows = search_report(
            int(study["year"]),
            str(study["poll_type"]),
            str(study["source_file"]),
            study["report_path"],
            taxonomy,
        )
        all_rows.extend(rows)

    df = pd.DataFrame(all_rows, columns=PAGE_CANDIDATE_COLUMNS)
    if not df.empty:
        df = df.sort_values(
            by=["recommended_action", "candidate_score", "year", "poll_type", "page"],
            ascending=[True, False, True, True, True],
        )
    df.to_csv(PAGE_CANDIDATES_PATH, index=False)
    return df


def main() -> None:
    df = run_search()
    auto_extract = int((df["recommended_action"] == "auto_extract").sum()) if not df.empty else 0
    review = int((df["recommended_action"] == "review").sum()) if not df.empty else 0
    pdfs = len(iter_study_reports())

    print("CSDS taxonomy-guided page search")
    print(f"  PDFs scanned: {pdfs}")
    print(f"  Candidate pages found: {len(df)}")
    print(f"  Pages marked auto_extract: {auto_extract}")
    print(f"  Pages marked review: {review}")
    print(f"  Saved: {PAGE_CANDIDATES_PATH}")


if __name__ == "__main__":
    main()
