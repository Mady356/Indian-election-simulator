"""
Exploratory correlation analysis between election swings and demographics.

Run:
    python -m src.analysis.analyze_vote_share_drivers
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.analysis.analysis_common import (
    ANALYSIS_DIR,
    FEATURE_COLUMNS,
    TARGET_COLUMNS,
)

MASTER_PATH = ANALYSIS_DIR / "constituency_election_demographic_master.csv"
CORRELATIONS_PATH = ANALYSIS_DIR / "vote_share_driver_correlations.csv"
TOP_SWINGS_PATH = ANALYSIS_DIR / "top_swing_constituencies.csv"
QUALITY_PATH = ANALYSIS_DIR / "analysis_quality_report.csv"

NEAR_ZERO_THRESHOLD = 0.05
TOP_N = 25


def load_master() -> pd.DataFrame:
    if not MASTER_PATH.exists():
        raise FileNotFoundError(
            f"Missing master table at {MASTER_PATH}. "
            "Run python -m src.analysis.build_constituency_election_demographic_master first."
        )
    return pd.read_csv(MASTER_PATH)


def classify_direction(correlation: float) -> str:
    if pd.isna(correlation) or abs(correlation) < NEAR_ZERO_THRESHOLD:
        return "near_zero"
    if correlation > 0:
        return "positive"
    return "negative"


def build_interpretation_stub(target: str, feature: str, direction: str) -> str:
    target_label = {
        "bjp_swing_2019_2024": "BJP swing",
        "inc_swing_2019_2024": "INC swing",
        "turnout_change": "turnout change",
        "margin_change": "margin change",
    }.get(target, target)

    if direction == "near_zero":
        return (
            f"Higher {feature} shows little linear association with {target_label}. "
            "This is correlation, not causation."
        )
    if direction == "positive":
        return (
            f"Higher {feature} is associated with higher {target_label}. "
            "This is correlation, not causation."
        )
    return (
        f"Higher {feature} is associated with lower {target_label}. "
        "This is correlation, not causation."
    )


def compute_correlations(master: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []

    for target in TARGET_COLUMNS:
        if target not in master.columns:
            continue
        target_values = pd.to_numeric(master[target], errors="coerce")

        for feature in FEATURE_COLUMNS:
            if feature not in master.columns:
                continue
            feature_values = pd.to_numeric(master[feature], errors="coerce")
            valid = target_values.notna() & feature_values.notna()
            n_obs = int(valid.sum())

            if n_obs < 3:
                correlation = np.nan
            else:
                correlation = target_values[valid].corr(feature_values[valid])

            direction = classify_direction(correlation)
            rows.append(
                {
                    "target": target,
                    "feature": feature,
                    "correlation": correlation,
                    "abs_correlation": abs(correlation) if pd.notna(correlation) else np.nan,
                    "n_observations": n_obs,
                    "direction": direction,
                    "interpretation_stub": build_interpretation_stub(
                        target,
                        feature,
                        direction,
                    ),
                }
            )

    out = pd.DataFrame(rows)
    return out.sort_values(
        ["target", "abs_correlation"],
        ascending=[True, False],
        na_position="last",
    ).reset_index(drop=True)


def select_top_rows(
    master: pd.DataFrame,
    section: str,
    sort_col: str,
    ascending: bool,
    extra_cols: list[str] | None = None,
) -> pd.DataFrame:
    cols = ["state", "constituency", sort_col]
    if extra_cols:
        cols.extend(extra_cols)
    cols = [c for c in cols if c in master.columns]

    subset = master[cols].copy()
    subset = subset.dropna(subset=[sort_col])
    subset = subset.sort_values(sort_col, ascending=ascending).head(TOP_N)
    subset.insert(0, "table_section", section)
    subset.insert(1, "rank", range(1, len(subset) + 1))
    return subset


def build_top_swing_tables(master: pd.DataFrame) -> pd.DataFrame:
    tables = [
        select_top_rows(
            master,
            "top_25_bjp_gains",
            "bjp_swing_2019_2024",
            ascending=False,
            extra_cols=["bjp_vote_share_2019", "bjp_vote_share_2024", "winner_party_2024"],
        ),
        select_top_rows(
            master,
            "top_25_bjp_losses",
            "bjp_swing_2019_2024",
            ascending=True,
            extra_cols=["bjp_vote_share_2019", "bjp_vote_share_2024", "winner_party_2024"],
        ),
        select_top_rows(
            master,
            "top_25_inc_gains",
            "inc_swing_2019_2024",
            ascending=False,
            extra_cols=["inc_vote_share_2019", "inc_vote_share_2024", "winner_party_2024"],
        ),
        select_top_rows(
            master,
            "top_25_inc_losses",
            "inc_swing_2019_2024",
            ascending=True,
            extra_cols=["inc_vote_share_2019", "inc_vote_share_2024", "winner_party_2024"],
        ),
        select_top_rows(
            master,
            "closest_25_seats_2024",
            "margin_2024",
            ascending=True,
            extra_cols=["winner_party_2024", "winner_2024", "margin_2019"],
        ),
        select_top_rows(
            master,
            "largest_margin_changes",
            "margin_change",
            ascending=False,
            extra_cols=["margin_2019", "margin_2024", "winner_party_2024"],
        ),
    ]
    return pd.concat(tables, ignore_index=True)


def build_quality_report(
    master: pd.DataFrame,
    correlations: pd.DataFrame,
    top_swings: pd.DataFrame,
) -> pd.DataFrame:
    low_quality_rows = int((master.get("change_quality_flag") == "low").sum())
    if "change_quality_flag" not in master.columns:
        low_quality_rows = 0

    rows = [
        {
            "dataset": "constituency_election_demographic_master",
            "row_count": len(master),
            "constituencies_covered": master["constituency_id"].nunique()
            if "constituency_id" in master.columns
            else master["constituency"].nunique(),
            "missing_bjp_swing": int(master["bjp_swing_2019_2024"].isna().sum()),
            "missing_inc_swing": int(master["inc_swing_2019_2024"].isna().sum()),
            "mean_nfhs5_coverage": pd.to_numeric(
                master.get("nfhs5_coverage_share"), errors="coerce"
            ).mean(),
            "mean_change_coverage": pd.to_numeric(
                master.get("change_coverage_share"), errors="coerce"
            ).mean(),
            "low_quality_rows": low_quality_rows,
            "notes": (
                "Partial NFHS coverage is expected because the constituency demographic "
                "panel currently covers delimitation-era seats only."
            ),
        },
        {
            "dataset": "vote_share_driver_correlations",
            "row_count": len(correlations),
            "constituencies_covered": np.nan,
            "missing_bjp_swing": np.nan,
            "missing_inc_swing": np.nan,
            "mean_nfhs5_coverage": np.nan,
            "mean_change_coverage": np.nan,
            "low_quality_rows": int(correlations["n_observations"].lt(30).sum()),
            "notes": "Pairs with fewer than 30 overlapping observations should be read cautiously.",
        },
        {
            "dataset": "top_swing_constituencies",
            "row_count": len(top_swings),
            "constituencies_covered": top_swings["constituency"].nunique(),
            "missing_bjp_swing": np.nan,
            "missing_inc_swing": np.nan,
            "mean_nfhs5_coverage": np.nan,
            "mean_change_coverage": np.nan,
            "low_quality_rows": np.nan,
            "notes": "Summary tables for swings, close seats, and margin shifts.",
        },
    ]
    return pd.DataFrame(rows)


def print_correlation_highlights(correlations: pd.DataFrame, target: str, label: str) -> None:
    subset = correlations[correlations["target"] == target].copy()
    subset = subset[subset["direction"] != "near_zero"].dropna(subset=["correlation"])
    if subset.empty:
        print(f"  {label}: no strong correlations found")
        return

    positive = subset[subset["direction"] == "positive"].head(3)
    negative = subset[subset["direction"] == "negative"].head(3)

    print(f"  {label} strongest positive:")
    for _, row in positive.iterrows():
        print(
            f"    {row['feature']}: {row['correlation']:.3f} "
            f"(n={int(row['n_observations'])})"
        )

    print(f"  {label} strongest negative:")
    for _, row in negative.iterrows():
        print(
            f"    {row['feature']}: {row['correlation']:.3f} "
            f"(n={int(row['n_observations'])})"
        )


def print_console_summary(
    master: pd.DataFrame,
    correlations: pd.DataFrame,
    quality: pd.DataFrame,
) -> None:
    print()
    print("=== Analysis summary ===")
    print(f"Master table rows: {len(master)}")
    print(f"Constituencies with valid BJP swing: {master['bjp_swing_2019_2024'].notna().sum()}")
    print(f"Constituencies with valid INC swing: {master['inc_swing_2019_2024'].notna().sum()}")
    print()
    print_correlation_highlights(correlations, "bjp_swing_2019_2024", "BJP swing")
    print()
    print_correlation_highlights(correlations, "inc_swing_2019_2024", "INC swing")
    print()
    print("Biggest quality issues:")
    master_row = quality.iloc[0]
    print(
        f"  NFHS-5 mean coverage: {master_row['mean_nfhs5_coverage']:.3f}"
        if pd.notna(master_row["mean_nfhs5_coverage"])
        else "  NFHS-5 mean coverage: n/a"
    )
    print(
        f"  Change-feature mean coverage: {master_row['mean_change_coverage']:.3f}"
        if pd.notna(master_row["mean_change_coverage"])
        else "  Change-feature mean coverage: n/a"
    )
    print(f"  Low-quality demographic change rows: {int(master_row['low_quality_rows'])}")
    print(f"  Missing BJP swing rows: {int(master_row['missing_bjp_swing'])}")
    print(f"  Missing INC swing rows: {int(master_row['missing_inc_swing'])}")
    print(f"  Note: {master_row['notes']}")


def main() -> None:
    master = load_master()
    correlations = compute_correlations(master)
    top_swings = build_top_swing_tables(master)
    quality = build_quality_report(master, correlations, top_swings)

    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    correlations.to_csv(CORRELATIONS_PATH, index=False)
    top_swings.to_csv(TOP_SWINGS_PATH, index=False)
    quality.to_csv(QUALITY_PATH, index=False)

    print("Saved driver analysis outputs:")
    print(f"  {CORRELATIONS_PATH}")
    print(f"  {TOP_SWINGS_PATH}")
    print(f"  {QUALITY_PATH}")

    print_console_summary(master, correlations, quality)


if __name__ == "__main__":
    main()
