"""Paths for the delimitation-order parsing pipeline."""

from pathlib import Path

from src.config import RAW_DIR, REFERENCE_DIR

DELIMITATION_PDF = RAW_DIR / "ls-as-mapping" / (
    "DelimitationofParliamentaryAssemblyConstituenciesOrder-2008(English).pdf"
)

DELIMITATION_RAW_TEXT = REFERENCE_DIR / "delimitation_raw_text.csv"
ASSEMBLY_DISTRICT_CROSSWALK = REFERENCE_DIR / "assembly_constituency_district_crosswalk.csv"
LOK_SABHA_ASSEMBLY_CROSSWALK = REFERENCE_DIR / "lok_sabha_assembly_crosswalk.csv"
LOK_SABHA_DISTRICT_CROSSWALK = REFERENCE_DIR / "lok_sabha_district_crosswalk_delimitation.csv"
LOK_SABHA_DISTRICT_SUMMARY = REFERENCE_DIR / "lok_sabha_district_summary_delimitation.csv"
DELIMITATION_CENSUS_DISTRICT_ALIAS = REFERENCE_DIR / "delimitation_census_district_alias.csv"

MANUAL_REVIEW_DIR = REFERENCE_DIR / "manual_review"
LOW_CONFIDENCE_ASSEMBLY = MANUAL_REVIEW_DIR / "delimitation_low_confidence_assembly.csv"
LOW_CONFIDENCE_LOK_SABHA = MANUAL_REVIEW_DIR / "delimitation_low_confidence_lok_sabha.csv"
UNMATCHED_LS_AC = MANUAL_REVIEW_DIR / "unmatched_ls_ac_segments.csv"
UNMATCHED_LS_AC_JOIN_DIAGNOSTICS = MANUAL_REVIEW_DIR / "unmatched_ls_ac_join_diagnostics.csv"
ASSEMBLY_DISTRICT_CROSSWALK_NORMALIZED = REFERENCE_DIR / "assembly_constituency_district_crosswalk_normalized.csv"
LOK_SABHA_ASSEMBLY_CROSSWALK_NORMALIZED = REFERENCE_DIR / "lok_sabha_assembly_crosswalk_normalized.csv"
