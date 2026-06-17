"""
Parse DHS Program distribution filenames ([CC][DD][VV][FF].ZIP).

Reference: https://www.dhsprogram.com/data/File-Types-and-Names.cfm
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

# India national + subnational codes from the DHS Program India state table.
INDIA_GEO_CODES: dict[str, str] = {
    "IA": "India (national)",
    "AP": "Andhra Pradesh",
    "AR": "Arunachal Pradesh",
    "AS": "Assam",
    "BH": "Bihar",
    "DL": "Delhi",
    "GJ": "Gujarat",
    "GO": "Goa",
    "HP": "Himachal Pradesh",
    "HR": "Haryana",
    "JM": "Jammu",
    "KA": "Karnataka",
    "KE": "Kerala",
    "MG": "Meghalaya",
    "MH": "Maharashtra",
    "MN": "Manipur",
    "MP": "Madhya Pradesh",
    "MZ": "Mizoram",
    "NA": "Nagaland",
    "OR": "Odisha",
    "PJ": "Punjab",
    "RJ": "Rajasthan",
    "SK": "Sikkim",
    "TN": "Tamil Nadu",
    "TR": "Tripura",
    "UP": "Uttar Pradesh",
    "WB": "West Bengal",
}

DATASET_TYPES: dict[str, str] = {
    "AI": "Accidents and Injuries Recode",
    "BR": "Births Recode",
    "CR": "Couples Recode",
    "GR": "Pregnancies Recode",
    "HR": "Household Recode",
    "IR": "Individual (Women) Recode",
    "KR": "Children Recode",
    "MR": "Men Recode",
    "NR": "Pregnancy and Postnatal Care Recode",
    "PR": "Household Member Recode",
    "SR": "Siblings Recode",
    "XR": "Child Under 5 Recode",
    "AR": "HIV Test Results Recode",
    "GE": "Geographic Data",
    "WI": "Wealth Index",
}

FILE_FORMATS: dict[str, str] = {
    "FL": "Flat (ASCII/Stata .dta)",
    "SV": "SPSS",
    "SD": "SAS",
    "DT": "Stata",
    "GE": "Geographic",
    "BC": "Biomarker",
}

# Common India NFHS version codes seen in this project.
INDIA_NFHS_VERSIONS: dict[str, str] = {
    "22": "NFHS-2 (1998-99)",
    "23": "NFHS-3 (2005-06)",
    "41": "NFHS-1 / early DHS-IV release",
    "42": "NFHS-4 (2015-16)",
    "52": "NFHS-5 (2019-21)",
    "71": "DHS Phase VII release 1",
    "74": "DHS Phase VII (likely NFHS-6+)",
    "7A": "DHS Phase VII release A",
    "7E": "DHS Phase VII release E",
}

_DHS_STEM_RE = re.compile(
    r"^([A-Z]{2})([A-Z]{2})([0-9A-Z]{2})([A-Z]{2})$"
)


@dataclass(frozen=True)
class DhsFilenameInfo:
    filename: str
    geo_code: str
    state: str
    dataset_type_code: str
    dataset_type: str
    version_code: str
    survey: str
    file_format_code: str
    file_format: str
    parse_ok: bool
    parse_note: str


def _describe_dhs_phase(version_code: str) -> str:
    if len(version_code) != 2:
        return f"DHS version {version_code}"
    phase_char, release_char = version_code[0], version_code[1]
    if phase_char.isdigit():
        phase_names = {
            "2": "DHS-II",
            "3": "DHS-III",
            "4": "DHS-IV",
            "5": "DHS-V",
            "6": "DHS-VI",
            "7": "DHS-VII",
            "8": "DHS-VIII",
        }
        phase = phase_names.get(phase_char, f"DHS phase {phase_char}")
        return f"{phase} release {release_char}"
    return f"DHS version {version_code}"


def describe_survey(geo_code: str, version_code: str) -> str:
    """Human-readable survey label for India NFHS/DHS files."""
    if geo_code in INDIA_GEO_CODES:
        if version_code in INDIA_NFHS_VERSIONS:
            return INDIA_NFHS_VERSIONS[version_code]
        return _describe_dhs_phase(version_code)
    return _describe_dhs_phase(version_code)


def parse_dhs_filename(filename: str) -> DhsFilenameInfo:
    """
    Parse a DHS distribution zip basename such as ``APHR42FL.zip``.

    Returns structured fields even when parsing fails (``parse_ok=False``).
    """
    stem = Path(filename).stem.upper()
    match = _DHS_STEM_RE.match(stem)
    if not match:
        return DhsFilenameInfo(
            filename=filename,
            geo_code="",
            state="",
            dataset_type_code="",
            dataset_type="",
            version_code="",
            survey="",
            file_format_code="",
            file_format="",
            parse_ok=False,
            parse_note=f"Does not match DHS pattern [CC][DD][VV][FF]: {stem}",
        )

    geo_code, dataset_type_code, version_code, file_format_code = match.groups()

    if dataset_type_code not in DATASET_TYPES:
        return DhsFilenameInfo(
            filename=filename,
            geo_code=geo_code,
            state=INDIA_GEO_CODES.get(geo_code, geo_code),
            dataset_type_code=dataset_type_code,
            dataset_type="",
            version_code=version_code,
            survey=describe_survey(geo_code, version_code),
            file_format_code=file_format_code,
            file_format=FILE_FORMATS.get(file_format_code, file_format_code),
            parse_ok=False,
            parse_note=f"Unknown dataset type code: {dataset_type_code}",
        )

    state = INDIA_GEO_CODES.get(geo_code, geo_code)
    return DhsFilenameInfo(
        filename=filename,
        geo_code=geo_code,
        state=state,
        dataset_type_code=dataset_type_code,
        dataset_type=DATASET_TYPES[dataset_type_code],
        version_code=version_code,
        survey=describe_survey(geo_code, version_code),
        file_format_code=file_format_code,
        file_format=FILE_FORMATS.get(file_format_code, file_format_code),
        parse_ok=True,
        parse_note="",
    )
