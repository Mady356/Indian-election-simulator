"""Output paths for the NFHS panel pipeline."""

from pathlib import Path

from src.config import (
    DEMOGRAPHICS_PROCESSED_DIR,
    RAW_DIR,
    REFERENCE_DIR,
)

NHFS_RAW_DIR = RAW_DIR / "NHFS-DATA"

NFHS_DISTRICT_FEATURES = DEMOGRAPHICS_PROCESSED_DIR / "nfhs_district_features.csv"
LOK_SABHA_DISTRICT_SUMMARY = REFERENCE_DIR / "lok_sabha_district_summary_delimitation.csv"
DISTRICT_MASTER_TABLE = DEMOGRAPHICS_PROCESSED_DIR / "district_master_table.csv"

NFHS_DISTRICT_PANEL = DEMOGRAPHICS_PROCESSED_DIR / "nfhs_district_panel.csv"
NFHS_DISTRICT_CHANGE = DEMOGRAPHICS_PROCESSED_DIR / "nfhs_district_change_features.csv"
CONSTITUENCY_DEMOGRAPHIC_PANEL = DEMOGRAPHICS_PROCESSED_DIR / "constituency_demographic_panel.csv"
CONSTITUENCY_DEMOGRAPHIC_CHANGE = (
    DEMOGRAPHICS_PROCESSED_DIR / "constituency_demographic_change_features.csv"
)
NFHS_PANEL_QUALITY_REPORT = DEMOGRAPHICS_PROCESSED_DIR / "nfhs_panel_quality_report.csv"
NFHS4_DISTRICT_CROSSWALK = DEMOGRAPHICS_PROCESSED_DIR / "nfhs4_district_code_crosswalk.csv"
CENSUS_DISTRICT_DEMOGRAPHICS = DEMOGRAPHICS_PROCESSED_DIR / "census_district_demographics_2011.csv"
