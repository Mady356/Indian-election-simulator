"""
Build Monte Carlo simulation base JSON for The 543 Forecast page.

Run:
    python -m src.simulation.build_monte_carlo_base
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pandas as pd

from src.simulation.build_simulation_base import (
    DEMOGRAPHIC_NFHS5_COLS,
    EXCLUDED_PARTIES,
    MASTER_PATH,
    RESULTS_CANDIDATES,
    _find_results_path,
    _has_demographics,
    _load_results_by_constituency,
    _nan_to_none,
    _round_num,
    _top_parties,
    data_quality_label,
)

ROOT = Path(__file__).resolve().parents[2]
REFERENCE_DIR = ROOT / "data" / "reference"
FRONTEND_DATA_DIR = ROOT / "frontend" / "public" / "data"
ALLIANCE_MAP_PATH = REFERENCE_DIR / "party_alliance_mapping.csv"
OUTPUT_PATH = FRONTEND_DATA_DIR / "monte_carlo_base.json"

ALLIANCE_BUCKETS = ("NDA", "INDIA", "Others", "Unknown")


def _load_alliance_map() -> dict[str, str]:
    if not ALLIANCE_MAP_PATH.exists():
        return {}
    df = pd.read_csv(ALLIANCE_MAP_PATH)
    mapping: dict[str, str] = {}
    for _, row in df.iterrows():
        party = str(row.get("normalized_party") or row.get("party", "")).strip().upper()
        alliance = str(row.get("alliance_2024", "Unknown")).strip()
        if not party:
            continue
        if alliance.upper() in {"NDA", "INDIA", "OTHERS", "UNKNOWN"}:
            mapping[party] = "Others" if alliance.upper() == "OTHERS" else alliance.upper()
            if mapping[party] == "UNKNOWN":
                mapping[party] = "Unknown"
        else:
            mapping[party] = "Unknown"
        raw = str(row.get("party", "")).strip().upper()
        if raw:
            mapping[raw] = mapping[party]
    return mapping


def _party_to_alliance(party: str, alliance_map: dict[str, str]) -> str:
    key = party.strip().upper()
    if key in EXCLUDED_PARTIES or key == "NOTA":
        return "Unknown"
    if key in alliance_map:
        alliance = alliance_map[key]
        return alliance if alliance != "Unknown" else "Others"
    if key in {"BJP"}:
        return "NDA"
    if key in {"INC", "CONGRESS"}:
        return "INDIA"
    return "Others"


def _aggregate_alliance_shares(
    party_shares: dict[str, float],
    alliance_map: dict[str, str],
) -> dict[str, float]:
    buckets = {"NDA": 0.0, "INDIA": 0.0, "Others": 0.0}
    for party, share in party_shares.items():
        alliance = _party_to_alliance(party, alliance_map)
        if alliance == "NDA":
            buckets["NDA"] += share
        elif alliance == "INDIA":
            buckets["INDIA"] += share
        elif alliance == "Others":
            buckets["Others"] += share
    return {k: round(v, 2) for k, v in buckets.items() if v > 0}


def _completeness(
    party_shares: dict[str, float] | None,
    row: pd.Series,
) -> str:
    if party_shares and len(party_shares) >= 3 and sum(party_shares.values()) >= 90:
        return "full_party_shares"
    bjp = _round_num(row.get("bjp_vote_share_2024"))
    inc = _round_num(row.get("inc_vote_share_2024"))
    winner = _nan_to_none(row.get("winner_party_2024"))
    margin = _round_num(row.get("margin_2024"))
    if bjp is not None or inc is not None or winner:
        return "bjp_inc_limited"
    if winner and margin is not None:
        return "winner_margin_only"
    return "bjp_inc_limited"


def _limited_alliance_shares(row: pd.Series) -> dict[str, float]:
    bjp = _round_num(row.get("bjp_vote_share_2024")) or 0.0
    inc = _round_num(row.get("inc_vote_share_2024")) or 0.0
    winner = str(_nan_to_none(row.get("winner_party_2024")) or "").upper()
    shares: dict[str, float] = {}
    if bjp:
        shares["NDA"] = shares.get("NDA", 0.0) + bjp
    if inc:
        shares["INDIA"] = shares.get("INDIA", 0.0) + inc
    others = max(0.0, 100.0 - bjp - inc)
    if others > 0:
        shares["Others"] = others
    if winner and winner not in {"BJP", "INC", "CONGRESS"} and others > 0:
        # Winner is regional; limited mode keeps Others bucket only.
        pass
    return {k: round(v, 2) for k, v in shares.items()}


def build_record(
    row: pd.Series,
    party_shares: dict[str, float] | None,
    alliance_map: dict[str, str],
) -> dict[str, object]:
    nfhs5_share = _round_num(row.get("nfhs5_coverage_share"), 4)
    has_demo = _has_demographics(row)
    quality = data_quality_label(
        nfhs5_share if isinstance(nfhs5_share, float) else None,
        has_demo,
    )
    completeness = _completeness(party_shares, row)

    alliance_shares: dict[str, float] | None = None
    if party_shares and completeness == "full_party_shares":
        alliance_shares = _aggregate_alliance_shares(party_shares, alliance_map)
    elif completeness == "bjp_inc_limited":
        alliance_shares = _limited_alliance_shares(row)

    return {
        "state": str(row["state"]),
        "constituency": str(row["constituency"]),
        "state_key": str(row["state_key"]),
        "constituency_key": str(row["constituency_key"]),
        "winner_2024": _nan_to_none(row.get("winner_2024")),
        "winner_party_2024": _nan_to_none(row.get("winner_party_2024")),
        "bjp_vote_share_2024": _round_num(row.get("bjp_vote_share_2024")),
        "inc_vote_share_2024": _round_num(row.get("inc_vote_share_2024")),
        "margin_2024": _round_num(row.get("margin_2024")),
        "turnout_2024": _round_num(row.get("turnout_2024")),
        "nfhs5_coverage_share": nfhs5_share,
        "data_quality_label": quality,
        "party_vote_shares_2024": (
            {party: round(share, 2) for party, share in sorted(party_shares.items(), key=lambda x: -x[1])}
            if party_shares
            else None
        ),
        "top_parties_2024": _top_parties(party_shares, limit=5) if party_shares else None,
        "alliance_vote_shares_2024": alliance_shares,
        "simulation_completeness": completeness,
    }


def main() -> None:
    if not MASTER_PATH.exists():
        raise FileNotFoundError(f"Missing master dataset: {MASTER_PATH}")

    master = pd.read_csv(MASTER_PATH)
    alliance_map = _load_alliance_map()
    results_path = _find_results_path()
    results_lookup: dict[str, dict[str, float]] = {}
    if results_path is not None:
        results_lookup = _load_results_by_constituency(results_path)

    records: list[dict[str, object]] = []
    counts = {"full_party_shares": 0, "bjp_inc_limited": 0, "winner_margin_only": 0}

    for _, row in master.iterrows():
        state = str(row["state"])
        constituency = str(row["constituency"])
        constituency_id = str(row.get("constituency_id", "")).strip()
        shares = results_lookup.get(f"{state}::{constituency}")
        if shares is None and constituency_id:
            shares = results_lookup.get(constituency_id)

        record = build_record(row, shares, alliance_map)
        counts[str(record["simulation_completeness"])] = (
            counts.get(str(record["simulation_completeness"]), 0) + 1
        )
        records.append(record)

    payload = {
        "meta": {
            "generated_at": date.today().isoformat(),
            "constituency_count": len(records),
            "completeness_counts": counts,
            "alliance_mapping_source": str(ALLIANCE_MAP_PATH),
            "results_source": str(results_path) if results_path else None,
            "majority_threshold": 272,
        },
        "alliance_mapping": alliance_map,
        "constituencies": records,
    }

    FRONTEND_DATA_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(f"Wrote {len(records)} Monte Carlo base records to {OUTPUT_PATH}")
    for key, value in counts.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
