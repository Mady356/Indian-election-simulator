"""
Build dashboard-ready CSDS vote-behavior database and poll-accuracy comparisons.

Run:
    python -m src.postpoll.build_vote_behavior_database
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.analysis.analysis_common import ELECTION_SEARCH_DIRS, discover_file
from src.postpoll.analyze_pre_post_shift import (
    COMPARISON_PATH,
    SHIFT_SUMMARY_PATH,
    build_pre_post_comparison,
    top_shifts,
)
from src.postpoll.clean_csds_tables import VOTE_BEHAVIOR_PATH
from src.postpoll.csds_manifest import (
    FRONTEND_DATA_DIR,
    MANIFEST_PATH,
    PROCESSED_DIR,
    REPORTS_DIR,
    STUDIES,
)

DATABASE_DIR = Path(__file__).resolve().parents[2] / "data" / "database"

VS_ACTUAL_PATH = PROCESSED_DIR / "csds_vs_actual_results.csv"
ACCURACY_SUMMARY_PATH = REPORTS_DIR / "csds_poll_accuracy_summary.csv"
MANUAL_REVIEW_PATH = REPORTS_DIR / "manual_extraction_needed.csv"

VS_ACTUAL_COLUMNS = [
    "year",
    "poll_type",
    "geography_level",
    "state",
    "party_or_alliance",
    "survey_vote_share",
    "actual_vote_share",
    "survey_minus_actual",
    "absolute_error",
    "sample_size",
    "constituencies_covered",
    "notes",
]

ACCURACY_SUMMARY_COLUMNS = [
    "year",
    "poll_type",
    "party_or_alliance",
    "survey_vote_share",
    "actual_vote_share",
    "absolute_error",
    "direction",
    "interpretation_stub",
]

SURVEY_PARTIES_FOR_ACCURACY = ["BJP", "INC", "NDA", "INDIA", "UPA", "Others"]

ALLIANCE_MAP_2024 = {
    "NDA": "NDA",
    "INDIA": "INDIA",
    "OTHER": "Others",
    "NONE": "Others",
}

ALLIANCE_MAP_2019 = {
    "NDA": "NDA",
    "UPA": "UPA",
    "INDIA": "UPA",  # project DB retro-label; treat as UPA for 2019 comparisons
    "OTHER": "Others",
    "NONE": "Others",
}


def _safe_discover(patterns: list[str]) -> Path | None:
    try:
        return discover_file("election file", patterns, ELECTION_SEARCH_DIRS)
    except FileNotFoundError:
        return None


def load_results_table(year: int) -> pd.DataFrame | None:
    exact = DATABASE_DIR / f"results_table_{year}.csv"
    if exact.exists():
        print(f"Selected election file: {exact}")
        return pd.read_csv(exact)
    path = _safe_discover([f"results_table_{year}.csv"])
    if path is None or not path.exists():
        return None
    return pd.read_csv(path)


def load_alliance_table(year: int) -> pd.DataFrame | None:
    exact = DATABASE_DIR / f"alliance_table_{year}.csv"
    if exact.exists():
        print(f"Selected election file: {exact}")
        return pd.read_csv(exact)
    path = _safe_discover([f"alliance_table_{year}.csv"])
    if path is None or not path.exists():
        return None
    return pd.read_csv(path)


def _alliance_column(year: int, df: pd.DataFrame) -> str | None:
    candidates = [f"alliance_{year}", "alliance", "alliance_2024", "alliance_2019"]
    for col in candidates:
        if col in df.columns:
            return col
    return None


def compute_actual_vote_shares(year: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (national_df, state_df) with party_or_alliance and actual_vote_share."""
    results = load_results_table(year)
    alliances = load_alliance_table(year)
    if results is None or alliances is None:
        return pd.DataFrame(), pd.DataFrame()

    alliance_col = _alliance_column(year, alliances)
    party_col = "party_clean" if "party_clean" in results.columns else "party"
    if alliance_col is None or party_col not in results.columns:
        return pd.DataFrame(), pd.DataFrame()

    merged = results.merge(
        alliances,
        left_on=party_col,
        right_on="party",
        how="left",
        suffixes=("", "_alliance"),
    )
    if "votes" not in merged.columns:
        return pd.DataFrame(), pd.DataFrame()

    alliance_map = ALLIANCE_MAP_2024 if year >= 2024 else ALLIANCE_MAP_2019
    merged["party_or_alliance"] = merged[alliance_col].map(alliance_map).fillna("Others")

    # National aggregation
    national = (
        merged.groupby("party_or_alliance", as_index=False)["votes"]
        .sum()
        .assign(actual_vote_share=lambda d: 100 * d["votes"] / d["votes"].sum())
    )
    national["geography_level"] = "national"
    national["state"] = ""

    state_df = pd.DataFrame()
    if "state" in merged.columns:
        totals = merged.groupby("state", as_index=False)["votes"].sum().rename(columns={"votes": "state_total"})
        state = merged.groupby(["state", "party_or_alliance"], as_index=False)["votes"].sum()
        state = state.merge(totals, on="state", how="left")
        state["actual_vote_share"] = 100 * state["votes"] / state["state_total"]
        state["geography_level"] = "state"
        state_df = state[["geography_level", "state", "party_or_alliance", "actual_vote_share"]]

    national = national[["geography_level", "state", "party_or_alliance", "actual_vote_share"]]
    return national, state_df


def _survey_national_shares(vote_df: pd.DataFrame, year: int, poll_type: str) -> pd.DataFrame:
    sub = vote_df[(vote_df["year"] == year) & (vote_df["poll_type"] == poll_type)].copy()
    if sub.empty:
        return pd.DataFrame()

    # Prefer overall / total rows when present; otherwise average within poll.
    overall_mask = sub["voter_group"].astype(str).str.upper().isin(
        {"ALL", "TOTAL", "ALL VOTERS", "OVERALL", "TOTAL VOTERS"}
    )
    if overall_mask.any():
        sub = sub[overall_mask]
    else:
        sub = sub[sub["voter_group_type"].isin(["other", "region", "state"])]

    if sub.empty:
        return pd.DataFrame()

    grouped = (
        sub.groupby("party_or_alliance", as_index=False)["vote_share"]
        .mean()
        .rename(columns={"vote_share": "survey_vote_share"})
    )
    grouped["geography_level"] = "national"
    grouped["state"] = ""
    return grouped


def build_vs_actual(vote_df: pd.DataFrame, manifest_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []

    for year in sorted(vote_df["year"].dropna().unique()) if not vote_df.empty else []:
        year = int(year)
        national_actual, state_actual = compute_actual_vote_shares(year)
        if national_actual.empty:
            continue

        for poll_type in ("pre_poll", "post_poll"):
            survey = _survey_national_shares(vote_df, year, poll_type)
            if survey.empty:
                continue

            meta = manifest_df[
                (manifest_df["year"] == year) & (manifest_df["poll_type"] == poll_type)
            ]
            sample_size = meta["sample_size"].iloc[0] if not meta.empty else ""
            constituencies = meta["constituencies_covered"].iloc[0] if not meta.empty else ""

            for _, srow in survey.iterrows():
                party = str(srow["party_or_alliance"])
                if party not in SURVEY_PARTIES_FOR_ACCURACY and party not in {"BJP", "INC"}:
                    continue

                actual_row = national_actual[
                    national_actual["party_or_alliance"] == party
                ]
                if actual_row.empty and party == "BJP":
                    actual_row = national_actual[national_actual["party_or_alliance"] == "NDA"]
                if actual_row.empty and party == "INC":
                    for alt in ("INDIA", "UPA"):
                        actual_row = national_actual[national_actual["party_or_alliance"] == alt]
                        if not actual_row.empty:
                            break

                if actual_row.empty:
                    continue

                actual_share = float(actual_row["actual_vote_share"].iloc[0])
                survey_share = float(srow["survey_vote_share"])
                diff = round(survey_share - actual_share, 3)
                rows.append(
                    {
                        "year": year,
                        "poll_type": poll_type,
                        "geography_level": "national",
                        "state": "",
                        "party_or_alliance": party,
                        "survey_vote_share": survey_share,
                        "actual_vote_share": round(actual_share, 3),
                        "survey_minus_actual": diff,
                        "absolute_error": round(abs(diff), 3),
                        "sample_size": sample_size,
                        "constituencies_covered": constituencies,
                        "notes": "national comparison from discovered election results",
                    }
                )

            if not state_actual.empty:
                state_survey = vote_df[
                    (vote_df["year"] == year)
                    & (vote_df["poll_type"] == poll_type)
                    & (vote_df["geography_level"] == "state")
                    & (vote_df["state"].astype(str).str.len() > 0)
                ]
                if not state_survey.empty:
                    for state_name in state_survey["state"].dropna().unique():
                        ssub = state_survey[state_survey["state"] == state_name]
                        for party in ssub["party_or_alliance"].dropna().unique():
                            survey_share = float(ssub[ssub["party_or_alliance"] == party]["vote_share"].mean())
                            actual_row = state_actual[
                                (state_actual["state"] == state_name)
                                & (state_actual["party_or_alliance"] == party)
                            ]
                            if actual_row.empty:
                                continue
                            actual_share = float(actual_row["actual_vote_share"].iloc[0])
                            diff = round(survey_share - actual_share, 3)
                            rows.append(
                                {
                                    "year": year,
                                    "poll_type": poll_type,
                                    "geography_level": "state",
                                    "state": state_name,
                                    "party_or_alliance": party,
                                    "survey_vote_share": survey_share,
                                    "actual_vote_share": round(actual_share, 3),
                                    "survey_minus_actual": diff,
                                    "absolute_error": round(abs(diff), 3),
                                    "sample_size": sample_size,
                                    "constituencies_covered": constituencies,
                                    "notes": "state-level comparison",
                                }
                            )

    return pd.DataFrame(rows, columns=VS_ACTUAL_COLUMNS)


def build_accuracy_summary(vs_actual_df: pd.DataFrame) -> pd.DataFrame:
    if vs_actual_df.empty:
        return pd.DataFrame(columns=ACCURACY_SUMMARY_COLUMNS)

    national = vs_actual_df[vs_actual_df["geography_level"] == "national"].copy()
    rows: list[dict[str, object]] = []
    for _, row in national.iterrows():
        diff = row["survey_minus_actual"]
        direction = "overestimated" if diff > 0 else "underestimated" if diff < 0 else "matched"
        rows.append(
            {
                "year": row["year"],
                "poll_type": row["poll_type"],
                "party_or_alliance": row["party_or_alliance"],
                "survey_vote_share": row["survey_vote_share"],
                "actual_vote_share": row["actual_vote_share"],
                "absolute_error": row["absolute_error"],
                "direction": direction,
                "interpretation_stub": (
                    f"In {int(row['year'])} {row['poll_type'].replace('_', '-')}, "
                    f"{row['party_or_alliance']} was {direction} by "
                    f"{row['absolute_error']:.1f} points versus actual national vote share. "
                    f"This is a descriptive survey-vs-result gap, not a formal polling-error model."
                ),
            }
        )
    return pd.DataFrame(rows, columns=ACCURACY_SUMMARY_COLUMNS)


def _df_to_records(df: pd.DataFrame) -> list[dict[str, object]]:
    if df.empty:
        return []
    cleaned = df.where(pd.notna(df), None)
    return json.loads(cleaned.to_json(orient="records"))


def export_frontend_json(
    vote_df: pd.DataFrame,
    comparison_df: pd.DataFrame,
    accuracy_df: pd.DataFrame,
) -> None:
    FRONTEND_DATA_DIR.mkdir(parents=True, exist_ok=True)

    vote_payload = {
        "generated_at": pd.Timestamp.now("UTC").isoformat(),
        "studies": [dict(study) for study in STUDIES],
        "rows": _df_to_records(vote_df),
        "row_count": len(vote_df),
    }
    comparison_payload = {
        "generated_at": pd.Timestamp.now("UTC").isoformat(),
        "rows": _df_to_records(comparison_df),
        "row_count": len(comparison_df),
    }
    accuracy_payload = {
        "generated_at": pd.Timestamp.now("UTC").isoformat(),
        "rows": _df_to_records(accuracy_df),
        "row_count": len(accuracy_df),
    }

    (FRONTEND_DATA_DIR / "csds_vote_behavior.json").write_text(
        json.dumps(vote_payload, indent=2),
        encoding="utf-8",
    )
    (FRONTEND_DATA_DIR / "csds_pre_post_comparison.json").write_text(
        json.dumps(comparison_payload, indent=2),
        encoding="utf-8",
    )
    (FRONTEND_DATA_DIR / "csds_poll_accuracy_summary.json").write_text(
        json.dumps(accuracy_payload, indent=2),
        encoding="utf-8",
    )


def build_database() -> dict[str, object]:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    vote_df = pd.read_csv(VOTE_BEHAVIOR_PATH) if VOTE_BEHAVIOR_PATH.exists() else pd.DataFrame()
    manifest_df = pd.read_csv(MANIFEST_PATH) if MANIFEST_PATH.exists() else pd.DataFrame()
    comparison_df = (
        pd.read_csv(COMPARISON_PATH)
        if COMPARISON_PATH.exists()
        else build_pre_post_comparison(vote_df)
    )

    vs_actual = build_vs_actual(vote_df, manifest_df)
    vs_actual.to_csv(VS_ACTUAL_PATH, index=False)

    accuracy = build_accuracy_summary(vs_actual)
    accuracy.to_csv(ACCURACY_SUMMARY_PATH, index=False)

    export_frontend_json(vote_df, comparison_df, accuracy)

    manual_count = 0
    if MANUAL_REVIEW_PATH.exists():
        manual_count = len(pd.read_csv(MANUAL_REVIEW_PATH))

    return {
        "vote_rows": len(vote_df),
        "comparison_rows": len(comparison_df),
        "matched_rows": len(comparison_df[comparison_df["shift_direction"] != "unavailable"])
        if not comparison_df.empty and "shift_direction" in comparison_df.columns
        else 0,
        "vs_actual_rows": len(vs_actual),
        "accuracy_rows": len(accuracy),
        "manual_review_items": manual_count,
        "biggest_shifts": top_shifts(comparison_df, n=5),
        "national_accuracy": accuracy,
    }


def main() -> None:
    stats = build_database()

    print("CSDS vote-behavior database")
    print(f"  Vote-behavior rows: {stats['vote_rows']}")
    print(f"  Pre/post comparison rows: {stats['comparison_rows']}")
    print(f"  Matched pre/post rows: {stats['matched_rows']}")
    print(f"  Survey vs actual rows: {stats['vs_actual_rows']}")
    print(f"  Manual review items: {stats['manual_review_items']}")
    print(f"  Saved: {VS_ACTUAL_PATH}")
    print(f"  Saved: {ACCURACY_SUMMARY_PATH}")
    print(f"  JSON: {FRONTEND_DATA_DIR}/csds_*.json")

    biggest = stats["biggest_shifts"]
    if isinstance(biggest, pd.DataFrame) and not biggest.empty:
        print("\n  Biggest pre-to-post shifts:")
        for _, row in biggest.iterrows():
            print(
                f"    {int(row['year'])} {row['voter_group']} / {row['party_or_alliance']}: "
                f"{row['pre_to_post_shift']:+.1f} pts"
            )

    accuracy = stats["national_accuracy"]
    if isinstance(accuracy, pd.DataFrame) and not accuracy.empty:
        print("\n  Survey vs actual (national):")
        for _, row in accuracy.iterrows():
            print(
                f"    {int(row['year'])} {row['poll_type']}: {row['party_or_alliance']} "
                f"survey={row['survey_vote_share']:.1f}% actual={row['actual_vote_share']:.1f}% "
                f"error={row['absolute_error']:.1f}"
            )
    elif stats["vote_rows"] == 0:
        print("\n  No survey rows yet — add CSDS PDFs and rerun the full pipeline.")
    else:
        print("\n  Survey vs actual comparison unavailable (no matched overall survey rows).")


if __name__ == "__main__":
    main()
