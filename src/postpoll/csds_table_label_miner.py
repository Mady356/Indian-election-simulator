"""
Mine row/column labels from extracted CSDS tables for taxonomy-guided extraction.

Run:
    python -m src.postpoll.csds_table_label_miner
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.postpoll.csds_manifest import EXTRACTED_DIR
from src.postpoll.csds_taxonomy import (
    PAGE_CANDIDATES_PATH,
    TABLE_LABEL_INVENTORY_PATH,
    build_table_page_index,
    classify_table_type,
    detect_likely_layout,
    ensure_taxonomy_dirs,
    is_likely_percent_value_column,
    is_percent_column,
    is_sample_size_column,
    load_page_text,
    load_taxonomy,
    match_party,
    match_voter_group,
    page_text_for_number,
    parse_extracted_table_filename,
    strip_csds_label,
)

INVENTORY_COLUMNS = [
    "year",
    "poll_type",
    "source_file",
    "source_page",
    "table_file",
    "row_labels",
    "column_labels",
    "recognized_party_labels",
    "recognized_group_labels",
    "numeric_cell_count",
    "percent_like_cell_count",
    "likely_layout",
    "table_type",
    "extraction_potential_score",
]

PARTY_SCAN_LABELS = [
    "BJP",
    "Bharatiya Janata Party",
    "Congress",
    "INC",
    "Indian National Congress",
    "NDA",
    "INDIA",
    "UPA",
    "Others",
    "Other",
    "Regional",
    "Left",
    "BSP",
    "SP",
    "AAP",
    "TMC",
    "DMK",
    "AIADMK",
    "BJD",
]

GROUP_SCAN_LABELS = [
    "Men",
    "Women",
    "Male",
    "Female",
    "Hindu",
    "Muslim",
    "Christian",
    "Sikh",
    "SC",
    "ST",
    "OBC",
    "Upper Caste",
    "Dalit",
    "Adivasi",
    "Rural",
    "Urban",
    "Poor",
    "Lower",
    "Middle",
    "Upper",
    "Rich",
    "Youth",
    "Young",
    "18-25",
    "26-35",
    "36-45",
    "46-55",
    "56+",
    "No education",
    "Primary",
    "Secondary",
    "College",
    "Graduate",
]


def _unique_labels(series: pd.Series, limit: int = 40) -> list[str]:
    labels: list[str] = []
    seen: set[str] = set()
    for value in series.astype(str).tolist():
        text = strip_csds_label(value)
        if not text or text.lower() in {"nan", "none"}:
            continue
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        labels.append(text)
        if len(labels) >= limit:
            break
    return labels


def _recognized_from_labels(labels: list[str], matcher) -> list[str]:
    found: list[str] = []
    seen: set[str] = set()
    for label in labels:
        result = matcher(label)
        if not result:
            continue
        canonical = result if isinstance(result, str) else result[1]
        if canonical not in seen:
            found.append(canonical)
            seen.add(canonical)
    return found


def _count_numeric_cells(df: pd.DataFrame) -> tuple[int, int]:
    numeric = 0
    percent_like = 0
    for col in df.columns:
        for value in df[col].tolist():
            text = str(value).strip()
            if not text or text.lower() in {"nan", "none"}:
                continue
            cleaned = text.replace("%", "").replace(",", "")
            try:
                num = float(cleaned)
            except ValueError:
                continue
            numeric += 1
            if 0 <= num <= 100:
                percent_like += 1
    return numeric, percent_like


def _score_table(
    *,
    party_labels: list[str],
    group_labels: list[str],
    layout: str,
    table_type: str,
    percent_like: int,
    numeric: int,
) -> float:
    score = 0.0
    score += min(len(party_labels), 6) * 4.0
    score += min(len(group_labels), 6) * 3.0
    if layout in {
        "groups_as_rows_parties_as_columns",
        "parties_as_rows_groups_as_columns",
        "party_marginal_percent",
    }:
        score += 12.0
    if table_type in {
        "post_poll_vote_choice_table",
        "pre_poll_vote_intention_table",
        "voter_group_party_table",
    }:
        score += 15.0
    elif table_type == "issue_preference_table":
        score += 4.0
    elif table_type in {"questionnaire_table", "methodology_table", "irrelevant"}:
        score -= 20.0
    score += min(percent_like, 30) * 0.4
    score += min(numeric, 40) * 0.05
    return round(max(score, 0.0), 2)


def analyze_table_file(
    path: Path,
    page_index: pd.DataFrame,
    page_candidates: pd.DataFrame,
) -> dict[str, object] | None:
    parsed = parse_extracted_table_filename(path)
    if not parsed:
        return None
    year, poll_type, table_index = parsed

    try:
        df = pd.read_csv(path)
    except Exception:
        return None
    if df.empty:
        return None

    idx_row = page_index[
        (page_index["year"] == year)
        & (page_index["poll_type"] == poll_type)
        & (page_index["table_index"] == table_index)
    ]
    source_page = int(idx_row.iloc[0]["source_page"]) if not idx_row.empty else ""
    source_file = str(idx_row.iloc[0]["source_file"]) if not idx_row.empty else ""

    row_labels = _unique_labels(df.iloc[:, 0])
    for col in df.columns[1:6]:
        row_labels.extend(_unique_labels(df[col], limit=10))
    column_labels = [strip_csds_label(col) for col in df.columns if str(col).strip()]

    party_labels = _recognized_from_labels(row_labels + column_labels, match_party)
    group_labels = _recognized_from_labels(row_labels + column_labels, match_voter_group)

    preferred_type = ""
    if source_page and not page_candidates.empty:
        cand = page_candidates[
            (page_candidates["year"] == year)
            & (page_candidates["poll_type"] == poll_type)
            & (page_candidates["page"] == source_page)
        ]
        if not cand.empty:
            preferred_type = str(cand.iloc[0].get("matched_group_types", "")).split(";")[0]

    layout = detect_likely_layout(df, preferred_type or None)
    page_text = page_text_for_number(load_page_text(year, poll_type), int(source_page)) if source_page else ""
    table_type = classify_table_type(page_text, poll_type, table_context=path.stem)
    numeric, percent_like = _count_numeric_cells(df)
    score = _score_table(
        party_labels=party_labels,
        group_labels=group_labels,
        layout=layout,
        table_type=table_type,
        percent_like=percent_like,
        numeric=numeric,
    )

    return {
        "year": year,
        "poll_type": poll_type,
        "source_file": source_file,
        "source_page": source_page,
        "table_file": path.name,
        "row_labels": json.dumps(row_labels[:40], ensure_ascii=False),
        "column_labels": json.dumps(column_labels[:30], ensure_ascii=False),
        "recognized_party_labels": ";".join(party_labels),
        "recognized_group_labels": ";".join(group_labels),
        "numeric_cell_count": numeric,
        "percent_like_cell_count": percent_like,
        "likely_layout": layout,
        "table_type": table_type,
        "extraction_potential_score": score,
    }


def run_miner() -> pd.DataFrame:
    ensure_taxonomy_dirs()
    load_taxonomy()

    page_index = build_table_page_index()
    page_candidates = pd.read_csv(PAGE_CANDIDATES_PATH) if PAGE_CANDIDATES_PATH.exists() else pd.DataFrame()

    rows: list[dict[str, object]] = []
    for path in sorted(EXTRACTED_DIR.glob("*_table_*.csv")):
        record = analyze_table_file(path, page_index, page_candidates)
        if record:
            rows.append(record)

    df = pd.DataFrame(rows, columns=INVENTORY_COLUMNS)
    df = df.sort_values("extraction_potential_score", ascending=False)
    df.to_csv(TABLE_LABEL_INVENTORY_PATH, index=False)
    return df


def main() -> None:
    df = run_miner()
    print("CSDS table label miner")
    print(f"  Tables scanned: {len(df)}")
    print(f"  Saved: {TABLE_LABEL_INVENTORY_PATH}")
    print("  Top 50 tables by extraction_potential_score:")
    top = df.head(50)
    for _, row in top.iterrows():
        print(
            f"    {row['extraction_potential_score']:6.1f}  "
            f"{row['table_file']}  layout={row['likely_layout']}  "
            f"parties={row['recognized_party_labels'] or '-'}  "
            f"groups={row['recognized_group_labels'] or '-'}"
        )


if __name__ == "__main__":
    main()
