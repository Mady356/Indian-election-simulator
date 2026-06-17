"""
2014 Andhra Pradesh / Telangana bifurcation helpers.

The 2008 delimitation order lists Telangana districts under schedule
"Andhra Pradesh". Census 2011 and NFHS-4 use undivided AP labels; NFHS-5
reports Telangana separately.
"""

from __future__ import annotations

from src.reference.delimitation_utils import normalize_key

# Census 2011 districts that became Telangana (were ANDHRA PRADESH in 2011).
TELANGANA_CENSUS_2011_DISTRICTS: frozenset[str] = frozenset(
    normalize_key(name)
    for name in (
        "ADILABAD",
        "HYDERABAD",
        "KARIMNAGAR",
        "KHAMMAM",
        "MAHBUBNAGAR",
        "MEDAK",
        "NALGONDA",
        "NIZAMABAD",
        "RANGAREDDY",
        "WARANGAL",
    )
)

# Delimitation Table A district labels under "Andhra Pradesh" that are Telangana.
AP_DELIMITATION_TELANGANA_DISTRICT_KEYS: frozenset[str] = frozenset(
    normalize_key(name)
    for name in (
        "ADILABAD",
        "HYDERABAD",
        "KARIMNAGAR",
        "MAHBUBNAGAR",
        "MEDAK",
        "NIZAMABAD",
        "RANGAREDDI",
    )
)

# Census / delimitation key → NFHS-5 Telangana microdata spelling.
TELANGANA_NFHS5_DISTRICT_NAMES: dict[str, str] = {
    "RANGAREDDY": "Ranga Reddy",
    "RANGAREDDI": "Ranga Reddy",
}

# Align NFHS-5 district keys with census / NFHS-4 keys for change pairing.
TELANGANA_PAIR_DISTRICT_KEYS: dict[str, str] = {
    "RANGA REDDY": "RANGAREDDY",
}

NFHS4_STATE_UNDIVIDED_AP = "Andhra Pradesh"
NFHS5_STATE_TELANGANA = "Telangana"


def pair_district_key(district_key: str) -> str:
    return TELANGANA_PAIR_DISTRICT_KEYS.get(district_key, district_key)


def pair_state_key(state: str, survey: str, district_key: str) -> str:
    """State key for pairing NFHS-4 and NFHS-5 rows across the 2014 bifurcation."""
    canonical_district = pair_district_key(district_key)
    if canonical_district in TELANGANA_CENSUS_2011_DISTRICTS:
        return normalize_key(NFHS5_STATE_TELANGANA)
    if survey == "NFHS-4" and state in ("Andhra Pradesh", "ANDHRA PRADESH"):
        return normalize_key(state)
    return normalize_key(state)


def is_telangana_census_district(census_state: str, census_district: str) -> bool:
    return (
        census_state.strip().upper() == "ANDHRA PRADESH"
        and normalize_key(census_district) in TELANGANA_CENSUS_2011_DISTRICTS
    )


def is_ap_delimitation_telangana_district(delim_state: str, delim_district: str) -> bool:
    return (
        delim_state.strip() == "Andhra Pradesh"
        and normalize_key(delim_district) in AP_DELIMITATION_TELANGANA_DISTRICT_KEYS
    )


def nfhs5_district_name(census_district: str) -> str | None:
    key = normalize_key(census_district)
    return TELANGANA_NFHS5_DISTRICT_NAMES.get(key)


def nfhs_state_for_survey(
    census_state: str,
    census_district: str,
    survey: str,
    *,
    default_nfhs5_state: str,
) -> str:
    """Return NFHS panel state label appropriate for the survey round."""
    if is_telangana_census_district(census_state, census_district):
        if survey == "NFHS-4":
            return NFHS4_STATE_UNDIVIDED_AP
        if survey == "NFHS-5":
            return NFHS5_STATE_TELANGANA
    return default_nfhs5_state
