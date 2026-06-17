"""
Validate taxonomy-guided CSDS candidate rows.

Run:
    python -m src.postpoll.validate_taxonomy_candidates
"""

from __future__ import annotations

import pandas as pd

from src.postpoll.csds_taxonomy import (
    ANALYTICAL_KEY,
    DUPLICATE_CANDIDATES_PATH,
    EXTRACTED_CANDIDATES_PATH,
    QUALITY_REPORT_PATH,
    VALIDATED_CANDIDATES_PATH,
    VALID_POLL_TYPES,
    ensure_taxonomy_dirs,
    normalize_key,
    parse_vote_share,
)


def _validation_flags(row: pd.Series) -> list[str]:
    flags: list[str] = []
    vote_share = parse_vote_share(row.get("vote_share"))
    if vote_share is None:
        flags.append("missing_or_invalid_vote_share")
    elif vote_share < 0 or vote_share > 100:
        flags.append("invalid_vote_share_range")

    if not normalize_key(row.get("voter_group")):
        flags.append("blank_voter_group")
    if not normalize_key(row.get("voter_group_type")):
        flags.append("blank_voter_group_type")
    if not normalize_key(row.get("party_or_alliance")):
        flags.append("blank_party_or_alliance")
    if not normalize_key(row.get("source_file")):
        flags.append("missing_source_file")
    if pd.isna(row.get("source_page")) or str(row.get("source_page")).strip() == "":
        flags.append("missing_source_page")
    if not normalize_key(row.get("evidence_text")):
        flags.append("missing_evidence_text")

    year = row.get("year")
    try:
        if pd.isna(year) or int(year) not in (2019, 2024):
            flags.append("invalid_year")
    except (TypeError, ValueError):
        flags.append("invalid_year")

    if normalize_key(row.get("poll_type")) not in VALID_POLL_TYPES:
        flags.append("invalid_poll_type")

    if row.get("candidate_status") == "rejected_by_validator":
        flags.append("rejected_by_validator")

    return flags


def build_duplicate_report(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()

    keyed = df.copy()
    for col in ANALYTICAL_KEY[1:]:
        keyed[f"{col}_norm"] = keyed[col].map(normalize_key)
    norm_cols = ["year"] + [f"{col}_norm" for col in ANALYTICAL_KEY[1:]]

    rows: list[dict[str, object]] = []
    for key_vals, group in keyed.groupby(norm_cols, dropna=False):
        if len(group) < 2:
            continue
        shares = sorted({parse_vote_share(v) for v in group["vote_share"] if parse_vote_share(v) is not None})
        row = dict(zip(ANALYTICAL_KEY, key_vals))
        row.update(
            {
                "duplicate_count": len(group),
                "vote_shares_found": ";".join(str(s) for s in shares),
                "candidate_ids": ";".join(group["candidate_id"].astype(str).tolist()),
                "source_files": ";".join(sorted(set(group["source_file"].astype(str)))),
                "duplicate_conflict": len(shares) > 1,
                "recommendation": "manual_review_conflict" if len(shares) > 1 else "keep_one",
            }
        )
        rows.append(row)

    return pd.DataFrame(rows)


def validate_candidates() -> tuple[pd.DataFrame, pd.DataFrame, dict[str, int]]:
    ensure_taxonomy_dirs()
    if not EXTRACTED_CANDIDATES_PATH.exists():
        raise FileNotFoundError(
            f"Missing {EXTRACTED_CANDIDATES_PATH}. Run taxonomy_guided_extract first."
        )

    raw = pd.read_csv(EXTRACTED_CANDIDATES_PATH)
    duplicate_report = build_duplicate_report(raw)

    conflict_ids: set[str] = set()
    duplicate_key_ids: set[str] = set()
    if not duplicate_report.empty:
        for _, dup in duplicate_report.iterrows():
            ids = str(dup.get("candidate_ids", "")).split(";")
            duplicate_key_ids.update(ids)
            if dup.get("duplicate_conflict"):
                conflict_ids.update(ids)

    validated_rows: list[dict[str, object]] = []
    for _, row in raw.iterrows():
        flags = _validation_flags(row)
        cid = str(row["candidate_id"])
        duplicate_key = cid in duplicate_key_ids
        duplicate_conflict = cid in conflict_ids
        is_valid = len(flags) == 0 and not duplicate_conflict

        status = row.get("candidate_status", "needs_review")
        if flags:
            status = "rejected_by_validator"
        elif duplicate_conflict:
            status = "needs_review"

        validated_rows.append(
            {
                "candidate_id": row["candidate_id"],
                "year": row["year"],
                "poll_type": row["poll_type"],
                "source": row["source"],
                "source_file": row["source_file"],
                "source_page": row["source_page"],
                "source_table_index": row.get("source_table_index"),
                "geography_level": row.get("geography_level", "national"),
                "state": row.get("state", ""),
                "voter_group_type": row["voter_group_type"],
                "voter_group": row["voter_group"],
                "party_or_alliance": row["party_or_alliance"],
                "vote_share": parse_vote_share(row.get("vote_share")),
                "extraction_confidence": row.get("extraction_confidence"),
                "evidence_text": row.get("evidence_text"),
                "candidate_status": status,
                "validation_flags": "|".join(flags),
                "is_valid": is_valid,
                "duplicate_key": duplicate_key,
                "duplicate_conflict": duplicate_conflict,
                "notes": row.get("notes", ""),
            }
        )

    validated = pd.DataFrame(validated_rows)
    validated.to_csv(VALIDATED_CANDIDATES_PATH, index=False)
    validated.to_csv(QUALITY_REPORT_PATH, index=False)
    duplicate_report.to_csv(DUPLICATE_CANDIDATES_PATH, index=False)

    stats = {
        "candidate_rows": len(raw),
        "valid_rows": int(validated["is_valid"].sum()),
        "duplicate_conflicts": int(validated["duplicate_conflict"].sum()),
        "high_confidence": int((validated["extraction_confidence"] == "high").sum()),
        "medium_confidence": int((validated["extraction_confidence"] == "medium").sum()),
        "low_confidence": int((validated["extraction_confidence"] == "low").sum()),
    }
    return validated, duplicate_report, stats


def main() -> None:
    _, _, stats = validate_candidates()
    print("CSDS taxonomy candidate validation")
    print(f"  Candidate rows: {stats['candidate_rows']}")
    print(f"  Valid rows: {stats['valid_rows']}")
    print(f"  High-confidence candidates: {stats['high_confidence']}")
    print(f"  Medium-confidence candidates: {stats['medium_confidence']}")
    print(f"  Low-confidence candidates: {stats['low_confidence']}")
    print(f"  Duplicate conflicts: {stats['duplicate_conflicts']}")
    print(f"  Saved: {VALIDATED_CANDIDATES_PATH}")
    print(f"  Saved: {QUALITY_REPORT_PATH}")
    print(f"  Saved: {DUPLICATE_CANDIDATES_PATH}")


if __name__ == "__main__":
    main()
