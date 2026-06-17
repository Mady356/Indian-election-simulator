"""
Load processed CSV files into PostgreSQL.

Run from project root:
    python backend/scripts/load_csvs_to_postgres.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
from sqlalchemy.orm import Session

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.database import Base, SessionLocal, engine  # noqa: E402
from backend.app.models import (  # noqa: E402
    Constituency,
    ConstituencyDistrict,
    ConstituencyYearSummary,
    DemographicFeature,
    District,
    ElectionResult,
)
from backend.app.utils import (  # noqa: E402
    clean_constituency_name,
    normalize_name,
    pick_column,
    row_value,
    safe_bool,
    safe_float,
    safe_int,
)

DATA = PROJECT_ROOT / "data"

PATHS = {
    "district_master": DATA / "demographics" / "processed" / "district_master_table.csv",
    "state_features": DATA / "demographics" / "processed" / "nfhs_state_features.csv",
    "ls_district_summary": DATA / "reference" / "lok_sabha_district_summary_delimitation.csv",
    "ls_district_crosswalk": DATA / "reference" / "lok_sabha_district_crosswalk_delimitation.csv",
    "ls_assembly_crosswalk": DATA / "reference" / "lok_sabha_assembly_crosswalk.csv",
    "constituency_2019": DATA / "database" / "constituency_table_2019.csv",
    "constituency_2024": DATA / "database" / "constituency_table_2024.csv",
    "results_2019": DATA / "database" / "results_table_2019.csv",
    "results_2024": DATA / "database" / "results_table_2024.csv",
    "party_alliance": DATA / "database" / "party_alliance_by_year.csv",
}

DEMO_FIELDS = [
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


def read_csv(path: Path, label: str) -> pd.DataFrame:
    if not path.exists():
        print(f"WARNING: Missing {label} CSV at {path}")
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except Exception as exc:  # noqa: BLE001
        print(f"WARNING: Could not read {label} from {path}: {exc}")
        return pd.DataFrame()


def reset_tables(session: Session) -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def load_districts(session: Session) -> dict[tuple[str, str], int]:
    df = read_csv(PATHS["district_master"], "district_master")
    district_map: dict[tuple[str, str], int] = {}
    seen: set[tuple[str, str]] = set()

    if df.empty:
        print("WARNING: No district rows loaded.")
        return district_map

    state_col = pick_column(df, ["state"])
    district_col = pick_column(df, ["district"])
    if not state_col or not district_col:
        print("WARNING: district_master missing state/district columns.")
        return district_map

    for _, row in df.iterrows():
        state = str(row[state_col]).strip()
        district = str(row[district_col]).strip()
        key = (state, district)
        if key in seen:
            continue
        seen.add(key)
        record = District(
            state=state,
            district=district,
            normalized_name=normalize_name(f"{state} {district}"),
        )
        session.add(record)
        session.flush()
        district_map[key] = record.id

    # One pseudo-row per state for state-level demographics.
    for state in sorted({key[0] for key in seen}):
        pseudo_key = (state, "__STATE__")
        if pseudo_key in district_map:
            continue
        record = District(
            state=state,
            district="__STATE__",
            normalized_name=normalize_name(f"{state} __STATE__"),
        )
        session.add(record)
        session.flush()
        district_map[pseudo_key] = record.id

    session.commit()
    return district_map


def _demo_from_row(
    row: pd.Series,
    geography_type: str,
    geography_id: int,
) -> DemographicFeature:
    return DemographicFeature(
        geography_type=geography_type,
        geography_id=geography_id,
        survey=row_value(row, ["survey"]),
        survey_year=safe_int(row_value(row, ["survey_year"])),
        fertility_rate=safe_float(row_value(row, ["fertility_rate"])),
        electricity_pct=safe_float(row_value(row, ["electricity_pct"])),
        improved_sanitation_pct=safe_float(row_value(row, ["improved_sanitation_pct"])),
        lpg_pct=safe_float(row_value(row, ["lpg_pct"])),
        mobile_phone_pct=safe_float(row_value(row, ["mobile_phone_pct"])),
        bank_account_pct=safe_float(row_value(row, ["bank_account_pct"])),
        women_secondary_edu_pct=safe_float(row_value(row, ["women_secondary_edu_pct"])),
        female_literacy_pct=safe_float(row_value(row, ["female_literacy_pct"])),
        male_literacy_pct=safe_float(row_value(row, ["male_literacy_pct"])),
        wealth_index_mean=safe_float(row_value(row, ["wealth_index_mean"])),
        urban_pct=safe_float(row_value(row, ["urban_pct"])),
    )


def load_demographics(session: Session, district_map: dict[tuple[str, str], int]) -> int:
    count = 0
    district_df = read_csv(PATHS["district_master"], "district_master")
    if not district_df.empty:
        state_col = pick_column(district_df, ["state"])
        district_col = pick_column(district_df, ["district"])
        district_id_col = pick_column(district_df, ["district_id"])
        for _, row in district_df.iterrows():
            state = str(row[state_col]).strip() if state_col else ""
            district = str(row[district_col]).strip() if district_col else ""
            geo_id = district_map.get((state, district))
            if geo_id is None and district_id_col:
                # Fallback: match by district label only within state.
                geo_id = district_map.get((state, district))
            if geo_id is None:
                continue
            session.add(_demo_from_row(row, "district", geo_id))
            count += 1

    state_df = read_csv(PATHS["state_features"], "state_features")
    if not state_df.empty:
        state_col = pick_column(state_df, ["state"])
        for _, row in state_df.iterrows():
            state = str(row[state_col]).strip() if state_col else ""
            geo_id = district_map.get((state, "__STATE__"))
            if geo_id is None:
                continue
            session.add(_demo_from_row(row, "state", geo_id))
            count += 1

    session.commit()
    return count


def _reservation_map() -> dict[tuple[str, str], tuple[int | None, str | None]]:
    df = read_csv(PATHS["ls_assembly_crosswalk"], "ls_assembly_crosswalk")
    mapping: dict[tuple[str, str], tuple[int | None, str | None]] = {}
    if df.empty:
        return mapping
    for _, row in df.iterrows():
        state = str(row_value(row, ["state"], "")).strip()
        name = clean_constituency_name(row_value(row, ["lok_sabha_constituency"], ""))
        if not state or not name:
            continue
        key = (state, normalize_name(name))
        mapping[key] = (
            safe_int(row_value(row, ["lok_sabha_no"])),
            str(row_value(row, ["reservation_status"], "") or "").strip() or None,
        )
    return mapping


def load_constituencies(session: Session) -> dict[tuple[str, str], int]:
    frames = []
    for year, path in ((2024, PATHS["constituency_2024"]), (2019, PATHS["constituency_2019"])):
        df = read_csv(path, f"constituency_{year}")
        if not df.empty:
            df = df.copy()
            df["_source_year"] = year
            frames.append(df)

    if not frames:
        print("WARNING: No constituency tables found.")
        return {}

    combined = pd.concat(frames, ignore_index=True)
    reservation_lookup = _reservation_map()
    constituency_map: dict[tuple[str, str], int] = {}
    seen: set[tuple[str, str]] = set()

    for _, row in combined.sort_values("_source_year", ascending=False).iterrows():
        state = str(row_value(row, ["state"], "")).strip()
        name = clean_constituency_name(row_value(row, ["constituency"], ""))
        if not state or not name:
            continue
        norm = normalize_name(name)
        key = (state, norm)
        if key in seen:
            continue
        seen.add(key)
        meta = reservation_lookup.get(key, (None, None))
        record = Constituency(
            state=state,
            constituency=name,
            normalized_name=norm,
            constituency_no=meta[0],
            reservation_status=meta[1],
        )
        session.add(record)
        session.flush()
        constituency_map[key] = record.id

    session.commit()
    return constituency_map


def load_constituency_districts(
    session: Session,
    district_map: dict[tuple[str, str], int],
    constituency_map: dict[tuple[str, str], int],
) -> int:
    df = read_csv(PATHS["ls_district_summary"], "ls_district_summary")
    if df.empty:
        print("WARNING: No constituency-district summary rows loaded.")
        return 0

    count = 0
    for _, row in df.iterrows():
        state = str(row_value(row, ["state"], "")).strip()
        constituency_name = clean_constituency_name(
            row_value(row, ["lok_sabha_constituency"], "")
        )
        district_name = str(row_value(row, ["district"], "")).strip()
        if not state or not constituency_name or not district_name:
            continue

        constituency_id = constituency_map.get((state, normalize_name(constituency_name)))
        district_id = district_map.get((state, district_name))
        if district_id is None:
            # Try uppercase district labels from delimitation (e.g. ADILABAD).
            for (st, dist), did in district_map.items():
                if st == state and normalize_name(dist) == normalize_name(district_name):
                    district_id = did
                    break
        if constituency_id is None or district_id is None:
            continue

        session.add(
            ConstituencyDistrict(
                constituency_id=constituency_id,
                district_id=district_id,
                assembly_segments_in_district=safe_int(
                    row_value(row, ["assembly_segments_in_district"])
                ),
                total_assembly_segments=safe_int(
                    row_value(row, ["total_assembly_segments"])
                ),
                district_segment_share=safe_float(
                    row_value(row, ["district_segment_share"])
                ),
                source="delimitation_order_2008",
            )
        )
        count += 1

    session.commit()
    return count


def _alliance_lookup() -> dict[tuple[int, str], str]:
    df = read_csv(PATHS["party_alliance"], "party_alliance")
    lookup: dict[tuple[int, str], str] = {}
    if df.empty:
        return lookup
    for _, row in df.iterrows():
        year = safe_int(row_value(row, ["election_year"]))
        party = str(row_value(row, ["party_id", "party"], "")).strip().upper()
        alliance = str(row_value(row, ["alliance", "alliance_2024", "alliance_2019"], "")).strip()
        if year and party and alliance:
            lookup[(year, party)] = alliance
    return lookup



def _resolve_constituency_id(
    row: pd.Series,
    constituency_map: dict[tuple[str, str], int],
) -> int | None:
    state = str(row_value(row, ["state"], "")).strip()
    name = clean_constituency_name(row_value(row, ["constituency"], ""))
    if state and name:
        cid = constituency_map.get((state, normalize_name(name)))
        if cid is not None:
            return cid
    external = str(row_value(row, ["constituency_id"], "")).strip()
    if external and "__" in external:
        state_part, name_part = external.split("__", 1)
        return constituency_map.get((state, normalize_name(name_part.replace("_", " ")))) or None
    return None


def load_election_results(
    session: Session,
    constituency_map: dict[tuple[str, str], int],
) -> int:
    alliances = _alliance_lookup()
    count = 0
    for year, path in ((2019, PATHS["results_2019"]), (2024, PATHS["results_2024"])):
        df = read_csv(path, f"results_{year}")
        if df.empty:
            print(f"WARNING: No election results loaded for {year}.")
            continue
        for _, row in df.iterrows():
            constituency_id = _resolve_constituency_id(row, constituency_map)
            if constituency_id is None:
                continue
            party = str(row_value(row, ["party", "party_clean"], "")).strip().upper()
            if not party:
                continue
            session.add(
                ElectionResult(
                    year=year,
                    state=str(row_value(row, ["state"], "")).strip(),
                    constituency_id=constituency_id,
                    party=party,
                    alliance=alliances.get((year, party)),
                    candidate=str(row_value(row, ["candidate", "candidate_clean"], "") or "") or None,
                    votes=safe_float(row_value(row, ["votes"])),
                    vote_share=safe_float(row_value(row, ["vote_share"])),
                    rank=safe_int(row_value(row, ["rank"])),
                    won=safe_bool(row_value(row, ["winner"], False)),
                )
            )
            count += 1
    session.commit()
    return count


def load_constituency_summaries(
    session: Session,
    constituency_map: dict[tuple[str, str], int],
) -> int:
    count = 0
    for year, path in ((2019, PATHS["constituency_2019"]), (2024, PATHS["constituency_2024"])):
        df = read_csv(path, f"constituency_summary_{year}")
        if df.empty:
            continue
        alliance_col = "alliance_2024" if year == 2024 else "alliance_2019"
        for _, row in df.iterrows():
            state = str(row_value(row, ["state"], "")).strip()
            name = clean_constituency_name(row_value(row, ["constituency"], ""))
            constituency_id = constituency_map.get((state, normalize_name(name)))
            if constituency_id is None:
                continue
            winner_party = str(row_value(row, ["winning_party"], "") or "").strip().upper() or None
            session.add(
                ConstituencyYearSummary(
                    year=year,
                    constituency_id=constituency_id,
                    winner_party=winner_party,
                    winner_alliance=str(row_value(row, [alliance_col], "") or "").strip() or None,
                    winner_vote_share=safe_float(row_value(row, ["winner_vote_share"])),
                    runner_up_party=None,
                    margin_votes=safe_float(row_value(row, ["margin_votes"])),
                    margin_pct=safe_float(row_value(row, ["top2_margin_pct", "margin_pct"])),
                    turnout_pct=None,
                )
            )
            count += 1

    session.commit()

    for year in (2019, 2024):
        summaries = (
            session.query(ConstituencyYearSummary)
            .filter(ConstituencyYearSummary.year == year)
            .all()
        )
        for summary in summaries:
            top_two = (
                session.query(ElectionResult)
                .filter(
                    ElectionResult.constituency_id == summary.constituency_id,
                    ElectionResult.year == year,
                )
                .order_by(ElectionResult.rank)
                .limit(2)
                .all()
            )
            if len(top_two) >= 2:
                summary.runner_up_party = top_two[1].party

    session.commit()
    return count


def print_counts(session: Session) -> None:
    tables = [
        ("districts", District),
        ("constituencies", Constituency),
        ("constituency_districts", ConstituencyDistrict),
        ("demographic_features", DemographicFeature),
        ("election_results", ElectionResult),
        ("constituency_year_summary", ConstituencyYearSummary),
    ]
    print("\nRows loaded:")
    for label, model in tables:
        print(f"  {label:28s}: {session.query(model).count()}")


def main() -> None:
    print("Recreating tables...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    session = SessionLocal()
    try:
        print("Loading districts...")
        district_map = load_districts(session)

        print("Loading constituencies...")
        constituency_map = load_constituencies(session)

        print("Loading demographic features...")
        demo_count = load_demographics(session, district_map)

        print("Loading constituency-district links...")
        link_count = load_constituency_districts(session, district_map, constituency_map)

        print("Loading election results...")
        result_count = load_election_results(session, constituency_map)

        print("Loading constituency year summaries...")
        summary_count = load_constituency_summaries(session, constituency_map)

        print_counts(session)
        print(
            f"\nLoader finished. demographics={demo_count}, links={link_count}, "
            f"results={result_count}, summaries={summary_count}"
        )
    finally:
        session.close()


if __name__ == "__main__":
    main()
