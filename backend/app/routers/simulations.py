"""Simulation routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.database import get_db_checked
from backend.app.schemas import SimulationRequest, SimulationResponse
from backend.app.services.simulation import run_simulation

router = APIRouter(prefix="/simulate", tags=["simulations"])


@router.post("", response_model=SimulationResponse)
def simulate(
    payload: SimulationRequest,
    db: Session = Depends(get_db_checked),
) -> SimulationResponse:
    return run_simulation(db, payload)
