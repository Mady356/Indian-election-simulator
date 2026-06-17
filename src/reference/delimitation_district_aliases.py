"""
Delimitation district name → Census 2011 / NFHS district aliases.

Used when lok_sabha_district_summary_delimitation.csv district labels differ
from census or NFHS spellings (e.g. RANGAREDDI → RANGAREDDY).
"""

from __future__ import annotations

import re
from difflib import SequenceMatcher

import pandas as pd

from src.reference.ap_telangana_bifurcation import (
    NFHS4_STATE_UNDIVIDED_AP,
    NFHS5_STATE_TELANGANA,
    is_telangana_census_district,
    nfhs5_district_name,
)
from src.reference.delimitation_utils import normalize_key

# Delimitation schedule state label → Census 2011 state_2011
DELIMITATION_TO_CENSUS_STATE: dict[str, str] = {
    "Andhra Pradesh": "ANDHRA PRADESH",
    "Arunachal Pradesh": "ARUNACHAL PRADESH",
    "Assam": "ASSAM",
    "Bihar": "BIHAR",
    "Chhattisgarh": "CHHATTISGARH",
    "Delhi": "NCT OF DELHI",
    "Goa": "GOA",
    "Gujarat": "GUJARAT",
    "Haryana": "HARYANA",
    "Jharkhand": "JHARKHAND",
    "Karnataka": "KARNATAKA",
    "Kerala": "KERALA",
    "Madhya Pradesh": "MADHYA PRADESH",
    "Maharashtra": "MAHARASHTRA",
    "Meghalaya": "MEGHALAYA",
    "Orissa": "ODISHA",
    "Punjab": "PUNJAB",
    "Rajasthan": "RAJASTHAN",
    "Tripura": "TRIPURA",
    "Tamil Nadu": "TAMIL NADU",
    "Uttar Pradesh": "UTTAR PRADESH",
    "Uttarakhand": "UTTARAKHAND",
    "West Bengal": "WEST BENGAL",
}

# Census state → common NFHS-5 state label
CENSUS_TO_NFHS5_STATE: dict[str, str] = {
    "NCT OF DELHI": "Delhi",
    "ODISHA": "Odisha",
    "JAMMU & KASHMIR": "Jammu & Kashmir",
    "ANDAMAN & NICOBAR ISLANDS": "Andaman & Nicobar Islands",
    "DADRA & NAGAR HAVELI": "Dadra & Nagar Haveli",
    "DAMAN & DIU": "Daman & Diu",
}

# Normalized delimitation district key → normalized census district key
DISTRICT_KEY_ALIASES: dict[str, str] = {
    "RANGAREDDI": "RANGAREDDY",
    "JAHANABAD": "JEHANABAD",
    "PASCHIM CHAMPARAN": "PASHCHIM CHAMPARAN",
    "PURVI CHAMPARAN": "PURBA CHAMPARAN",
    "HOOGHLY": "HUGLI",
    "BARDHAMAN": "BARDDHAMAN",
    "NORTH 24 PARGANAS": "NORTH TWENTY FOUR PARGANAS",
    "SOUTH 24 PARGANAS": "SOUTH TWENTY FOUR PARGANAS",
    "COOCHBEHAR": "KOCH BIHAR",
    "DARJEELING": "DARJILING",
    "PURBO MEDINIPUR": "PURBA MEDINIPUR",
    "PASCHIM MEDINIPUR": "PASCHIM MEDINIPUR",
    "BALASORE": "BALESHWAR",
    "KEONJHAR": "KENDUJHAR",
    "PHULBANI": "KANDHAMAL",
    "NAWAPARA": "NUAPADA",
    "SONEPUR": "SUBARNAPUR",
    "KORIA": "KORIYA",
    "DANGS": "THE DANGS",
    "PANCHMAHALS": "PANCH MAHAL",
    "PANCH MAHALS": "PANCH MAHAL",
    "AHMEDABAD": "AHMADABAD",
    "PALAMAU": "PALAMU",
    "EAST SINGHBHUM": "PURBI SINGHBHUM",
    "WEST SINGHBHUM": "PASCHIMI SINGHBHUM",
    "WEST SINGHBHUM": "PASCHIMI SINGHBHUM",
    "UDHAMSINGH NAGAR": "UDHAM SINGH NAGAR",
    "JAGATSINGHPUR": "JAGATSINGHAPUR",
    "SABARKANTHA": "SABAR KANTHA",
    "CHICKMAGALUR": "CHIKMAGALUR",
    "NABARANGPUR": "NABARANGAPUR",
    "BULANDSHAHAR": "BULANDSHAHR",
    "ASHOK NAGAR": "ASHOKNAGAR",
    "KUSHI NAGAR": "KUSHINAGAR",
    "PURULIA": "PURULIYA",
    "MALDAHA": "MALDAH",
    "JAJPUR": "JAJAPUR",
    "PAKAUR": "PAKUR",
    "ANGUL": "ANUGUL",
    "SAHEBGANJ": "SAHIBGANJ",
    "MANDSOUR": "MANDSAUR",
    "BOLANGIR": "BALANGIR",
    "CHITTORGARH": "CHITTAURGARH",
    "BADWANI": "BARWANI",
    "KABIRDHAM": "KABEERDHAM",
    "SANT RAVIDAS NAGAR": "SANT RAVIDAS NAGAR BHADOHI",
    "BOUDH": "BAUDH",
    "DEOGARH": "DEBAGARH",
    "CUTTACK": "CUTTACK",
    "KHURDA": "KHORDHA",
    "NORTH SINGHBHUM": "PURBI SINGHBHUM",
    "SOUTH SINGHBHUM": "PASCHIMI SINGHBHUM",
    "HOWRAH": "HAORA",
    "BURDWAN": "BARDDHAMAN",
    "BARDHAMAN": "BARDDHAMAN",
    "MIDNAPORE": "PASCHIM MEDINIPUR",
    "MEDINIPUR": "PASCHIM MEDINIPUR",
    "NOWGONG": "NAGAON",
    "SIBSAGAR": "SIVASAGAR",
    "GAUHATI": "KAMRUP METROPOLITAN",
    "KAMRUP": "KAMRUP METROPOLITAN",
    "NORTH CACHAR HILLS": "DIMA HASAO",
    "MIKIR HILLS": "KARBI ANGLONG",
    "DARRANG": "SONITPUR",
    "DAHOD": "DOHAD",
    "DANG": "THE DANGS",
    "NARSINGPUR": "NARSIMHAPUR",
    "WEST NIMAR KHAORGONE": "KHARGONE WEST NIMAR",
    "EAST NIMAR KHANDWA": "KHANDWA EAST NIMAR",
    "RAIGAD": "RAIGARH",
    "MUMBAI CITY": "MUMBAI",
    "NAWAN SHAHR": "SHAHID BHAGAT SINGH NAGAR",
    "KAIMUR BHABUA": "KAIMUR BHABUA",
    "DAKSHIN BASTAR DANTEWADA": "DAKSHIN BASTAR DANTEWADA",
    "UTTAR BASTAR KANKER": "UTTAR BASTAR KANKER",
    "EAST SINGHBHUM": "PURBI SINGHBHUM",
}

FUZZY_HIGH = 0.92
FUZZY_MEDIUM = 0.85

NCT_PLACEHOLDER_DISTRICTS = {"DELHI"}


def census_state_for_delimitation(delim_state: str) -> str:
    return DELIMITATION_TO_CENSUS_STATE.get(delim_state.strip(), delim_state.strip().upper())


def nfhs5_state_for_census(census_state: str, census_district: str | None = None) -> str:
    if census_district and is_telangana_census_district(census_state, census_district):
        return NFHS5_STATE_TELANGANA
    return CENSUS_TO_NFHS5_STATE.get(census_state.strip().upper(), census_state.strip().title())


def nfhs4_state_for_census(census_state: str, census_district: str | None = None) -> str:
    if census_district and is_telangana_census_district(census_state, census_district):
        return NFHS4_STATE_UNDIVIDED_AP
    return nfhs5_state_for_census(census_state, census_district)


def canonical_district_key(district: str) -> str:
    text = str(district).strip().upper()
    # Expand parenthetical text: "KAIMUR (BHABUA)" → "KAIMUR BHABUA"
    text = re.sub(r"\(([^)]*)\)", r" \1 ", text)
    key = normalize_key(text)
    return DISTRICT_KEY_ALIASES.get(key, key)


def fuzzy_best_match(query_key: str, candidates: dict[str, str]) -> tuple[str | None, float]:
    if not query_key or not candidates:
        return None, 0.0
    if query_key in candidates:
        return candidates[query_key], 1.0

    best_key: str | None = None
    best_score = 0.0
    for cand_key in candidates:
        score = SequenceMatcher(None, query_key, cand_key).ratio()
        if score > best_score:
            best_score = score
            best_key = cand_key
    if best_key is None:
        return None, 0.0
    return candidates[best_key], best_score


def confidence_from_score(method: str, score: float) -> str:
    if method == "nct_expansion":
        return "high"
    if method == "exact" or score >= FUZZY_HIGH:
        return "high"
    if score >= FUZZY_MEDIUM or method in {"alias", "census_rank_nfhs5"}:
        return "medium"
    return "low"


def resolve_nfhs_district_name(
    nfhs_districts: pd.DataFrame,
    census_state: str,
    census_district: str,
    nfhs_state: str | None = None,
) -> str:
    """Map census district label to NFHS district label when spelling differs."""
    if nfhs_state is None:
        nfhs_state = nfhs5_state_for_census(census_state, census_district)
    telangana_name = nfhs5_district_name(census_district)
    if telangana_name and nfhs_state == NFHS5_STATE_TELANGANA:
        return telangana_name
    sub = nfhs_districts[
        (nfhs_districts["state"].astype(str).str.strip() == nfhs_state)
        | (nfhs_districts["state_key"] == normalize_key(nfhs_state))
    ]
    if sub.empty:
        return census_district.title()

    census_key = normalize_key(census_district)
    for _, row in sub.iterrows():
        if row["district_key"] == census_key:
            return str(row["district"])
    name, score = fuzzy_best_match(census_key, {r["district_key"]: r["district"] for _, r in sub.iterrows()})
    if name and score >= FUZZY_HIGH:
        return name
    return str(census_district).strip().title()
