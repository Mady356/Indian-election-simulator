"""Constituency-related API routes."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from backend.app.database import get_db_checked
from backend.app.models import (
    Constituency,
    ConstituencyDistrict,
    ConstituencyYearSummary,
    DemographicFeature,
    District,
    ElectionResult,
)
from backend.app.schemas import (
    ConstituencyDemographicsOut,
    ConstituencyDetailOut,
    ConstituencyDistrictOut,
    ConstituencyOut,
    ConstituencyResultsOut,
    ConstituencyYearSummaryOut,
    DemographicFeatureOut,
    ElectionResultOut,
)
from backend.app.services.demographics import aggregate_constituency_demographics

router = APIRouter(prefix="/constituencies", tags=["constituencies"])


@router.get("", response_model=list[ConstituencyOut])
def list_constituencies(
    state: str | None = Query(None),
    search: str | None = Query(None),
    party_winner: str | None = Query(None, description="Filter by winning party in a given year"),
    year: int | None = Query(None, description="Election year used with party_winner"),
    db: Session = Depends(get_db_checked),
) -> list[Constituency]:
    query = db.query(Constituency)
    if state:
        query = query.filter(Constituency.state.ilike(state.strip()))
    if search:
        term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Constituency.constituency.ilike(term),
                Constituency.normalized_name.ilike(term.upper()),
            )
        )
    if party_winner:
        summary_year = year or 2024
        query = query.join(ConstituencyYearSummary).filter(
            ConstituencyYearSummary.year == summary_year,
            ConstituencyYearSummary.winner_party.ilike(party_winner.strip()),
        )
    return query.order_by(Constituency.state, Constituency.constituency).all()


@router.get("/{constituency_id}", response_model=ConstituencyDetailOut)
def get_constituency(
    constituency_id: int,
    db: Session = Depends(get_db_checked),
) -> ConstituencyDetailOut:
    constituency = (
        db.query(Constituency)
        .options(
            joinedload(Constituency.district_links).joinedload(ConstituencyDistrict.district),
            joinedload(Constituency.year_summaries),
        )
        .filter(Constituency.id == constituency_id)
        .first()
    )
    if constituency is None:
        raise HTTPException(status_code=404, detail="Constituency not found")

    districts = [
        ConstituencyDistrictOut(
            district_id=link.district_id,
            district=link.district.district,
            state=link.district.state,
            assembly_segments_in_district=link.assembly_segments_in_district,
            total_assembly_segments=link.total_assembly_segments,
            district_segment_share=link.district_segment_share,
            source=link.source,
        )
        for link in constituency.district_links
    ]
    history = [
        ConstituencyYearSummaryOut.model_validate(summary)
        for summary in sorted(constituency.year_summaries, key=lambda row: row.year)
    ]
    return ConstituencyDetailOut(
        id=constituency.id,
        state=constituency.state,
        constituency=constituency.constituency,
        normalized_name=constituency.normalized_name,
        constituency_no=constituency.constituency_no,
        reservation_status=constituency.reservation_status,
        districts=districts,
        election_history=history,
    )


@router.get("/{constituency_id}/demographics", response_model=ConstituencyDemographicsOut)
def get_constituency_demographics(
    constituency_id: int,
    db: Session = Depends(get_db_checked),
) -> ConstituencyDemographicsOut:
    constituency = db.query(Constituency).filter(Constituency.id == constituency_id).first()
    if constituency is None:
        raise HTTPException(status_code=404, detail="Constituency not found")

    aggregated = aggregate_constituency_demographics(db, constituency_id)
    if aggregated is None:
        raise HTTPException(status_code=404, detail="No demographic data available for constituency")

    return ConstituencyDemographicsOut(
        constituency_id=constituency.id,
        constituency=constituency.constituency,
        state=constituency.state,
        demographics=DemographicFeatureOut.model_validate(aggregated),
    )


@router.get("/{constituency_id}/results", response_model=ConstituencyResultsOut)
def get_constituency_results(
    constituency_id: int,
    db: Session = Depends(get_db_checked),
) -> ConstituencyResultsOut:
    constituency = db.query(Constituency).filter(Constituency.id == constituency_id).first()
    if constituency is None:
        raise HTTPException(status_code=404, detail="Constituency not found")

    results_by_year: dict[int, list[ElectionResultOut]] = {}
    for year in (2019, 2024):
        rows = (
            db.query(ElectionResult)
            .filter(
                ElectionResult.constituency_id == constituency_id,
                ElectionResult.year == year,
            )
            .order_by(ElectionResult.rank)
            .all()
        )
        if rows:
            results_by_year[year] = [ElectionResultOut.model_validate(row) for row in rows]

    return ConstituencyResultsOut(
        constituency_id=constituency_id,
        results=results_by_year,
    )
