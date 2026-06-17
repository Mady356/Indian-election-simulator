"""District-related API routes."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from backend.app.database import get_db_checked
from backend.app.models import DemographicFeature, District
from backend.app.schemas import DemographicFeatureOut, DistrictDetailOut, DistrictOut

router = APIRouter(prefix="/districts", tags=["districts"])


@router.get("", response_model=list[DistrictOut])
def list_districts(
    state: str | None = Query(None, description="Filter by state name"),
    search: str | None = Query(None, description="Search district name"),
    db: Session = Depends(get_db_checked),
) -> list[District]:
    query = db.query(District)
    if state:
        query = query.filter(District.state.ilike(state.strip()))
    if search:
        term = f"%{search.strip()}%"
        query = query.filter(
            or_(District.district.ilike(term), District.normalized_name.ilike(term.upper()))
        )
    return query.order_by(District.state, District.district).all()


@router.get("/{district_id}", response_model=DistrictDetailOut)
def get_district(district_id: int, db: Session = Depends(get_db_checked)) -> DistrictDetailOut:
    district = db.query(District).filter(District.id == district_id).first()
    if district is None:
        raise HTTPException(status_code=404, detail="District not found")

    demographics = (
        db.query(DemographicFeature)
        .filter(
            DemographicFeature.geography_type == "district",
            DemographicFeature.geography_id == district_id,
        )
        .all()
    )
    return DistrictDetailOut(
        id=district.id,
        state=district.state,
        district=district.district,
        normalized_name=district.normalized_name,
        demographics=[DemographicFeatureOut.model_validate(row) for row in demographics],
    )
