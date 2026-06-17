"""
Deduplicate CSDS vote-behavior rows and rebuild trustworthy pre/post comparisons.

Run:
    python -m src.postpoll.deduplicate_vote_behavior
"""

from __future__ import annotations

import pandas as pd

from src.postpoll.qa_common import (
    COMPARISON_DEDUPED_COLUMNS,
    COMPARISON_DEDUPED_PATH,
    COMPARISON_PATH,
    DEDUPED_EXTRA_COLUMNS,
    JOIN_AUDIT_PATH,
    JOIN_KEY,
    VOTE_BEHAVIOR_BASE_COLUMNS,
    VOTE_BEHAVIOR_DEDUPED_PATH,
    VOTE_BEHAVIOR_PATH,
    add_normalized_keys,
    confidence_rank,
    export_dashboard_json,
    normalize_key_value,
    parse_vote_share,
    shift_direction,
)

ORIGINAL_COMPARISON_ROWS = 0


def deduplicate_vote_behavior(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    if df.empty:
        empty = pd.DataFrame(columns=VOTE_BEHAVIOR_BASE_COLUMNS + DEDUPED_EXTRA_COLUMNS)
        return empty, pd.DataFrame()

    keyed = add_normalized_keys(df)
    norm_cols = ["year"] + [f"{col}_norm" for col in [
        "poll_type",
        "geography_level",
        "state",
        "voter_group_type",
        "voter_group",
        "party_or_alliance",
    ]]

    kept_rows: list[dict[str, object]] = []
    duplicate_audit: list[dict[str, object]] = []

    for _, group in keyed.groupby(norm_cols, dropna=False):
        group = group.copy()
        duplicate_count = len(group)
        vote_shares = group["vote_share"].map(parse_vote_share)
        unique_shares = sorted({v for v in vote_shares.dropna().tolist()})

        group["_confidence_rank"] = group["confidence"].map(confidence_rank)
        group = group.sort_values(
            by=["_confidence_rank", "source_table"],
            ascending=[False, True],
        )

        conflict = len(unique_shares) > 1 and group["_confidence_rank"].max() == group["_confidence_rank"].min()

        if duplicate_count == 1:
            dedupe_status = "unique"
            dedupe_notes = ""
            conflict_flag = False
            winner = group.iloc[0]
        elif not conflict and len(unique_shares) <= 1:
            dedupe_status = "duplicate_resolved_same_vote_share"
            dedupe_notes = f"collapsed {duplicate_count} identical rows"
            conflict_flag = False
            winner = group.iloc[0]
        elif not conflict:
            dedupe_status = "duplicate_resolved_highest_confidence"
            dedupe_notes = (
                f"kept highest-confidence row from {duplicate_count} duplicates; "
                f"vote_shares={';'.join(str(v) for v in unique_shares)}"
            )
            conflict_flag = False
            winner = group.iloc[0]
        else:
            dedupe_status = "duplicate_conflict"
            dedupe_notes = (
                f"conflicting vote_shares with tied confidence; "
                f"values={';'.join(str(v) for v in unique_shares)}"
            )
            conflict_flag = True
            winner = group.iloc[0]

        row = {col: winner.get(col) for col in VOTE_BEHAVIOR_BASE_COLUMNS if col in winner.index}
        row.update(
            {
                "dedupe_status": dedupe_status,
                "duplicate_count": duplicate_count,
                "conflict_flag": conflict_flag,
                "dedupe_notes": dedupe_notes,
            }
        )
        kept_rows.append(row)

        if duplicate_count > 1:
            duplicate_audit.append(
                {
                    "year": winner.get("year"),
                    "poll_type": winner.get("poll_type"),
                    "geography_level": winner.get("geography_level"),
                    "state": winner.get("state"),
                    "voter_group_type": winner.get("voter_group_type"),
                    "voter_group": winner.get("voter_group"),
                    "party_or_alliance": winner.get("party_or_alliance"),
                    "duplicate_count": duplicate_count,
                    "vote_shares_found": ";".join(str(v) for v in unique_shares),
                    "source_tables": ";".join(
                        sorted({str(v) for v in group["source_table"].dropna().tolist() if str(v).strip()})
                    ),
                    "source_pages": ";".join(
                        sorted({str(v) for v in group["source_page"].dropna().tolist() if str(v).strip()})
                    ),
                    "recommendation": "manual_review_conflict" if conflict_flag else "deduped",
                    "dedupe_status": dedupe_status,
                }
            )

    deduped = pd.DataFrame(kept_rows)
    audit = pd.DataFrame(duplicate_audit)
    return deduped, audit


def build_join_audit(pre_df: pd.DataFrame, post_df: pd.DataFrame) -> pd.DataFrame:
    pre = add_normalized_keys(pre_df)
    post = add_normalized_keys(post_df)
    join_norm_cols = ["year"] + [f"{col}_norm" for col in JOIN_KEY[1:]]

    pre_counts = pre.groupby(join_norm_cols, dropna=False).size().rename("pre_rows_available")
    post_counts = post.groupby(join_norm_cols, dropna=False).size().rename("post_rows_available")

    all_keys = pre_counts.index.union(post_counts.index)
    rows: list[dict[str, object]] = []

    for key in all_keys:
        pre_n = int(pre_counts.get(key, 0))
        post_n = int(post_counts.get(key, 0))
        values = list(key)
        row = dict(zip(JOIN_KEY, values))

        if pre_n == 1 and post_n == 1:
            matched_status = "clean_one_to_one"
            notes = ""
        elif pre_n == 0 and post_n > 0:
            matched_status = "pre_missing"
            notes = "no pre-poll row for join key"
        elif pre_n > 0 and post_n == 0:
            matched_status = "post_missing"
            notes = "no post-poll row for join key"
        elif pre_n > 1 or post_n > 1:
            matched_status = "duplicate_conflict"
            notes = f"pre_rows={pre_n}; post_rows={post_n}"
        else:
            matched_status = "unmatched"
            notes = "no rows on either side"

        row.update(
            {
                "pre_rows_available": pre_n,
                "post_rows_available": post_n,
                "matched_status": matched_status,
                "notes": notes,
            }
        )
        rows.append(row)

    return pd.DataFrame(rows)


def build_deduped_comparison(deduped: pd.DataFrame, join_audit: pd.DataFrame) -> pd.DataFrame:
    usable = deduped[~deduped["conflict_flag"].fillna(False)].copy()
    pre = add_normalized_keys(usable[usable["poll_type"] == "pre_poll"].copy())
    post = add_normalized_keys(usable[usable["poll_type"] == "post_poll"].copy())

    join_norm_cols = ["year"] + [f"{col}_norm" for col in JOIN_KEY[1:]]
    if pre.empty or post.empty:
        return pd.DataFrame(columns=COMPARISON_DEDUPED_COLUMNS)

    clean_keys = join_audit[join_audit["matched_status"] == "clean_one_to_one"].copy()
    if clean_keys.empty:
        return pd.DataFrame(columns=COMPARISON_DEDUPED_COLUMNS)

    for col in JOIN_KEY[1:]:
        clean_keys[f"{col}_norm"] = clean_keys[col].map(normalize_key_value)

    pre_one = pre.merge(clean_keys[join_norm_cols], on=join_norm_cols, how="inner")
    post_one = post.merge(clean_keys[join_norm_cols], on=join_norm_cols, how="inner")

    merged = pre_one.merge(
        post_one,
        on=join_norm_cols,
        how="inner",
        suffixes=("_pre", "_post"),
    )

    rows: list[dict[str, object]] = []
    for _, row in merged.iterrows():
        pre_share = parse_vote_share(row.get("vote_share_pre"))
        post_share = parse_vote_share(row.get("vote_share_post"))
        shift = None if pre_share is None or post_share is None else round(post_share - pre_share, 3)
        abs_shift = None if shift is None else round(abs(shift), 3)
        conf_pre = confidence_rank(row.get("confidence_pre"))
        conf_post = confidence_rank(row.get("confidence_post"))
        combined_conf = (
            "high"
            if min(conf_pre, conf_post) >= 3
            else "medium"
            if min(conf_pre, conf_post) >= 2
            else "low"
        )

        rows.append(
            {
                "year": row["year"],
                "geography_level": row.get("geography_level_pre"),
                "state": row.get("state_pre"),
                "voter_group_type": row.get("voter_group_type_pre"),
                "voter_group": row.get("voter_group_pre"),
                "party_or_alliance": row.get("party_or_alliance_pre"),
                "pre_poll_vote_share": pre_share,
                "post_poll_vote_share": post_share,
                "pre_to_post_shift": shift,
                "absolute_shift": abs_shift,
                "shift_direction": shift_direction(pre_share, post_share),
                "pre_source_table": row.get("source_table_pre"),
                "post_source_table": row.get("source_table_post"),
                "confidence": combined_conf,
                "notes": "",
            }
        )

    return pd.DataFrame(rows, columns=COMPARISON_DEDUPED_COLUMNS)


def run_deduplication() -> dict[str, int]:
    global ORIGINAL_COMPARISON_ROWS

    original = pd.read_csv(VOTE_BEHAVIOR_PATH) if VOTE_BEHAVIOR_PATH.exists() else pd.DataFrame()
    original_comparison = (
        pd.read_csv(COMPARISON_PATH) if COMPARISON_PATH.exists() else pd.DataFrame()
    )
    ORIGINAL_COMPARISON_ROWS = len(original_comparison)

    deduped, _dup_audit = deduplicate_vote_behavior(original)

    usable = deduped[~deduped["conflict_flag"].fillna(False)].copy()
    pre_df = usable[usable["poll_type"] == "pre_poll"]
    post_df = usable[usable["poll_type"] == "post_poll"]
    join_audit = build_join_audit(pre_df, post_df)
    comparison = build_deduped_comparison(usable, join_audit)

    VOTE_BEHAVIOR_DEDUPED_PATH.parent.mkdir(parents=True, exist_ok=True)
    deduped.to_csv(VOTE_BEHAVIOR_DEDUPED_PATH, index=False)
    join_audit.to_csv(JOIN_AUDIT_PATH, index=False)
    comparison.to_csv(COMPARISON_DEDUPED_PATH, index=False)
    export_dashboard_json(deduped, comparison)

    return {
        "original_rows": len(original),
        "deduped_rows": len(deduped),
        "conflict_rows": int(deduped["conflict_flag"].fillna(False).sum()) if not deduped.empty else 0,
        "original_comparison_rows": len(original_comparison),
        "deduped_comparison_rows": len(comparison),
        "clean_one_to_one": int((join_audit["matched_status"] == "clean_one_to_one").sum())
        if not join_audit.empty
        else 0,
        "duplicate_keys_before": int(
            original.groupby(
                ["year", "poll_type", "geography_level", "state", "voter_group_type", "voter_group", "party_or_alliance"],
                dropna=False,
            )
            .size()
            .gt(1)
            .sum()
        )
        if not original.empty
        else 0,
    }


def main() -> None:
    stats = run_deduplication()
    print("CSDS vote-behavior deduplication")
    print(f"  Original vote-behavior rows: {stats['original_rows']}")
    print(f"  Deduped vote-behavior rows: {stats['deduped_rows']}")
    print(f"  Conflict duplicate rows: {stats['conflict_rows']}")
    print(f"  Original comparison rows: {stats['original_comparison_rows']}")
    print(f"  Deduped comparison rows: {stats['deduped_comparison_rows']}")
    print(f"  Clean one-to-one pre/post matches: {stats['clean_one_to_one']}")
    print(f"  Saved: {VOTE_BEHAVIOR_DEDUPED_PATH}")
    print(f"  Saved: {JOIN_AUDIT_PATH}")
    print(f"  Saved: {COMPARISON_DEDUPED_PATH}")
    print("  Updated dashboard JSON from deduped files")


if __name__ == "__main__":
    main()
