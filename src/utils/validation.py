"""
Lightweight sanity checks to run after building each intermediate table.

Functions print [OK]/[WARN] lines and return a bool so they can be chained or
asserted in tests. They're deliberately cheap: no heavy stats, just quick
guards against the kinds of breakage that have actually hurt us before
(missing columns, duplicated winners, vote shares outside 0..100, etc.).
"""

from typing import Iterable

import pandas as pd


EXPECTED_WINNERS = 543  # Lok Sabha total constituencies


def check_expected_winners(df: pd.DataFrame, expected: int = EXPECTED_WINNERS) -> bool:
    """If `df` has a `winner` column, count winners; otherwise treat df as the winners table."""
    if "winner" in df.columns:
        n = int(df["winner"].sum())
    else:
        n = len(df)
    ok = n == expected
    print(f"[{'OK' if ok else 'WARN'}] winners={n} expected={expected}")
    return ok


def check_required_columns(df: pd.DataFrame, required_columns: Iterable[str]) -> bool:
    required = list(required_columns)
    missing = [c for c in required if c not in df.columns]
    if missing:
        # We raise here because downstream code will almost certainly KeyError
        # in confusing ways if a required column is missing.
        raise KeyError(f"Missing required columns: {missing}")
    print(f"[OK] all required columns present: {required}")
    return True


def check_no_duplicate_winners(df: pd.DataFrame) -> bool:
    """Each (state, constituency) should map to exactly one winning row."""
    winners = df[df["winner"] == True] if "winner" in df.columns else df
    dup = int(winners.duplicated(subset=["state", "constituency"]).sum())
    ok = dup == 0
    print(f"[{'OK' if ok else 'WARN'}] duplicate winners (state, constituency) = {dup}")
    return ok


def check_vote_share_bounds(df: pd.DataFrame, col: str = "vote_share") -> bool:
    """Catches sign / normalisation bugs by asserting the column stays in [0, 100]."""
    s = df[col].dropna()
    bad = int(((s < 0) | (s > 100)).sum())
    ok = bad == 0
    print(f"[{'OK' if ok else 'WARN'}] {col} out-of-bounds rows = {bad} (expected 0..100)")
    return ok


def print_basic_dataset_summary(df: pd.DataFrame, label: str = "dataset") -> None:
    """One-shot human summary you can drop into any notebook cell."""
    print(f"--- {label} ---")
    print(f"shape   : {df.shape}")
    print(f"columns : {list(df.columns)}")
    print("nulls   :")
    print(df.isna().sum().to_string())
