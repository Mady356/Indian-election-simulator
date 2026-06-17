"""
Load and apply the CSDS voter-behavior taxonomy.

Run indirectly via taxonomy-guided pipeline modules.
"""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from src.postpoll.csds_manifest import (
    BEHAVIOUR_ANALYSIS_DIR,
    EXTRACTED_DIR,
    FRONTEND_DATA_DIR,
    POSTPOLL_DIR,
    STUDIES,
    resolve_report_path,
)

TAXONOMY_DIR = POSTPOLL_DIR / "taxonomy"
CANDIDATES_DIR = POSTPOLL_DIR / "candidates"
MANUAL_DIR = POSTPOLL_DIR / "manual"
MANUAL_ENTERED_DIR = MANUAL_DIR / "entered"
MANUAL_REVIEW_PAGES_DIR = MANUAL_DIR / "review_pages"
PROCESSED_DIR = POSTPOLL_DIR / "processed"
REPORTS_DIR = POSTPOLL_DIR / "reports"

TAXONOMY_PATH = TAXONOMY_DIR / "csds_voter_behavior_taxonomy.yml"
PAGE_CANDIDATES_PATH = CANDIDATES_DIR / "csds_taxonomy_page_candidates.csv"
EXTRACTED_CANDIDATES_PATH = CANDIDATES_DIR / "csds_taxonomy_extracted_candidates.csv"
VALIDATED_CANDIDATES_PATH = CANDIDATES_DIR / "csds_taxonomy_candidates_validated.csv"
REVIEW_PATH = MANUAL_ENTERED_DIR / "csds_taxonomy_candidate_review.csv"
APPROVED_PATH = PROCESSED_DIR / "csds_vote_behavior_taxonomy_approved.csv"
CURATED_PATH = PROCESSED_DIR / "csds_vote_behavior_curated.csv"
COMPARISON_CURATED_PATH = PROCESSED_DIR / "csds_pre_post_comparison_curated.csv"

QUALITY_REPORT_PATH = REPORTS_DIR / "csds_taxonomy_candidate_quality_report.csv"
DUPLICATE_CANDIDATES_PATH = REPORTS_DIR / "csds_taxonomy_duplicate_candidates.csv"
TABLE_LABEL_INVENTORY_PATH = REPORTS_DIR / "csds_table_label_inventory.csv"
TABLE_PAGE_INDEX_PATH = REPORTS_DIR / "csds_table_page_index.csv"
TAXONOMY_REVIEW_INDEX_PATH = MANUAL_REVIEW_PAGES_DIR / "taxonomy_review_index.html"

ANALYTICAL_KEY = [
    "year",
    "poll_type",
    "geography_level",
    "state",
    "voter_group_type",
    "voter_group",
    "party_or_alliance",
]

JOIN_KEY = [
    "year",
    "geography_level",
    "state",
    "voter_group_type",
    "voter_group",
    "party_or_alliance",
]

VALID_POLL_TYPES = {"pre_poll", "post_poll"}

CSDS_CODE_RE = re.compile(r"^\s*\d{1,3}\s*:\s*")
RESPONSE_OPTION_RE = re.compile(r"^\s*\d{1,3}\s*:\s*(no|yes|don't know|dont know|did not respond|not applicable|n\.a\.)\b", re.I)

STATE_HEADER_RE = re.compile(
    r"\b(ANDHRA PRADESH|ASSAM|BIHAR|CHHATTISGARH|DELHI|GOA|GUJARAT|HARYANA|"
    r"HIMACHAL PRADESH|JAMMU AND KASHMIR|JHARKHAND|KARNATAKA|KERALA|MADHYA PRADESH|"
    r"MAHARASHTRA|MANIPUR|MEGHALAYA|NAGALAND|ODISHA|PUNJAB|RAJASTHAN|TAMIL NADU|"
    r"TELANGANA|UTTAR PRADESH|UTTARAKHAND|WEST BENGAL)\b",
    re.I,
)

VOTE_QUESTION_RE = re.compile(
    r"(which party did you vote|who did you vote|whom did you vote|"
    r"which party will you vote|would you vote for|vote for in the)",
    re.I,
)

YES_NO_HEADER_TOKENS = {
    "no",
    "yes",
    "don't know",
    "dont know",
    "did not respond",
    "not applicable",
    "n.a.",
}


def normalize_text(value: object) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    text = str(value).strip().lower()
    text = re.sub(r"\s+", " ", text)
    return text


def normalize_key(value: object) -> str:
    text = normalize_text(value)
    if text in {"", "nan", "none", "null", "na", "n/a"}:
        return ""
    return text


def strip_csds_label(label: object) -> str:
    text = str(label).strip() if label is not None else ""
    text = CSDS_CODE_RE.sub("", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


@lru_cache(maxsize=1)
def load_taxonomy(path: Path | None = None) -> dict[str, Any]:
    source = path or TAXONOMY_PATH
    with source.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def _invalidate_taxonomy_cache() -> None:
    load_taxonomy.cache_clear()
    build_party_alias_map.cache_clear()
    build_group_alias_map.cache_clear()


@lru_cache(maxsize=1)
def build_party_alias_map(taxonomy_path: str | None = None) -> dict[str, str]:
    tax = load_taxonomy(Path(taxonomy_path) if taxonomy_path else None)
    alias_map: dict[str, str] = {}
    party_spec = tax.get("party_or_alliance", {})
    for canonical in party_spec.get("canonical", []):
        alias_map[normalize_text(canonical)] = canonical
    for canonical, aliases in party_spec.get("aliases", {}).items():
        alias_map[normalize_text(canonical)] = canonical
        for alias in aliases or []:
            alias_map[normalize_text(alias)] = canonical
    return alias_map


@lru_cache(maxsize=1)
def build_group_alias_map(taxonomy_path: str | None = None) -> dict[str, tuple[str, str]]:
    tax = load_taxonomy(Path(taxonomy_path) if taxonomy_path else None)
    alias_map: dict[str, tuple[str, str]] = {}
    for group_type, spec in tax.get("voter_group_types", {}).items():
        for group in spec.get("groups", []):
            alias_map[normalize_text(group)] = (group_type, str(group))
        for group, aliases in (spec.get("aliases") or {}).items():
            alias_map[normalize_text(group)] = (group_type, str(group))
            for alias in aliases or []:
                alias_map[normalize_text(alias)] = (group_type, str(group))
        for keyword in spec.get("keywords", []):
            kw = normalize_text(keyword)
            if kw and kw not in alias_map:
                alias_map[kw] = (group_type, str(keyword))
    return alias_map


def taxonomy_group_types(taxonomy: dict[str, Any] | None = None) -> dict[str, dict[str, Any]]:
    tax = taxonomy or load_taxonomy()
    return tax.get("voter_group_types", {})


def taxonomy_skip_labels(taxonomy: dict[str, Any] | None = None) -> set[str]:
    tax = taxonomy or load_taxonomy()
    labels = {normalize_text(label) for label in tax.get("skip_labels", [])}
    labels.update(YES_NO_HEADER_TOKENS)
    return labels


def taxonomy_party_keywords(taxonomy: dict[str, Any] | None = None) -> list[str]:
    tax = taxonomy or load_taxonomy()
    return [normalize_text(k) for k in tax.get("party_or_alliance", {}).get("keywords", [])]


def taxonomy_party_canonical(taxonomy: dict[str, Any] | None = None) -> list[str]:
    tax = taxonomy or load_taxonomy()
    return tax.get("party_or_alliance", {}).get("canonical", [])


def _is_yes_no_response_label(label: object) -> bool:
    stripped = strip_csds_label(label)
    text = normalize_text(stripped)
    if text in YES_NO_HEADER_TOKENS:
        return True
    return bool(RESPONSE_OPTION_RE.match(str(label).strip()))


def match_party(label: object, taxonomy: dict[str, Any] | None = None) -> str | None:
    raw = str(label).strip() if label is not None else ""
    if not raw:
        return None
    stripped = strip_csds_label(raw)
    text = normalize_text(stripped)
    if not text or text in taxonomy_skip_labels(taxonomy):
        return None

    alias_map = build_party_alias_map()
    if text in alias_map:
        return alias_map[text]

    for alias, canonical in sorted(alias_map.items(), key=lambda item: -len(item[0])):
        if len(alias) < 3:
            continue
        if alias in text or text in alias:
            return canonical

    if re.search(r"\bbjp\b|\bbharatiya janata\b", text):
        return "BJP"
    if re.search(r"\bcongress\b|\binc\b", text) and "yuvajana" not in text:
        return "INC"
    if re.search(r"\bnda\b", text):
        return "NDA"
    if re.search(r"\bindia\b", text) and "indian national congress" not in text:
        return "INDIA"
    if re.search(r"\bupa\b", text):
        return "UPA"
    if re.search(r"\bother", text) or "independent" in text or "nota" in text:
        return "Others"
    if re.search(r"\bregional\b", text):
        return "Regional"
    if re.search(r"\bbsp\b|bahujan samaj", text):
        return "BSP"
    if re.search(r"\bsamajwadi\b|\bsp\b", text) and "party" in text:
        return "SP"

    canonical = taxonomy_party_canonical(taxonomy)
    for party in canonical:
        if normalize_text(party) in text:
            return party
    return None


def _is_age_group_label(text: str, stripped: str) -> bool:
    if re.fullmatch(r"\d{1,2}-\d{1,2}", stripped):
        return True
    if re.fullmatch(r"\d{2}\+", stripped):
        return True
    if stripped.lower() in {"youth", "young", "elderly", "elder"}:
        return True
    if re.fullmatch(r"\d{1,2}", stripped) and int(stripped) >= 18:
        return True
    return False


def match_voter_group(
    label: object,
    preferred_type: str | None = None,
    taxonomy: dict[str, Any] | None = None,
) -> tuple[str, str] | None:
    raw = str(label).strip() if label is not None else ""
    if not raw:
        return None
    text = normalize_text(raw)
    if not text or text in taxonomy_skip_labels(taxonomy):
        return None
    if text.startswith("col_"):
        return None
    if _is_yes_no_response_label(raw):
        return None

    stripped = strip_csds_label(raw)
    stripped_norm = normalize_text(stripped)
    if not stripped_norm or stripped_norm in taxonomy_skip_labels(taxonomy):
        return None

    alias_map = build_group_alias_map()
    if stripped_norm in alias_map:
        group_type, group = alias_map[stripped_norm]
        if group_type == "age" and not _is_age_group_label(stripped_norm, stripped):
            pass
        else:
            return group_type, group

    for alias, (group_type, group) in sorted(alias_map.items(), key=lambda item: -len(item[0])):
        if group_type == "age" and not _is_age_group_label(alias, stripped):
            continue
        if len(alias) <= 3:
            if not re.search(rf"\b{re.escape(alias)}\b", stripped_norm):
                continue
        elif len(alias) < 3:
            continue
        if alias == stripped_norm or alias in stripped_norm or stripped_norm in alias:
            return group_type, group

    group_types = taxonomy_group_types(taxonomy)
    search_order = [preferred_type] if preferred_type else []
    search_order.extend([gt for gt in group_types if gt != preferred_type])

    for group_type in search_order:
        if not group_type or group_type not in group_types:
            continue
        spec = group_types[group_type]
        for group in spec.get("groups", []):
            group_norm = normalize_text(group)
            if group_type == "age" and not _is_age_group_label(group_norm, stripped):
                continue
            if group_norm == stripped_norm or group_norm in stripped_norm or stripped_norm in group_norm:
                return group_type, str(group)

    return None


def score_page_keywords(
    page_text: str,
    taxonomy: dict[str, Any] | None = None,
) -> tuple[int, list[str], list[str]]:
    tax = taxonomy or load_taxonomy()
    text = normalize_text(page_text)
    matched_types: list[str] = []
    matched_keywords: list[str] = []
    score = 0

    for group_type, spec in tax.get("voter_group_types", {}).items():
        for keyword in spec.get("keywords", []):
            kw = normalize_text(keyword)
            if kw and kw in text:
                score += 2
                matched_keywords.append(kw)
                if group_type not in matched_types:
                    matched_types.append(group_type)

    for keyword in taxonomy_party_keywords(tax):
        if keyword in text:
            score += 3
            matched_keywords.append(keyword)

    return score, matched_types, sorted(set(matched_keywords))


def page_context_signals(
    page_text: str,
    table_context: str = "",
    taxonomy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    tax = taxonomy or load_taxonomy()
    combined = f"{page_text}\n{table_context}"
    text = normalize_text(combined)
    positive = [normalize_text(k) for k in tax.get("vote_context_positive", [])]
    negative = [normalize_text(k) for k in tax.get("vote_context_negative", [])]

    pos_hits = [kw for kw in positive if kw and kw in text]
    neg_hits = [kw for kw in negative if kw and kw in text]
    vote_question = bool(VOTE_QUESTION_RE.search(combined))

    return {
        "positive_hits": pos_hits,
        "negative_hits": neg_hits,
        "vote_question": vote_question,
        "positive_score": len(pos_hits) + (2 if vote_question else 0),
        "negative_score": len(neg_hits),
    }


def classify_table_type(
    page_text: str,
    poll_type: str,
    taxonomy: dict[str, Any] | None = None,
    table_context: str = "",
) -> str:
    tax = taxonomy or load_taxonomy()
    text = normalize_text(f"{page_text}\n{table_context}")
    table_keywords = tax.get("table_type_keywords", {})

    scores: dict[str, int] = {}
    for table_type, keywords in table_keywords.items():
        scores[table_type] = sum(1 for kw in keywords if normalize_text(kw) in text)

    if poll_type == "pre_poll" and scores.get("pre_poll_vote_intention_table", 0) > 0:
        scores["pre_poll_vote_intention_table"] += 2
    if poll_type == "post_poll" and scores.get("post_poll_vote_choice_table", 0) > 0:
        scores["post_poll_vote_choice_table"] += 2

    signals = page_context_signals(page_text, table_context, tax)
    if signals["negative_score"] >= 2 and signals["positive_score"] == 0:
        if scores.get("methodology_table", 0) > 0:
            return "methodology_table"
        if scores.get("questionnaire_table", 0) > 0:
            return "questionnaire_table"

    if not scores or max(scores.values()) == 0:
        if any(k in text for k in ("questionnaire", "codebook", "item number")):
            return "questionnaire_table"
        if any(k in text for k in ("methodology", "sample size", "fieldwork")):
            return "methodology_table"
        return "irrelevant"

    best = max(scores, key=scores.get)
    if best in {"methodology_table", "questionnaire_table"} and scores.get("voter_group_party_table", 0) >= 2:
        return "voter_group_party_table"
    return best


def recommended_action(score: int, table_type: str) -> str:
    if table_type in {"methodology_table", "questionnaire_table", "irrelevant"}:
        return "ignore"
    if table_type in {
        "voter_group_party_table",
        "pre_poll_vote_intention_table",
        "post_poll_vote_choice_table",
        "issue_preference_table",
    }:
        if score >= 8:
            return "auto_extract"
        if score >= 4:
            return "review"
    return "ignore"


def parse_vote_share(value: object) -> float | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text = str(value).strip()
    if not text or text.lower() in {"-", "—", "na", "n/a", "*", "."}:
        return None

    if re.search(r"\bn\s*=\s*\d+", text, re.I):
        return None

    text = re.sub(r"\(.*?\)", "", text)
    text = text.replace("%", "").replace(",", "").strip()
    text = re.sub(r"\s+per\s+cent\b", "", text, flags=re.I)
    text = re.sub(r"\s+pct\b", "", text, flags=re.I)
    if not text:
        return None
    try:
        num = float(text)
    except ValueError:
        match = re.search(r"(\d+(?:\.\d+)?)", text)
        if not match:
            return None
        num = float(match.group(1))

    if 0 <= num <= 1:
        num *= 100
    if 0 <= num <= 100:
        return round(num, 3)
    return None


def is_sample_size_column(header: object) -> bool:
    text = normalize_text(header)
    return text in {"n", "n=", "sample", "count", "freq", "frequency", "no", "no."}


def is_percent_column(header: object) -> bool:
    text = normalize_text(header)
    return "%" in text or "percent" in text or "share" in text or text in {"(%)", "pct", "valid (%)"}


def is_likely_percent_value_column(series: pd.Series) -> bool:
    parsed = series.map(parse_vote_share)
    valid = parsed.notna().sum()
    return valid >= max(2, len(series) // 4)


def infer_geography_from_text(page_text: str) -> tuple[str, str]:
    match = STATE_HEADER_RE.search(page_text or "")
    if not match:
        return "national", ""
    state = match.group(1).title()
    replacements = {
        "Jammu And Kashmir": "Jammu and Kashmir",
        "Andhra Pradesh": "Andhra Pradesh",
    }
    return "state", replacements.get(state, state)


def infer_voter_group_from_context(
    page_text: str,
    preferred_types: list[str] | None = None,
    taxonomy: dict[str, Any] | None = None,
    *,
    strict: bool = True,
) -> tuple[str, str] | None:
    signals = page_context_signals(page_text, taxonomy=taxonomy)
    if signals["vote_question"]:
        return "electorate", "all voters"

    if strict:
        return None

    preferred = preferred_types or []
    header = (page_text or "")[:600]
    explicit_patterns = [
        (r"\bamong\s+(sc|st|obc)\b", "caste"),
        (r"\bamong\s+(hindus?|muslims?|christians?|sikhs?)\b", "religion"),
        (r"\bamong\s+(men|women|males?|females?)\b", "gender"),
        (r"\bamong\s+(rural|urban)\b", "rural_urban"),
    ]
    for pattern, group_type in explicit_patterns:
        match = re.search(pattern, header, re.I)
        if match:
            token = match.group(1)
            group_match = match_voter_group(token, group_type, taxonomy)
            if group_match:
                return group_match

    for line in header.splitlines()[:8]:
        for preferred_type in preferred:
            match = match_voter_group(line, preferred_type, taxonomy)
            if match and match[0] != "electorate":
                return match
    return None


def score_extraction_confidence(
    *,
    party_count: int,
    group_count: int,
    vote_share: float | None,
    page_text: str,
    table_type: str,
    layout: str,
    has_explicit_group: bool,
    context_signals: dict[str, Any] | None = None,
) -> str:
    signals = context_signals or page_context_signals(page_text)
    negative = signals["negative_score"] >= 2
    positive = signals["positive_score"] >= 1 or signals["vote_question"]

    if table_type in {"questionnaire_table", "methodology_table"}:
        return "low"
    if negative and not positive:
        return "low"
    if vote_share is None:
        return "low"

    if (
        party_count >= 2
        and group_count >= 2
        and positive
        and not negative
        and table_type in {
            "voter_group_party_table",
            "pre_poll_vote_intention_table",
            "post_poll_vote_choice_table",
        }
    ):
        return "high"

    if (
        party_count >= 2
        and positive
        and table_type in {
            "voter_group_party_table",
            "pre_poll_vote_intention_table",
            "post_poll_vote_choice_table",
        }
        and layout in {"party_marginal_percent", "layout_a_rows_groups", "layout_b_rows_parties"}
    ):
        if has_explicit_group or group_count >= 1:
            return "high" if not negative else "medium"
        return "medium"

    if party_count >= 1 and (positive or has_explicit_group):
        return "medium"
    return "low"


def detect_likely_layout(
    df: pd.DataFrame,
    preferred_type: str | None = None,
) -> str:
    if df.empty:
        return "unknown"

    col_labels = [str(c) for c in df.columns]
    row_labels = [str(v) for v in df.iloc[:, 0].tolist()]
    party_cols = sum(1 for label in col_labels if match_party(label))
    party_rows = sum(1 for label in row_labels if match_party(label))
    group_cols = sum(1 for label in col_labels if match_voter_group(label, preferred_type))
    group_rows = sum(1 for label in row_labels if match_voter_group(label, preferred_type))

    if party_cols >= 2 and group_rows >= 2:
        return "groups_as_rows_parties_as_columns"
    if party_rows >= 2 and group_cols >= 2:
        return "parties_as_rows_groups_as_columns"

  # party marginal: coded party labels in rows, percent column
    label_col = _best_label_column(df)
    if label_col is not None:
        labels = df[label_col].astype(str).tolist()
        party_hits = sum(1 for label in labels if match_party(label))
        pct_col = _best_percent_column(df, exclude={label_col})
        if party_hits >= 2 and pct_col is not None:
            return "party_marginal_percent"

    if party_cols >= 1 and group_rows >= 1:
        return "groups_as_rows_parties_as_columns"
    if party_rows >= 1 and group_cols >= 1:
        return "parties_as_rows_groups_as_columns"

    text_blob = " ".join(col_labels + row_labels).lower()
    if any(token in text_blob for token in ("questionnaire", "codebook", "item number")):
        return "methodology_table" if "methodology" in text_blob else "questionnaire_grid"
    if "methodology" in text_blob or "sample size" in text_blob:
        return "methodology_table"
    if "issue" in text_blob and party_cols >= 1:
        return "issue_rows_party_columns"
    return "unknown"


def _best_label_column(df: pd.DataFrame) -> str | None:
    best_col = None
    best_score = 0
    for idx, col in enumerate(df.columns):
        col_name = str(col)
        if is_percent_column(col_name) or is_sample_size_column(col_name):
            continue
        series = df.iloc[:, idx]
        labels = series.astype(str).tolist()
        party_hits = sum(1 for label in labels if match_party(label))
        group_hits = sum(1 for label in labels if match_voter_group(label))
        score = party_hits * 2 + group_hits
        if score > best_score:
            best_score = score
            best_col = col_name
    return best_col if best_score >= 2 else None


def _best_percent_column(df: pd.DataFrame, exclude: set[str] | None = None) -> str | None:
    exclude = exclude or set()
    for col in df.columns:
        if str(col) in exclude:
            continue
        if is_percent_column(col):
            return str(col)
    for col in df.columns:
        if str(col) in exclude or is_sample_size_column(col):
            continue
        if is_likely_percent_value_column(df[col]):
            return str(col)
    return None


def flatten_multiline_header(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or len(df) < 2:
        return df

    work = df.copy()
    work.columns = [str(c).strip() for c in work.columns]
    headerish = 0
    for _, row in work.head(3).iterrows():
        values = [normalize_text(v) for v in row.tolist()]
        if any(v in {"valid", "(%)"} for v in values):
            headerish += 1
        if sum(1 for v in values if match_party(v)) >= 2:
            headerish += 1
    if headerish == 0:
        return work

    data_start = 0
    for idx, row in work.iterrows():
        values = [str(v).strip() for v in row.tolist()]
        party_hits = sum(1 for v in values if match_party(v))
        group_hits = sum(1 for v in values if match_voter_group(v))
        if party_hits >= 2 or group_hits >= 2:
            data_start = idx
            break
        data_start = idx + 1

    if data_start <= 0:
        return work
    return work.iloc[data_start:].reset_index(drop=True)


def parse_extracted_table_filename(path: Path) -> tuple[int, str, int] | None:
    match = re.match(r"(\d{4})_(pre_poll|post_poll)_table_(\d+)\.csv$", path.name)
    if not match:
        return None
    return int(match.group(1)), match.group(2), int(match.group(3))


def build_table_page_index(force: bool = False) -> pd.DataFrame:
    if TABLE_PAGE_INDEX_PATH.exists() and not force:
        return pd.read_csv(TABLE_PAGE_INDEX_PATH)

    rows: list[dict[str, object]] = []
    try:
        import pdfplumber
    except ImportError as exc:
        raise RuntimeError("pdfplumber is required") from exc

    for study in STUDIES:
        report_path = resolve_report_path(study)
        if not report_path.exists():
            continue
        year = int(study["year"])
        poll_type = str(study["poll_type"])
        prefix = f"{year}_{poll_type}"
        table_count = 0
        with pdfplumber.open(report_path) as pdf:
            for page_idx, page in enumerate(pdf.pages, start=1):
                try:
                    tables = page.extract_tables() or []
                except Exception:
                    tables = []
                for _ in tables:
                    table_count += 1
                    rows.append(
                        {
                            "year": year,
                            "poll_type": poll_type,
                            "source_file": str(report_path.relative_to(BEHAVIOUR_ANALYSIS_DIR)),
                            "table_index": table_count,
                            "table_file": f"{prefix}_table_{table_count:03d}.csv",
                            "source_page": page_idx,
                        }
                    )

    df = pd.DataFrame(rows)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(TABLE_PAGE_INDEX_PATH, index=False)
    return df


def load_page_text(year: int, poll_type: str) -> str:
    text_path = EXTRACTED_DIR / f"{year}_{poll_type}_text.txt"
    if text_path.exists():
        return text_path.read_text(encoding="utf-8", errors="ignore")
    return ""


def page_text_for_number(full_text: str, page_num: int) -> str:
    if not full_text or page_num < 1:
        return ""
    chunks = re.split(r"=== PAGE (\d+) ===", full_text)
    for idx in range(1, len(chunks), 2):
        if int(chunks[idx]) == page_num:
            return chunks[idx + 1] if idx + 1 < len(chunks) else ""
    return ""


def iter_study_reports() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for study in STUDIES:
        report_path = resolve_report_path(study)
        if report_path.exists():
            rows.append(
                {
                    "year": int(study["year"]),
                    "poll_type": str(study["poll_type"]),
                    "source": str(study["source"]),
                    "source_file": str(report_path.relative_to(BEHAVIOUR_ANALYSIS_DIR)),
                    "report_path": report_path,
                }
            )
    return rows


def ensure_taxonomy_dirs() -> None:
    for directory in (
        TAXONOMY_DIR,
        CANDIDATES_DIR,
        MANUAL_DIR,
        MANUAL_ENTERED_DIR,
        MANUAL_REVIEW_PAGES_DIR,
        PROCESSED_DIR,
        REPORTS_DIR,
        FRONTEND_DATA_DIR,
    ):
        directory.mkdir(parents=True, exist_ok=True)
