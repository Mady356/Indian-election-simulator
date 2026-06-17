"""
Repair priority-state delimitation mappings and rebuild demographic coverage.

Run:
    python -m src.reference.repair_priority_state_mappings

This script:
1. Re-parses Tamil Nadu and Assam delimitation tables with fixed parser rules
2. Writes transparent repair artifacts under data/reference/repairs/
3. Rebuilds delimitation summary, alias table, constituency panel, and analysis master
4. Prints before/after coverage for West Bengal, Tamil Nadu, Assam, and Uttarakhand
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.analysis.analysis_common import NFHS5_LEVEL_COLUMNS, normalise_state_key
from src.reference.build_ls_district_crosswalk_from_delimitation import (
    assign_district_roles,
    build_summary,
)
from src.reference.delimitation_normalize import join_ls_to_district
from src.reference.delimitation_paths import (
    ASSEMBLY_DISTRICT_CROSSWALK,
    DELIMITATION_CENSUS_DISTRICT_ALIAS,
    DELIMITATION_RAW_TEXT,
    LOK_SABHA_ASSEMBLY_CROSSWALK,
    LOK_SABHA_DISTRICT_SUMMARY,
)
from src.reference.delimitation_utils import parse_delimitation_pages

REPAIRS_DIR = ROOT / "data" / "reference" / "repairs"
BACKUPS_DIR = REPAIRS_DIR / "backups"
DEMOGRAPHICS_PROCESSED = ROOT / "data" / "demographics" / "processed"
ANALYSIS_MASTER = ROOT / "data/analysis/constituency_election_demographic_master.csv"
NFHS_DISTRICT_PANEL = DEMOGRAPHICS_PROCESSED / "nfhs_district_panel.csv"

PRIORITY_STATES = ["Tamil Nadu", "West Bengal", "Assam", "Uttarakhand"]

TN_SUMMARY_REPAIR = REPAIRS_DIR / "tamil_nadu_ls_district_summary.csv"
WB_ALIAS_REPAIR = REPAIRS_DIR / "west_bengal_alias_repairs.csv"
ASSAM_MAPPING_REPAIR = REPAIRS_DIR / "assam_mapping_repairs.csv"
REPAIR_REPORT = REPAIRS_DIR / "priority_state_mapping_repair_report.csv"
UTTARAKHAND_DIAG = REPAIRS_DIR / "uttarakhand_nfhs_diagnostic.txt"


WB_ALIAS_REPAIRS = [
    {
        "delimitation_state": "West Bengal",
        "delimitation_district": "HOOGHLY",
        "census_district": "Hugli",
        "nfhs_district": "Hugli",
        "notes": "Delimitation HOOGHLY maps to Census/NFHS Hugli",
    },
    {
        "delimitation_state": "West Bengal",
        "delimitation_district": "HOWRAH",
        "census_district": "Haora",
        "nfhs_district": "Haora",
        "notes": "Delimitation HOWRAH maps to Census/NFHS Haora",
    },
    {
        "delimitation_state": "West Bengal",
        "delimitation_district": "BARDHAMAN",
        "census_district": "Barddhaman",
        "nfhs_district": "Barddhaman",
        "notes": "Delimitation BARDHAMAN maps to NFHS Barddhaman",
    },
    {
        "delimitation_state": "West Bengal",
        "delimitation_district": "NORTH 24 PARGANAS",
        "census_district": "North Twenty Four Parganas",
        "nfhs_district": "North Twenty Four Parganas",
        "notes": "Numeric district spelling variant",
    },
    {
        "delimitation_state": "West Bengal",
        "delimitation_district": "SOUTH 24 PARGANAS",
        "census_district": "South Twenty Four Parganas",
        "nfhs_district": "South Twenty Four Parganas",
        "notes": "Numeric district spelling variant",
    },
    {
        "delimitation_state": "West Bengal",
        "delimitation_district": "COOCHBEHAR",
        "census_district": "Koch Bihar",
        "nfhs_district": "Koch Bihar",
        "notes": "Delimitation COOCHBEHAR maps to Census/NFHS Koch Bihar",
    },
    {
        "delimitation_state": "West Bengal",
        "delimitation_district": "DARJEELING",
        "census_district": "Darjiling",
        "nfhs_district": "Darjiling",
        "notes": "Delimitation DARJEELING maps to Census/NFHS Darjiling",
    },
    {
        "delimitation_state": "West Bengal",
        "delimitation_district": "MALDAHA",
        "census_district": "Maldah",
        "nfhs_district": "Maldah",
        "notes": "Delimitation MALDAHA maps to Census/NFHS Maldah",
    },
    {
        "delimitation_state": "West Bengal",
        "delimitation_district": "PURULIA",
        "census_district": "Puruliya",
        "nfhs_district": "Puruliya",
        "notes": "Delimitation PURULIA maps to Census/NFHS Puruliya",
    },
    {
        "delimitation_state": "West Bengal",
        "delimitation_district": "PURBO MEDINIPUR",
        "census_district": "Purba Medinipur",
        "nfhs_district": "",
        "notes": "NFHS district panel missing Purba Medinipur; no values imputed",
    },
    {
        "delimitation_state": "West Bengal",
        "delimitation_district": "PASCHIM MEDINIPUR",
        "census_district": "Paschim Medinipur",
        "nfhs_district": "",
        "notes": "NFHS district panel missing Paschim Medinipur; GE clusters exist but features not built",
    },
]


def backup_file(path: Path) -> Path | None:
    if not path.exists():
        return None
    BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    dest = BACKUPS_DIR / f"{path.name}.{stamp}.bak"
    shutil.copy2(path, dest)
    return dest


def run_module(module: str) -> None:
    print(f"\nRunning: python -m {module}")
    subprocess.run([sys.executable, "-m", module], check=True, cwd=ROOT)


def coverage_for_state(master: pd.DataFrame, state: str) -> dict[str, object]:
    state_key = normalise_state_key(state)
    sub = master[master["state"].map(normalise_state_key) == state_key]
    if sub.empty:
        sub = master[master["state"] == state]
    has_nfhs5 = sub[NFHS5_LEVEL_COLUMNS].notna().any(axis=1).sum() if not sub.empty else 0
    has_coverage = sub["nfhs5_coverage_share"].notna().sum() if "nfhs5_coverage_share" in sub.columns else 0
    mean_cov = pd.to_numeric(sub.get("nfhs5_coverage_share"), errors="coerce").mean()
    return {
        "state": state,
        "election_constituencies": len(sub),
        "with_nfhs5_values": int(has_nfhs5),
        "with_coverage_metadata": int(has_coverage),
        "mean_nfhs5_coverage_share": float(mean_cov) if pd.notna(mean_cov) else 0.0,
    }


def measure_coverage(label: str) -> tuple[pd.DataFrame, int]:
    if not ANALYSIS_MASTER.exists():
        empty = pd.DataFrame([{**coverage_for_state(pd.DataFrame(), st), "phase": label} for st in PRIORITY_STATES])
        return empty, 0
    master = pd.read_csv(ANALYSIS_MASTER)
    rows = [coverage_for_state(master, state) for state in PRIORITY_STATES]
    total_nfhs5 = int(master[NFHS5_LEVEL_COLUMNS].notna().any(axis=1).sum())
    print(f"\n{label}")
    for row in rows:
        print(
            f"  {row['state']}: {row['with_nfhs5_values']}/{row['election_constituencies']} "
            f"with NFHS-5 values; mean coverage_share={row['mean_nfhs5_coverage_share']:.3f}"
        )
    print(f"  Total constituencies with NFHS-5 values: {total_nfhs5}")
    out = pd.DataFrame(rows)
    out["phase"] = label
    return out, total_nfhs5


def reparse_crosswalks() -> tuple[pd.DataFrame, pd.DataFrame]:
    print(f"Re-parsing delimitation text from {DELIMITATION_RAW_TEXT}")
    pages = pd.read_csv(DELIMITATION_RAW_TEXT)
    ac_df, ls_df = parse_delimitation_pages(pages)
    backup_file(ASSEMBLY_DISTRICT_CROSSWALK)
    backup_file(LOK_SABHA_ASSEMBLY_CROSSWALK)
    ac_df.to_csv(ASSEMBLY_DISTRICT_CROSSWALK, index=False)
    ls_df.to_csv(LOK_SABHA_ASSEMBLY_CROSSWALK, index=False)
    print(f"  Saved {ASSEMBLY_DISTRICT_CROSSWALK.name} ({len(ac_df)} rows)")
    print(f"  Saved {LOK_SABHA_ASSEMBLY_CROSSWALK.name} ({len(ls_df)} rows)")
    return ac_df, ls_df


def build_state_summary(
    ac_df: pd.DataFrame,
    ls_df: pd.DataFrame,
    state: str,
) -> pd.DataFrame:
    merged = join_ls_to_district(ls_df[ls_df["state"] == state], ac_df[ac_df["state"] == state])
    crosswalk = assign_district_roles(merged)
    return build_summary(crosswalk)


def save_tamil_nadu_repair(ac_df: pd.DataFrame, ls_df: pd.DataFrame) -> pd.DataFrame:
    summary = build_state_summary(ac_df, ls_df, "Tamil Nadu")
    REPAIRS_DIR.mkdir(parents=True, exist_ok=True)
    summary.to_csv(TN_SUMMARY_REPAIR, index=False)
    seats = summary["lok_sabha_constituency"].nunique()
    print(f"Tamil Nadu repair summary: {len(summary)} rows, {seats} LS seats")
    if seats != 39:
        print(f"  WARNING: expected 39 LS seats, found {seats}")
    return summary


def save_assam_repair(ac_df: pd.DataFrame, ls_df: pd.DataFrame) -> pd.DataFrame:
    merged = join_ls_to_district(ls_df[ls_df["state"] == "Assam"], ac_df[ac_df["state"] == "Assam"])
    summary = build_summary(assign_district_roles(merged))
    repair_rows = merged[
        ["state", "lok_sabha_no", "lok_sabha_constituency", "assembly_no", "assembly_constituency", "district", "match_method"]
    ].copy()
    repair_rows.to_csv(ASSAM_MAPPING_REPAIR, index=False)
    print(
        f"Assam mapping repair: {summary['lok_sabha_constituency'].nunique()} constituencies, "
        f"{summary['district'].nunique()} districts"
    )
    return summary


def save_west_bengal_alias_repairs() -> pd.DataFrame:
    df = pd.DataFrame(WB_ALIAS_REPAIRS)
    df.to_csv(WB_ALIAS_REPAIR, index=False)
    print(f"West Bengal alias repairs: {len(df)} rows -> {WB_ALIAS_REPAIR}")
    return df


def merge_manual_alias_repairs(alias_df: pd.DataFrame, repairs: pd.DataFrame) -> pd.DataFrame:
    from src.reference.delimitation_district_aliases import canonical_district_key, census_state_for_delimitation

    out = alias_df.copy()
    for _, row in repairs.iterrows():
        delim_state = row["delimitation_state"]
        delim_district = row["delimitation_district"]
        if not row.get("nfhs_district"):
            continue
        key = canonical_district_key(delim_district)
        mask = (
            (out["delimitation_state"] == delim_state)
            & (out["delimitation_district_key"] == key)
        )
        replacement = {
            "delimitation_state": delim_state,
            "delimitation_district": delim_district,
            "delimitation_district_key": key,
            "census_state": census_state_for_delimitation(delim_state),
            "census_district": row["census_district"],
            "census_district_code": pd.NA,
            "census_district_key": canonical_district_key(row["census_district"]),
            "nfhs_district": row["nfhs_district"],
            "nfhs4_state": delim_state,
            "nfhs5_state": delim_state,
            "nfhs_state": delim_state,
            "match_method": "manual_repair",
            "match_score": 1.0,
            "confidence": "high",
            "aggregate_share": 1.0,
            "notes": row.get("notes", "priority_state_mapping_repair"),
        }
        if mask.any():
            for col, val in replacement.items():
                out.loc[mask, col] = val
        else:
            out = pd.concat([out, pd.DataFrame([replacement])], ignore_index=True)
    return out.drop_duplicates(
        subset=["delimitation_state", "delimitation_district_key"],
        keep="last",
    )


def rebuild_delimitation_summary(ac_df: pd.DataFrame, ls_df: pd.DataFrame) -> pd.DataFrame:
    merged = join_ls_to_district(ls_df, ac_df)
    summary = build_summary(assign_district_roles(merged))
    backup_file(LOK_SABHA_DISTRICT_SUMMARY)
    summary.to_csv(LOK_SABHA_DISTRICT_SUMMARY, index=False)
    print(f"Rebuilt {LOK_SABHA_DISTRICT_SUMMARY.name} ({len(summary)} rows, {summary.state.nunique()} states)")
    return summary


def uttarakhand_diagnostic() -> str:
    lines = [
        "Uttarakhand NFHS diagnostic",
        "===========================",
        "",
    ]
    nfhs_panel = pd.read_csv(NFHS_DISTRICT_PANEL) if NFHS_DISTRICT_PANEL.exists() else pd.DataFrame()
    uk_panel = nfhs_panel[nfhs_panel["state"].astype(str).str.fullmatch("Uttarakhand", case=False)]
    lines.append(f"Rows in nfhs_district_panel for Uttarakhand: {len(uk_panel)}")

    audit_path = ROOT / "data/demographics/outputs/dhs_downloads_audit.csv"
    if audit_path.exists():
        audit = pd.read_csv(audit_path)
        state_col = "state_name" if "state_name" in audit.columns else "state"
        uk_audit = audit[audit[state_col].astype(str).str.fullmatch("Uttarakhand", case=False)]
        lines.append(f"Rows in dhs_downloads_audit for Uttarakhand: {len(uk_audit)}")
        if uk_audit.empty:
            lines.append(
                "Conclusion: Uttarakhand DHS/NFHS raw files are not present in the local download audit. "
                "The parser did not skip Uttarakhand — district features were never extracted because "
                "source microdata is missing."
            )
        else:
            lines.append("Sample audit files:")
            for name in uk_audit.get("zip_name", uk_audit.get("file_name", pd.Series(dtype=str))).head(5):
                lines.append(f"  - {name}")

    geopath = DEMOGRAPHICS_PROCESSED / "dhs_cluster_geospatial.csv"
    if geopath.exists():
        ge = pd.read_csv(geopath)
        ge_state_col = "state_or_region" if "state_or_region" in ge.columns else "state"
        if ge_state_col in ge.columns:
            uk_ge = ge[ge[ge_state_col].astype(str).str.contains("Uttarakhand", case=False, na=False)]
            lines.append(f"Uttarakhand clusters in dhs_cluster_geospatial.csv: {len(uk_ge)}")

    delim = pd.read_csv(LOK_SABHA_DISTRICT_SUMMARY)
    uk_delim = delim[delim["state"] == "Uttarakhand"]
    lines.append(f"Uttarakhand rows in delimitation summary: {len(uk_delim)}")
    lines.append("")
    lines.append("Recommended next step: download Uttarakhand NFHS HR/IR files and rerun")
    lines.append("python -m src.demographics.dhs.build_nfhs_district_features")
    text = "\n".join(lines) + "\n"
    UTTARAKHAND_DIAG.write_text(text, encoding="utf-8")
    print(text)
    return text


def build_repair_report(
    before: pd.DataFrame,
    after: pd.DataFrame,
    before_total: int,
    after_total: int,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for state in PRIORITY_STATES:
        b = before[before["state"] == state].iloc[0]
        a = after[after["state"] == state].iloc[0]
        rows.append(
            {
                "state": state,
                "before_election_constituencies": b["election_constituencies"],
                "after_election_constituencies": a["election_constituencies"],
                "before_nfhs5_values": b["with_nfhs5_values"],
                "after_nfhs5_values": a["with_nfhs5_values"],
                "before_mean_coverage_share": b["mean_nfhs5_coverage_share"],
                "after_mean_coverage_share": a["mean_nfhs5_coverage_share"],
                "delta_nfhs5_values": a["with_nfhs5_values"] - b["with_nfhs5_values"],
                "delta_mean_coverage_share": a["mean_nfhs5_coverage_share"] - b["mean_nfhs5_coverage_share"],
            }
        )
    rows.append(
        {
            "state": "ALL",
            "before_election_constituencies": pd.NA,
            "after_election_constituencies": pd.NA,
            "before_nfhs5_values": before_total,
            "after_nfhs5_values": after_total,
            "before_mean_coverage_share": pd.NA,
            "after_mean_coverage_share": pd.NA,
            "delta_nfhs5_values": after_total - before_total,
            "delta_mean_coverage_share": pd.NA,
        }
    )
    report = pd.DataFrame(rows)
    report.to_csv(REPAIR_REPORT, index=False)
    return report


def main() -> None:
    REPAIRS_DIR.mkdir(parents=True, exist_ok=True)

    before_df, before_total = measure_coverage("Before repairs")

    ac_df, ls_df = reparse_crosswalks()
    tn_summary = save_tamil_nadu_repair(ac_df, ls_df)
    assam_summary = save_assam_repair(ac_df, ls_df)
    wb_repairs = save_west_bengal_alias_repairs()

    rebuild_delimitation_summary(ac_df, ls_df)
    uttarakhand_diagnostic()

    run_module("src.reference.build_delimitation_census_district_alias")
    alias_df = pd.read_csv(DELIMITATION_CENSUS_DISTRICT_ALIAS)
    alias_df = merge_manual_alias_repairs(alias_df, wb_repairs)
    backup_file(DELIMITATION_CENSUS_DISTRICT_ALIAS)
    alias_df.to_csv(DELIMITATION_CENSUS_DISTRICT_ALIAS, index=False)

    run_module("src.demographics.nfhs.build_constituency_demographic_panel")
    run_module("src.analysis.build_constituency_election_demographic_master")
    run_module("src.analysis.analyze_vote_share_drivers")

    after_df, after_total = measure_coverage("After repairs")
    report = build_repair_report(before_df, after_df, before_total, after_total)

    print("\nSaved repair artifacts:")
    print(f"  {TN_SUMMARY_REPAIR}")
    print(f"  {WB_ALIAS_REPAIR}")
    print(f"  {ASSAM_MAPPING_REPAIR}")
    print(f"  {REPAIR_REPORT}")
    print(f"  {UTTARAKHAND_DIAG}")
    print("\nRepair summary:")
    print(report.to_string(index=False))


if __name__ == "__main__":
    main()
