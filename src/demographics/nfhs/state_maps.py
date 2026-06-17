"""Shared NFHS state name mappings (no pandas imports)."""

from __future__ import annotations

import re

NFHS4_TO_CENSUS_STATE: dict[str, str] = {
    "Andhra Pradesh": "ANDHRA PRADESH",
    "Arunachalpradesh": "ARUNACHAL PRADESH",
    "Assam": "ASSAM",
    "Bihar": "BIHAR",
    "Goa": "GOA",
    "Gujarat": "GUJARAT",
    "Haryana": "HARYANA",
    "Himachal Pradesh": "HIMACHAL PRADESH",
    "Jammu": "JAMMU & KASHMIR",
    "Karnataka": "KARNATAKA",
    "Kerala": "KERALA",
    "Madhya Pradesh": "MADHYA PRADESH",
    "Maharashtra": "MAHARASHTRA",
    "Manipur": "MANIPUR",
    "Meghalaya": "MEGHALAYA",
    "Mizoram": "MIZORAM",
    "Nagaland": "NAGALAND",
    "New Delhi": "NCT OF DELHI",
    "Delhi": "NCT OF DELHI",
    "Orissa": "ODISHA",
    "Punjab": "PUNJAB",
    "Rajasthan": "RAJASTHAN",
    "Sikkim": "SIKKIM",
    "Tamil Nadu": "TAMIL NADU",
    "Tripura": "TRIPURA",
    "Uttar Pradesh": "UTTAR PRADESH",
    "West Bengal": "WEST BENGAL",
}

NFHS4_TO_NFHS5_STATE: dict[str, str] = {
    "Arunachalpradesh": "Arunachal Pradesh",
    "Jammu": "Jammu & Kashmir",
    "New Delhi": "Delhi",
    "Delhi": "Delhi",
    "Orissa": "Odisha",
}


def normalize_key(value: object) -> str:
    if value is None:
        return ""
    text = str(value).strip().upper()
    text = text.replace("&", " AND ")
    text = re.sub(r"[–—\-/]", " ", text)
    text = re.sub(r"[^A-Z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def nfhs5_state_label(nfhs4_state: str) -> str:
    return NFHS4_TO_NFHS5_STATE.get(nfhs4_state, nfhs4_state)
