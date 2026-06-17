"""Simple transparent election simulation."""

from __future__ import annotations

from collections import defaultdict

from sqlalchemy.orm import Session

from backend.app.models import Constituency, ConstituencyYearSummary, ElectionResult
from backend.app.schemas import ConstituencyProjection, SimulationRequest, SimulationResponse
from backend.app.services.demographics import NUMERIC_FIELDS, aggregate_constituency_demographics


def _base_shares(db: Session, constituency_id: int, base_year: int) -> dict[str, float]:
    rows = (
        db.query(ElectionResult)
        .filter(
            ElectionResult.constituency_id == constituency_id,
            ElectionResult.year == base_year,
        )
        .all()
    )
    shares: dict[str, float] = {}
    for row in rows:
        if row.party and row.vote_share is not None:
            shares[row.party.upper()] = float(row.vote_share)
    return shares


def _base_winner(db: Session, constituency_id: int, base_year: int) -> str | None:
    summary = (
        db.query(ConstituencyYearSummary)
        .filter(
            ConstituencyYearSummary.constituency_id == constituency_id,
            ConstituencyYearSummary.year == base_year,
        )
        .first()
    )
    if summary and summary.winner_party:
        return summary.winner_party.upper()
    shares = _base_shares(db, constituency_id, base_year)
    if not shares:
        return None
    return max(shares, key=shares.get)


def _apply_variable_effects(
    shares: dict[str, float],
    demo_values: dict[str, float | None],
    variable_effects: dict,
) -> None:
    for variable, effect in variable_effects.items():
        base_value = demo_values.get(variable)
        if base_value is None:
            continue
        party = effect.party.upper()
        delta = float(base_value) * float(effect.effect_per_unit)
        shares[party] = shares.get(party, 0.0) + delta


def _normalize_shares(shares: dict[str, float]) -> dict[str, float]:
    total = sum(max(v, 0.0) for v in shares.values())
    if total <= 0:
        return shares
    return {party: max(value, 0.0) * 100.0 / total for party, value in shares.items()}


def run_simulation(db: Session, payload: SimulationRequest) -> SimulationResponse:
    constituencies = db.query(Constituency).order_by(Constituency.id).all()
    base_totals: dict[str, int] = defaultdict(int)
    projected_totals: dict[str, int] = defaultdict(int)
    changes: list[ConstituencyProjection] = []

    for constituency in constituencies:
        shares = _base_shares(db, constituency.id, payload.base_year)
        if not shares:
            continue

        base_winner = _base_winner(db, constituency.id, payload.base_year)
        if base_winner:
            base_totals[base_winner] += 1

        adjusted = dict(shares)
        for party, swing in payload.party_swings.items():
            adjusted[party.upper()] = adjusted.get(party.upper(), 0.0) + float(swing)

        demo = aggregate_constituency_demographics(db, constituency.id)
        demo_values = {field: getattr(demo, field) if demo else None for field in NUMERIC_FIELDS}
        _apply_variable_effects(adjusted, demo_values, payload.variable_effects)

        projected_shares = _normalize_shares(adjusted)
        projected_winner = max(projected_shares, key=projected_shares.get)
        projected_totals[projected_winner] += 1

        changed = base_winner != projected_winner
        if changed:
            changes.append(
                ConstituencyProjection(
                    constituency_id=constituency.id,
                    state=constituency.state,
                    constituency=constituency.constituency,
                    base_winner=base_winner,
                    projected_winner=projected_winner,
                    changed=True,
                    projected_shares=projected_shares,
                )
            )

    return SimulationResponse(
        base_year=payload.base_year,
        constituencies_projected=sum(projected_totals.values()),
        seats_changed=len(changes),
        projected_seat_totals=dict(sorted(projected_totals.items())),
        base_seat_totals=dict(sorted(base_totals.items())),
        sample_changes=changes[:50],
    )
