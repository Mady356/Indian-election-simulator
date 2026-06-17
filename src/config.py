"""
Central paths and project-wide constants.

Single source of truth for:
    * filesystem layout       (ROOT_DIR / DATA_DIR / RAW_DIR / RAW_YEAR_DIR /
                               PROCESSED_DIR / DATABASE_DIR / OUTPUTS_DIR)
    * which election we model (ACTIVE_YEAR, ELECTION_TYPE)
    * derived names that change when the year changes (ALLIANCE_COL)

Bumping ACTIVE_YEAR (and, if needed, ELECTION_TYPE) is intended to be the
*only* edit required to switch the whole pipeline to a different election.
Every other module must read year/type from here rather than hardcoding
"2024" or "lok_sabha" literals.
"""

from pathlib import Path

# -----------------------------------------------------------------------------
# Active election (declared first so paths and column-name constants below
# can reference it).
# -----------------------------------------------------------------------------

# The active election year. This is the *only* knob in the project that you
# should ever have to change to switch the entire pipeline to a new year.
ACTIVE_YEAR: int = 2019
ELECTION_TYPE: str = "lok_sabha"

# Backwards-compatible aliases. New code should prefer ACTIVE_YEAR; ELECTION_YEAR
# and YEAR are kept around so older imports don't break.
ELECTION_YEAR: int = ACTIVE_YEAR
YEAR: int = ACTIVE_YEAR


# -----------------------------------------------------------------------------
# Filesystem layout
# -----------------------------------------------------------------------------

# ROOT_DIR points at the project root (the folder that contains data/, src/,
# notebooks/). __file__ is .../src/config.py, so parents[1] is the project root.
ROOT_DIR = Path(__file__).resolve().parents[1]

DATA_DIR = ROOT_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
# Raw inputs are organised one folder per election year so 2019 / 2014 raw
# files can sit next to 2024 without colliding. The cleaner reads from
# RAW_YEAR_DIR; RAW_DIR is only the parent.
RAW_YEAR_DIR = RAW_DIR / str(ACTIVE_YEAR)
# DHS / NFHS microdata zips downloaded from dhsprogram.com (read-only).
DHS_DOWNLOADS_DIR = RAW_DIR / "dhs_downloads"

# Demographic data warehouse (catalog + raw + processed + outputs).
DEMOGRAPHICS_DIR = DATA_DIR / "demographics"
DEMOGRAPHICS_CATALOG_DIR = DEMOGRAPHICS_DIR / "catalog"
DEMOGRAPHICS_RAW_DIR = DEMOGRAPHICS_DIR / "raw"
DEMOGRAPHICS_RAW_CENSUS_2011 = DEMOGRAPHICS_RAW_DIR / "census_2011"
DEMOGRAPHICS_RAW_NFHS = DEMOGRAPHICS_RAW_DIR / "nfhs"
DEMOGRAPHICS_RAW_MOSPI = DEMOGRAPHICS_RAW_DIR / "mospi"
DEMOGRAPHICS_RAW_RBI = DEMOGRAPHICS_RAW_DIR / "rbi"
DEMOGRAPHICS_PROCESSED_DIR = DEMOGRAPHICS_DIR / "processed"
DEMOGRAPHICS_OUTPUTS_DIR = DEMOGRAPHICS_DIR / "outputs"
# Extracted DHS/NFHS Stata files (local only — never commit microdata).
DHS_EXTRACTED_DIR = DEMOGRAPHICS_RAW_DIR / "dhs_extracted"

# Legacy paths (older layout / manual uploads) — still scanned by the audit.
RAW_DEMOGRAPHICS_DIR = RAW_DIR / "demographics"
CENSUS_2011_DIR = RAW_DEMOGRAPHICS_DIR / "census_2011"
LEGACY_CENSUS_2011_DIRS = (
    DEMOGRAPHICS_RAW_CENSUS_2011,
    DEMOGRAPHICS_RAW_DIR / "demographics-census-2011",
    CENSUS_2011_DIR,
    RAW_DIR / "demographics-census-2011",
)

PROCESSED_DIR = DATA_DIR / "processed"
DATABASE_DIR = DATA_DIR / "database"
OUTPUTS_DIR = DATA_DIR / "outputs"
REFERENCE_DIR = DATA_DIR / "reference"

# Make sure write targets exist; raw dirs are read-only so we don't create them.
for _d in (PROCESSED_DIR, DATABASE_DIR, OUTPUTS_DIR):
    _d.mkdir(parents=True, exist_ok=True)


# -----------------------------------------------------------------------------
# Schema constants that depend on the active election
# -----------------------------------------------------------------------------

# Column name used for the per-party alliance assignment within a year. The
# alliance landscape changes every election, so the column is year-stamped.
# Importing this constant lets downstream code stay year-agnostic, e.g.
#     winners.groupby(ALLIANCE_COL)
# (For cross-year work, prefer the long-format `party_alliance_by_year` table
# produced by `src.metadata.build_party_alliances`.)
ALLIANCE_COL: str = f"alliance_{ACTIVE_YEAR}"


# -----------------------------------------------------------------------------
# Analysis tuning constants
# -----------------------------------------------------------------------------

# A constituency is considered "close" when the winner's margin (in vote-share
# percentage points) is below this threshold. Used by state_swing_sensitivity
# and similarity/risk analyses.
CLOSE_MARGIN_THRESHOLD: float = 5.0
