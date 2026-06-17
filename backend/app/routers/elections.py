"""Election summary routes."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.database import get_db_checked
from backend.app.models import ConstituencyYearSummary, ElectionResult
from backend.app.schemas import ConstituencyYearSummaryOut, ElectionResultOut

router = APIRouter(prefix="/elections", tags=["elections"])


@router.get("/results", response_model=list[ElectionResultOut])
def list_election_results(
    year: int = Query(..., description="Election year"),
    state: str | None = Query(None),
    party: str | None = Query(None),
    db: Session = Depends(get_db_checked),
) -> list[ElectionResult]:
    query = db.query(ElectionResult).filter(ElectionResult.year == year)
    if state:
        query = query.filter(ElectionResult.state.ilike(state.strip()))
    if party:
        query = query.filter(ElectionResult.party.ilike(party.strip()))
    return query.order_by(ElectionResult.state, ElectionResult.constituency_id, ElectionResult.rank).all()


@router.get("/summaries", response_model=list[ConstituencyYearSummaryOut])
def list_constituency_summaries(
    year: int = Query(...),
    state: str | None = Query(None),
    db: Session = Depends(get_db_checked),
) -> list[ConstituencyYearSummary]:
    query = (
        db.query(ConstituencyYearSummary)
        .join(ConstituencyYearSummary.constituency)
        .filter(ConstituencyYearSummary.year == year)
    )
    if state:
        from backend.app.models import Constituency

        query = query.filter(Constituency.state.ilike(state.strip()))
    return query.all()
