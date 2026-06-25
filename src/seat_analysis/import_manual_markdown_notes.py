"""Import validated Markdown seat notes into manual_seat_notes.csv."""

from __future__ import annotations

import sys
from datetime import date

import pandas as pd

from src.seat_analysis.common import (
    MANUAL_COLUMNS,
    MANUAL_NOTES_DIR,
    MANUAL_NOTES_PATH,
    MANUAL_NOTES_SEED_PATH,
    ensure_dirs,
    lookup_key,
)
from src.seat_analysis.markdown_notes import (
    load_baseline_lookup,
    load_constituency_lookup,
    list_note_files,
    match_seed_block_to_constituency,
    note_filename,
    note_to_csv_row,
    parse_markdown_note,
    parse_seed_file,
    render_note_markdown,
    validate_note,
)


DEFAULT_KEY_FACTORS = "candidate profile;alliance arithmetic;turnout;local context;state mood"
DEFAULT_ANALYST = "Maadhavan Gupta"
DEFAULT_SOURCE_NOTES = (
    "Based on The 543 election data and analyst-written local context; "
    "requires later source review."
)
DEFAULT_CAVEATS = (
    "This note is interpretive. Language such as “may have mattered” and "
    "“could reflect” is intentional. Patterns in The 543 data are not causal claims. "
    "Local context requires later source review."
)


def _baseline_demographic_block(baseline_lookup: dict, key: str) -> str:
    row = baseline_lookup.get(key)
    if row is None:
        return "_No baseline demographic context available._"
    demo = str(row.get("demographic_context", "")).strip()
    district = str(row.get("district_context", "")).strip()
    if demo and district:
        return f"{demo}\n\n{district}"
    return demo or district or "_No baseline demographic context available._"


def convert_seed_to_markdown(
    *,
    overwrite: bool = False,
    analyst_name: str = DEFAULT_ANALYST,
    source_notes: str = DEFAULT_SOURCE_NOTES,
    last_reviewed: str | None = None,
) -> list[str]:
    """Create or update Markdown notes from the seed file."""
    ensure_dirs()
    constituency_lookup = load_constituency_lookup()
    baseline_lookup = load_baseline_lookup()
    blocks = parse_seed_file(MANUAL_NOTES_SEED_PATH)
    if not blocks:
        raise FileNotFoundError(f"No seed blocks found in {MANUAL_NOTES_SEED_PATH}")

    reviewed = last_reviewed or date.today().isoformat()
    written: list[str] = []

    for block in blocks:
        constituency = match_seed_block_to_constituency(block["name"], constituency_lookup)
        if constituency is None:
            print(f"Warning: could not match seed constituency {block['name']!r}; skipping")
            continue

        key = lookup_key(constituency["state_key"], constituency["constituency_key"])
        out_path = MANUAL_NOTES_DIR / note_filename(
            constituency["state_key"],
            constituency["constituency_key"],
        )
        if out_path.exists() and not overwrite:
            print(f"Skipping existing note (use --from-seed to refresh): {out_path.name}")
            continue

        content = render_note_markdown(
            constituency,
            what_happened=block.get("what_happened", "").strip(),
            why_it_mattered=block.get("why_it_mattered", "").strip(),
            factors=block.get("factors", "").strip(),
            demographic_context=_baseline_demographic_block(baseline_lookup, key),
            what_to_watch=block.get("what_to_watch", "").strip(),
            notes_caveats=DEFAULT_CAVEATS,
            key_factors=DEFAULT_KEY_FACTORS,
            analyst_name=analyst_name,
            source_notes=source_notes,
            last_reviewed=reviewed,
        )
        out_path.write_text(content, encoding="utf-8")
        written.append(str(out_path))

    return written


def import_markdown_notes() -> pd.DataFrame:
    ensure_dirs()
    constituency_lookup = load_constituency_lookup()
    baseline_lookup = load_baseline_lookup()
    note_files = list_note_files(MANUAL_NOTES_DIR)

    if not note_files:
        raise FileNotFoundError(f"No Markdown notes found in {MANUAL_NOTES_DIR}")

    rows: list[dict[str, object]] = []
    for path in note_files:
        note = parse_markdown_note(path)
        issues = validate_note(note, constituency_lookup)
        if issues:
            messages = "; ".join(issue.message for issue in issues)
            raise ValueError(f"{path}: {messages}")
        rows.append(note_to_csv_row(note, baseline_lookup, constituency_lookup))

    imported = pd.DataFrame(rows, columns=MANUAL_COLUMNS)
    imported = imported.drop_duplicates(subset=["state_key", "constituency_key"], keep="last")

    if MANUAL_NOTES_PATH.exists():
        existing = pd.read_csv(MANUAL_NOTES_PATH)
        imported_keys = {
            lookup_key(str(row["state_key"]), str(row["constituency_key"]))
            for _, row in imported.iterrows()
        }
        keep = existing[
            ~existing.apply(
                lambda row: lookup_key(str(row["state_key"]), str(row["constituency_key"])) in imported_keys,
                axis=1,
            )
        ]
        merged = pd.concat([keep, imported], ignore_index=True)
    else:
        merged = imported

    merged = merged.drop_duplicates(subset=["state_key", "constituency_key"], keep="last")
    merged.to_csv(MANUAL_NOTES_PATH, index=False)
    return merged


def main() -> int:
    from_seed = "--from-seed" in sys.argv
    try:
        if from_seed:
            written = convert_seed_to_markdown(overwrite=True)
            print(f"Wrote {len(written)} note(s) from seed")
        df = import_markdown_notes()
    except (FileNotFoundError, ValueError) as exc:
        print(exc)
        return 1

    print(f"Imported {len(df)} manual note row(s) to {MANUAL_NOTES_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
