"""
State-level coverage gap audit for recovering missing constituency demographics.

Traces where coverage breaks across:
NFHS district panel → district aliases → delimitation mapping → constituency panel → master table

Run:
    python -m src.analysis.state_gap_audit
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from src.analysis.analysis_common import (
    ANALYSIS_DIR,
    DEMOGRAPHICS_DIR,
    NFHS5_LEVEL_COLUMNS,
    REFERENCE_DIR,
    add_join_keys,
    normalise_constituency_key,
    normalise_state_key,
)
from src.analysis.coverage_diagnostics import STATE_KEY_ALIASES
from src.reference.delimitation_district_aliases import canonical_district_key

MASTER_PATH = ANALYSIS_DIR / "constituency_election_demographic_master.csv"
NFHS_DISTRICT_PANEL_PATH = DEMOGRAPHICS_DIR / "nfhs_district_panel.csv"
NFHS_DISTRICT_CHANGE_PATH = DEMOGRAPHICS_DIR / "nfhs_district_change_features.csv"
CONSTITUENCY_PANEL_PATH = DEMOGRAPHICS_DIR / "constituency_demographic_panel.csv"
DELIMITATION_SUMMARY_PATH = REFERENCE_DIR / "lok_sabha_district_summary_delimitation.csv"
DELIMITATION_CROSSWALK_PATH = REFERENCE_DIR / "lok_sabha_district_crosswalk_delimitation.csv"
DISTRICT_ALIAS_PATH = REFERENCE_DIR / "delimitation_census_district_alias.csv"

OUTPUT_DIR = ANALYSIS_DIR / "coverage" / "state_gap_audits"
SUMMARY_PATH = OUTPUT_DIR / "state_gap_summary.txt"

PRIORITY_STATES = ["West Bengal", "Tamil Nadu", "Assam", "Uttarakhand"]

STATE_OUTPUT_FILES = {
    "West Bengal": "west_bengal_gap_audit.csv",
    "Tamil Nadu": "tamil_nadu_gap_audit.csv",
    "Assam": "assam_gap_audit.csv",
    "Uttarakhand": "uttarakhand_gap_audit.csv",
}

NFHS_VALUE_COLUMNS = [
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

LOW_COVERAGE_THRESHOLD = 0.5


def normalise_district_key(value: object) -> str:
    if pd.isna(value):
        return ""
    return canonical_district_key(str(value))


def state_keys_for(state: str) -> set[str]:
    keys = {normalise_state_key(state)}
    alias = STATE_KEY_ALIASES.get(normalise_state_key(state))
    if alias:
        keys.add(alias)
    return keys


def has_any_numeric_values(row: pd.Series, columns: list[str]) -> bool:
    values = pd.to_numeric(row[columns], errors="coerce")
    return bool(values.notna().any())


def split_list_field(value: object) -> list[str]:
    if pd.isna(value) or value == "":
        return []
    return [part.strip() for part in str(value).split(";") if part.strip()]


class GapAuditContext:
    """Load and index all audit layers once."""

    def __init__(self) -> None:
        self.master = pd.read_csv(MASTER_PATH)
        self.nfhs_panel = pd.read_csv(NFHS_DISTRICT_PANEL_PATH)
        self.nfhs_change = pd.read_csv(NFHS_DISTRICT_CHANGE_PATH)
        self.constituency_panel = pd.read_csv(CONSTITUENCY_PANEL_PATH)
        self.delimitation_summary = pd.read_csv(DELIMITATION_SUMMARY_PATH)
        self.delimitation_crosswalk = pd.read_csv(DELIMITATION_CROSSWALK_PATH)
        self.district_alias = pd.read_csv(DISTRICT_ALIAS_PATH)

        self.master = add_join_keys(self.master, "state", "constituency")
        self.constituency_panel_nfhs5 = add_join_keys(
            self.constituency_panel[self.constituency_panel["survey"] == "NFHS-5"].copy(),
            "state",
            "lok_sabha_constituency",
        )
        self._build_indexes()

    def _build_indexes(self) -> None:
        self.alias_by_state_district: dict[tuple[str, str], pd.Series] = {}
        for _, row in self.district_alias.iterrows():
            state_key = normalise_state_key(row["delimitation_state"])
            district_key = normalise_district_key(row["delimitation_district"])
            self.alias_by_state_district[(state_key, district_key)] = row

        self.nfhs_by_state_district: dict[tuple[str, str], pd.DataFrame] = {}
        for _, row in self.nfhs_panel.iterrows():
            state_key = normalise_state_key(row.get("state_key", row["state"]))
            district_key = normalise_district_key(row.get("district_key", row["district"]))
            self.nfhs_by_state_district.setdefault((state_key, district_key), []).append(row)
        for key, rows in self.nfhs_by_state_district.items():
            self.nfhs_by_state_district[key] = pd.DataFrame(rows)

        self.delim_districts_by_state: dict[str, set[str]] = {}
        self.delim_constituencies_by_state: dict[str, set[str]] = {}
        self.delim_constituency_districts: dict[tuple[str, str], set[str]] = {}
        self.delim_constituency_names: dict[tuple[str, str], str] = {}
        self.delim_district_names_by_key: dict[tuple[str, str], str] = {}
        for _, row in self.delimitation_summary.iterrows():
            state = row["state"]
            state_key = normalise_state_key(state)
            district_key = normalise_district_key(row["district"])
            constituency_key = normalise_constituency_key(row["lok_sabha_constituency"])
            base_key = constituency_key.split()[0] if constituency_key else constituency_key
            self.delim_districts_by_state.setdefault(state, set()).add(row["district"])
            self.delim_constituencies_by_state.setdefault(state, set()).add(
                row["lok_sabha_constituency"]
            )
            self.delim_constituency_districts.setdefault((state_key, base_key), set()).add(
                row["district"]
            )
            existing_name = self.delim_constituency_names.get((state_key, base_key), "")
            new_name = str(row["lok_sabha_constituency"])
            if not existing_name or len(new_name) < len(existing_name):
                self.delim_constituency_names[(state_key, base_key)] = new_name
            self.delim_district_names_by_key[(state_key, district_key)] = row["district"]

        self.panel_by_state_constituency: dict[tuple[str, str], pd.Series] = {}
        self.panel_by_state_base_key: dict[tuple[str, str], pd.Series] = {}
        for _, row in self.constituency_panel_nfhs5.iterrows():
            key = (row["state_key"], row["constituency_key"])
            self.panel_by_state_constituency[key] = row
            base_key = row["constituency_key"].split()[0] if row["constituency_key"] else ""
            if base_key:
                self.panel_by_state_base_key[(row["state_key"], base_key)] = row

        self.master_by_state_constituency: dict[tuple[str, str], pd.Series] = {}
        for _, row in self.master.iterrows():
            self.master_by_state_constituency[
                (row["state_key"], row["constituency_key"])
            ] = row

    def rows_for_state(self, df: pd.DataFrame, state: str, state_col: str = "state") -> pd.DataFrame:
        keys = state_keys_for(state)
        if "state_key" in df.columns:
            return df[df["state_key"].isin(keys)].copy()
        return df[df[state_col].map(normalise_state_key).isin(keys)].copy()

    def lookup_alias(self, state: str, district: str) -> pd.Series | None:
        state_key = normalise_state_key(state)
        district_key = normalise_district_key(district)
        return self.alias_by_state_district.get((state_key, district_key))

    def resolved_nfhs_district_key(self, state: str, district: str) -> str:
        district_key = normalise_district_key(district)
        alias_row = self.lookup_alias(state, district)
        if alias_row is not None and pd.notna(alias_row.get("census_district_key")):
            return str(alias_row["census_district_key"]).strip().upper()
        return district_key

    def nfhs_rows(self, state: str, district: str) -> pd.DataFrame:
        keys = state_keys_for(state)
        resolved = self.resolved_nfhs_district_key(state, district)
        frames = []
        for state_key in keys:
            match = self.nfhs_by_state_district.get((state_key, resolved))
            if match is not None:
                frames.append(match)
            match_direct = self.nfhs_by_state_district.get(
                (state_key, normalise_district_key(district))
            )
            if match_direct is not None:
                frames.append(match_direct)
        if not frames:
            return pd.DataFrame()
        return pd.concat(frames, ignore_index=True).drop_duplicates()

    def panel_row(self, state: str, constituency: str) -> pd.Series | None:
        constituency_key = normalise_constituency_key(constituency)
        base_key = constituency_key.split()[0] if constituency_key else ""
        for state_key in state_keys_for(state):
            row = self.panel_by_state_constituency.get((state_key, constituency_key))
            if row is not None:
                return row
            if base_key:
                row = self.panel_by_state_base_key.get((state_key, base_key))
                if row is not None:
                    return row
        return None

    def master_row(self, state: str, constituency: str) -> pd.Series | None:
        constituency_key = normalise_constituency_key(constituency)
        base_key = constituency_base_key(constituency)
        for state_key in state_keys_for(state):
            row = self.master_by_state_constituency.get((state_key, constituency_key))
            if row is not None:
                return row
            row = self.master_by_state_constituency.get((state_key, base_key))
            if row is not None:
                return row
        return None


def repair_suggestion_for_district(
    state: str,
    district: str,
    break_point: str,
    ctx: GapAuditContext,
    alias_row: pd.Series | None,
    nfhs_rows: pd.DataFrame,
) -> str:
    district_key = normalise_district_key(district)
    resolved = ctx.resolved_nfhs_district_key(state, district)

    if break_point == "district_alias_missing":
        return (
            f"Add district alias: {district} -> {resolved} "
            f"(state={state})"
        )
    if break_point == "missing_nfhs_district_features":
        if nfhs_rows.empty:
            return f"District {district} has no NFHS district panel rows; extract or map NFHS district features."
        return f"District {district} exists in NFHS panel but all demographic values are null."
    if break_point == "delimitation_summary_missing":
        if not nfhs_rows.empty:
            return "District exists in NFHS but not delimitation summary; add delimitation district mapping."
        return "District missing from delimitation summary and NFHS district panel."
    if break_point == "name_normalization_mismatch" and alias_row is not None:
        return (
            f"District alias exists ({alias_row.get('delimitation_district')} -> "
            f"{alias_row.get('census_district_key')}) but NFHS lookup still failed."
        )
    if break_point == "constituency_panel_aggregation_failed":
        return (
            f"District {district} maps to NFHS key {resolved}; "
            "check constituency panel district-segment weighting."
        )
    return "Review district mapping across NFHS panel, alias table, and delimitation summary."


def repair_suggestion_for_constituency(
    state: str,
    constituency: str,
    break_point: str,
    ctx: GapAuditContext,
    districts_missing: list[str],
) -> str:
    if break_point == "delimitation_summary_missing":
        if normalise_state_key(state) == normalise_state_key("Tamil Nadu"):
            return (
                "Tamil Nadu is missing from lok_sabha_district_summary_delimitation.csv; "
                "parse Schedule XXVI from the 2008 delimitation order."
            )
        return "Constituency missing from delimitation district summary."
    if break_point == "name_normalization_mismatch":
        state_key = normalise_state_key(state)
        if state_key in STATE_KEY_ALIASES:
            return (
                f"Likely state name mismatch: {state} vs "
                f"{STATE_KEY_ALIASES[state_key]} (check master join keys)."
            )
        return "Constituency name normalization mismatch between election and demographic sources."
    if break_point == "low_coverage_share":
        return "Panel row exists but coverage_share is below threshold; improve district NFHS coverage."
    if break_point == "constituency_panel_aggregation_failed":
        if districts_missing:
            missing = ", ".join(districts_missing[:4])
            return (
                f"Constituency exists in delimitation summary but panel aggregation failed; "
                f"missing districts: {missing}"
            )
        return "Constituency exists in delimitation summary but not in constituency demographic panel."
    if break_point == "analysis_master_join_failed":
        return "Constituency panel has values but analysis master join did not populate them."
    if break_point == "missing_nfhs_district_features":
        return "Upstream district NFHS features are missing for one or more mapped districts."
    return "Review constituency mapping across delimitation summary, panel, and master table."


def classify_district_break_point(
    state: str,
    district: str,
    ctx: GapAuditContext,
    in_delim: bool,
    in_alias: bool,
    nfhs_rows: pd.DataFrame,
    has_values: bool,
    in_panel_path: bool,
) -> str:
    if not in_delim and nfhs_rows.empty:
        return "unknown"
    if not in_delim and not nfhs_rows.empty:
        return "delimitation_summary_missing"
    if in_delim and not in_alias and normalise_district_key(district) != ctx.resolved_nfhs_district_key(
        state, district
    ):
        return "district_alias_missing"
    if nfhs_rows.empty:
        return "missing_nfhs_district_features"
    if not has_values:
        return "missing_nfhs_district_features"
    if in_delim and not in_panel_path:
        return "constituency_panel_aggregation_failed"
    return "unknown"


def classify_constituency_break_point(
    state: str,
    constituency: str,
    ctx: GapAuditContext,
    in_master: bool,
    in_delim: bool,
    panel_row: pd.Series | None,
    master_row: pd.Series | None,
    has_nfhs5_values: bool,
    coverage_share: float | None,
    districts_missing: list[str],
) -> str:
    if not in_delim:
        return "delimitation_summary_missing"

    if panel_row is None:
        if ctx.panel_row(state, constituency) is None:
            for state_key in state_keys_for(state):
                alias_state = STATE_KEY_ALIASES.get(state_key)
                if alias_state and ctx.panel_row(alias_state, constituency) is not None:
                    return "name_normalization_mismatch"
        return "constituency_panel_aggregation_failed"

    if coverage_share is not None and coverage_share < LOW_COVERAGE_THRESHOLD:
        if districts_missing:
            return "missing_nfhs_district_features"
        return "low_coverage_share"

    if panel_row is not None and has_any_numeric_values(panel_row, NFHS_VALUE_COLUMNS):
        if master_row is not None and not has_nfhs5_values:
            return "analysis_master_join_failed"

    if panel_row is not None and not has_any_numeric_values(panel_row, NFHS_VALUE_COLUMNS):
        return "constituency_panel_aggregation_failed"

    if has_nfhs5_values:
        return "unknown"

    return "low_coverage_share"


def collect_districts(state: str, ctx: GapAuditContext) -> list[str]:
    districts: set[str] = set()
    districts.update(ctx.delim_districts_by_state.get(state, set()))
    for _, row in ctx.rows_for_state(ctx.nfhs_panel, state).iterrows():
        districts.add(str(row["district"]))
    for _, row in ctx.district_alias[ctx.district_alias["delimitation_state"] == state].iterrows():
        districts.add(str(row["delimitation_district"]))
    for _, row in ctx.rows_for_state(ctx.delimitation_summary, state).iterrows():
        districts.add(str(row["district"]))
    return sorted(districts, key=lambda x: normalise_district_key(x))


def constituency_base_key(constituency: str) -> str:
    key = normalise_constituency_key(constituency)
    return key.split()[0] if key else ""


def collect_constituencies(state: str, ctx: GapAuditContext) -> list[str]:
    names_by_key: dict[str, str] = {}
    state_key = normalise_state_key(state)

    for _, row in ctx.rows_for_state(ctx.master, state).iterrows():
        names_by_key[constituency_base_key(row["constituency"])] = str(row["constituency"])

    for (sk, ck), display_name in ctx.delim_constituency_names.items():
        if sk == state_key:
            names_by_key.setdefault(ck, str(display_name))

    for _, row in ctx.rows_for_state(ctx.constituency_panel_nfhs5, state).iterrows():
        base = constituency_base_key(row["lok_sabha_constituency"])
        names_by_key.setdefault(base, str(row["lok_sabha_constituency"]))

    return [names_by_key[key] for key in sorted(names_by_key.keys())]


def audit_district(state: str, district: str, ctx: GapAuditContext) -> dict[str, object]:
    district_key = normalise_district_key(district)
    state_key = normalise_state_key(state)
    alias_row = ctx.lookup_alias(state, district)
    nfhs_rows = ctx.nfhs_rows(state, district)
    in_delim = district_key in {
        normalise_district_key(d) for d in ctx.delim_districts_by_state.get(state, set())
    }
    in_alias = alias_row is not None
    has_nfhs4 = (
        not nfhs_rows.empty and (nfhs_rows["survey"] == "NFHS-4").any()
        if "survey" in nfhs_rows.columns
        else False
    )
    has_nfhs5 = (
        not nfhs_rows.empty and (nfhs_rows["survey"] == "NFHS-5").any()
        if "survey" in nfhs_rows.columns
        else False
    )
    has_values = False
    if not nfhs_rows.empty:
        has_values = nfhs_rows.apply(
            lambda row: has_any_numeric_values(row, NFHS_VALUE_COLUMNS),
            axis=1,
        ).any()

    state_key = normalise_state_key(state)
    in_panel_path = any(
        district_key == normalise_district_key(district_name)
        for (sk, _), districts in ctx.delim_constituency_districts.items()
        if sk == state_key
        for district_name in districts
    )

    break_point = classify_district_break_point(
        state,
        district,
        ctx,
        in_delim,
        in_alias,
        nfhs_rows,
        has_values,
        in_panel_path,
    )
    suggestion = repair_suggestion_for_district(
        state, district, break_point, ctx, alias_row, nfhs_rows
    )

    return {
        "audit_level": "district",
        "state": state,
        "district": district,
        "district_key": district_key,
        "constituency": "",
        "constituency_key": "",
        "exists_in_nfhs_district_panel": not nfhs_rows.empty,
        "has_nfhs4": has_nfhs4,
        "has_nfhs5": has_nfhs5,
        "has_any_nfhs_values": has_values,
        "exists_in_district_alias_table": in_alias,
        "alias_target": alias_row.get("census_district_key") if alias_row is not None else "",
        "appears_in_delimitation_district_summary": in_delim,
        "appears_in_constituency_panel": in_panel_path,
        "appears_in_analysis_master": False,
        "exists_in_election_master": False,
        "exists_in_delimitation_summary": False,
        "exists_in_constituency_panel": False,
        "has_nfhs5_values": False,
        "nfhs5_coverage_share": np.nan,
        "districts_expected": "",
        "districts_found_in_nfhs": "",
        "districts_missing_in_nfhs": "",
        "suspected_break_point": break_point,
        "repair_suggestion": suggestion,
    }


def districts_for_constituency(
    state: str,
    constituency: str,
    ctx: GapAuditContext,
) -> set[str]:
    base_key = constituency_base_key(constituency)
    state_key = normalise_state_key(state)
    districts = set(ctx.delim_constituency_districts.get((state_key, base_key), set()))
    if districts:
        return districts
    panel_row = ctx.panel_row(state, constituency)
    if panel_row is not None:
        districts.update(split_list_field(panel_row.get("districts_used")))
        districts.update(split_list_field(panel_row.get("districts_missing")))
    return districts


def audit_constituency(state: str, constituency: str, ctx: GapAuditContext) -> dict[str, object]:
    constituency_key = normalise_constituency_key(constituency)
    base_key = constituency_base_key(constituency)
    state_key = normalise_state_key(state)
    master_row = ctx.master_row(state, constituency)
    panel_row = ctx.panel_row(state, constituency)
    in_master = master_row is not None
    in_delim = (state_key, base_key) in ctx.delim_constituency_districts
    in_panel = panel_row is not None

    has_nfhs5_values = False
    coverage_share = np.nan
    districts_used = ""
    districts_missing = ""

    if master_row is not None:
        has_nfhs5_values = bool(
            pd.to_numeric(master_row[NFHS5_LEVEL_COLUMNS], errors="coerce").notna().any()
        )
        coverage_share = pd.to_numeric(master_row.get("nfhs5_coverage_share"), errors="coerce")
        districts_used = master_row.get("districts_used", "")
        districts_missing = master_row.get("districts_missing", "")

    if panel_row is not None and pd.isna(coverage_share):
        coverage_share = pd.to_numeric(panel_row.get("coverage_share"), errors="coerce")
    if panel_row is not None and not districts_used:
        districts_used = panel_row.get("districts_used", "")
    if panel_row is not None and not districts_missing:
        districts_missing = panel_row.get("districts_missing", "")

    expected_districts = sorted(districts_for_constituency(state, constituency, ctx))
    found_districts: list[str] = []
    missing_districts: list[str] = []
    for district in expected_districts:
        nfhs_rows = ctx.nfhs_rows(state, district)
        if nfhs_rows.empty or not nfhs_rows.apply(
            lambda row: has_any_numeric_values(row, NFHS_VALUE_COLUMNS),
            axis=1,
        ).any():
            missing_districts.append(district)
        else:
            found_districts.append(district)

    break_point = classify_constituency_break_point(
        state,
        constituency,
        ctx,
        in_master,
        in_delim,
        panel_row,
        master_row,
        has_nfhs5_values,
        float(coverage_share) if pd.notna(coverage_share) else None,
        missing_districts,
    )
    suggestion = repair_suggestion_for_constituency(
        state,
        constituency,
        break_point,
        ctx,
        missing_districts,
    )

    return {
        "audit_level": "constituency",
        "state": state,
        "district": "",
        "district_key": "",
        "constituency": constituency,
        "constituency_key": constituency_key,
        "exists_in_nfhs_district_panel": False,
        "has_nfhs4": False,
        "has_nfhs5": False,
        "has_any_nfhs_values": False,
        "exists_in_district_alias_table": False,
        "alias_target": "",
        "appears_in_delimitation_district_summary": in_delim,
        "appears_in_constituency_panel": in_panel,
        "appears_in_analysis_master": in_master and has_nfhs5_values,
        "exists_in_election_master": in_master,
        "exists_in_delimitation_summary": in_delim,
        "exists_in_constituency_panel": in_panel,
        "has_nfhs5_values": has_nfhs5_values,
        "nfhs5_coverage_share": coverage_share,
        "districts_expected": "; ".join(expected_districts),
        "districts_found_in_nfhs": "; ".join(found_districts),
        "districts_missing_in_nfhs": "; ".join(missing_districts),
        "suspected_break_point": break_point,
        "repair_suggestion": suggestion,
    }


def audit_state(state: str, ctx: GapAuditContext) -> pd.DataFrame:
    district_rows = [audit_district(state, district, ctx) for district in collect_districts(state, ctx)]
    constituency_rows = [
        audit_constituency(state, constituency, ctx)
        for constituency in collect_constituencies(state, ctx)
    ]
    return pd.DataFrame(district_rows + constituency_rows)


def state_metrics(state: str, audit_df: pd.DataFrame, ctx: GapAuditContext) -> dict[str, object]:
    constituency_rows = audit_df[audit_df["audit_level"] == "constituency"]
    district_rows = audit_df[audit_df["audit_level"] == "district"]
    state_key = normalise_state_key(state)

    break_counts = constituency_rows["suspected_break_point"].value_counts()
    top_break = break_counts.index[0] if not break_counts.empty else "unknown"

    nfhs_state_rows = ctx.rows_for_state(ctx.nfhs_panel, state)
    return {
        "state": state,
        "election_constituencies": int(
            ctx.rows_for_state(ctx.master, state)["constituency_key"].nunique()
        ),
        "constituencies_in_delimitation_summary": len(
            [k for k in ctx.delim_constituency_districts if k[0] == state_key]
        ),
        "constituencies_in_panel": int(constituency_rows["exists_in_constituency_panel"].sum()),
        "constituencies_with_nfhs5_values": int(constituency_rows["has_nfhs5_values"].sum()),
        "districts_in_nfhs_panel": int(nfhs_state_rows["district_key"].nunique())
        if "district_key" in nfhs_state_rows.columns
        else int(nfhs_state_rows["district"].nunique()),
        "districts_in_delimitation_summary": len(ctx.delim_districts_by_state.get(state, set())),
        "districts_with_nfhs_values": int(
            district_rows[district_rows["has_any_nfhs_values"]]["district_key"].nunique()
        ),
        "top_suspected_break_point": top_break,
        "top_break_count": int(break_counts.iloc[0]) if not break_counts.empty else 0,
    }


def problem_type(state: str, metrics: dict[str, object], audit_df: pd.DataFrame) -> str:
    constituency_rows = audit_df[audit_df["audit_level"] == "constituency"]
    top_break = metrics["top_suspected_break_point"]
    if top_break == "delimitation_summary_missing":
        return "mapping problem (delimitation reference missing)"
    if top_break == "name_normalization_mismatch":
        return "mapping problem (state/constituency naming)"
    if top_break in {"missing_nfhs_district_features", "low_coverage_share"}:
        return "data problem (NFHS district features missing or empty)"
    if top_break == "constituency_panel_aggregation_failed":
        if metrics["districts_with_nfhs_values"] > 0:
            return "mapping problem (district aliases / aggregation logic)"
        return "data problem (upstream NFHS district coverage)"
    if state == "Tamil Nadu":
        return "mapping problem (state absent from delimitation summary)"
    return "mixed data and mapping problem"


def build_summary_text(
    all_audits: dict[str, pd.DataFrame],
    metrics_list: list[dict[str, object]],
) -> str:
    lines = [
        "State gap audit summary",
        "=======================",
        "",
        "Priority states audited: West Bengal, Tamil Nadu, Assam, Uttarakhand",
        "",
        "Biggest missing state problems",
        "------------------------------",
    ]

    for metrics in sorted(metrics_list, key=lambda m: m["constituencies_with_nfhs5_values"]):
        state = metrics["state"]
        lines.append(
            f"- {state}: {metrics['constituencies_with_nfhs5_values']}/"
            f"{metrics['election_constituencies']} constituencies with NFHS-5 values; "
            f"top break = {metrics['top_suspected_break_point']} "
            f"({metrics['top_break_count']} constituencies)"
        )
        lines.append(f"  Problem type: {problem_type(state, metrics, all_audits[state])}")

    lines.extend(
        [
            "",
            "Recommended fix order",
            "---------------------",
            "1. Tamil Nadu — parse/add Schedule XXVI delimitation district summary (blocks entire state).",
            "2. Uttarakhand — extract NFHS district features (no Uttarakhand rows in nfhs_district_panel).",
            "3. West Bengal — fix district alias application for Medinipur/Bardhaman splits and panel aggregation.",
            "4. Assam — complete district alias coverage and NFHS district feature joins.",
            "",
            "Whether issues are data vs mapping",
            "----------------------------------",
        ]
    )

    for metrics in metrics_list:
        state = metrics["state"]
        lines.append(f"- {state}: {problem_type(state, metrics, all_audits[state])}")

    lines.extend(
        [
            "",
            "Notes",
            "-----",
            "- This audit is diagnostics only; source files were not modified.",
            "- West Bengal has NFHS district rows for 19 districts but constituency panel coverage_share is 0 for all seats.",
            "- Tamil Nadu has NFHS district data but no delimitation constituency-district summary in the reference tables.",
            "- Uttarakhand has delimitation and alias mappings but zero Uttarakhand rows in nfhs_district_panel.csv.",
        ]
    )
    return "\n".join(lines) + "\n"


def print_state_summary(metrics: dict[str, object]) -> None:
    print(f"\n{metrics['state']}")
    print(f"  Election constituencies: {metrics['election_constituencies']}")
    print(f"  In delimitation summary: {metrics['constituencies_in_delimitation_summary']}")
    print(f"  In constituency panel: {metrics['constituencies_in_panel']}")
    print(f"  With NFHS-5 values: {metrics['constituencies_with_nfhs5_values']}")
    print(f"  Districts in NFHS panel: {metrics['districts_in_nfhs_panel']}")
    print(f"  Districts in delimitation summary: {metrics['districts_in_delimitation_summary']}")
    print(
        f"  Top suspected break point: {metrics['top_suspected_break_point']} "
        f"({metrics['top_break_count']} constituencies)"
    )


def main() -> None:
    ctx = GapAuditContext()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    all_frames: list[pd.DataFrame] = []
    metrics_list: list[dict[str, object]] = []
    all_audits: dict[str, pd.DataFrame] = {}

    print("Running state gap audits...")
    for state in PRIORITY_STATES:
        audit_df = audit_state(state, ctx)
        all_audits[state] = audit_df
        metrics = state_metrics(state, audit_df, ctx)
        metrics_list.append(metrics)

        out_path = OUTPUT_DIR / STATE_OUTPUT_FILES[state]
        audit_df.to_csv(out_path, index=False)
        all_frames.append(audit_df)
        print(f"  Saved {out_path} ({len(audit_df)} rows)")

    combined = pd.concat(all_frames, ignore_index=True)
    combined_path = OUTPUT_DIR / "all_priority_states_gap_audit.csv"
    combined.to_csv(combined_path, index=False)
    print(f"  Saved {combined_path} ({len(combined)} rows)")

    summary_text = build_summary_text(all_audits, metrics_list)
    SUMMARY_PATH.write_text(summary_text, encoding="utf-8")
    print(f"  Saved {SUMMARY_PATH}")

    print("\n=== State gap audit summary ===")
    for metrics in metrics_list:
        print_state_summary(metrics)


if __name__ == "__main__":
    main()
