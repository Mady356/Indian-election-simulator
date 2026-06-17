"""Paths and output filenames for the DHS/NFHS pipeline."""

from pathlib import Path

from src.config import (
    DEMOGRAPHICS_OUTPUTS_DIR,
    DEMOGRAPHICS_PROCESSED_DIR,
    DEMOGRAPHICS_RAW_DIR,
    DHS_DOWNLOADS_DIR,
    DHS_EXTRACTED_DIR,
    ROOT_DIR,
)

INVENTORY_CANDIDATES = (
    DHS_DOWNLOADS_DIR / "dhs_file_inventory.csv",
    DEMOGRAPHICS_OUTPUTS_DIR / "dhs_downloads_audit.csv",
)

FEATURE_DICTIONARY = DEMOGRAPHICS_PROCESSED_DIR / "dhs_feature_dictionary.csv"
NFHS_STATE_FEATURES = DEMOGRAPHICS_PROCESSED_DIR / "nfhs_state_features.csv"
NFHS_DISTRICT_FEATURES = DEMOGRAPHICS_PROCESSED_DIR / "nfhs_district_features.csv"
DHS_CLUSTER_GEOSPATIAL = DEMOGRAPHICS_PROCESSED_DIR / "dhs_cluster_geospatial.csv"
DHS_GEOSPATIAL_PUBLIC = ROOT_DIR / "visualizer" / "data" / "dhs_geospatial_clusters_public.csv"

SURVEY_VERSIONS = {
    "42": {"survey": "NFHS-4", "survey_year": 2016},
    "52": {"survey": "NFHS-5", "survey_year": 2020},
}

NATIONAL_FILESETS = {
    "42": {
        "HR": "IAHR42FL",
        "IR": "IAIR42FL",
        "PR": "IAPR42FL",
        "MR": "IAMR42FL",
    },
    "52": {
        "HR": "IAHR52FL",
        "IR": "IAIR52FL",
        "PR": "IAPR52FL",
        "MR": "IAMR52FL",
    },
}

STATE_FEATURE_COLUMNS = [
    "survey",
    "survey_year",
    "state",
    "household_count",
    "person_count",
    "internet_pct",
    "electricity_pct",
    "improved_sanitation_pct",
    "lpg_pct",
    "mobile_phone_pct",
    "bank_account_pct",
    "women_secondary_edu_pct",
    "female_literacy_pct",
    "male_literacy_pct",
    "fertility_rate",
    "wealth_index_mean",
    "urban_pct",
]

DISTRICT_FEATURE_COLUMNS = [
    "survey",
    "survey_year",
    "state",
    "district",
    *STATE_FEATURE_COLUMNS[3:],
]

TREND_COLUMNS = [
    "internet_growth_nfhs4_to_nfhs5",
    "electricity_growth_nfhs4_to_nfhs5",
    "sanitation_growth_nfhs4_to_nfhs5",
    "fertility_decline_nfhs4_to_nfhs5",
]

GE_SHAPEFILE_STEMS = ("IAGE7AFL", "IAGE71FL")
GE_SHAPEFILE_STEMS_NFHS4 = ("IAGE71FL", "IAGE7AFL")
GE_SHAPEFILE_STEMS_NFHS5 = ("IAGE71FL", "IAGE7AFL")

NFHS5_GE_JOIN_DIAGNOSTICS = DEMOGRAPHICS_PROCESSED_DIR / "nfhs5_ge_join_diagnostics.csv"
DISTRICT_MASTER_TABLE = DEMOGRAPHICS_PROCESSED_DIR / "district_master_table.csv"

DISTRICT_MASTER_COLUMNS = [
    "district_id",
    "state",
    "district",
    "survey",
    "survey_year",
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
