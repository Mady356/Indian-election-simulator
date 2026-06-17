"""
Approve taxonomy candidates and merge into curated CSDS database.

Run:
    python -m src.postpoll.approve_taxonomy_candidates
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.postpoll.csds_taxonomy import (
    APPROVED_PATH,
    COMPARISON_CURATED_PATH,
    CURATED_PATH,
    FRONTEND_DATA_DIR,
    JOIN_KEY,
    REVIEW_PATH,
    VALIDATED_CANDIDATES_PATH,
    ensure_taxonomy_dirs,
    normalize_key,
    parse_vote_share,
)
from src.postpoll.qa_common import VOTE_BEHAVIOR_DEDUPED_PATH, shift_direction

APPROVED_COLUMNS = [
    "year",
    "poll_type",
    "source",
    "source_file",
    "source_page",
    "geography_level",
    "state",
    "voter_group_type",
    "voter_group",
    "party_or_alliance",
    "vote_share",
    "confidence",
    "data_origin",
    "approval_status",
    "evidence_text",
    "notes",
]

REVIEW_COLUMNS = [
    "candidate_id",
    "year",
    "poll_type",
    "source_file",
    "source_page",
    "voter_group_type",
    "voter_group",
    "party_or_alliance",
    "vote_share",
    "extraction_confidence",
    "evidence_text",
    "review_decision",
    "review_notes",
]

COMPARISON_CURATED_COLUMNS = [
    "year",
    "geography_level",
    "state",
    "voter_group_type",
    "voter_group",
    "party_or_alliance",
    "pre_poll_vote_share",
    "post_poll_vote_share",
    "pre_to_post_shift",
    "absolute_shift",
    "shift_direction",
    "pre_source_file",
    "pre_source_page",
    "post_source_file",
    "post_source_page",
    "confidence",
    "notes",
]


def _load_validated() -> pd.DataFrame:
    if not VALIDATED_CANDIDATES_PATH.exists():
        raise FileNotFoundError(
            f"Missing {VALIDATED_CANDIDATES_PATH}. Run validate_taxonomy_candidates first."
        )
    return pd.read_csv(VALIDATED_CANDIDATES_PATH)


def build_review_file(validated: pd.DataFrame) -> pd.DataFrame:
    if REVIEW_PATH.exists():
        existing = pd.read_csv(REVIEW_PATH)
        reviewed_ids = set(existing["candidate_id"].astype(str))
        pending = validated[~validated["candidate_id"].astype(str).isin(reviewed_ids)].copy()
        if pending.empty:
            return existing
        new_rows = pending[
            [
                "candidate_id",
                "year",
                "poll_type",
                "source_file",
                "source_page",
                "voter_group_type",
                "voter_group",
                "party_or_alliance",
                "vote_share",
                "extraction_confidence",
                "evidence_text",
            ]
        ].copy()
        new_rows["review_decision"] = ""
        new_rows["review_notes"] = ""
        combined = pd.concat([existing, new_rows], ignore_index=True)
        combined.to_csv(REVIEW_PATH, index=False)
        return combined

    rows = validated[
        [
            "candidate_id",
            "year",
            "poll_type",
            "source_file",
            "source_page",
            "voter_group_type",
            "voter_group",
            "party_or_alliance",
            "vote_share",
            "extraction_confidence",
            "evidence_text",
        ]
    ].copy()
    rows["review_decision"] = ""
    rows["review_notes"] = ""
    rows.to_csv(REVIEW_PATH, index=False)
    return rows


def resolve_approvals(validated: pd.DataFrame, review: pd.DataFrame) -> pd.DataFrame:
    review = review.copy()
    review["candidate_id"] = review["candidate_id"].astype(str)
    validated = validated.copy()
    validated["candidate_id"] = validated["candidate_id"].astype(str)

    merged = validated.merge(review, on="candidate_id", how="left", suffixes=("", "_review"))

    approved_rows: list[dict[str, object]] = []
    for _, row in merged.iterrows():
        decision = normalize_key(row.get("review_decision"))
        confidence = str(row.get("extraction_confidence", "")).lower()
        duplicate_conflict = bool(row.get("duplicate_conflict", False))
        rejected_validator = row.get("candidate_status") == "rejected_by_validator"

        if rejected_validator:
            approval_status = "rejected"
        elif decision == "reject":
            approval_status = "rejected"
        elif decision == "approve":
            approval_status = "approved"
        elif decision == "edit":
            approval_status = "approved"
        elif not decision:
            if confidence == "high" and not duplicate_conflict and bool(row.get("is_valid", False)):
                approval_status = "approved"
            else:
                approval_status = "needs_review"
        else:
            approval_status = "needs_review"

        vote_share = parse_vote_share(row.get("vote_share_review") or row.get("vote_share"))
        if decision == "edit" and pd.notna(row.get("vote_share_review")):
            vote_share = parse_vote_share(row.get("vote_share_review"))

        approved_rows.append(
            {
                "year": row["year"],
                "poll_type": row["poll_type"],
                "source": row["source"],
                "source_file": row["source_file"],
                "source_page": row["source_page"],
                "geography_level": row.get("geography_level", "national"),
                "state": row.get("state", ""),
                "voter_group_type": row["voter_group_type"],
                "voter_group": row["voter_group"],
                "party_or_alliance": row["party_or_alliance"],
                "vote_share": vote_share,
                "confidence": confidence,
                "data_origin": "taxonomy_reviewed" if decision in {"approve", "edit", "reject"} else "taxonomy_auto",
                "approval_status": approval_status,
                "evidence_text": row.get("evidence_text"),
                "notes": row.get("review_notes") or row.get("notes", ""),
                "candidate_id": row["candidate_id"],
            }
        )

    return pd.DataFrame(approved_rows)


def merge_curated(approved: pd.DataFrame) -> pd.DataFrame:
    approved_only = approved[approved["approval_status"] == "approved"].copy()
    taxonomy_rows = approved_only.drop(columns=["candidate_id"], errors="ignore")

    existing_manual = pd.DataFrame()
    if CURATED_PATH.exists():
        existing_manual = pd.read_csv(CURATED_PATH)
        if "data_origin" in existing_manual.columns:
            manual = existing_manual[
                existing_manual["data_origin"].astype(str).str.contains("manual", case=False, na=False)
            ].copy()
        else:
            manual = existing_manual.copy()
    else:
        manual = pd.DataFrame()

    auto_legacy = pd.DataFrame()
    if VOTE_BEHAVIOR_DEDUPED_PATH.exists():
        legacy = pd.read_csv(VOTE_BEHAVIOR_DEDUPED_PATH)
        if not legacy.empty:
            auto_legacy = pd.DataFrame(
                {
                    "year": legacy["year"],
                    "poll_type": legacy["poll_type"],
                    "source": "CSDS-Lokniti National Election Study",
                    "source_file": legacy.get("source_table", ""),
                    "source_page": legacy.get("source_page", ""),
                    "geography_level": legacy.get("geography_level", "national"),
                    "state": legacy.get("state", ""),
                    "voter_group_type": legacy.get("voter_group_type", ""),
                    "voter_group": legacy.get("voter_group", ""),
                    "party_or_alliance": legacy.get("party_or_alliance", ""),
                    "vote_share": legacy.get("vote_share"),
                    "confidence": legacy.get("confidence", "low"),
                    "data_origin": "legacy_auto",
                    "approval_status": "needs_review",
                    "evidence_text": legacy.get("original_label", ""),
                    "notes": "legacy generic extraction; superseded by taxonomy when high confidence",
                    "curation_status": "untrusted",
                }
            )

    combined = pd.concat([manual, taxonomy_rows, auto_legacy], ignore_index=True)
    if combined.empty:
        combined = pd.DataFrame(columns=APPROVED_COLUMNS + ["curation_status", "conflict_review_needed"])

    key_cols = [
        "year",
        "poll_type",
        "geography_level",
        "state",
        "voter_group_type",
        "voter_group",
        "party_or_alliance",
    ]

    def origin_rank(value: object) -> int:
        text = str(value).lower()
        if "manual" in text:
            return 4
        if "taxonomy_reviewed" in text:
            return 3
        if "taxonomy_auto" in text:
            return 2
        return 1

    combined["origin_rank"] = combined["data_origin"].map(origin_rank)
    combined["confidence_rank"] = combined["confidence"].map(
        lambda x: {"high": 3, "medium": 2, "low": 1}.get(str(x).lower(), 0)
    )

    curated_rows: list[dict[str, object]] = []
    for _, group in combined.groupby(key_cols, dropna=False):
        group = group.sort_values(["origin_rank", "confidence_rank"], ascending=False)
        winner = group.iloc[0].to_dict()
        shares = {parse_vote_share(v) for v in group["vote_share"] if parse_vote_share(v) is not None}
        conflict = len(shares) > 1
        winner["conflict_review_needed"] = conflict
        if conflict:
            winner["approval_status"] = "needs_review"
            winner["curation_status"] = "conflict_review_needed"
        elif winner.get("approval_status") == "approved":
            conf = str(winner.get("confidence", "")).lower()
            winner["curation_status"] = "trusted" if conf == "high" else "usable_with_caution"
        else:
            winner["curation_status"] = "untrusted"
        curated_rows.append(winner)

    curated = pd.DataFrame(curated_rows)
    for col in APPROVED_COLUMNS:
        if col not in curated.columns:
            curated[col] = ""
    curated = curated[APPROVED_COLUMNS + ["curation_status", "conflict_review_needed"]]
    curated.to_csv(CURATED_PATH, index=False)
    approved_only.to_csv(APPROVED_PATH, index=False)
    return curated


def build_curated_comparison(curated: pd.DataFrame) -> pd.DataFrame:
    usable = curated[
        (curated["approval_status"] == "approved")
        & (curated["curation_status"].isin(["trusted", "usable_with_caution"]))
        & (~curated["conflict_review_needed"].fillna(False))
    ].copy()

    pre = usable[usable["poll_type"] == "pre_poll"].copy()
    post = usable[usable["poll_type"] == "post_poll"].copy()

    for col in JOIN_KEY[1:]:
        pre[f"{col}_norm"] = pre[col].map(normalize_key)
        post[f"{col}_norm"] = post[col].map(normalize_key)
    join_cols = ["year"] + [f"{col}_norm" for col in JOIN_KEY[1:]]

    merged = pre.merge(post, on=join_cols, how="inner", suffixes=("_pre", "_post"))
    rows: list[dict[str, object]] = []
    for _, row in merged.iterrows():
        pre_share = parse_vote_share(row.get("vote_share_pre"))
        post_share = parse_vote_share(row.get("vote_share_post"))
        shift = None if pre_share is None or post_share is None else round(post_share - pre_share, 3)
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
                "absolute_shift": None if shift is None else round(abs(shift), 3),
                "shift_direction": shift_direction(pre_share, post_share),
                "pre_source_file": row.get("source_file_pre"),
                "pre_source_page": row.get("source_page_pre"),
                "post_source_file": row.get("source_file_post"),
                "post_source_page": row.get("source_page_post"),
                "confidence": row.get("confidence_pre"),
                "notes": "",
            }
        )

    comparison = pd.DataFrame(rows, columns=COMPARISON_CURATED_COLUMNS)
    comparison.to_csv(COMPARISON_CURATED_PATH, index=False)
    return comparison


def export_curated_json(curated: pd.DataFrame, comparison: pd.DataFrame) -> None:
    FRONTEND_DATA_DIR.mkdir(parents=True, exist_ok=True)
    dashboard_rows = curated[
        curated["curation_status"].isin(["trusted", "usable_with_caution"])
        & (curated["approval_status"] == "approved")
    ].copy()

    def records(frame: pd.DataFrame) -> list[dict[str, object]]:
        if frame.empty:
            return []
        cleaned = frame.where(pd.notna(frame), None)
        return json.loads(cleaned.to_json(orient="records"))

    vote_payload = {
        "generated_at": pd.Timestamp.now("UTC").isoformat(),
        "source": str(CURATED_PATH),
        "curated": True,
        "rows": records(dashboard_rows),
        "row_count": len(dashboard_rows),
    }
    comparison_payload = {
        "generated_at": pd.Timestamp.now("UTC").isoformat(),
        "source": str(COMPARISON_CURATED_PATH),
        "curated": True,
        "rows": records(comparison),
        "row_count": len(comparison),
    }

    (FRONTEND_DATA_DIR / "csds_vote_behavior_curated.json").write_text(
        json.dumps(vote_payload, indent=2),
        encoding="utf-8",
    )
    (FRONTEND_DATA_DIR / "csds_pre_post_comparison_curated.json").write_text(
        json.dumps(comparison_payload, indent=2),
        encoding="utf-8",
    )


def run_approval() -> dict[str, int]:
    ensure_taxonomy_dirs()
    validated = _load_validated()
    review = build_review_file(validated)
    approved = resolve_approvals(validated, review)
    curated = merge_curated(approved)
    comparison = build_curated_comparison(curated)
    export_curated_json(curated, comparison)

    return {
        "validated_rows": len(validated),
        "approved_rows": int((approved["approval_status"] == "approved").sum()),
        "needs_review_rows": int((approved["approval_status"] == "needs_review").sum()),
        "curated_rows": len(curated),
        "comparison_rows": len(comparison),
    }


def main() -> None:
    stats = run_approval()
    print("CSDS taxonomy candidate approval")
    print(f"  Validated candidates: {stats['validated_rows']}")
    print(f"  Approved rows: {stats['approved_rows']}")
    print(f"  Rows needing review: {stats['needs_review_rows']}")
    print(f"  Curated database rows: {stats['curated_rows']}")
    print(f"  Pre/post comparison rows: {stats['comparison_rows']}")
    print(f"  Saved: {APPROVED_PATH}")
    print(f"  Saved: {CURATED_PATH}")
    print(f"  Saved: {COMPARISON_CURATED_PATH}")
    print(f"  Saved: {REVIEW_PATH}")
    print("  Updated frontend/public/data/csds_*_curated.json")


if __name__ == "__main__":
    main()
