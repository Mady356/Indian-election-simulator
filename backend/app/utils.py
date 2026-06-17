"""Shared helpers for normalization and safe CSV access."""

from __future__ import annotations

import re
from typing import Any

import pandas as pd


def normalize_name(value: object) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    text = str(value).strip().upper()
    text = re.sub(r"\((SC|ST)\)", "", text, flags=re.I)
    text = text.replace("&", " AND ")
    text = re.sub(r"[–—\-/]", " ", text)
    text = re.sub(r"[^A-Z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def clean_constituency_name(value: object) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    text = str(value).strip()
    text = re.sub(r"\s*\((SC|ST)\)\s*$", "", text, flags=re.I)
    return text.strip()


def safe_float(value: object) -> float | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def safe_int(value: object) -> int | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def safe_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return False
    return str(value).strip().lower() in {"1", "true", "t", "yes", "y"}


def pick_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    lower_map = {col.lower(): col for col in df.columns}
    for candidate in candidates:
        if candidate.lower() in lower_map:
            return lower_map[candidate.lower()]
    return None


def row_value(row: pd.Series, candidates: list[str], default: Any = None) -> Any:
    for candidate in candidates:
        if candidate in row.index:
            value = row[candidate]
            if not (isinstance(value, float) and pd.isna(value)):
                return value
    return default
