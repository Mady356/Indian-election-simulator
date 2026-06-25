"""Validate Seat Intelligence manual Markdown notes."""

from __future__ import annotations

import sys

from src.seat_analysis.common import MANUAL_NOTES_DIR, ensure_dirs
from src.seat_analysis.markdown_notes import (
    load_constituency_lookup,
    list_note_files,
    parse_markdown_note,
    validate_note,
)


def main() -> int:
    ensure_dirs()
    constituency_lookup = load_constituency_lookup()
    note_files = list_note_files(MANUAL_NOTES_DIR)

    if not note_files:
        print(f"No Markdown notes found in {MANUAL_NOTES_DIR}")
        return 1

    all_issues = []
    for path in note_files:
        try:
            note = parse_markdown_note(path)
        except ValueError as exc:
            all_issues.append((str(path), str(exc)))
            continue
        for issue in validate_note(note, constituency_lookup):
            all_issues.append((issue.path, issue.message))

    if all_issues:
        print(f"Validation failed for {len(all_issues)} issue(s):")
        for path, message in all_issues:
            print(f"  - {path}: {message}")
        return 1

    print(f"Validated {len(note_files)} manual note(s) in {MANUAL_NOTES_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
