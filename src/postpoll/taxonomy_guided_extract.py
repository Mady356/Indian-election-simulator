"""
Taxonomy-guided table extraction from candidate CSDS pages and extracted CSV tables.

Run:
    python -m src.postpoll.taxonomy_guided_extract
"""

from __future__ import annotations

import uuid
from pathlib import Path

import pandas as pd

from src.postpoll.csds_manifest import BEHAVIOUR_ANALYSIS_DIR, EXTRACTED_DIR
from src.postpoll.csds_taxonomy import (
    EXTRACTED_CANDIDATES_PATH,
    PAGE_CANDIDATES_PATH,
    TABLE_LABEL_INVENTORY_PATH,
    build_table_page_index,
    classify_table_type,
    detect_likely_layout,
    ensure_taxonomy_dirs,
    flatten_multiline_header,
    infer_geography_from_text,
    infer_voter_group_from_context,
    is_percent_column,
    is_sample_size_column,
    load_page_text,
    load_taxonomy,
    match_party,
    match_voter_group,
    page_context_signals,
    page_text_for_number,
    parse_extracted_table_filename,
    parse_vote_share,
    score_extraction_confidence,
    strip_csds_label,
    taxonomy_skip_labels,
)

EXTRACTED_CANDIDATE_COLUMNS = [
    "candidate_id",
    "year",
    "poll_type",
    "source",
    "source_file",
    "source_page",
    "source_table_index",
    "source_table_title",
    "geography_level",
    "state",
    "voter_group_type",
    "voter_group",
    "party_or_alliance",
    "vote_share",
    "raw_row_label",
    "raw_column_label",
    "raw_cell_value",
    "extraction_confidence",
    "evidence_text",
    "candidate_status",
    "notes",
]

SKIP_TABLE_TYPES = {"questionnaire_table", "methodology_table", "irrelevant"}
MIN_INVENTORY_SCORE = 12.0


def _clean_table(table: list[list[object | None]]) -> pd.DataFrame:
    if not table:
        return pd.DataFrame()
    max_cols = max(len(row) for row in table)
    rows: list[list[str]] = []
    for row in table:
        cells = [str(cell).strip() if cell is not None else "" for cell in row]
        if len(cells) < max_cols:
            cells.extend([""] * (max_cols - len(cells)))
        rows.append(cells)
    if not rows:
        return pd.DataFrame()
    header = rows[0]
    if all(not cell for cell in header):
        header = [f"col_{i}" for i in range(max_cols)]
    else:
        header = [cell or f"col_{i}" for i, cell in enumerate(header)]
    data = rows[1:] if len(rows) > 1 else rows
    return pd.DataFrame(data, columns=header)


def _count_party_matches(labels: list[str]) -> int:
    return sum(1 for label in labels if match_party(label))


def _count_group_matches(labels: list[str], preferred_type: str | None) -> int:
    return sum(1 for label in labels if match_voter_group(label, preferred_type))


def _pick_share_column(df: pd.DataFrame, exclude_cols: set[str]) -> str | None:
    for col in df.columns:
        if str(col) in exclude_cols:
            continue
        if is_percent_column(col):
            return str(col)
    for col in df.columns:
        if str(col) in exclude_cols or is_sample_size_column(col):
            continue
        parsed = df[col].map(parse_vote_share).notna().sum()
        if parsed >= max(2, len(df) // 3):
            return str(col)
    return None


def _candidate_row(
    meta: dict[str, object],
    table_index: int,
    group_type: str,
    group: str,
    party: str,
    vote_share: float,
    raw_row: object,
    raw_col: object,
    raw_value: object,
    confidence: str,
    page_text: str,
    layout: str,
    table_title: str = "",
) -> dict[str, object]:
    status = "auto_accepted_candidate" if confidence == "high" else "needs_review"
    excerpt = page_text.strip().replace("\n", " ")[:250]
    return {
        "candidate_id": str(uuid.uuid4()),
        "year": meta["year"],
        "poll_type": meta["poll_type"],
        "source": meta["source"],
        "source_file": meta["source_file"],
        "source_page": meta["source_page"],
        "source_table_index": table_index,
        "source_table_title": table_title,
        "geography_level": meta.get("geography_level", "national"),
        "state": meta.get("state", ""),
        "voter_group_type": group_type,
        "voter_group": group,
        "party_or_alliance": party,
        "vote_share": vote_share,
        "raw_row_label": str(raw_row).strip(),
        "raw_column_label": str(raw_col).strip(),
        "raw_cell_value": str(raw_value).strip(),
        "extraction_confidence": confidence,
        "evidence_text": excerpt,
        "candidate_status": status,
        "notes": layout,
    }


def extract_layout_a(
    df: pd.DataFrame,
    preferred_type: str | None,
    page_text: str,
    meta: dict[str, object],
    table_index: int,
    table_type: str,
    context_signals: dict[str, object],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    if df.empty or len(df.columns) < 2:
        return rows

    first_col = df.columns[0]
    party_cols = [col for col in df.columns[1:] if match_party(col)]
    if not party_cols:
        party_cols = [
            col
            for col in df.columns[1:]
            if not is_sample_size_column(col) and not is_percent_column(col)
        ]

    party_count = len([col for col in party_cols if match_party(col)])
    skip = taxonomy_skip_labels()
    group_count = 0

    for _, record in df.iterrows():
        row_label = record[first_col]
        row_norm = normalize_row_label(row_label)
        if row_norm in skip:
            continue
        group_match = match_voter_group(row_label, preferred_type)
        if not group_match:
            continue
        group_type, group = group_match
        group_count += 1

        for party_col in party_cols:
            party = match_party(party_col)
            if not party:
                continue
            raw_value = record[party_col]
            vote_share = parse_vote_share(raw_value)
            if vote_share is None:
                continue
            confidence = score_extraction_confidence(
                party_count=party_count,
                group_count=group_count,
                vote_share=vote_share,
                page_text=page_text,
                table_type=table_type,
                layout="layout_a_rows_groups",
                has_explicit_group=True,
                context_signals=context_signals,
            )
            rows.append(
                _candidate_row(
                    meta,
                    table_index,
                    group_type,
                    group,
                    party,
                    vote_share,
                    row_label,
                    party_col,
                    raw_value,
                    confidence,
                    page_text,
                    "layout_a_rows_groups",
                )
            )
    return rows


def extract_layout_b(
    df: pd.DataFrame,
    preferred_type: str | None,
    page_text: str,
    meta: dict[str, object],
    table_index: int,
    table_type: str,
    context_signals: dict[str, object],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    if df.empty or len(df.columns) < 2:
        return rows

    first_col = df.columns[0]
    group_cols = [col for col in df.columns[1:] if match_voter_group(col, preferred_type)]
    if not group_cols:
        return rows

    skip = taxonomy_skip_labels()
    group_count = len(group_cols)
    party_count = 0

    for _, record in df.iterrows():
        row_label = record[first_col]
        party = match_party(row_label)
        if not party:
            continue
        party_count += 1
        for group_col in group_cols:
            group_match = match_voter_group(group_col, preferred_type)
            if not group_match:
                continue
            group_type, group = group_match
            raw_value = record[group_col]
            vote_share = parse_vote_share(raw_value)
            if vote_share is None:
                continue
            confidence = score_extraction_confidence(
                party_count=party_count,
                group_count=group_count,
                vote_share=vote_share,
                page_text=page_text,
                table_type=table_type,
                layout="layout_b_rows_parties",
                has_explicit_group=True,
                context_signals=context_signals,
            )
            rows.append(
                _candidate_row(
                    meta,
                    table_index,
                    group_type,
                    group,
                    party,
                    vote_share,
                    row_label,
                    group_col,
                    raw_value,
                    confidence,
                    page_text,
                    "layout_b_rows_parties",
                )
            )
    return rows


def extract_layout_shifted_header(
    df: pd.DataFrame,
    preferred_type: str | None,
    page_text: str,
    meta: dict[str, object],
    table_index: int,
    table_type: str,
    context_signals: dict[str, object],
) -> list[dict[str, object]]:
    if df.empty:
        return []

    header_row = df.iloc[0].tolist()
    party_by_col: dict[str, str] = {}
    for col, value in zip(df.columns, header_row):
        party = match_party(value)
        if party:
            party_by_col[str(col)] = party
    if len(party_by_col) < 2:
        return []

    body = df.iloc[1:].reset_index(drop=True)
    return extract_layout_a(
        body, preferred_type, page_text, meta, table_index, table_type, context_signals
    )


def extract_party_marginal(
    df: pd.DataFrame,
    preferred_types: list[str],
    page_text: str,
    meta: dict[str, object],
    table_index: int,
    table_type: str,
    context_signals: dict[str, object],
    table_title: str = "",
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    if df.empty:
        return rows

    label_col_idx = None
    best_party_hits = 0
    for idx, col in enumerate(df.columns):
        col_name = str(col)
        if is_percent_column(col_name) or is_sample_size_column(col_name):
            continue
        hits = sum(1 for value in df.iloc[:, idx] if match_party(value))
        if hits > best_party_hits:
            best_party_hits = hits
            label_col_idx = idx
    if label_col_idx is None or best_party_hits < 2:
        return rows

    label_col = str(df.columns[label_col_idx])
    pct_col = _pick_share_column(df, {label_col})
    if not pct_col:
        return rows

    context_group = infer_voter_group_from_context(page_text, preferred_types, strict=True)
    if not context_group:
        if table_type in {
            "post_poll_vote_choice_table",
            "pre_poll_vote_intention_table",
            "voter_group_party_table",
        } and context_signals.get("vote_question"):
            context_group = ("electorate", "all voters")
        elif not context_signals.get("vote_question"):
            return rows
        else:
            return rows

    group_type, group = context_group
    skip = taxonomy_skip_labels()
    party_count = 0

    for _, record in df.iterrows():
        row_label = record.iloc[label_col_idx]
        row_norm = normalize_row_label(row_label)
        if row_norm in skip:
            continue
        party = match_party(row_label)
        if not party:
            continue
        party_count += 1
        raw_value = record[pct_col]
        vote_share = parse_vote_share(raw_value)
        if vote_share is None:
            continue
        confidence = score_extraction_confidence(
            party_count=party_count,
            group_count=1,
            vote_share=vote_share,
            page_text=page_text,
            table_type=table_type,
            layout="party_marginal_percent",
            has_explicit_group=group_type != "electorate",
            context_signals=context_signals,
        )
        rows.append(
            _candidate_row(
                meta,
                table_index,
                group_type,
                group,
                party,
                vote_share,
                row_label,
                pct_col,
                raw_value,
                confidence,
                page_text,
                "party_marginal_percent",
                table_title=table_title,
            )
        )
    return rows


def normalize_row_label(label: object) -> str:
    from src.postpoll.csds_taxonomy import normalize_text

    return normalize_text(strip_csds_label(label))


def extract_from_dataframe(
    df: pd.DataFrame,
    *,
    preferred_types: list[str],
    page_text: str,
    meta: dict[str, object],
    table_index: int,
    poll_type: str,
    table_title: str = "",
    table_context: str = "",
) -> list[dict[str, object]]:
    if df.empty or df.shape[0] < 2:
        return []

    work = flatten_multiline_header(df.copy())
    preferred_type = preferred_types[0] if preferred_types else None
    table_type = classify_table_type(page_text, poll_type, table_context=table_context)
    if table_type in SKIP_TABLE_TYPES:
        return []

    signals = page_context_signals(page_text, table_context)
    if signals["negative_score"] >= 2 and not signals["vote_question"]:
        return []

    if table_type == "issue_preference_table" and not signals["vote_question"]:
        return []

    geo_level, state = infer_geography_from_text(page_text)
    meta = {**meta, "geography_level": geo_level, "state": state}

    layout = detect_likely_layout(work, preferred_type)
    col_labels = [str(c) for c in work.columns]
    row_labels = [str(v) for v in work.iloc[:, 0].tolist()]
    party_in_cols = _count_party_matches(col_labels)
    party_in_rows = _count_party_matches(row_labels)
    group_in_cols = _count_group_matches(col_labels, preferred_type)
    group_in_rows = _count_group_matches(row_labels, preferred_type)

    extracted: list[dict[str, object]] = []

    if layout == "party_marginal_percent" or (party_in_rows >= 2 and group_in_cols == 0 and group_in_rows == 0):
        extracted.extend(
            extract_party_marginal(
                work,
                preferred_types,
                page_text,
                meta,
                table_index,
                table_type,
                signals,
                table_title,
            )
        )

    if party_in_cols >= 1 and group_in_rows >= 1:
        extracted.extend(
            extract_layout_a(work, preferred_type, page_text, meta, table_index, table_type, signals)
        )
    elif party_in_rows >= 1 and group_in_cols >= 1:
        extracted.extend(
            extract_layout_b(work, preferred_type, page_text, meta, table_index, table_type, signals)
        )
    elif party_in_cols >= 2 and group_in_rows == 0:
        extracted.extend(
            extract_layout_shifted_header(work, preferred_type, page_text, meta, table_index, table_type, signals)
        )

    deduped: list[dict[str, object]] = []
    seen: set[tuple[object, ...]] = set()
    for row in extracted:
        key = (
            row["source_page"],
            row["source_table_index"],
            row["voter_group_type"],
            row["voter_group"],
            row["party_or_alliance"],
            row["vote_share"],
            row["raw_row_label"],
            row["raw_column_label"],
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(row)
    return deduped


def extract_page_tables(
    report_path: Path,
    page_num: int,
    preferred_types: list[str],
    meta: dict[str, object],
) -> list[dict[str, object]]:
    try:
        import pdfplumber
    except ImportError as exc:
        raise RuntimeError("pdfplumber is required") from exc

    rows: list[dict[str, object]] = []
    with pdfplumber.open(report_path) as pdf:
        if page_num < 1 or page_num > len(pdf.pages):
            return rows
        page = pdf.pages[page_num - 1]
        page_text = page.extract_text() or ""
        tables = page.extract_tables() or []

        for table_index, table in enumerate(tables, start=1):
            df = _clean_table(table)
            rows.extend(
                extract_from_dataframe(
                    df,
                    preferred_types=preferred_types,
                    page_text=page_text,
                    meta=meta,
                    table_index=table_index,
                    poll_type=str(meta["poll_type"]),
                    table_context=f"pdf_table_{table_index}",
                )
            )
    return rows


def extract_csv_table(
    csv_path: Path,
    *,
    source_file: str,
    source_page: int,
    preferred_types: list[str],
    source: str,
) -> list[dict[str, object]]:
    parsed = parse_extracted_table_filename(csv_path)
    if not parsed:
        return []
    year, poll_type, table_index = parsed

    try:
        df = pd.read_csv(csv_path)
    except Exception:
        return []

    page_text = page_text_for_number(load_page_text(year, poll_type), source_page)
    meta = {
        "year": year,
        "poll_type": poll_type,
        "source": source,
        "source_file": source_file,
        "source_page": source_page,
    }
    return extract_from_dataframe(
        df,
        preferred_types=preferred_types,
        page_text=page_text,
        meta=meta,
        table_index=table_index,
        poll_type=poll_type,
        table_title=csv_path.name,
        table_context=csv_path.name,
    )


def run_extract() -> tuple[pd.DataFrame, int, int]:
    ensure_taxonomy_dirs()
    load_taxonomy()

    page_index = build_table_page_index()
    inventory = (
        pd.read_csv(TABLE_LABEL_INVENTORY_PATH)
        if TABLE_LABEL_INVENTORY_PATH.exists()
        else pd.DataFrame()
    )
    page_candidates = (
        pd.read_csv(PAGE_CANDIDATES_PATH)
        if PAGE_CANDIDATES_PATH.exists()
        else pd.DataFrame()
    )

    all_rows: list[dict[str, object]] = []
    tables_extracted = 0
    pages_processed = 0

    inventory_pages: set[tuple[int, str, int]] = set()

    if not inventory.empty:
        targets = inventory[
            (inventory["extraction_potential_score"] >= MIN_INVENTORY_SCORE)
            & (~inventory["table_type"].isin(SKIP_TABLE_TYPES))
            & (
                inventory["table_type"].isin(
                    {
                        "post_poll_vote_choice_table",
                        "pre_poll_vote_intention_table",
                        "voter_group_party_table",
                    }
                )
            )
        ]
        for _, inv_row in targets.iterrows():
            table_file = str(inv_row["table_file"])
            csv_path = EXTRACTED_DIR / table_file
            if not csv_path.exists():
                continue

            year = int(inv_row["year"])
            poll_type = str(inv_row["poll_type"])
            source_page = int(inv_row["source_page"]) if pd.notna(inv_row["source_page"]) else 0
            source_file = str(inv_row.get("source_file", ""))

            preferred_types: list[str] = []
            if not page_candidates.empty and source_page:
                cand = page_candidates[
                    (page_candidates["year"] == year)
                    & (page_candidates["poll_type"] == poll_type)
                    & (page_candidates["page"] == source_page)
                ]
                if not cand.empty:
                    preferred_types = [
                        t for t in str(cand.iloc[0].get("matched_group_types", "")).split(";") if t
                    ]

            if not source_file:
                idx = page_index[
                    (page_index["year"] == year)
                    & (page_index["poll_type"] == poll_type)
                    & (page_index["table_file"] == table_file)
                ]
                if not idx.empty:
                    source_file = str(idx.iloc[0]["source_file"])
                    source_page = int(idx.iloc[0]["source_page"])

            extracted = extract_csv_table(
                csv_path,
                source_file=source_file,
                source_page=source_page,
                preferred_types=preferred_types,
                source="CSDS-Lokniti National Election Study",
            )
            if extracted:
                tables_extracted += 1
                inventory_pages.add((year, poll_type, source_page))
            all_rows.extend(extracted)

    if PAGE_CANDIDATES_PATH.exists():
        pages = pd.read_csv(PAGE_CANDIDATES_PATH)
        targets = pages[pages["recommended_action"].isin(["auto_extract", "review"])]
        pages_processed = len(targets)

        for _, page_row in targets.iterrows():
            page_key = (int(page_row["year"]), str(page_row["poll_type"]), int(page_row["page"]))
            if page_key in inventory_pages:
                continue
            report_path = BEHAVIOUR_ANALYSIS_DIR / str(page_row["source_file"])
            if not report_path.exists():
                continue
            preferred_types = [t for t in str(page_row.get("matched_group_types", "")).split(";") if t]
            meta = {
                "year": int(page_row["year"]),
                "poll_type": str(page_row["poll_type"]),
                "source": "CSDS-Lokniti National Election Study",
                "source_file": str(page_row["source_file"]),
                "source_page": int(page_row["page"]),
            }
            extracted = extract_page_tables(report_path, int(page_row["page"]), preferred_types, meta)
            if extracted:
                tables_extracted += len({r["source_table_index"] for r in extracted})
            all_rows.extend(extracted)

    if all_rows:
        out = pd.DataFrame(all_rows)
        out = out.drop_duplicates(
            subset=[
                "year",
                "poll_type",
                "source_file",
                "source_page",
                "source_table_index",
                "voter_group_type",
                "voter_group",
                "party_or_alliance",
                "vote_share",
                "raw_row_label",
                "raw_column_label",
            ],
            keep="first",
        )
        out = out.reindex(columns=EXTRACTED_CANDIDATE_COLUMNS)
    else:
        out = pd.DataFrame(columns=EXTRACTED_CANDIDATE_COLUMNS)

    out.to_csv(EXTRACTED_CANDIDATES_PATH, index=False)
    return out, tables_extracted, pages_processed


def main() -> None:
    df, tables_extracted, pages_processed = run_extract()

    high = int((df["extraction_confidence"] == "high").sum()) if not df.empty else 0
    medium = int((df["extraction_confidence"] == "medium").sum()) if not df.empty else 0
    low = int((df["extraction_confidence"] == "low").sum()) if not df.empty else 0

    print("CSDS taxonomy-guided extraction")
    print(f"  Candidate pages processed: {pages_processed}")
    print(f"  Tables extracted: {tables_extracted}")
    print(f"  Candidate rows created: {len(df)}")
    print(f"  High-confidence candidates: {high}")
    print(f"  Medium-confidence candidates: {medium}")
    print(f"  Low-confidence candidates: {low}")
    print(f"  Saved: {EXTRACTED_CANDIDATES_PATH}")


if __name__ == "__main__":
    main()
