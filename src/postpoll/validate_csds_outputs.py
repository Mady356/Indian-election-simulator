"""
Validate CSDS vote-behavior rows and detect duplicate analytical keys.

Run:
    python -m src.postpoll.validate_csds_outputs
"""

from __future__ import annotations

import pandas as pd

from src.postpoll.qa_common import (
    ANALYTICAL_KEY,
    DUPLICATE_KEYS_PATH,
    QUALITY_REPORT_PATH,
    VOTE_BEHAVIOR_PATH,
    add_normalized_keys,
    confidence_rank,
    parse_vote_share,
)

QUALITY_FLAG_COLUMNS = [
    "valid",
    "missing_party",
    "missing_group_type",
    "missing_vote_share",
    "invalid_vote_share",
    "duplicate_key",
    "low_confidence",
    "needs_manual_review",
]


def _is_missing_group_type(row: pd.Series) -> bool:
    group_type = str(row.get("voter_group_type_norm", "")).lower()
    group = str(row.get("voter_group_norm", ""))
    if group_type in {"", "other", "unknown"} and not group:
        return True
    if group_type in {"", "unknown"}:
        return True
    return False


def assess_row_quality(row: pd.Series, duplicate_keys: set[tuple[object, ...]]) -> dict[str, bool]:
    flags = {name: False for name in QUALITY_FLAG_COLUMNS}

    year = row.get("year")
    poll_type = str(row.get("poll_type_norm", ""))
    party = str(row.get("party_or_alliance_norm", ""))
    vote_share = parse_vote_share(row.get("vote_share"))
    confidence = str(row.get("confidence_norm", "")).lower()
    source_table = str(row.get("source_table_norm", ""))
    key = (
        int(year) if pd.notna(year) else year,
        poll_type,
        str(row.get("geography_level_norm", "")),
        str(row.get("state_norm", "")),
        str(row.get("voter_group_type_norm", "")),
        str(row.get("voter_group_norm", "")),
        party,
    )

    if party in {"", "unknown"}:
        flags["missing_party"] = True
    if _is_missing_group_type(row):
        flags["missing_group_type"] = True
    if vote_share is None:
        flags["missing_vote_share"] = True
    else:
        raw = row.get("vote_share")
        try:
            num = float(raw)
            if num < 0 or num > 100:
                flags["invalid_vote_share"] = True
        except (TypeError, ValueError):
            flags["invalid_vote_share"] = True

    if key in duplicate_keys:
        flags["duplicate_key"] = True
    if confidence_rank(confidence) <= 1:
        flags["low_confidence"] = True
    if not source_table:
        flags["needs_manual_review"] = True

    if year not in (2019, 2024) or poll_type not in {"pre_poll", "post_poll"}:
        flags["needs_manual_review"] = True

    flags["valid"] = not any(
        flags[name]
        for name in QUALITY_FLAG_COLUMNS
        if name != "valid"
    )
    return flags


def quality_flags_text(flags: dict[str, bool]) -> str:
    return "|".join(name for name, enabled in flags.items() if enabled and name != "valid")


def build_quality_report(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()

    keyed = add_normalized_keys(df)
    duplicate_mask = keyed.duplicated(
        subset=[f"{col}_norm" if col != "year" else "year" for col in ANALYTICAL_KEY],
        keep=False,
    )
    duplicate_keys = set(
        (
            int(row["year"]) if pd.notna(row["year"]) else row["year"],
            *[row[f"{col}_norm"] for col in ANALYTICAL_KEY[1:]],
        )
        for _, row in keyed[duplicate_mask].iterrows()
    )

    rows: list[dict[str, object]] = []
    for idx, row in keyed.iterrows():
        flags = assess_row_quality(row, duplicate_keys)
        rows.append(
            {
                "row_index": idx,
                "year": row.get("year"),
                "poll_type": row.get("poll_type"),
                "geography_level": row.get("geography_level"),
                "state": row.get("state"),
                "voter_group_type": row.get("voter_group_type"),
                "voter_group": row.get("voter_group"),
                "party_or_alliance": row.get("party_or_alliance"),
                "vote_share": row.get("vote_share"),
                "source_table": row.get("source_table"),
                "source_page": row.get("source_page"),
                "confidence": row.get("confidence"),
                "is_valid": flags["valid"],
                "quality_flags": quality_flags_text(flags),
                **flags,
            }
        )
    return pd.DataFrame(rows)


def build_duplicate_key_report(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(
            columns=[
                *ANALYTICAL_KEY,
                "duplicate_count",
                "vote_shares_found",
                "source_tables",
                "source_pages",
                "recommendation",
            ]
        )

    keyed = add_normalized_keys(df)
    norm_cols = ["year"] + [f"{col}_norm" for col in ANALYTICAL_KEY[1:]]
    grouped = keyed.groupby(norm_cols, dropna=False)

    rows: list[dict[str, object]] = []
    for key_vals, group in grouped:
        if len(group) < 2:
            continue

        vote_shares = sorted(
            {
                round(float(v), 3)
                for v in group["vote_share"].map(parse_vote_share).dropna().tolist()
            }
        )
        source_tables = sorted({str(v) for v in group["source_table"].dropna().tolist() if str(v).strip()})
        source_pages = sorted({str(v) for v in group["source_page"].dropna().tolist() if str(v).strip()})

        if len(vote_shares) <= 1:
            recommendation = "keep_one_same_vote_share"
        elif group["confidence"].map(confidence_rank).nunique() > 1:
            recommendation = "keep_highest_confidence"
        else:
            recommendation = "manual_review_conflict"

        row = dict(zip(ANALYTICAL_KEY, key_vals))
        row.update(
            {
                "duplicate_count": len(group),
                "vote_shares_found": ";".join(str(v) for v in vote_shares),
                "source_tables": ";".join(source_tables),
                "source_pages": ";".join(source_pages),
                "recommendation": recommendation,
            }
        )
        rows.append(row)

    return pd.DataFrame(rows)


def run_validation() -> dict[str, int]:
    df = pd.read_csv(VOTE_BEHAVIOR_PATH) if VOTE_BEHAVIOR_PATH.exists() else pd.DataFrame()
    quality = build_quality_report(df)
    duplicates = build_duplicate_key_report(df)

    QUALITY_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    quality.to_csv(QUALITY_REPORT_PATH, index=False)
    duplicates.to_csv(DUPLICATE_KEYS_PATH, index=False)

    return {
        "original_rows": len(df),
        "valid_rows": int(quality["is_valid"].sum()) if not quality.empty else 0,
        "duplicate_keys": len(duplicates),
        "conflict_duplicate_keys": int(
            (duplicates["recommendation"] == "manual_review_conflict").sum()
        )
        if not duplicates.empty
        else 0,
    }


def main() -> None:
    stats = run_validation()
    print("CSDS vote-behavior validation")
    print(f"  Original vote-behavior rows: {stats['original_rows']}")
    print(f"  Valid rows: {stats['valid_rows']}")
    print(f"  Duplicate analytical keys: {stats['duplicate_keys']}")
    print(f"  Conflict duplicate keys: {stats['conflict_duplicate_keys']}")
    print(f"  Saved: {QUALITY_REPORT_PATH}")
    print(f"  Saved: {DUPLICATE_KEYS_PATH}")


if __name__ == "__main__":
    main()
