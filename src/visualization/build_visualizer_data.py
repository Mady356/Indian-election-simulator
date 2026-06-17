"""
Build the static data bundle used by the local visualizer.

Run as:
    venv/bin/python -m src.visualization.build_visualizer_data

Writes:
    visualizer/data/election_demographics_bundle.json

The bundle is intentionally relational:
    states -> districts
    states -> state_party_swings
    states -> constituencies

No map boundary geometry is invented here. If real state/district GeoJSON files
are added later, the visualizer can join them by state/district names.
"""

from __future__ import annotations

import json
import math
import re
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
OUTPUTS_DIR = ROOT / "data" / "outputs"
DEMOGRAPHICS_PROCESSED_DIR = ROOT / "data" / "demographics" / "processed"
VISUALIZER_DATA_DIR = ROOT / "visualizer" / "data"
OUT_PATH = VISUALIZER_DATA_DIR / "election_demographics_bundle.json"


STATE_ANALYSIS_PATH = OUTPUTS_DIR / "state_election_demographic_analysis.csv"
STATE_PARTY_PATH = OUTPUTS_DIR / "state_party_swing_analysis.csv"
DISTRICT_PATH = DEMOGRAPHICS_PROCESSED_DIR / "census_district_demographics_2011.csv"
STATE_FROM_DISTRICTS_PATH = DEMOGRAPHICS_PROCESSED_DIR / "census_state_from_districts_2011.csv"
CONSTITUENCY_VOLATILITY_PATH = OUTPUTS_DIR / "constituency_volatility_2019_2024.csv"


STATE_GRID_POSITIONS = {
    "JAMMU AND KASHMIR": (1, 4),
    "LADAKH": (1, 5),
    "HIMACHAL PRADESH": (2, 4),
    "PUNJAB": (3, 3),
    "CHANDIGARH": (3, 4),
    "UTTARAKHAND": (3, 5),
    "HARYANA": (4, 3),
    "NCT OF DELHI": (4, 4),
    "RAJASTHAN": (5, 2),
    "UTTAR PRADESH": (5, 5),
    "BIHAR": (5, 7),
    "SIKKIM": (4, 8),
    "ARUNACHAL PRADESH": (4, 10),
    "ASSAM": (5, 9),
    "NAGALAND": (5, 10),
    "MEGHALAYA": (6, 8),
    "MANIPUR": (6, 10),
    "TRIPURA": (7, 9),
    "MIZORAM": (7, 10),
    "GUJARAT": (6, 2),
    "MADHYA PRADESH": (6, 4),
    "JHARKHAND": (6, 7),
    "WEST BENGAL": (6, 8),
    "DADRA AND NAGAR HAVELI AND DAMAN AND DIU": (7, 1),
    "MAHARASHTRA": (7, 4),
    "CHHATTISGARH": (7, 6),
    "ODISHA": (7, 7),
    "GOA": (8, 3),
    "TELANGANA": (8, 5),
    "ANDHRA PRADESH": (9, 6),
    "KARNATAKA": (9, 4),
    "TAMIL NADU": (10, 5),
    "KERALA": (10, 4),
    "PUDUCHERRY": (10, 6),
    "LAKSHADWEEP": (9, 2),
    "ANDAMAN AND NICOBAR ISLANDS": (10, 8),
}


FIELD_GROUPS = {
    "election": [
        "seats",
        "seat_flips",
        "flip_rate",
        "alliance_flips",
        "alliance_flip_rate",
        "close_seats_5pct",
        "close_seat_rate_5pct",
        "avg_top2_margin_pct",
        "avg_effective_num_parties",
        "avg_volatility_score",
        "bjp_seat_change",
        "bjp_avg_swing",
        "inc_seat_change",
        "inc_avg_swing",
    ],
    "demographic": [
        "population_total",
        "urban_pct",
        "rural_pct",
        "sc_pct",
        "st_pct",
        "sex_ratio",
        "literacy_rate",
        "male_literacy",
        "female_literacy",
        "hindu_pct",
        "muslim_pct",
        "christian_pct",
        "sikh_pct",
        "buddhist_pct",
        "jain_pct",
        "youth_pct",
        "working_age_pct",
        "elderly_pct",
    ],
    "district": [
        "population_total",
        "urban_pct",
        "rural_pct",
        "sc_pct",
        "st_pct",
        "sex_ratio",
        "literacy_rate",
        "female_literacy",
        "child_0_6_pct",
        "worker_pct",
        "main_worker_pct",
        "marginal_worker_pct",
    ],
}


FIELD_LABELS = {
    "population_total": "Population",
    "urban_pct": "Urban %",
    "rural_pct": "Rural %",
    "sc_pct": "SC %",
    "st_pct": "ST %",
    "sex_ratio": "Sex ratio",
    "literacy_rate": "Literacy %",
    "male_literacy": "Male literacy %",
    "female_literacy": "Female literacy %",
    "child_0_6_pct": "Age 0-6 %",
    "worker_pct": "Worker %",
    "main_worker_pct": "Main worker %",
    "marginal_worker_pct": "Marginal worker %",
    "flip_rate": "Seat flip rate %",
    "seat_flips": "Seat flips",
    "alliance_flip_rate": "Alliance flip rate %",
    "close_seat_rate_5pct": "Close seat rate %",
    "avg_top2_margin_pct": "Avg top-2 margin %",
    "avg_effective_num_parties": "Avg effective parties",
    "avg_volatility_score": "Avg volatility",
    "bjp_avg_swing": "BJP avg swing",
    "inc_avg_swing": "INC avg swing",
    "bjp_seat_change": "BJP seat change",
    "inc_seat_change": "INC seat change",
}


STATE_NAME_ALIASES = {
    "JAMMU & KASHMIR": "JAMMU AND KASHMIR",
    "DADRA & NAGAR HAVELI": "DADRA AND NAGAR HAVELI",
    "DAMAN & DIU": "DAMAN AND DIU",
    "DADRA & NAGAR HAVELI AND DAMAN & DIU": "DADRA AND NAGAR HAVELI AND DAMAN AND DIU",
}


def clean_json_value(value):
    if pd.isna(value):
        return None
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if hasattr(value, "item"):
        return value.item()
    return value


def records(df: pd.DataFrame) -> list[dict]:
    out = []
    for row in df.to_dict(orient="records"):
        out.append({k: clean_json_value(v) for k, v in row.items()})
    return out


def name_key(value: object) -> str:
    if pd.isna(value):
        return ""
    name = str(value).strip().upper()
    name = name.replace("&", "AND")
    name = re.sub(r"\s+", " ", name)
    return STATE_NAME_ALIASES.get(name, name)


def canonical_state_for_district(state_2011: str, district: str) -> str:
    state_key = name_key(state_2011)
    district_key = name_key(district)

    telangana = {
        "ADILABAD",
        "NIZAMABAD",
        "KARIMNAGAR",
        "MEDAK",
        "HYDERABAD",
        "RANGAREDDY",
        "MAHBUBNAGAR",
        "NALGONDA",
        "WARANGAL",
        "KHAMMAM",
    }
    ladakh = {"LEH(LADAKH)", "KARGIL"}

    if state_key == "ANDHRA PRADESH" and district_key in telangana:
        return "TELANGANA"
    if state_key == "JAMMU AND KASHMIR" and district_key in ladakh:
        return "LADAKH"
    if state_key == "JAMMU AND KASHMIR":
        return "JAMMU AND KASHMIR"
    return state_key


def add_state_grid(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["state_key"] = out["state"].map(name_key)
    out["grid_row"] = out["state_key"].map(lambda k: STATE_GRID_POSITIONS.get(k, (None, None))[0])
    out["grid_col"] = out["state_key"].map(lambda k: STATE_GRID_POSITIONS.get(k, (None, None))[1])
    return out


def build_field_catalog(bundle_tables: dict[str, pd.DataFrame]) -> list[dict]:
    catalog = []
    for group, fields in FIELD_GROUPS.items():
        table_name = "states" if group in {"election", "demographic"} else "districts"
        df = bundle_tables[table_name]
        for field in fields:
            if field not in df.columns:
                continue
            non_null = int(df[field].notna().sum())
            catalog.append(
                {
                    "field": field,
                    "label": FIELD_LABELS.get(field, field.replace("_", " ").title()),
                    "group": group,
                    "table": table_name,
                    "available_rows": non_null,
                    "total_rows": int(len(df)),
                }
            )
    return catalog


def main() -> None:
    states = pd.read_csv(STATE_ANALYSIS_PATH)
    state_party = pd.read_csv(STATE_PARTY_PATH)
    districts = pd.read_csv(DISTRICT_PATH)
    state_from_districts = pd.read_csv(STATE_FROM_DISTRICTS_PATH)
    constituencies = pd.read_csv(CONSTITUENCY_VOLATILITY_PATH)

    states = add_state_grid(states)

    districts = districts.copy()
    districts["state_key"] = districts.apply(
        lambda r: canonical_state_for_district(r["state_2011"], r["district"]),
        axis=1,
    )
    state_key_to_name = states.set_index("state_key")["state"].to_dict()
    districts["state"] = districts["state_key"].map(state_key_to_name).fillna(districts["state_2011"])

    state_party = state_party.copy()
    state_party["state_key"] = state_party["state"].map(name_key)

    constituencies = constituencies.copy()
    constituencies["state_key"] = constituencies["state"].map(name_key)

    tables = {
        "states": states,
        "districts": districts,
        "state_party_swings": state_party,
        "constituencies": constituencies,
        "state_from_districts": state_from_districts,
    }

    bundle = {
        "meta": {
            "title": "India Election + Demographics Visualizer",
            "generated_from": [
                str(STATE_ANALYSIS_PATH.relative_to(ROOT)),
                str(STATE_PARTY_PATH.relative_to(ROOT)),
                str(DISTRICT_PATH.relative_to(ROOT)),
                str(CONSTITUENCY_VOLATILITY_PATH.relative_to(ROOT)),
            ],
            "notes": [
                "District rows are Census 2011 PCA-derived demographics.",
                "Election rows are Lok Sabha 2019-2024 comparison outputs.",
                "No geographic boundary geometry is included yet; the app uses a state grid and district drilldown tables.",
            ],
        },
        "fields": build_field_catalog(tables),
        "states": records(states),
        "districts": records(districts),
        "state_party_swings": records(state_party),
        "constituencies": records(constituencies),
        "state_from_districts": records(state_from_districts),
    }

    VISUALIZER_DATA_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(bundle, indent=2), encoding="utf-8")
    print(f"Saved visualizer data bundle: {OUT_PATH}")
    print(f"  states              : {len(states)}")
    print(f"  districts           : {len(districts)}")
    print(f"  state_party_swings  : {len(state_party)}")
    print(f"  constituencies      : {len(constituencies)}")


if __name__ == "__main__":
    main()
