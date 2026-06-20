"""
Build static simulation base JSON for The 543 Forecast / Simulator.

Run:
    python -m src.simulation.build_simulation_base
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
ANALYSIS_DIR = ROOT / "data" / "analysis"
DATABASE_DIR = ROOT / "data" / "database"
ELECTIONS_DIR = ROOT / "data" / "elections" / "processed"
OUTPUTS_DIR = ROOT / "data" / "outputs"
PROCESSED_DIR = ROOT / "data" / "processed"
FRONTEND_DATA_DIR = ROOT / "frontend" / "public" / "data"

MASTER_PATH = ANALYSIS_DIR / "constituency_election_demographic_master.csv"
OUTPUT_PATH = FRONTEND_DATA_DIR / "simulation_base.json"

RESULTS_CANDIDATES = [
    DATABASE_DIR / "results_table_2024.csv",
    DATABASE_DIR / "results_table.csv",
    OUTPUTS_DIR / "results_table_2024.csv",
    PROCESSED_DIR / "results_table_2024.csv",
    ELECTIONS_DIR / "results_table_2024.csv",
]

DEMOGRAPHIC_NFHS5_COLS = [
    "fertility_rate_nfhs5",
    "electricity_pct_nfhs5",
    "improved_sanitation_pct_nfhs5",
    "lpg_pct_nfhs5",
    "mobile_phone_pct_nfhs5",
    "bank_account_pct_nfhs5",
    "women_secondary_edu_pct_nfhs5",
    "female_literacy_pct_nfhs5",
    "male_literacy_pct_nfhs5",
    "wealth_index_mean_nfhs5",
    "urban_pct_nfhs5",
]

EXCLUDED_PARTIES = {"NOTA", "NONE"}


def _nan_to_none(value: object) -> object | None:
    if value is None:
        return None
    if isinstance(value, float) and pd.isna(value):
        return None
    if isinstance(value, str) and value.strip().lower() in {"", "nan", "none"}:
        return None
    return value


def _round_num(value: object, digits: int = 2) -> float | None:
    cleaned = _nan_to_none(value)
    if cleaned is None:
        return None
    try:
        return round(float(cleaned), digits)
    except (TypeError, ValueError):
        return None


def _has_demographics(row: pd.Series) -> bool:
    return any(_nan_to_none(row.get(col)) is not None for col in DEMOGRAPHIC_NFHS5_COLS)


def data_quality_label(nfhs5_coverage_share: float | None, has_demo: bool) -> str:
    if not has_demo or nfhs5_coverage_share is None or nfhs5_coverage_share <= 0:
        return "election_only"
    if nfhs5_coverage_share >= 0.75:
        return "high"
    if nfhs5_coverage_share >= 0.5:
        return "medium"
    return "low"


def _find_results_path() -> Path | None:
    for path in RESULTS_CANDIDATES:
        if path.exists():
            return path
    return None


def _load_results_by_constituency(results_path: Path) -> dict[str, dict[str, float]]:
    df = pd.read_csv(results_path)
    year_col = "election_year" if "election_year" in df.columns else None
    if year_col is not None:
        df = df[df[year_col].astype(str) == "2024"]

    id_col = "constituency_id" if "constituency_id" in df.columns else None
    party_col = "party_id" if "party_id" in df.columns else "party"
    share_col = "vote_share"

    grouped: dict[str, dict[str, float]] = {}
    for key, group in df.groupby(["state", "constituency"], sort=False):
        state, constituency = key
        lookup = f"{state}::{constituency}"
        shares: dict[str, float] = {}
        for _, row in group.iterrows():
            party = str(row.get(party_col, "")).strip().upper()
            if not party or party in EXCLUDED_PARTIES:
                continue
            share = _round_num(row.get(share_col))
            if share is None:
                continue
            shares[party] = shares.get(party, 0.0) + share
        if shares:
            grouped[lookup] = shares
            if id_col:
                cid = str(group.iloc[0].get(id_col, "")).strip()
                if cid:
                    grouped[cid] = shares
    return grouped


def _top_parties(shares: dict[str, float], limit: int = 5) -> list[dict[str, object]]:
    ranked = sorted(shares.items(), key=lambda item: item[1], reverse=True)
    return [{"party": party, "vote_share": round(share, 2)} for party, share in ranked[:limit]]


def _completeness(shares: dict[str, float] | None) -> tuple[str, str]:
    if not shares:
        return (
            "limited",
            "Simulation uses BJP/INC 2024 vote shares and winner fields only; regional-party shares are incomplete.",
        )
    total = sum(shares.values())
    if total >= 90 and len(shares) >= 2:
        return (
            "full",
            "Full 2024 party vote shares are available from ECI results for scenario renormalization.",
        )
    return (
        "limited",
        "Partial 2024 party vote shares are available; scenario projections should be interpreted cautiously.",
    )


def build_record(row: pd.Series, party_shares: dict[str, float] | None) -> dict[str, object]:
    nfhs5_share = _round_num(row.get("nfhs5_coverage_share"), 4)
    has_demo = _has_demographics(row)
    quality = data_quality_label(
        nfhs5_share if isinstance(nfhs5_share, float) else None,
        has_demo,
    )
    completeness, notes = _completeness(party_shares)

    record: dict[str, object] = {
        "state": str(row["state"]),
        "constituency": str(row["constituency"]),
        "state_key": str(row["state_key"]),
        "constituency_key": str(row["constituency_key"]),
        "winner_2019": _nan_to_none(row.get("winner_2019")),
        "winner_2024": _nan_to_none(row.get("winner_2024")),
        "winner_party_2019": _nan_to_none(row.get("winner_party_2019")),
        "winner_party_2024": _nan_to_none(row.get("winner_party_2024")),
        "bjp_vote_share_2019": _round_num(row.get("bjp_vote_share_2019")),
        "bjp_vote_share_2024": _round_num(row.get("bjp_vote_share_2024")),
        "inc_vote_share_2019": _round_num(row.get("inc_vote_share_2019")),
        "inc_vote_share_2024": _round_num(row.get("inc_vote_share_2024")),
        "margin_2024": _round_num(row.get("margin_2024")),
        "turnout_2024": _round_num(row.get("turnout_2024")),
        "data_quality_label": quality,
        "nfhs5_coverage_share": nfhs5_share,
        "simulation_completeness": completeness,
        "simulation_notes": notes,
    }

    if party_shares:
        record["available_party_vote_shares_2024"] = {
            party: round(share, 2) for party, share in sorted(party_shares.items(), key=lambda x: -x[1])
        }
        record["top_parties_2024"] = _top_parties(party_shares)
    else:
        record["available_party_vote_shares_2024"] = None
        record["top_parties_2024"] = None

    return record


def main() -> None:
    if not MASTER_PATH.exists():
        raise FileNotFoundError(f"Missing master dataset: {MASTER_PATH}")

    master = pd.read_csv(MASTER_PATH)
    results_path = _find_results_path()
    results_lookup: dict[str, dict[str, float]] = {}
    if results_path is not None:
        results_lookup = _load_results_by_constituency(results_path)

    records: list[dict[str, object]] = []
    full_count = 0
    limited_count = 0

    for _, row in master.iterrows():
        state = str(row["state"])
        constituency = str(row["constituency"])
        constituency_id = str(row.get("constituency_id", "")).strip()
        shares = results_lookup.get(f"{state}::{constituency}")
        if shares is None and constituency_id:
            shares = results_lookup.get(constituency_id)

        record = build_record(row, shares)
        if record["simulation_completeness"] == "full":
            full_count += 1
        else:
            limited_count += 1
        records.append(record)

    payload = {
        "meta": {
            "generated_at": date.today().isoformat(),
            "constituency_count": len(records),
            "full_completeness_count": full_count,
            "limited_completeness_count": limited_count,
            "results_source": str(results_path) if results_path else None,
        },
        "constituencies": records,
    }

    FRONTEND_DATA_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(f"Wrote {len(records)} simulation base records to {OUTPUT_PATH}")
    print(f"  Full completeness: {full_count}")
    print(f"  Limited completeness: {limited_count}")


if __name__ == "__main__":
    main()
