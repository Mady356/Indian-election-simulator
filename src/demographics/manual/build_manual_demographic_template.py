"""Build a long-format CSV template for manual demographic entry."""

from __future__ import annotations

import argparse

import pandas as pd

from src.demographics.manual.common import (
    ALLOWED_VARIABLES,
    MANUAL_TEMPLATE_PATH,
    MASTER_PATH,
    TEMPLATE_COLUMNS,
    constituency_needs_manual_template,
    default_unit,
    ensure_dirs,
    generated_value_for_variable,
    lookup_key,
)


def build_template() -> pd.DataFrame:
    master = pd.read_csv(MASTER_PATH)
    rows: list[dict[str, str]] = []

    for _, row in master.iterrows():
        if not constituency_needs_manual_template(row):
            continue

        state = str(row["state"])
        constituency = str(row["constituency"])
        state_key = str(row["state_key"])
        constituency_key = str(row["constituency_key"])

        for variable in ALLOWED_VARIABLES:
            if generated_value_for_variable(row, variable) is not None:
                continue

            rows.append(
                {
                    "state": state,
                    "constituency": constituency,
                    "state_key": state_key,
                    "constituency_key": constituency_key,
                    "variable": variable,
                    "value": "",
                    "unit": default_unit(variable),
                    "source_name": "",
                    "source_url_or_document": "",
                    "source_year": "",
                    "geography_level": "",
                    "method": "",
                    "confidence": "",
                    "notes": "",
                    "entered_by": "",
                    "last_updated": "",
                    "override_allowed": "false",
                }
            )

    return pd.DataFrame(rows, columns=TEMPLATE_COLUMNS)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()

    ensure_dirs()
    template = build_template()
    template.to_csv(MANUAL_TEMPLATE_PATH, index=False)

    seats = template[["state_key", "constituency_key"]].drop_duplicates()
    print(f"Wrote {len(template)} template rows for {len(seats)} constituencies")
    print(f"Output: {MANUAL_TEMPLATE_PATH}")


if __name__ == "__main__":
    main()
