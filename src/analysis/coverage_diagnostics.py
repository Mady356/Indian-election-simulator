"""
Coverage diagnostics for the constituency election-demographic master table.

Run:
    python -m src.analysis.coverage_diagnostics
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from src.analysis.analysis_common import (
    ANALYSIS_DIR,
    CHANGE_COLUMNS,
    DEMOGRAPHICS_DIR,
    NFHS5_LEVEL_COLUMNS,
    REFERENCE_DIR,
    TARGET_COLUMNS,
    add_join_keys,
    demographic_lookup_keys,
    normalise_constituency_key,
    normalise_state_key,
)

MASTER_PATH = ANALYSIS_DIR / "constituency_election_demographic_master.csv"
PANEL_PATH = DEMOGRAPHICS_DIR / "constituency_demographic_panel.csv"
CHANGE_PATH = DEMOGRAPHICS_DIR / "constituency_demographic_change_features.csv"
DELIMITATION_PATH = REFERENCE_DIR / "lok_sabha_district_summary_delimitation.csv"

COVERAGE_DIR = ANALYSIS_DIR / "coverage"
STATE_COVERAGE_PATH = COVERAGE_DIR / "state_coverage.csv"
VARIABLE_COVERAGE_PATH = COVERAGE_DIR / "variable_coverage.csv"
CONSTITUENCY_COVERAGE_PATH = COVERAGE_DIR / "constituency_coverage.csv"
MISSING_REASONS_PATH = COVERAGE_DIR / "missing_coverage_reasons.csv"
SUMMARY_PATH = COVERAGE_DIR / "coverage_summary.txt"

ALL_VARIABLES = NFHS5_LEVEL_COLUMNS + CHANGE_COLUMNS
LOW_COVERAGE_THRESHOLD = 0.5
MIN_CORRELATION_OBS = 3

# Known state naming drift between election files and demographic sources.
STATE_KEY_ALIASES = {
    "ODISHA": "ORISSA",
    "ORISSA": "ODISHA",
    "NCT OF DELHI": "DELHI",
    "DELHI": "NCT OF DELHI",
}


def load_inputs() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    print("Loading coverage diagnostic inputs...")
    print(f"  Master: {MASTER_PATH}")
    print(f"  Panel: {PANEL_PATH}")
    print(f"  Change features: {CHANGE_PATH}")
    print(f"  Delimitation: {DELIMITATION_PATH}")

    master = pd.read_csv(MASTER_PATH)
    panel = pd.read_csv(PANEL_PATH)
    delimitation = pd.read_csv(DELIMITATION_PATH)
    return master, panel, delimitation


def expand_lookup_keys(state_key: str, constituency_key: str) -> list[tuple[str, str]]:
    keys = demographic_lookup_keys(state_key, constituency_key)
    alias_state = STATE_KEY_ALIASES.get(state_key)
    if alias_state:
        keys.append((alias_state, constituency_key))
    return keys


def build_key_index(
    df: pd.DataFrame,
    state_col: str,
    constituency_col: str,
    already_keyed: bool = False,
    include_aliases: bool = True,
) -> set[tuple[str, str]]:
    if already_keyed:
        keyed = df
    else:
        keyed = add_join_keys(df, state_col, constituency_col)

    keys = set(zip(keyed["state_key"], keyed["constituency_key"]))

    if include_aliases:
        ap_rows = keyed[keyed["state_key"] == "ANDHRA PRADESH"]
        for _, row in ap_rows.iterrows():
            keys.add(("TELANGANA", row["constituency_key"]))

        for state_key, alias_state in STATE_KEY_ALIASES.items():
            alias_rows = keyed[keyed["state_key"] == alias_state]
            for _, row in alias_rows.iterrows():
                keys.add((state_key, row["constituency_key"]))

    return keys


def lookup_in_index(
    index: set[tuple[str, str]],
    state_key: str,
    constituency_key: str,
) -> bool:
    return any(key in index for key in expand_lookup_keys(state_key, constituency_key))


def lookup_panel_row(
    panel_nfhs5: pd.DataFrame,
    state_key: str,
    constituency_key: str,
) -> pd.Series | None:
    for sk, ck in expand_lookup_keys(state_key, constituency_key):
        match = panel_nfhs5[
            (panel_nfhs5["state_key"] == sk) & (panel_nfhs5["constituency_key"] == ck)
        ]
        if not match.empty:
            return match.iloc[0]
    return None


def has_any_value(row: pd.Series, columns: list[str]) -> bool:
    present = [col for col in columns if col in row.index]
    if not present:
        return False
    return pd.to_numeric(row[present], errors="coerce").notna().any()


def build_state_coverage(master: pd.DataFrame) -> pd.DataFrame:
    has_nfhs5_any = master[NFHS5_LEVEL_COLUMNS].notna().any(axis=1)
    has_change_any = master[CHANGE_COLUMNS].notna().any(axis=1)
    has_coverage_share = master["nfhs5_coverage_share"].notna()

    work = master.copy()
    work["has_nfhs5_any"] = has_nfhs5_any
    work["has_change_any"] = has_change_any
    work["has_coverage_share"] = has_coverage_share

    state = (
        work.groupby("state", as_index=False)
        .agg(
            total_election_constituencies=("constituency", "count"),
            constituencies_with_nfhs5_any=("has_nfhs5_any", "sum"),
            constituencies_with_nfhs5_coverage_share=("has_coverage_share", "sum"),
            mean_nfhs5_coverage_share=("nfhs5_coverage_share", "mean"),
            constituencies_with_change_features=("has_change_any", "sum"),
        )
    )

    state["missing_count"] = (
        state["total_election_constituencies"] - state["constituencies_with_nfhs5_any"]
    )
    state["coverage_pct"] = (
        state["constituencies_with_nfhs5_any"]
        / state["total_election_constituencies"]
        * 100
    ).round(2)

    return state.sort_values("coverage_pct", ascending=False).reset_index(drop=True)


def build_variable_coverage(master: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    total_rows = len(master)

    for variable in ALL_VARIABLES:
        if variable not in master.columns:
            continue

        values = pd.to_numeric(master[variable], errors="coerce")
        non_null_mask = values.notna()
        non_null_count = int(non_null_mask.sum())

        subset = master[non_null_mask]
        correlation_ready = 0
        for target in TARGET_COLUMNS:
            if target not in master.columns:
                continue
            target_values = pd.to_numeric(master[target], errors="coerce")
            correlation_ready = max(
                correlation_ready,
                int((non_null_mask & target_values.notna()).sum()),
            )

        rows.append(
            {
                "variable": variable,
                "non_null_count": non_null_count,
                "non_null_pct": round(non_null_count / total_rows * 100, 2)
                if total_rows
                else 0.0,
                "states_available": subset["state"].nunique() if non_null_count else 0,
                "constituencies_available": len(subset),
                "correlation_ready_count": correlation_ready,
            }
        )

    out = pd.DataFrame(rows)
    return out.sort_values("non_null_pct", ascending=False).reset_index(drop=True)


def build_constituency_coverage(master: pd.DataFrame) -> pd.DataFrame:
    has_nfhs5_any = master[NFHS5_LEVEL_COLUMNS].notna().any(axis=1)
    has_change_any = master[CHANGE_COLUMNS].notna().any(axis=1)

    available_counts = master[ALL_VARIABLES].notna().sum(axis=1)
    missing_counts = len(ALL_VARIABLES) - available_counts

    out = pd.DataFrame(
        {
            "state": master["state"],
            "constituency": master["constituency"],
            "constituency_id": master.get("constituency_id"),
            "state_key": master.get("state_key"),
            "constituency_key": master.get("constituency_key"),
            "has_election_data": True,
            "has_nfhs5_any": has_nfhs5_any,
            "nfhs5_coverage_share": master.get("nfhs5_coverage_share"),
            "has_change_any": has_change_any,
            "change_quality_flag": master.get("change_quality_flag"),
            "missing_features_count": missing_counts,
            "available_features_count": available_counts,
            "districts_used": master.get("districts_used"),
            "districts_missing": master.get("districts_missing"),
        }
    )
    return out.sort_values(["state", "constituency"]).reset_index(drop=True)


def direct_panel_match(
    panel_keys_direct: set[tuple[str, str]],
    state_key: str,
    constituency_key: str,
) -> bool:
    if (state_key, constituency_key) in panel_keys_direct:
        return True
    return (
        state_key == "TELANGANA"
        and ("ANDHRA PRADESH", constituency_key) in panel_keys_direct
    )


def diagnose_missing_reason(
    row: pd.Series,
    panel_nfhs5: pd.DataFrame,
    panel_keys_direct: set[tuple[str, str]],
    panel_keys_with_aliases: set[tuple[str, str]],
    delim_keys: set[tuple[str, str]],
) -> tuple[str, str]:
    state_key = str(row.get("state_key", ""))
    constituency_key = str(row.get("constituency_key", ""))

    in_delimitation = lookup_in_index(delim_keys, state_key, constituency_key)
    direct_panel = direct_panel_match(panel_keys_direct, state_key, constituency_key)
    alias_panel = lookup_in_index(panel_keys_with_aliases, state_key, constituency_key)
    panel_row = lookup_panel_row(panel_nfhs5, state_key, constituency_key)

    coverage_share = pd.to_numeric(row.get("nfhs5_coverage_share"), errors="coerce")
    districts_missing = row.get("districts_missing")

    if not in_delimitation:
        return (
            "no_delimitation_district_mapping",
            "Constituency is not in the delimitation district reference used by the demographic pipeline.",
        )

    if not direct_panel and alias_panel:
        return (
            "name_normalization_mismatch",
            "Constituency appears in the demographic panel under a different state naming convention.",
        )

    if panel_row is None:
        return (
            "no_constituency_demographic_match",
            "Constituency is in delimitation reference but has no NFHS-5 demographic panel row.",
        )

    if pd.notna(coverage_share) and coverage_share < LOW_COVERAGE_THRESHOLD:
        return (
            "low_coverage_share",
            f"Demographic panel row exists but coverage_share is below {LOW_COVERAGE_THRESHOLD}.",
        )

    if isinstance(districts_missing, str) and districts_missing.strip():
        return (
            "missing_nfhs_district_features",
            "District mapping exists but one or more districts are missing NFHS district features.",
        )

    if panel_row is not None and not has_any_value(panel_row, list(NFHS5_LEVEL_COLUMNS)):
        return (
            "missing_nfhs_district_features",
            "Demographic panel row exists but NFHS district features are empty.",
        )

    return (
        "unknown",
        "Missing coverage could not be classified confidently from available evidence.",
    )


def build_missing_reasons(
    master: pd.DataFrame,
    panel: pd.DataFrame,
    delimitation: pd.DataFrame,
) -> pd.DataFrame:
    panel_nfhs5 = add_join_keys(
        panel[panel["survey"] == "NFHS-5"].copy(),
        "state",
        "lok_sabha_constituency",
    )
    panel_keys_direct = build_key_index(
        panel_nfhs5,
        "state_key",
        "constituency_key",
        already_keyed=True,
        include_aliases=False,
    )
    panel_keys_with_aliases = build_key_index(
        panel_nfhs5,
        "state_key",
        "constituency_key",
        already_keyed=True,
        include_aliases=True,
    )
    delim_keys = build_key_index(delimitation, "state", "lok_sabha_constituency")

    has_nfhs5_any = master[NFHS5_LEVEL_COLUMNS].notna().any(axis=1)
    missing_rows = master[~has_nfhs5_any].copy()

    rows: list[dict[str, object]] = []
    for _, row in missing_rows.iterrows():
        state_key = str(row.get("state_key", normalise_state_key(row["state"])))
        constituency_key = str(
            row.get("constituency_key", normalise_constituency_key(row["constituency"]))
        )

        reason, notes = diagnose_missing_reason(
            row,
            panel_nfhs5,
            panel_keys_direct,
            panel_keys_with_aliases,
            delim_keys,
        )
        panel_row = lookup_panel_row(panel_nfhs5, state_key, constituency_key)

        rows.append(
            {
                "state": row["state"],
                "constituency": row["constituency"],
                "state_key": state_key,
                "constituency_key": constituency_key,
                "in_election_master": True,
                "in_demographic_panel": panel_row is not None,
                "in_delimitation_reference": lookup_in_index(
                    delim_keys,
                    state_key,
                    constituency_key,
                ),
                "normalized_key_match": direct_panel_match(
                    panel_keys_direct,
                    state_key,
                    constituency_key,
                ),
                "coverage_share_present": pd.notna(row.get("nfhs5_coverage_share")),
                "districts_missing_present": bool(
                    isinstance(row.get("districts_missing"), str)
                    and str(row.get("districts_missing")).strip()
                ),
                "nfhs5_coverage_share": row.get("nfhs5_coverage_share"),
                "districts_missing": row.get("districts_missing"),
                "suspected_reason": reason,
                "notes": notes,
            }
        )

    out = pd.DataFrame(rows)
    return out.sort_values(["suspected_reason", "state", "constituency"]).reset_index(drop=True)


def build_recommendations(
    master: pd.DataFrame,
    state_coverage: pd.DataFrame,
    variable_coverage: pd.DataFrame,
    missing_reasons: pd.DataFrame,
    panel: pd.DataFrame,
) -> list[str]:
    lines: list[str] = []
    total = len(master)
    with_nfhs5 = int(master[NFHS5_LEVEL_COLUMNS].notna().any(axis=1).sum())

    reason_counts = missing_reasons["suspected_reason"].value_counts()
    top_reason = reason_counts.index[0] if not reason_counts.empty else "unknown"
    top_reason_count = int(reason_counts.iloc[0]) if not reason_counts.empty else 0

    alias_count = int((missing_reasons["suspected_reason"] == "name_normalization_mismatch").sum())
    join_bug_recoverable = 0
    for _, row in missing_reasons.iterrows():
        if row["suspected_reason"] != "name_normalization_mismatch":
            continue
        panel_row = lookup_panel_row(
            add_join_keys(
                panel[panel["survey"] == "NFHS-5"].copy(),
                "state",
                "lok_sabha_constituency",
            ),
            row["state_key"],
            row["constituency_key"],
        )
        if panel_row is not None and has_any_value(panel_row, list(NFHS5_LEVEL_COLUMNS)):
            join_bug_recoverable += 1
    delim_gap = int(
        (missing_reasons["suspected_reason"] == "no_delimitation_district_mapping").sum()
    )
    low_cov = int((missing_reasons["suspected_reason"] == "low_coverage_share").sum())

    lines.append("Recommendations")
    lines.append("---------------")

    if alias_count > 0:
        lines.append(
            "- Join bug likely for some rows: "
            f"{alias_count} constituencies match the demographic panel only after state-name "
            "aliases (for example Odisha/Orissa or Delhi/NCT of Delhi)."
        )
        if join_bug_recoverable > 0:
            lines.append(
                f"  {join_bug_recoverable} of those alias-mismatch rows already have NFHS-5 "
                "values in the panel and could be recovered by fixing the master join."
            )
        else:
            lines.append(
                "  Most alias-mismatch rows still have empty district features in the panel, "
                "so a join fix alone will not recover many values."
            )
    else:
        lines.append(
            "- Join bug unlikely to be the main issue: few rows look like pure state-name mismatches."
        )

    if delim_gap > total * 0.3:
        lines.append(
            "- Real missing data is the main issue: "
            f"{delim_gap} of {total - with_nfhs5} uncovered constituencies are absent from the "
            "delimitation reference. Many are 2024-redistricted seats or states not yet mapped "
            "in the demographic pipeline."
        )
    else:
        lines.append(
            "- Coverage gaps are mixed: some constituencies are missing from delimitation mapping, "
            "while others have panel rows with weak district feature coverage."
        )

    fix_states = state_coverage.sort_values("coverage_pct").head(5)
    lines.append("- States to fix first:")
    for _, row in fix_states.iterrows():
        lines.append(
            f"  * {row['state']}: {row['coverage_pct']}% covered "
            f"({int(row['constituencies_with_nfhs5_any'])}/{int(row['total_election_constituencies'])})"
        )

    safe_vars = variable_coverage[
        (variable_coverage["non_null_pct"] >= 30)
        & (variable_coverage["correlation_ready_count"] >= MIN_CORRELATION_OBS)
    ]
    lines.append("- Variables relatively safe for exploratory analysis now:")
    if safe_vars.empty:
        lines.append("  * None meet the 30% non-null threshold yet.")
    else:
        for variable in safe_vars["variable"].head(6):
            lines.append(f"  * {variable}")

    weak_vars = variable_coverage.sort_values("non_null_pct").head(5)
    lines.append("- Variables to treat cautiously for now:")
    for _, row in weak_vars.iterrows():
        lines.append(f"  * {row['variable']}: {row['non_null_pct']}% non-null")

    lines.append(
        "- District-level analysis is currently safer than constituency-level analysis because "
        "constituency coverage is partial ("
        f"{with_nfhs5}/{total} constituencies with any NFHS-5 value) and many gaps come from "
        "district-to-constituency allocation or missing district NFHS features."
    )

    lines.append(
        f"- Biggest suspected missing reason: {top_reason} ({top_reason_count} constituencies)."
    )
    if low_cov > 0:
        lines.append(
            f"- {low_cov} constituencies have demographic panel rows but coverage_share below "
            f"{LOW_COVERAGE_THRESHOLD}; improving district NFHS coverage should help these seats."
        )

    return lines


def write_coverage_summary(
    master: pd.DataFrame,
    state_coverage: pd.DataFrame,
    variable_coverage: pd.DataFrame,
    missing_reasons: pd.DataFrame,
    panel: pd.DataFrame,
) -> None:
    total = len(master)
    with_nfhs5 = int(master[NFHS5_LEVEL_COLUMNS].notna().any(axis=1).sum())
    with_change = int(master[CHANGE_COLUMNS].notna().any(axis=1).sum())
    with_coverage_meta = int(master["nfhs5_coverage_share"].notna().sum())

    reason_counts = missing_reasons["suspected_reason"].value_counts()

    lines = [
        "Coverage diagnostics summary",
        "============================",
        "",
        f"Overall election rows: {total}",
        f"Rows with any NFHS-5 value: {with_nfhs5} ({with_nfhs5 / total * 100:.1f}%)",
        f"Rows with NFHS-5 coverage metadata: {with_coverage_meta}",
        f"Rows with any change feature: {with_change} ({with_change / total * 100:.1f}%)",
        "",
        "Top 10 states by NFHS-5 coverage:",
    ]

    for _, row in state_coverage.head(10).iterrows():
        lines.append(
            f"  {row['state']}: {row['coverage_pct']}% "
            f"({int(row['constituencies_with_nfhs5_any'])}/{int(row['total_election_constituencies'])})"
        )

    lines.append("")
    lines.append("Bottom 10 states by NFHS-5 coverage:")
    for _, row in state_coverage.tail(10).iterrows():
        lines.append(
            f"  {row['state']}: {row['coverage_pct']}% "
            f"({int(row['constituencies_with_nfhs5_any'])}/{int(row['total_election_constituencies'])})"
        )

    lines.append("")
    lines.append("Top 10 best-covered variables:")
    for _, row in variable_coverage.head(10).iterrows():
        lines.append(
            f"  {row['variable']}: {row['non_null_pct']}% "
            f"({int(row['non_null_count'])} constituencies)"
        )

    lines.append("")
    lines.append("Top 10 worst-covered variables:")
    for _, row in variable_coverage.tail(10).iterrows():
        lines.append(
            f"  {row['variable']}: {row['non_null_pct']}% "
            f"({int(row['non_null_count'])} constituencies)"
        )

    lines.append("")
    lines.append("Missing reason counts:")
    for reason, count in reason_counts.items():
        lines.append(f"  {reason}: {count}")

    lines.append("")
    lines.extend(
        build_recommendations(master, state_coverage, variable_coverage, missing_reasons, panel)
    )
    lines.append("")

    SUMMARY_PATH.write_text("\n".join(lines), encoding="utf-8")


def print_console_summary(
    master: pd.DataFrame,
    state_coverage: pd.DataFrame,
    variable_coverage: pd.DataFrame,
    missing_reasons: pd.DataFrame,
) -> None:
    total = len(master)
    with_nfhs5 = int(master[NFHS5_LEVEL_COLUMNS].notna().any(axis=1).sum())
    with_change = int(master[CHANGE_COLUMNS].notna().any(axis=1).sum())
    top_reason = (
        missing_reasons["suspected_reason"].value_counts().idxmax()
        if not missing_reasons.empty
        else "n/a"
    )

    print()
    print("=== Coverage diagnostics ===")
    print(f"Overall election rows: {total}")
    print(f"Rows with any NFHS-5 value: {with_nfhs5}")
    print(f"Rows with change features: {with_change}")
    print()
    print("Top 10 states by coverage:")
    print(
        state_coverage.head(10)[
            ["state", "coverage_pct", "constituencies_with_nfhs5_any", "total_election_constituencies"]
        ].to_string(index=False)
    )
    print()
    print("Bottom 10 states by coverage:")
    print(
        state_coverage.tail(10)[
            ["state", "coverage_pct", "constituencies_with_nfhs5_any", "total_election_constituencies"]
        ].to_string(index=False)
    )
    print()
    print("Top 10 best-covered variables:")
    print(
        variable_coverage.head(10)[
            ["variable", "non_null_pct", "correlation_ready_count"]
        ].to_string(index=False)
    )
    print()
    print("Top 10 worst-covered variables:")
    print(
        variable_coverage.tail(10)[
            ["variable", "non_null_pct", "correlation_ready_count"]
        ].to_string(index=False)
    )
    print()
    print(f"Biggest suspected missing reason: {top_reason}")
    print(f"Full report written to: {SUMMARY_PATH}")


def main() -> None:
    master, panel, delimitation = load_inputs()

    if "state_key" not in master.columns or "constituency_key" not in master.columns:
        master = add_join_keys(master, "state", "constituency")

    state_coverage = build_state_coverage(master)
    variable_coverage = build_variable_coverage(master)
    constituency_coverage = build_constituency_coverage(master)
    missing_reasons = build_missing_reasons(master, panel, delimitation)

    COVERAGE_DIR.mkdir(parents=True, exist_ok=True)
    state_coverage.to_csv(STATE_COVERAGE_PATH, index=False)
    variable_coverage.to_csv(VARIABLE_COVERAGE_PATH, index=False)
    constituency_coverage.to_csv(CONSTITUENCY_COVERAGE_PATH, index=False)
    missing_reasons.to_csv(MISSING_REASONS_PATH, index=False)
    write_coverage_summary(master, state_coverage, variable_coverage, missing_reasons, panel)

    print("Saved coverage diagnostics:")
    print(f"  {STATE_COVERAGE_PATH}")
    print(f"  {VARIABLE_COVERAGE_PATH}")
    print(f"  {CONSTITUENCY_COVERAGE_PATH}")
    print(f"  {MISSING_REASONS_PATH}")
    print(f"  {SUMMARY_PATH}")

    print_console_summary(master, state_coverage, variable_coverage, missing_reasons)


if __name__ == "__main__":
    main()
