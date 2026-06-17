"""Aggregate constituency demographics from linked districts."""

from __future__ import annotations

from sqlalchemy.orm import Session

from backend.app.models import ConstituencyDistrict, DemographicFeature

NUMERIC_FIELDS = [
    "fertility_rate",
    "electricity_pct",
    "improved_sanitation_pct",
    "lpg_pct",
    "mobile_phone_pct",
    "bank_account_pct",
    "women_secondary_edu_pct",
    "female_literacy_pct",
    "male_literacy_pct",
    "wealth_index_mean",
    "urban_pct",
]


def aggregate_constituency_demographics(
    db: Session,
    constituency_id: int,
) -> DemographicFeature | None:
    links = (
        db.query(ConstituencyDistrict)
        .filter(ConstituencyDistrict.constituency_id == constituency_id)
        .all()
    )
    if not links:
        return None

    weighted_values: dict[str, float] = {}
    weight_total = 0.0
    survey = None
    survey_year = None

    for link in links:
        weight = link.district_segment_share or 0.0
        if weight <= 0:
            continue
        demo_rows = (
            db.query(DemographicFeature)
            .filter(
                DemographicFeature.geography_type == "district",
                DemographicFeature.geography_id == link.district_id,
            )
            .all()
        )
        if not demo_rows:
            continue
        demo = demo_rows[0]
        survey = demo.survey or survey
        survey_year = demo.survey_year or survey_year
        weight_total += weight
        for field in NUMERIC_FIELDS:
            value = getattr(demo, field)
            if value is None:
                continue
            weighted_values[field] = weighted_values.get(field, 0.0) + float(value) * weight

    if weight_total <= 0:
        return None

    aggregated = DemographicFeature(
        geography_type="constituency",
        geography_id=constituency_id,
        survey=survey,
        survey_year=survey_year,
    )
    for field in NUMERIC_FIELDS:
        if field in weighted_values:
            setattr(aggregated, field, weighted_values[field] / weight_total)
    return aggregated
