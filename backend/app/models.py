"""SQLAlchemy ORM models."""

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.database import Base


class District(Base):
    __tablename__ = "districts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    state: Mapped[str] = mapped_column(String(128), index=True)
    district: Mapped[str] = mapped_column(String(256))
    normalized_name: Mapped[str] = mapped_column(String(512), index=True)

    demographic_features: Mapped[list["DemographicFeature"]] = relationship(
        back_populates="district",
        foreign_keys="DemographicFeature.geography_id",
        primaryjoin="and_(District.id==DemographicFeature.geography_id, "
        "DemographicFeature.geography_type=='district')",
        viewonly=True,
    )
    constituency_links: Mapped[list["ConstituencyDistrict"]] = relationship(
        back_populates="district"
    )


class Constituency(Base):
    __tablename__ = "constituencies"
    __table_args__ = (UniqueConstraint("state", "normalized_name", name="uq_state_constituency"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    state: Mapped[str] = mapped_column(String(128), index=True)
    constituency: Mapped[str] = mapped_column(String(256))
    normalized_name: Mapped[str] = mapped_column(String(512), index=True)
    constituency_no: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reservation_status: Mapped[str | None] = mapped_column(String(16), nullable=True)

    district_links: Mapped[list["ConstituencyDistrict"]] = relationship(
        back_populates="constituency"
    )
    election_results: Mapped[list["ElectionResult"]] = relationship(
        back_populates="constituency"
    )
    year_summaries: Mapped[list["ConstituencyYearSummary"]] = relationship(
        back_populates="constituency"
    )


class ConstituencyDistrict(Base):
    __tablename__ = "constituency_districts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    constituency_id: Mapped[int] = mapped_column(ForeignKey("constituencies.id"), index=True)
    district_id: Mapped[int] = mapped_column(ForeignKey("districts.id"), index=True)
    assembly_segments_in_district: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_assembly_segments: Mapped[int | None] = mapped_column(Integer, nullable=True)
    district_segment_share: Mapped[float | None] = mapped_column(Float, nullable=True)
    source: Mapped[str | None] = mapped_column(String(128), nullable=True)

    constituency: Mapped["Constituency"] = relationship(back_populates="district_links")
    district: Mapped["District"] = relationship(back_populates="constituency_links")


class DemographicFeature(Base):
    __tablename__ = "demographic_features"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    geography_type: Mapped[str] = mapped_column(String(32), index=True)
    geography_id: Mapped[int] = mapped_column(Integer, index=True)
    survey: Mapped[str | None] = mapped_column(String(64), nullable=True)
    survey_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fertility_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    electricity_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    improved_sanitation_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    lpg_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    mobile_phone_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    bank_account_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    women_secondary_edu_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    female_literacy_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    male_literacy_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    wealth_index_mean: Mapped[float | None] = mapped_column(Float, nullable=True)
    urban_pct: Mapped[float | None] = mapped_column(Float, nullable=True)

    district: Mapped["District | None"] = relationship(
        back_populates="demographic_features",
        foreign_keys=[geography_id],
        primaryjoin="and_(District.id==DemographicFeature.geography_id, "
        "DemographicFeature.geography_type=='district')",
        viewonly=True,
    )


class ElectionResult(Base):
    __tablename__ = "election_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    year: Mapped[int] = mapped_column(Integer, index=True)
    state: Mapped[str] = mapped_column(String(128), index=True)
    constituency_id: Mapped[int] = mapped_column(ForeignKey("constituencies.id"), index=True)
    party: Mapped[str] = mapped_column(String(64), index=True)
    alliance: Mapped[str | None] = mapped_column(String(64), nullable=True)
    candidate: Mapped[str | None] = mapped_column(String(256), nullable=True)
    votes: Mapped[float | None] = mapped_column(Float, nullable=True)
    vote_share: Mapped[float | None] = mapped_column(Float, nullable=True)
    rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    won: Mapped[bool] = mapped_column(Boolean, default=False)

    constituency: Mapped["Constituency"] = relationship(back_populates="election_results")


class ConstituencyYearSummary(Base):
    __tablename__ = "constituency_year_summary"
    __table_args__ = (
        UniqueConstraint("year", "constituency_id", name="uq_year_constituency_summary"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    year: Mapped[int] = mapped_column(Integer, index=True)
    constituency_id: Mapped[int] = mapped_column(ForeignKey("constituencies.id"), index=True)
    winner_party: Mapped[str | None] = mapped_column(String(64), nullable=True)
    winner_alliance: Mapped[str | None] = mapped_column(String(64), nullable=True)
    winner_vote_share: Mapped[float | None] = mapped_column(Float, nullable=True)
    runner_up_party: Mapped[str | None] = mapped_column(String(64), nullable=True)
    margin_votes: Mapped[float | None] = mapped_column(Float, nullable=True)
    margin_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    turnout_pct: Mapped[float | None] = mapped_column(Float, nullable=True)

    constituency: Mapped["Constituency"] = relationship(back_populates="year_summaries")
