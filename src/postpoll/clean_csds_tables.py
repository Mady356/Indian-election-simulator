"""
Normalize extracted CSDS voter-group tables into a long vote-behavior schema.

Run:
    python -m src.postpoll.clean_csds_tables
"""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd

from src.postpoll.csds_manifest import EXTRACTED_DIR, PROCESSED_DIR, REPORTS_DIR, STUDIES

VOTE_BEHAVIOR_PATH = PROCESSED_DIR / "csds_vote_behavior_tables.csv"
MANUAL_REVIEW_PATH = REPORTS_DIR / "manual_extraction_needed.csv"

VOTE_BEHAVIOR_COLUMNS = [
    "year",
    "poll_type",
    "geography_level",
    "state",
    "voter_group_type",
    "voter_group",
    "party_or_alliance",
    "vote_share",
    "sample_size",
    "source_table",
    "source_page",
    "confidence",
    "notes",
    "original_label",
]

PARTY_ALIASES: dict[str, str] = {
    "BJP": "BJP",
    "BHARATIYA JANATA PARTY": "BJP",
    "BHARATIYA JANATA": "BJP",
    "NDA": "NDA",
    "N.D.A.": "NDA",
    "NATIONAL DEMOCRATIC ALLIANCE": "NDA",
    "INC": "INC",
    "CONGRESS": "INC",
    "INDIAN NATIONAL CONGRESS": "INC",
    "I.N.C.": "INC",
    "INDIA": "INDIA",
    "INDIA BLOC": "INDIA",
    "INDIA ALLIANCE": "INDIA",
    "UPA": "UPA",
    "UNITED PROGRESSIVE ALLIANCE": "UPA",
    "OTHERS": "Others",
    "OTHER": "Others",
    "OTHER PARTIES": "Others",
    "DK/OTHERS": "Others",
    "DON'T KNOW": "Others",
    "DK": "Others",
    "REFUSED": "Others",
    "NOTA": "Others",
    "REGIONAL": "Regional",
    "REGIONAL PARTIES": "Regional",
    "SP": "Regional",
    "BSP": "Regional",
    "AITC": "Regional",
    "TMC": "Regional",
    "DMK": "Regional",
    "YSRCP": "Regional",
    "TDP": "Regional",
    "BJD": "Regional",
    "JD(U)": "Regional",
    "JDU": "Regional",
    "RJD": "Regional",
    "AAP": "Regional",
    "AAAP": "Regional",
}

VOTER_GROUP_RULES: list[tuple[str, list[str]]] = [
    ("gender", ["GENDER", "MALE", "FEMALE", "MEN", "WOMEN"]),
    ("age", ["AGE", "YOUNG", "MIDDLE", "OLD", "18-22", "18-25", "26-35", "36-45", "46-55", "56+"]),
    ("religion", ["RELIGION", "HINDU", "MUSLIM", "CHRISTIAN", "SIKH", "BUDDHIST", "JAIN", "OTHERS"]),
    ("caste", ["CASTE", "COMMUNITY", "SC", "ST", "OBC", "UPPER CASTE", "DALIT", "ADIVASI"]),
    ("class", ["CLASS", "INCOME", "POOR", "MIDDLE CLASS", "RICH", "AFFLUENT", "ECONOMIC"]),
    ("education", ["EDUCATION", "LITERATE", "ILLITERATE", "GRADUATE", "PRIMARY", "SECONDARY"]),
    ("rural_urban", ["RURAL", "URBAN", "RURAL/URBAN", "LOCALITY"]),
    ("region", ["REGION", "ZONE", "NORTH", "SOUTH", "EAST", "WEST", "CENTRAL", "NORTHEAST"]),
    ("state", ["STATE", "UTTAR PRADESH", "MAHARASHTRA", "BIHAR", "WEST BENGAL"]),
]

SKIP_ROW_LABELS = {
    "TOTAL",
    "ALL",
    "ALL VOTERS",
    "VOTERS",
    "RESPONDENTS",
    "SAMPLE",
    "DK",
    "DON'T KNOW",
    "REFUSED",
    "N",
    "N=",
}


def _normalize_key(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip().upper()
    text = re.sub(r"[^A-Z0-9+()/&\-\s]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def normalize_party(label: object) -> str:
    key = _normalize_key(label)
    if not key:
        return "Unknown"
    if key in PARTY_ALIASES:
        return PARTY_ALIASES[key]
    for alias, canonical in PARTY_ALIASES.items():
        if alias in key or key in alias:
            return canonical
    if re.search(r"\bBJP\b", key):
        return "BJP"
    if re.search(r"\bCONGRESS\b|\bINC\b", key):
        return "INC"
    if re.search(r"\bNDA\b", key):
        return "NDA"
    if re.search(r"\bINDIA\b", key):
        return "INDIA"
    if re.search(r"\bUPA\b", key):
        return "UPA"
    if re.search(r"\bOTHER", key):
        return "Others"
    return "Unknown"


def infer_voter_group_type(label: object, table_context: str = "") -> str:
    key = _normalize_key(label)
    context = _normalize_key(table_context)
    combined = f"{key} {context}"
    for group_type, keywords in VOTER_GROUP_RULES:
        if any(word in combined for word in keywords):
            return group_type
    return "other"


def _parse_percent(value: object) -> float | None:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return None
    text = str(value).strip()
    if not text or text in {"-", "—", "–", "NA", "N/A", "*", "**"}:
        return None
    text = text.replace("%", "").replace(",", "").strip()
    try:
        num = float(text)
    except ValueError:
        return None
    if 0 <= num <= 1:
        num *= 100
    if 0 <= num <= 100:
        return round(num, 3)
    return None


def _is_party_header(label: object) -> bool:
    key = _normalize_key(label)
    if not key or key in SKIP_ROW_LABELS:
        return False
    return normalize_party(label) != "Unknown" or any(
        token in key
        for token in ("BJP", "CONGRESS", "NDA", "INDIA", "UPA", "OTHER", "PARTY", "ALLIANCE")
    )


def _is_voter_group_label(label: object) -> bool:
    key = _normalize_key(label)
    if not key or key in SKIP_ROW_LABELS:
        return False
    if _is_party_header(label):
        return False
    return len(key) >= 2


def _parse_source_table(path: Path) -> tuple[int, str]:
    match = re.search(r"(\d{4})_(pre_poll|post_poll)_table_(\d+)", path.stem)
    if not match:
        return 0, "pre_poll"
    return int(match.group(1)), match.group(2)


def _parse_page_from_notes(notes: str) -> str:
    match = re.search(r"page\s*(\d+)", notes, re.I)
    return match.group(1) if match else ""


def _table_context(df: pd.DataFrame) -> str:
    sample = " ".join(df.astype(str).fillna("").values.flatten()[:40])
    return sample[:500]


def _clean_wide_table(
    df: pd.DataFrame,
    year: int,
    poll_type: str,
    source_table: str,
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    rows: list[dict[str, object]] = []
    manual: list[dict[str, object]] = []
    if df.empty:
        return rows, manual

    work = df.copy()
    work.columns = [str(col).strip() for col in work.columns]
    context = _table_context(work)

    first_col = work.columns[0]
    party_cols = [col for col in work.columns[1:] if _is_party_header(col)]
    group_rows = sum(_is_voter_group_label(val) for val in work[first_col])

    if not party_cols or group_rows < 1:
        return rows, manual

    extracted = 0
    for _, record in work.iterrows():
        group_label = record[first_col]
        if not _is_voter_group_label(group_label):
            continue
        group_type = infer_voter_group_type(group_label, context)
        for party_col in party_cols:
            vote_share = _parse_percent(record[party_col])
            if vote_share is None:
                continue
            extracted += 1
            rows.append(
                {
                    "year": year,
                    "poll_type": poll_type,
                    "geography_level": "national",
                    "state": "",
                    "voter_group_type": group_type,
                    "voter_group": str(group_label).strip(),
                    "party_or_alliance": normalize_party(party_col),
                    "vote_share": vote_share,
                    "sample_size": "",
                    "source_table": source_table,
                    "source_page": "",
                    "confidence": "medium",
                    "notes": "auto-cleaned wide table",
                    "original_label": f"{group_label} | {party_col}",
                }
            )

    if extracted == 0:
        manual.append(
            {
                "year": year,
                "poll_type": poll_type,
                "page": "",
                "reason": f"wide table not parsed: {source_table}",
                "suggested_action": "verify party/group headers and transcribe manually",
            }
        )
    return rows, manual


def _clean_long_table(
    df: pd.DataFrame,
    year: int,
    poll_type: str,
    source_table: str,
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    rows: list[dict[str, object]] = []
    manual: list[dict[str, object]] = []
    if df.empty:
        return rows, manual

    work = df.copy()
    work.columns = [str(col).strip() for col in work.columns]
    context = _table_context(work)
    normalized_cols = {_normalize_key(col): col for col in work.columns}

    group_col = None
    party_col = None
    share_col = None

    for col in work.columns:
        key = _normalize_key(col)
        if group_col is None and any(token in key for token in ("GROUP", "CATEGORY", "SOCIAL", "DEMOGRAPHIC")):
            group_col = col
        if party_col is None and any(token in key for token in ("PARTY", "ALLIANCE", "VOTE FOR", "PREFERENCE")):
            party_col = col
        if share_col is None and any(token in key for token in ("%", "PERCENT", "VOTE SHARE", "SHARE")):
            share_col = col

    if group_col is None:
        for col in work.columns:
            if infer_voter_group_type(col, context) != "other":
                group_col = col
                break
    if group_col is None and len(work.columns) >= 1:
        group_col = work.columns[0]
    if party_col is None:
        for col in work.columns:
            if _is_party_header(col):
                party_col = col
                break
        if party_col is None:
            for col in work.columns[1:]:
                if work[col].astype(str).map(_is_party_header).any():
                    party_col = col
                    break
    if share_col is None:
        for col in work.columns:
            if work[col].map(_parse_percent).notna().sum() >= max(2, len(work) // 3):
                share_col = col
                break

    if not group_col or not party_col or not share_col:
        return rows, manual

    extracted = 0
    for _, record in work.iterrows():
        group_label = record[group_col]
        party_label = record[party_col]
        vote_share = _parse_percent(record[share_col])
        if not _is_voter_group_label(group_label) and infer_voter_group_type(group_label, context) == "other":
            continue
        if vote_share is None:
            continue
        party = normalize_party(party_label)
        if party == "Unknown":
            continue
        extracted += 1
        rows.append(
            {
                "year": year,
                "poll_type": poll_type,
                "geography_level": "national",
                "state": "",
                "voter_group_type": infer_voter_group_type(group_label, context),
                "voter_group": str(group_label).strip(),
                "party_or_alliance": party,
                "vote_share": vote_share,
                "sample_size": "",
                "source_table": source_table,
                "source_page": "",
                "confidence": "medium",
                "notes": "auto-cleaned long table",
                "original_label": f"{group_label} | {party_label}",
            }
        )

    if extracted == 0:
        manual.append(
            {
                "year": year,
                "poll_type": poll_type,
                "page": "",
                "reason": f"long table not parsed: {source_table}",
                "suggested_action": "map group/party/share columns manually",
            }
        )
    return rows, manual


def clean_extracted_table(path: Path) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    year, poll_type = _parse_source_table(path)
    if year == 0:
        return [], []

    try:
        df = pd.read_csv(path)
    except Exception:
        return [], [
            {
                "year": year,
                "poll_type": poll_type,
                "page": "",
                "reason": f"could not read CSV: {path.name}",
                "suggested_action": "re-extract or transcribe manually",
            }
        ]

    wide_rows, wide_manual = _clean_wide_table(df, year, poll_type, path.name)
    if wide_rows:
        return wide_rows, wide_manual

    long_rows, long_manual = _clean_long_table(df, year, poll_type, path.name)
    if long_rows:
        return long_rows, long_manual

    return [], [
        {
            "year": year,
            "poll_type": poll_type,
            "page": "",
            "reason": f"table structure unrecognized: {path.name}",
            "suggested_action": "inspect extracted CSV and add manual mapping",
        }
    ]


def append_manual_review(new_rows: list[dict[str, object]]) -> None:
    if not new_rows:
        return
    new_df = pd.DataFrame(new_rows)
    if MANUAL_REVIEW_PATH.exists():
        existing = pd.read_csv(MANUAL_REVIEW_PATH)
        combined = pd.concat([existing, new_df], ignore_index=True)
    else:
        combined = new_df
    combined = combined.drop_duplicates(
        subset=["year", "poll_type", "page", "reason", "suggested_action"],
        keep="last",
    )
    combined.to_csv(MANUAL_REVIEW_PATH, index=False)


def clean_all_tables() -> tuple[pd.DataFrame, int, int]:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    all_rows: list[dict[str, object]] = []
    manual_rows: list[dict[str, object]] = []
    table_paths = sorted(EXTRACTED_DIR.glob("*_table_*.csv"))
    cleaned_tables = 0

    for path in table_paths:
        rows, manual = clean_extracted_table(path)
        if rows:
            cleaned_tables += 1
            all_rows.extend(rows)
        manual_rows.extend(manual)

    append_manual_review(manual_rows)

    if all_rows:
        out = pd.DataFrame(all_rows)
        for col in VOTE_BEHAVIOR_COLUMNS:
            if col not in out.columns:
                out[col] = ""
        out = out[VOTE_BEHAVIOR_COLUMNS]
    else:
        out = pd.DataFrame(columns=VOTE_BEHAVIOR_COLUMNS)

    out = out.drop_duplicates(
        subset=[
            "year",
            "poll_type",
            "geography_level",
            "state",
            "voter_group_type",
            "voter_group",
            "party_or_alliance",
            "source_table",
        ],
        keep="first",
    )
    out.to_csv(VOTE_BEHAVIOR_PATH, index=False)
    return out, len(table_paths), cleaned_tables


def main() -> None:
    df, tables_seen, tables_cleaned = clean_all_tables()

    print("CSDS table cleaning")
    print(f"  Extracted tables found: {tables_seen}")
    print(f"  Tables cleaned: {tables_cleaned}")
    print(f"  Vote-behavior rows: {len(df)}")
    print(f"  Saved: {VOTE_BEHAVIOR_PATH}")
    if tables_seen == 0:
        print(
            "  Run extract_csds_tables after adding PDFs to "
            "data/behaviour-analysis/post-poll/ or pre-poll/"
        )


if __name__ == "__main__":
    main()
