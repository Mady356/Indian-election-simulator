"""Build structured research packets for every constituency."""

from __future__ import annotations

import json

import pandas as pd

from src.seat_analysis.common import (
    BASELINE_CSV_PATH,
    CONSTITUENCY_COVERAGE_PATH,
    FINAL_CSV_PATH,
    MONTE_CARLO_BASE_PATH,
    PRIORITY_CSV_PATH,
    RESEARCH_PACKETS_JSON_DIR,
    RESEARCH_PACKETS_MD_DIR,
    ensure_dirs,
    load_master,
    lookup_key,
    packet_filename,
)
from src.seat_analysis.research_packet import (
    build_research_packet,
    load_manual_csv_lookup,
    load_manual_markdown_lookup,
    load_monte_carlo_lookup,
    load_priority_lookup_by_keys,
    load_state_lookup,
    render_packet_markdown,
)


def _lookup_from_csv(path, key_cols=("state_key", "constituency_key")) -> dict[str, pd.Series]:
    if not path.exists():
        return {}
    df = pd.read_csv(path)
    lookup: dict[str, pd.Series] = {}
    for _, row in df.iterrows():
        key = lookup_key(str(row[key_cols[0]]), str(row[key_cols[1]]))
        lookup[key] = row
    return lookup


def main() -> None:
    ensure_dirs()
    master = load_master()
    priority_df = pd.read_csv(PRIORITY_CSV_PATH) if PRIORITY_CSV_PATH.exists() else pd.DataFrame()

    state_lookup = load_state_lookup()
    priority_lookup = load_priority_lookup_by_keys(master, priority_df)
    baseline_lookup = _lookup_from_csv(BASELINE_CSV_PATH)
    final_lookup = _lookup_from_csv(FINAL_CSV_PATH)
    coverage_lookup = _lookup_from_csv(CONSTITUENCY_COVERAGE_PATH)
    monte_carlo_lookup = load_monte_carlo_lookup(MONTE_CARLO_BASE_PATH)
    manual_md_lookup = load_manual_markdown_lookup()
    manual_csv_lookup = load_manual_csv_lookup()

    count = 0
    for _, row in master.iterrows():
        packet = build_research_packet(
            row,
            state_lookup=state_lookup,
            priority_lookup=priority_lookup,
            baseline_lookup=baseline_lookup,
            final_lookup=final_lookup,
            coverage_lookup=coverage_lookup,
            monte_carlo_lookup=monte_carlo_lookup,
            manual_md_lookup=manual_md_lookup,
            manual_csv_lookup=manual_csv_lookup,
        )
        state_key = str(row["state_key"])
        constituency_key = str(row["constituency_key"])
        json_path = RESEARCH_PACKETS_JSON_DIR / packet_filename(state_key, constituency_key, "json")
        md_path = RESEARCH_PACKETS_MD_DIR / packet_filename(state_key, constituency_key, "md")
        json_path.write_text(json.dumps(packet, indent=2), encoding="utf-8")
        md_path.write_text(render_packet_markdown(packet), encoding="utf-8")
        count += 1

    print(f"Wrote {count} research packets to:")
    print(f"  JSON: {RESEARCH_PACKETS_JSON_DIR}")
    print(f"  Markdown: {RESEARCH_PACKETS_MD_DIR}")


if __name__ == "__main__":
    main()
