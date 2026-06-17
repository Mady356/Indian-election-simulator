"""
Reusable election metrics.

Centralising these formulas means we get *exactly the same* ENP / vote-share /
distortion numbers everywhere the project uses them — features, analyses,
simulators and notebooks all import from here.
"""

from typing import Iterable, Sequence

import numpy as np
import pandas as pd


def effective_number_of_parties(vote_shares: Iterable[float]) -> float:
    """
    Laakso-Taagepera Effective Number of Parties: ENP = 1 / sum(p_i^2),
    where p_i is each party's share *as a proportion* (0..1).

    Input here is expected in *percentage* form (0..100) to match the rest of
    the project, so we divide by 100 inside.
    """
    p = np.asarray(list(vote_shares), dtype=float) / 100.0
    s = float(np.sum(p ** 2))
    return 1.0 / s if s > 0 else float("nan")


def calculate_vote_share(
    df: pd.DataFrame,
    group_cols: Sequence[str],
    vote_col: str = "votes",
) -> pd.DataFrame:
    """Add a `vote_share` column = vote_col / sum(vote_col) within each group, expressed in %."""
    out = df.copy()
    total = out.groupby(list(group_cols))[vote_col].transform("sum")
    out["vote_share"] = out[vote_col] / total * 100
    return out


def calculate_top2_margin(
    df: pd.DataFrame,
    group_cols: Sequence[str] = ("state", "constituency"),
    share_col: str = "vote_share",
) -> pd.DataFrame:
    """
    For each group, sort by vote share desc and return rank-1 minus rank-2.
    Returns: (state, constituency, top2_margin_pct) — one row per group.
    """
    group_cols = list(group_cols)
    ordered = (
        df.sort_values(group_cols + [share_col], ascending=[True] * len(group_cols) + [False])
          .groupby(group_cols)
          .head(2)
    )

    def _gap(x: pd.Series) -> float:
        return float(x.iloc[0] - x.iloc[1]) if len(x) >= 2 else float("nan")

    margins = (
        ordered.groupby(group_cols)[share_col]
               .apply(_gap)
               .reset_index(name="top2_margin_pct")
    )
    return margins


def calculate_seat_counts(winners: pd.DataFrame, group_col: str = "party") -> pd.DataFrame:
    """Count seats per party (or alliance) from a winners table."""
    return (
        winners.groupby(group_col)
               .size()
               .reset_index(name="seats")
               .sort_values("seats", ascending=False)
               .reset_index(drop=True)
    )


def calculate_vote_seat_distortion(
    results: pd.DataFrame,
    winners: pd.DataFrame,
    party_col: str = "party",
    vote_col: str = "votes",
) -> pd.DataFrame:
    """
    Combine national vote share and seat share per party and compute the gap.

    representation_gap = seat_share_pct - vote_share_pct, so:
      * positive => party is over-represented under FPTP
      * negative => party is under-represented
    """
    total_votes = float(results[vote_col].sum())
    votes = (
        results.groupby(party_col)[vote_col]
               .sum()
               .reset_index()
    )
    votes["vote_share_pct"] = votes[vote_col] / total_votes * 100

    seats = calculate_seat_counts(winners, group_col=party_col)
    total_seats = len(winners)
    seats["seat_share_pct"] = seats["seats"] / total_seats * 100

    out = votes.merge(seats, on=party_col, how="left")
    out["seats"] = out["seats"].fillna(0)
    out["seat_share_pct"] = out["seat_share_pct"].fillna(0)
    out["representation_gap"] = out["seat_share_pct"] - out["vote_share_pct"]
    return out.sort_values("vote_share_pct", ascending=False).reset_index(drop=True)
