"""Demographic lookup routes."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.database import get_db_checked
from backend.app.models import DemographicFeature, District
from backend.app.schemas import DemographicFeatureOut

router = APIRouter(prefix="/demographics", tags=["demographics"])


@router.get("/district/{district_id}", response_model=list[DemographicFeatureOut])
def get_district_demographics(
    district_id: int,
    db: Session = Depends(get_db_checked),
) -> list[DemographicFeature]:
    district = db.query(District).filter(District.id == district_id).first()
    if district is None:
        raise HTTPException(status_code=404, detail="District not found")
    return (
        db.query(DemographicFeature)
        .filter(
            DemographicFeature.geography_type == "district",
            DemographicFeature.geography_id == district_id,
        )
        .all()
    )


@router.get("/state/{state_name}", response_model=list[DemographicFeatureOut])
def get_state_demographics(
    state_name: str,
    db: Session = Depends(get_db_checked),
) -> list[DemographicFeature]:
    rows = (
        db.query(DemographicFeature)
        .join(District, District.id == DemographicFeature.geography_id)
        .filter(
            DemographicFeature.geography_type == "state",
            District.state.ilike(state_name.strip()),
        )
        .all()
    )
    if not rows:
        raise HTTPException(status_code=404, detail="State demographic data not found")
    return rows
