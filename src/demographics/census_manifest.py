"""
Curated list of Census 2011 tables for electoral analysis.

We do NOT scrape all ~779 Census tables. This file is the single checklist of
which Excel files belong in the project and what to name them when you upload
them manually.

Drop files into:
    data/raw/demographics/census_2011/

Recommended filename (any of these extensions is fine):
    census_2011_<code>_<name>.xlsx
    census_2011_<code>_<name>.xls

Example:
    census_2011_A01_population_households_area.xlsx

You may use the Census site's original filename instead; cleaners will be
written table-by-table once real files are on disk. The names below are the
*preferred* convention so scripts can find tables predictably.
"""

from pathlib import Path

# Finest geography each table typically provides.
LEVEL_STATE_DISTRICT = "state_district"

CENSUS_2011_TABLES = [
    {
        "code": "A01",
        "name": "population_households_area",
        "description": "Population, households, area, rural/urban base data",
        "level": LEVEL_STATE_DISTRICT,
        "priority": "high",
    },
    {
        "code": "C01",
        "name": "religion",
        "description": "Religion-wise population",
        "level": LEVEL_STATE_DISTRICT,
        "priority": "high",
    },
    {
        "code": "SC_PCA",
        "name": "scheduled_caste_population",
        "description": "Scheduled caste population share",
        "level": LEVEL_STATE_DISTRICT,
        "priority": "high",
    },
    {
        "code": "ST_PCA",
        "name": "scheduled_tribe_population",
        "description": "Scheduled tribe population share",
        "level": LEVEL_STATE_DISTRICT,
        "priority": "high",
    },
    {
        "code": "EDUCATION",
        "name": "literacy_education",
        "description": "Literacy and education levels",
        "level": LEVEL_STATE_DISTRICT,
        "priority": "high",
    },
    {
        "code": "AGE",
        "name": "age_structure",
        "description": "Age groups, youth share, working-age share",
        "level": LEVEL_STATE_DISTRICT,
        "priority": "medium",
    },
    {
        "code": "MIGRATION",
        "name": "migration",
        "description": "Migration patterns",
        "level": LEVEL_STATE_DISTRICT,
        "priority": "low",
    },
]

PRIORITIES = ("high", "medium", "low")
VALID_EXTENSIONS = (".xlsx", ".xls", ".csv")


def expected_basename(entry: dict, ext: str = ".xlsx") -> str:
    """Preferred on-disk name for one manifest entry."""
    return f"census_2011_{entry['code']}_{entry['name']}{ext}"


def find_uploaded_file(raw_dir: Path, entry: dict) -> Path | None:
    """
    Return the path to an uploaded file for this entry, if present.

    Matches the preferred basename with any supported extension, or any file
    whose name starts with census_2011_<code>_.
    """
    if not raw_dir.exists():
        return None

    prefix = f"census_2011_{entry['code']}_"
    for ext in VALID_EXTENSIONS:
        candidate = raw_dir / expected_basename(entry, ext)
        if candidate.is_file():
            return candidate

    for path in sorted(raw_dir.iterdir()):
        if path.is_file() and path.name.startswith(prefix):
            return path
    return None


def tables_by_priority(priority: str | None = None) -> list[dict]:
    """Manifest subset; None means all tables."""
    if priority is None:
        return list(CENSUS_2011_TABLES)
    return [t for t in CENSUS_2011_TABLES if t.get("priority") == priority]
