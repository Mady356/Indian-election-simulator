"""Pytest configuration and shared fixtures."""

from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, delete
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Use in-memory SQLite for tests unless DATABASE_URL is already set.
os.environ.setdefault("DATABASE_URL", "sqlite://")

from backend.app.database import Base, get_db_checked  # noqa: E402
from backend.app.main import app  # noqa: E402
from backend.app.models import (  # noqa: E402
    Constituency,
    ConstituencyDistrict,
    ConstituencyYearSummary,
    DemographicFeature,
    District,
    ElectionResult,
)

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def create_test_database() -> None:
    Base.metadata.create_all(bind=engine)


@pytest.fixture(autouse=True)
def seed_sample_data() -> None:
    db = TestingSessionLocal()
    try:
        for table in reversed(Base.metadata.sorted_tables):
            db.execute(delete(table))
        db.commit()

        district = District(
            state="Test State",
            district="Test District",
            normalized_name="TEST STATE TEST DISTRICT",
        )
        db.add(district)
        db.flush()

        constituency = Constituency(
            state="Test State",
            constituency="Test Constituency",
            normalized_name="TEST CONSTITUENCY",
            constituency_no=1,
            reservation_status=None,
        )
        db.add(constituency)
        db.flush()

        db.add(
            DemographicFeature(
                geography_type="district",
                geography_id=district.id,
                survey="NFHS-5",
                survey_year=2020,
                urban_pct=40.0,
                female_literacy_pct=55.0,
            )
        )
        db.add(
            ConstituencyDistrict(
                constituency_id=constituency.id,
                district_id=district.id,
                assembly_segments_in_district=1,
                total_assembly_segments=1,
                district_segment_share=1.0,
                source="test",
            )
        )
        db.add(
            ConstituencyYearSummary(
                year=2024,
                constituency_id=constituency.id,
                winner_party="BJP",
                winner_alliance="NDA",
                winner_vote_share=52.0,
                runner_up_party="INC",
                margin_votes=10000,
                margin_pct=4.0,
            )
        )
        db.add(
            ElectionResult(
                year=2024,
                state="Test State",
                constituency_id=constituency.id,
                party="BJP",
                alliance="NDA",
                candidate="Test Candidate",
                votes=100000,
                vote_share=52.0,
                rank=1,
                won=True,
            )
        )
        db.add(
            ElectionResult(
                year=2024,
                state="Test State",
                constituency_id=constituency.id,
                party="INC",
                alliance="INDIA",
                candidate="Runner Candidate",
                votes=90000,
                vote_share=48.0,
                rank=2,
                won=False,
            )
        )
        db.commit()
    finally:
        db.close()


@pytest.fixture
def client() -> TestClient:
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db_checked] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
