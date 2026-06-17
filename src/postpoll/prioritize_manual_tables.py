"""
Prioritize manual CSDS table extraction by likely voter-behavior value.

Run:
    python -m src.postpoll.prioritize_manual_tables
"""

from __future__ import annotations

import re

import pandas as pd

from src.postpoll.qa_common import EXTRACTED_DIR, MANUAL_PRIORITY_PATH, MANUAL_REVIEW_PATH, extract_table_file

HIGH_PRIORITY_KEYWORDS = [
    "vote",
    "voted",
    "voting",
    "party",
    "bjp",
    "congress",
    "inc",
    "nda",
    "india",
    "upa",
    "caste",
    "religion",
    "muslim",
    "hindu",
    "women",
    "youth",
    "age",
    "education",
    "rural",
    "urban",
    "class",
    "income",
    "region",
    "state",
]

LOW_PRIORITY_KEYWORDS = [
    "methodology",
    "method",
    "questionnaire",
    "sampling",
    "fieldwork",
    "acknowledgement",
    "appendix",
    "contents",
    "table of contents",
    "page ",
    "total",
    "col_0",
    "blank",
    "malformed",
]

CLEANING_TYPE_KEYWORDS = {
    "questionnaire": ["questionnaire", "question", "q.", "item", "codebook"],
    "methodology_metadata": ["method", "sample", "weight", "fieldwork", "methodology"],
    "voter_group_party_table": [
        "vote",
        "party",
        "bjp",
        "congress",
        "caste",
        "religion",
        "gender",
        "age",
        "rural",
        "urban",
    ],
}


def _parse_year_poll_type(table_file: str) -> tuple[int | None, str]:
    match = re.search(r"(\d{4})_(pre_poll|post_poll)_table_", table_file)
    if not match:
        return None, ""
    return int(match.group(1)), match.group(2)


def _load_text_snippet(year: int | None, poll_type: str, table_file: str, max_chars: int = 4000) -> str:
    if not year or not poll_type:
        return ""

    table_path = EXTRACTED_DIR / table_file
    table_text = ""
    if table_path.exists():
        try:
            table_text = table_path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            table_text = ""

    text_path = EXTRACTED_DIR / f"{year}_{poll_type}_text.txt"
    full_text = ""
    if text_path.exists():
        try:
            full_text = text_path.read_text(encoding="utf-8", errors="ignore")[:max_chars]
        except OSError:
            full_text = ""

    return f"{table_text}\n{full_text}".lower()


def _keywords_found(text: str) -> list[str]:
    return sorted({kw for kw in HIGH_PRIORITY_KEYWORDS if kw in text})


def _score_text(text: str) -> tuple[int, list[str]]:
    keywords = _keywords_found(text)
    score = len(keywords)
    for boost_kw in ("vote", "voted", "voting", "bjp", "congress", "inc", "nda", "india", "upa"):
        if boost_kw in text:
            score += 1
            if boost_kw not in keywords:
                keywords.append(boost_kw)
    return score, sorted(set(keywords))


def _priority_bucket(score: int, text: str) -> str:
    low_hits = sum(1 for kw in LOW_PRIORITY_KEYWORDS if kw in text)
    if score >= 4 and low_hits <= 2:
        return "high"
    if score >= 2:
        return "medium"
    return "low"


def _suggested_cleaning_type(text: str, reason: str) -> str:
    reason_lower = reason.lower()
    for cleaning_type, keywords in CLEANING_TYPE_KEYWORDS.items():
        if any(kw in text or kw in reason_lower for kw in keywords):
            return cleaning_type
    if "unrecognized" in reason_lower or "malformed" in reason_lower:
        return "unclear"
    return "unclear"


def prioritize_manual_tables() -> pd.DataFrame:
    if not MANUAL_REVIEW_PATH.exists():
        return pd.DataFrame(
            columns=[
                "year",
                "poll_type",
                "source_file",
                "table_file",
                "page",
                "priority_score",
                "priority_bucket",
                "keywords_found",
                "suggested_cleaning_type",
                "notes",
            ]
        )

    manual = pd.read_csv(MANUAL_REVIEW_PATH)
    rows: list[dict[str, object]] = []
    seen_tables: set[str] = set()

    for _, record in manual.iterrows():
        reason = str(record.get("reason", ""))
        table_file = extract_table_file(reason)
        if not table_file or table_file in seen_tables:
            continue
        seen_tables.add(table_file)

        year = int(record["year"]) if pd.notna(record.get("year")) else None
        poll_type = str(record.get("poll_type", ""))
        if not year or not poll_type:
            parsed_year, parsed_poll = _parse_year_poll_type(table_file)
            year = year or parsed_year
            poll_type = poll_type or parsed_poll

        text = _load_text_snippet(year, poll_type, table_file)
        score, keywords = _score_text(text)
        bucket = _priority_bucket(score, text)
        cleaning_type = _suggested_cleaning_type(text, reason)

        notes = str(record.get("suggested_action", ""))
        if bucket == "low":
            notes = f"{notes}; likely low-value table".strip("; ")

        rows.append(
            {
                "year": year,
                "poll_type": poll_type,
                "source_file": f"{year}_{poll_type}_text.txt" if year and poll_type else "",
                "table_file": table_file,
                "page": record.get("page", ""),
                "priority_score": score,
                "priority_bucket": bucket,
                "keywords_found": ";".join(keywords),
                "suggested_cleaning_type": cleaning_type,
                "notes": notes,
            }
        )

    out = pd.DataFrame(rows)
    if out.empty:
        return out

    return out.sort_values(
        by=["priority_score", "year", "poll_type", "table_file"],
        ascending=[False, True, True, True],
    )


def main() -> None:
    ranked = prioritize_manual_tables()
    MANUAL_PRIORITY_PATH.parent.mkdir(parents=True, exist_ok=True)
    ranked.to_csv(MANUAL_PRIORITY_PATH, index=False)

    high = ranked[ranked["priority_bucket"] == "high"] if not ranked.empty else ranked
    print("CSDS manual extraction prioritization")
    print(f"  Manual tables ranked: {len(ranked)}")
    print(f"  High-priority tables: {len(high)}")
    print(f"  Saved: {MANUAL_PRIORITY_PATH}")

    if not high.empty:
        print("\n  Top 20 high-priority manual tables:")
        for _, row in high.head(20).iterrows():
            keywords = str(row["keywords_found"])[:80]
            print(
                f"    [{row['priority_score']}] {row['table_file']} "
                f"({row['suggested_cleaning_type']}; {keywords})"
            )
    else:
        print("  No high-priority manual tables identified yet.")


if __name__ == "__main__":
    main()
