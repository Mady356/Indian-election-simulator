"""
Normalization and fuzzy matching helpers for delimitation AC joins.

Table A stores assembly names with extent text; Table B stores short names.
This module extracts comparable keys and applies layered matching.
"""

from __future__ import annotations

import re
from difflib import SequenceMatcher
from typing import Any

import numpy as np
import pandas as pd

try:
    from rapidfuzz import fuzz
    from rapidfuzz.process import extract

    _HAS_RAPIDFUZZ = True
except ImportError:
    _HAS_RAPIDFUZZ = False

FUZZY_THRESHOLD = 92

# Map alternate spellings to a canonical normalized token.
SPELLING_ALIASES: dict[str, str] = {
    "ODISHA": "ORISSA",
    "ORISSA": "ORISSA",
    "GUWAHATI": "GAUHATI",
    "GAUHATI": "GAUHATI",
    "NARSAPUR": "NARSAPURAM",
    "NARSAPURAM": "NARSAPURAM",
    "RAJAHMUNDRY": "RAJAHMAHENDRAVARAM",
    "RAJAHMAHENDRAVARAM": "RAJAHMAHENDRAVARAM",
    "CUDDAPAH": "YSR KADAPA",
    "KADAPA": "YSR KADAPA",
    "BENGALURU": "BANGALORE",
    "BANGALORE": "BANGALORE",
    "MUMBAI": "MUMBAI",
    "BARODA": "VADODARA",
    "VADODARA": "VADODARA",
    "POONCH": "POONCH",
    "MUZAFFARABAD": "MUZAFFARABAD",
}

EXTENT_MARKER_RE = re.compile(
    r"\s+(?:"
    r"CD Blocks?|C\.D\. Blocks?|Mandals?|Gram Panchayats?|Wards?|DMC|"
    r"Tehsils?|Taluks?|Blocks?|Nagar Parishad|Nagar Palika|Nagar|Including|"
    r"Comprising|Revenue|Circle|Town|Village|Area|Entire|Part of|P\.S\.|M\.C\.|"
    r"M\.P\.|District|Assembly Constituency"
    r")\b",
    re.I,
)

RESERVATION_RE = re.compile(r"\((SC|ST)\)", re.I)


def _apply_spelling_aliases(text: str) -> str:
    tokens = text.split()
    out: list[str] = []
    for token in tokens:
        out.append(SPELLING_ALIASES.get(token, token))
    # Also replace multi-token aliases
    joined = " ".join(out)
    for src, dst in SPELLING_ALIASES.items():
        if " " in src:
            joined = joined.replace(src, dst)
    return joined


def normalize_assembly_name(value: object) -> str:
    """Normalize an assembly constituency name for matching."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    text = str(value).strip().upper()
    text = RESERVATION_RE.sub(" ", text)
    text = text.replace("&", " AND ")
    text = re.sub(r"[–—\-~]", " ", text)
    text = text.replace(".", " ")
    text = re.sub(r"[^A-Z0-9]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    text = _apply_spelling_aliases(text)
    return re.sub(r"\s+", " ", text).strip()


def normalize_state(value: object) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    text = str(value).strip().upper()
    text = re.sub(r"[^A-Z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def extract_ac_short_name(value: object) -> str:
    """
    Extract the constituency label from Table A text.

    Table A often stores names like:
      'Valmiki Nagar CD Blocks Piprasi...'
      'Chennur (SC) Jaipur, Chennur, Kotapalli...'
    """
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    text = str(value).strip()
    text = RESERVATION_RE.sub(" ", text)
    text = re.sub(r"\s+", " ", text)

    marker = EXTENT_MARKER_RE.search(text)
    if marker:
        text = text[: marker.start()]

    # Drop trailing comma-separated extent fragments.
    if "," in text:
        head = text.split(",")[0].strip()
        if head and len(head) <= 60:
            text = head

    words = text.split()
    if not words:
        return ""

    # Keep leading capitalized words (e.g. Valmiki Nagar, Moradabad Rural).
    name_words = [words[0]]
    keepers = {
        "AND",
        "CUM",
        "PUR",
        "NAGAR",
        "RURAL",
        "URBAN",
        "NORTH",
        "SOUTH",
        "EAST",
        "WEST",
        "CITY",
        "CANTONMENT",
        "SADAR",
    }
    for word in words[1:6]:
        upper = word.upper()
        if upper in keepers or (word[0].isupper() and not word.islower()):
            name_words.append(word)
        else:
            break

    short = " ".join(name_words).strip(" .,-")
    return re.sub(r"\s+", " ", short)


def fuzzy_score(query: str, choice: str) -> float:
    if not query or not choice:
        return 0.0
    if _HAS_RAPIDFUZZ:
        return float(fuzz.ratio(query, choice))
    return SequenceMatcher(None, query, choice).ratio() * 100.0


def best_fuzzy_match(
    query: str,
    choices: list[str],
    threshold: float = FUZZY_THRESHOLD,
) -> tuple[str | None, float]:
    if not query or not choices:
        return None, 0.0

    if _HAS_RAPIDFUZZ:
        results = extract(query, choices, scorer=fuzz.ratio, limit=2)
        if not results:
            return None, 0.0
        best_name, best_score, _ = results[0]
        if best_score < threshold:
            return None, float(best_score)
        if len(results) > 1 and results[1][1] >= threshold:
            return None, float(best_score)
        return best_name, float(best_score)

    scored = sorted(
        ((c, fuzzy_score(query, c)) for c in choices),
        key=lambda item: item[1],
        reverse=True,
    )
    if not scored or scored[0][1] < threshold:
        return None, scored[0][1] if scored else 0.0
    if len(scored) > 1 and scored[1][1] >= threshold:
        return None, scored[0][1]
    return scored[0][0], scored[0][1]


def _word_boundary_match(name: str, text: str) -> bool:
    if not name or not text:
        return False
    if len(name) < 3:
        return False
    return re.search(rf"\b{re.escape(name)}\b", text, re.I) is not None


def _starts_with_name(full_text: str, short_name: str) -> bool:
    if not full_text or not short_name:
        return False
    cleaned = RESERVATION_RE.sub(" ", str(full_text)).strip().upper()
    short = str(short_name).strip().upper()
    if cleaned.startswith(short):
        return True
    return cleaned.split()[: len(short.split())] == short.split()


def prepare_ac_table(ac_dist: pd.DataFrame) -> pd.DataFrame:
    ac = ac_dist.copy()
    ac["assembly_no"] = pd.to_numeric(ac["assembly_no"], errors="coerce")
    ac["state_key"] = ac["state"].map(normalize_state)
    ac["assembly_constituency_normalized"] = ac["assembly_constituency"].map(
        normalize_assembly_name
    )
    ac["ac_short_name"] = ac["assembly_constituency"].map(extract_ac_short_name)
    ac["ac_short_name_normalized"] = ac["ac_short_name"].map(normalize_assembly_name)
    ac["district"] = ac["district"].fillna("").astype(str).str.strip()
    # Delhi Table A rows omit district; treat as Delhi for join purposes.
    ac.loc[(ac["state_key"] == "DELHI") & ac["district"].eq(""), "district"] = "Delhi"
    return ac


def prepare_ls_table(ls_ac: pd.DataFrame) -> pd.DataFrame:
    ls = ls_ac.copy()
    ls["assembly_no"] = pd.to_numeric(ls["assembly_no"], errors="coerce")
    ls["state_key"] = ls["state"].map(normalize_state)
    ls["assembly_constituency_normalized"] = ls["assembly_constituency"].map(
        normalize_assembly_name
    )
    ls["ac_short_name"] = ls["assembly_constituency"].map(extract_ac_short_name)
    ls["ac_short_name_normalized"] = ls["ac_short_name"].map(normalize_assembly_name)
    return ls


def build_ac_lookups(ac: pd.DataFrame) -> dict[str, dict[str, Any]]:
    lookups: dict[str, dict[str, Any]] = {}
    for state_key, grp in ac.groupby("state_key"):
        scored = grp.copy()
        scored["_extent_len"] = scored["raw_extent_text"].astype(str).str.len()
        by_no = (
            scored.dropna(subset=["assembly_no"])
            .sort_values("_extent_len", ascending=False)
            .drop_duplicates(subset=["assembly_no"], keep="first")
            .set_index("assembly_no")
        )
        by_short = (
            scored.sort_values("_extent_len", ascending=False)
            .drop_duplicates(subset=["ac_short_name_normalized"], keep="first")
        )
        short_map = {
            row.ac_short_name_normalized: row
            for row in by_short.itertuples()
            if row.ac_short_name_normalized
        }
        lookups[state_key] = {
            "rows": grp,
            "by_no": by_no,
            "short_map": short_map,
            "short_choices": list(short_map.keys()),
        }
    return lookups


def diagnose_row(row: pd.Series, lookup: dict[str, Any] | None) -> dict[str, object]:
    """Return diagnostic fields for one LS-AC row."""
    result: dict[str, object] = {
        "match_by_number": False,
        "match_by_exact_name": False,
        "match_by_fuzzy_name": False,
        "fuzzy_score": pd.NA,
        "fuzzy_candidate": "",
        "number_lookup_found": False,
        "exact_name_candidates": 0,
        "failure_reason": "",
    }
    if lookup is None:
        result["failure_reason"] = "no_assembly_rows_for_state_in_table_a"
        return result

    ac_no = row.get("assembly_no")
    if pd.notna(ac_no):
        ac_no_int = int(ac_no)
        if ac_no_int in lookup["by_no"].index:
            result["number_lookup_found"] = True
            ac_row = lookup["by_no"].loc[ac_no_int]
            if isinstance(ac_row, pd.DataFrame):
                ac_row = ac_row.iloc[-1]
            if str(ac_row.get("district", "")).strip():
                result["match_by_number"] = True
                return result
            result["failure_reason"] = "assembly_no_found_but_district_empty"
            return result
        result["failure_reason"] = "assembly_no_missing_in_table_a"

    short_key = str(row.get("ac_short_name_normalized", "")).strip()
    if not short_key:
        result["failure_reason"] = "missing_assembly_no_and_name"
        return result

    if short_key in lookup["short_map"]:
        result["exact_name_candidates"] = 1
        result["match_by_exact_name"] = True
        return result

    exact_hits = [
        key for key in lookup["short_choices"] if key == short_key
    ]
    result["exact_name_candidates"] = len(exact_hits)
    if exact_hits:
        result["match_by_exact_name"] = True
        return result

    candidate, score = best_fuzzy_match(short_key, lookup["short_choices"])
    result["fuzzy_score"] = score
    result["fuzzy_candidate"] = candidate or ""
    if candidate:
        result["match_by_fuzzy_name"] = True
        return result

    if result["failure_reason"] == "":
        result["failure_reason"] = "no_exact_or_fuzzy_name_match"
    return result


def match_ls_row(row: pd.Series, lookup: dict[str, Any] | None) -> dict[str, object]:
    """Match one LS-AC row to a district using layered strategies."""
    empty: dict[str, object] = {
        "district": "",
        "matched_assembly_no": pd.NA,
        "matched_assembly_constituency": "",
        "match_method": "unmatched",
        "mapping_confidence": "low",
        "match_detail": "",
    }
    if lookup is None:
        empty["match_detail"] = "no_assembly_rows_for_state_in_table_a"
        return empty

    ac_no = row.get("assembly_no")

    # 1) state + assembly_no
    if pd.notna(ac_no):
        ac_no_int = int(ac_no)
        if ac_no_int in lookup["by_no"].index:
            ac_row = lookup["by_no"].loc[ac_no_int]
            if isinstance(ac_row, pd.DataFrame):
                ac_row = ac_row.iloc[-1]
            district = str(ac_row.get("district", "")).strip()
            if district:
                return {
                    "district": district,
                    "matched_assembly_no": ac_no_int,
                    "matched_assembly_constituency": ac_row.get(
                        "assembly_constituency", ""
                    ),
                    "match_method": "by_number",
                    "mapping_confidence": "high",
                    "match_detail": "",
                }

    short_key = str(row.get("ac_short_name_normalized", "")).strip()
    ls_name = str(row.get("assembly_constituency", "")).strip()
    grp = lookup["rows"]

    # 2) exact normalized short name
    if short_key and short_key in lookup["short_map"]:
        ac_row = lookup["short_map"][short_key]
        district = str(ac_row.district).strip()
        if district:
            return {
                "district": district,
                "matched_assembly_no": ac_row.assembly_no,
                "matched_assembly_constituency": ac_row.assembly_constituency,
                "match_method": "by_exact_name",
                "mapping_confidence": "medium",
                "match_detail": "",
            }

    # 3) substring in full Table A text (unique)
    if ls_name:
        hits = grp[
            grp.apply(
                lambda ac_row: _word_boundary_match(ls_name, ac_row.assembly_constituency),
                axis=1,
            )
            & grp["district"].astype(str).str.strip().ne("")
        ]
        if len(hits) == 1:
            ac_row = hits.iloc[0]
            return {
                "district": ac_row.district,
                "matched_assembly_no": ac_row.assembly_no,
                "matched_assembly_constituency": ac_row.assembly_constituency,
                "match_method": "by_substring",
                "mapping_confidence": "medium",
                "match_detail": "unique substring in Table A text",
            }

    # 4) starts-with on Table A text (unique)
    if ls_name:
        hits = grp[
            grp.apply(
                lambda ac_row: _starts_with_name(ac_row.assembly_constituency, ls_name),
                axis=1,
            )
            & grp["district"].astype(str).str.strip().ne("")
        ]
        if len(hits) == 1:
            ac_row = hits.iloc[0]
            return {
                "district": ac_row.district,
                "matched_assembly_no": ac_row.assembly_no,
                "matched_assembly_constituency": ac_row.assembly_constituency,
                "match_method": "by_prefix",
                "mapping_confidence": "medium",
                "match_detail": "unique prefix in Table A text",
            }

    # 5) fuzzy normalized short name (unique best)
    if short_key:
        candidate, score = best_fuzzy_match(short_key, lookup["short_choices"])
        if candidate:
            ac_row = lookup["short_map"][candidate]
            district = str(ac_row.district).strip()
            if district:
                return {
                    "district": district,
                    "matched_assembly_no": ac_row.assembly_no,
                    "matched_assembly_constituency": ac_row.assembly_constituency,
                    "match_method": "by_fuzzy_name",
                    "mapping_confidence": "medium",
                    "match_detail": f"fuzzy_score={score:.1f}",
                }

    if pd.notna(ac_no) and int(ac_no) in lookup["by_no"].index:
        empty["match_detail"] = "assembly_no_found_but_district_empty"
    elif pd.notna(ac_no):
        empty["match_detail"] = "assembly_no_missing_in_table_a"
    elif not short_key:
        empty["match_detail"] = "missing_assembly_no_and_name"
    else:
        empty["match_detail"] = "no_exact_or_fuzzy_name_match"
    return empty


def join_ls_to_district(ls_ac: pd.DataFrame, ac_dist: pd.DataFrame) -> pd.DataFrame:
    """Join LS-AC rows to districts using layered matching."""
    ac = prepare_ac_table(ac_dist)
    ls = prepare_ls_table(ls_ac)
    lookups = build_ac_lookups(ac)

    match_rows: list[dict[str, object]] = []
    for row in ls.itertuples(index=False):
        row_series = pd.Series(row._asdict())
        state_key = row_series.get("state_key", "")
        matched = match_ls_row(row_series, lookups.get(str(state_key)))
        match_rows.append(matched)

    match_df = pd.DataFrame(match_rows)
    out = pd.concat([ls.reset_index(drop=True), match_df], axis=1)
    out["source"] = "delimitation_order_2008"
    out["notes"] = np_where_empty_district(out)
    return out


def np_where_empty_district(df: pd.DataFrame) -> pd.Series:
    default = "Assembly segment could not be matched to Table A district"
    detail = df.get("match_detail", pd.Series([""] * len(df))).astype(str)
    return np.where(
        df["district"].astype(str).str.strip().eq(""),
        np.where(detail.str.strip().eq(""), default, detail),
        "",
    )
