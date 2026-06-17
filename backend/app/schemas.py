"""Pydantic request/response schemas."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class HealthResponse(BaseModel):
    status: str
    database: str


class DistrictOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    state: str
    district: str
    normalized_name: str


class DemographicFeatureOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    geography_type: str
    survey: str | None = None
    survey_year: int | None = None
    fertility_rate: float | None = None
    electricity_pct: float | None = None
    improved_sanitation_pct: float | None = None
    lpg_pct: float | None = None
    mobile_phone_pct: float | None = None
    bank_account_pct: float | None = None
    women_secondary_edu_pct: float | None = None
    female_literacy_pct: float | None = None
    male_literacy_pct: float | None = None
    wealth_index_mean: float | None = None
    urban_pct: float | None = None


class DistrictDetailOut(DistrictOut):
    demographics: list[DemographicFeatureOut] = Field(default_factory=list)


class ConstituencyDistrictOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    district_id: int
    district: str
    state: str
    assembly_segments_in_district: int | None = None
    total_assembly_segments: int | None = None
    district_segment_share: float | None = None
    source: str | None = None


class ElectionResultOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    year: int
    party: str
    alliance: str | None = None
    candidate: str | None = None
    votes: float | None = None
    vote_share: float | None = None
    rank: int | None = None
    won: bool


class ConstituencyYearSummaryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    year: int
    winner_party: str | None = None
    winner_alliance: str | None = None
    winner_vote_share: float | None = None
    runner_up_party: str | None = None
    margin_votes: float | None = None
    margin_pct: float | None = None
    turnout_pct: float | None = None


class ConstituencyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    state: str
    constituency: str
    normalized_name: str
    constituency_no: int | None = None
    reservation_status: str | None = None


class ConstituencyDetailOut(ConstituencyOut):
    districts: list[ConstituencyDistrictOut] = Field(default_factory=list)
    election_history: list[ConstituencyYearSummaryOut] = Field(default_factory=list)


class ConstituencyDemographicsOut(BaseModel):
    constituency_id: int
    constituency: str
    state: str
    demographics: DemographicFeatureOut
    method: str = "district_segment_share_weighted_average"


class ConstituencyResultsOut(BaseModel):
    constituency_id: int
    results: dict[int, list[ElectionResultOut]]


class VariableEffect(BaseModel):
    party: str
    effect_per_unit: float


class SimulationRequest(BaseModel):
    base_year: int = 2024
    party_swings: dict[str, float] = Field(default_factory=dict)
    variable_effects: dict[str, VariableEffect] = Field(default_factory=dict)


class ConstituencyProjection(BaseModel):
    constituency_id: int
    state: str
    constituency: str
    base_winner: str | None = None
    projected_winner: str | None = None
    changed: bool = False
    projected_shares: dict[str, float] = Field(default_factory=dict)


class SimulationResponse(BaseModel):
    base_year: int
    constituencies_projected: int
    seats_changed: int
    projected_seat_totals: dict[str, int]
    base_seat_totals: dict[str, int]
    sample_changes: list[ConstituencyProjection] = Field(default_factory=list)
