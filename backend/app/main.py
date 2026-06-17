"""FastAPI application entry point."""

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.routers import constituencies, demographics, districts, elections, simulations
from backend.app.schemas import HealthResponse

app = FastAPI(
    title="Indian Election Intelligence Platform",
    description="Milestone 1 API for districts, constituencies, demographics, and simulations.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(districts.router)
app.include_router(constituencies.router)
app.include_router(elections.router)
app.include_router(demographics.router)
app.include_router(simulations.router)


@app.get("/", include_in_schema=False)
def root() -> RedirectResponse:
    return RedirectResponse(url="/docs")


@app.get("/health", response_model=HealthResponse)
def health(db: Session = Depends(get_db)) -> HealthResponse:
    try:
        db.execute(text("SELECT 1"))
        return HealthResponse(status="ok", database="connected")
    except SQLAlchemyError:
        return HealthResponse(status="degraded", database="unavailable")
