"""
Compare CSDS pre-poll and post-poll voter-group estimates.

Run:
    python -m src.postpoll.analyze_pre_post_shift
"""

from __future__ import annotations

import pandas as pd

from src.postpoll.clean_csds_tables import VOTE_BEHAVIOR_PATH
from src.postpoll.csds_manifest import PROCESSED_DIR, REPORTS_DIR

COMPARISON_PATH = PROCESSED_DIR / "csds_pre_post_comparison.csv"
SHIFT_SUMMARY_PATH = REPORTS_DIR / "csds_pre_post_shift_summary.csv"

COMPARISON_COLUMNS = [
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
    "notes",
]

SHIFT_SUMMARY_COLUMNS = [
    "year",
    "voter_group_type",
    "voter_group",
    "party_or_alliance",
    "pre_poll_vote_share",
    "post_poll_vote_share",
    "pre_to_post_shift",
    "absolute_shift",
    "interpretation_stub",
]

SHIFT_TOLERANCE = 0.5


def _shift_direction(pre: float | None, post: float | None) -> str:
    if pre is None or post is None:
        return "unavailable"
    delta = post - pre
    if abs(delta) < SHIFT_TOLERANCE:
        return "unchanged"
    if delta > 0:
        return "increased_post_poll"
    return "decreased_post_poll"


def _interpretation_stub(
    year: int,
    voter_group_type: str,
    voter_group: str,
    party: str,
    shift: float | None,
) -> str:
    group_phrase = voter_group or voter_group_type or "this group"
    party_phrase = party or "the selected party/alliance"
    if shift is None:
        return (
            f"Pre-poll and post-poll estimates for {group_phrase} ({year}) "
            f"could not be matched for {party_phrase}."
        )
    direction = "higher" if shift > 0 else "lower" if shift < 0 else "similar"
    return (
        f"Among {group_phrase}, {party_phrase} support was {direction} in the "
        f"post-poll than the pre-poll ({shift:+.1f} points). This may indicate "
        f"late swing, turnout differences, or survey-design differences; it is "
        f"not automatically causal."
    )


def build_pre_post_comparison(vote_df: pd.DataFrame) -> pd.DataFrame:
    if vote_df.empty:
        return pd.DataFrame(columns=COMPARISON_COLUMNS)

    pre = vote_df[vote_df["poll_type"] == "pre_poll"].copy()
    post = vote_df[vote_df["poll_type"] == "post_poll"].copy()

    join_keys = [
        "year",
        "geography_level",
        "state",
        "voter_group_type",
        "voter_group",
        "party_or_alliance",
    ]

    merged = pre.merge(
        post,
        on=join_keys,
        how="outer",
        suffixes=("_pre", "_post"),
        indicator=True,
    )

    rows: list[dict[str, object]] = []
    for _, row in merged.iterrows():
        pre_share = row.get("vote_share_pre")
        post_share = row.get("vote_share_post")
        pre_val = float(pre_share) if pd.notna(pre_share) else None
        post_val = float(post_share) if pd.notna(post_share) else None
        shift = None if pre_val is None or post_val is None else round(post_val - pre_val, 3)
        abs_shift = None if shift is None else round(abs(shift), 3)
        notes = []
        if row["_merge"] == "left_only":
            notes.append("post-poll row missing")
        elif row["_merge"] == "right_only":
            notes.append("pre-poll row missing")

        rows.append(
            {
                "year": row["year"],
                "geography_level": row["geography_level"],
                "state": row["state"],
                "voter_group_type": row["voter_group_type"],
                "voter_group": row["voter_group"],
                "party_or_alliance": row["party_or_alliance"],
                "pre_poll_vote_share": pre_val,
                "post_poll_vote_share": post_val,
                "pre_to_post_shift": shift,
                "absolute_shift": abs_shift,
                "shift_direction": _shift_direction(pre_val, post_val),
                "notes": "; ".join(notes),
            }
        )

    return pd.DataFrame(rows, columns=COMPARISON_COLUMNS)


def build_shift_summary(comparison_df: pd.DataFrame) -> pd.DataFrame:
    if comparison_df.empty:
        return pd.DataFrame(columns=SHIFT_SUMMARY_COLUMNS)

    available = comparison_df[comparison_df["shift_direction"] != "unavailable"].copy()
    rows: list[dict[str, object]] = []
    for _, row in available.iterrows():
        rows.append(
            {
                "year": row["year"],
                "voter_group_type": row["voter_group_type"],
                "voter_group": row["voter_group"],
                "party_or_alliance": row["party_or_alliance"],
                "pre_poll_vote_share": row["pre_poll_vote_share"],
                "post_poll_vote_share": row["post_poll_vote_share"],
                "pre_to_post_shift": row["pre_to_post_shift"],
                "absolute_shift": row["absolute_shift"],
                "interpretation_stub": _interpretation_stub(
                    int(row["year"]),
                    str(row["voter_group_type"]),
                    str(row["voter_group"]),
                    str(row["party_or_alliance"]),
                    row["pre_to_post_shift"] if pd.notna(row["pre_to_post_shift"]) else None,
                ),
            }
        )
    return pd.DataFrame(rows, columns=SHIFT_SUMMARY_COLUMNS)


def top_shifts(comparison_df: pd.DataFrame, n: int = 5) -> pd.DataFrame:
    if comparison_df.empty:
        return comparison_df
    ranked = comparison_df.dropna(subset=["absolute_shift"]).copy()
    if ranked.empty:
        return ranked
    return ranked.sort_values("absolute_shift", ascending=False).head(n)


def run_analysis() -> tuple[pd.DataFrame, pd.DataFrame]:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    if VOTE_BEHAVIOR_PATH.exists():
        vote_df = pd.read_csv(VOTE_BEHAVIOR_PATH)
    else:
        vote_df = pd.DataFrame()

    comparison = build_pre_post_comparison(vote_df)
    comparison.to_csv(COMPARISON_PATH, index=False)

    summary = build_shift_summary(comparison)
    summary.to_csv(SHIFT_SUMMARY_PATH, index=False)
    return comparison, summary


def main() -> None:
    comparison, summary = run_analysis()
    matched = comparison[comparison["shift_direction"] != "unavailable"]
    biggest = top_shifts(comparison, n=5)

    print("CSDS pre-poll vs post-poll analysis")
    print(f"  Vote-behavior rows input: {len(pd.read_csv(VOTE_BEHAVIOR_PATH)) if VOTE_BEHAVIOR_PATH.exists() else 0}")
    print(f"  Comparison rows: {len(comparison)}")
    print(f"  Matched pre/post rows: {len(matched)}")
    print(f"  Saved: {COMPARISON_PATH}")
    print(f"  Saved: {SHIFT_SUMMARY_PATH}")

    if not biggest.empty:
        print("\n  Biggest pre-to-post shifts:")
        for _, row in biggest.iterrows():
            print(
                f"    {int(row['year'])} {row['voter_group']} / {row['party_or_alliance']}: "
                f"{row['pre_to_post_shift']:+.1f} pts"
            )
    else:
        print("  No matched pre/post rows yet — add PDFs and rerun the pipeline.")


if __name__ == "__main__":
    main()
