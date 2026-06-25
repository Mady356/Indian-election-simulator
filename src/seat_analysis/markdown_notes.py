"""Parse and validate Seat Intelligence manual Markdown notes."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd
import yaml

from src.seat_analysis.common import (
    BASELINE_CSV_PATH,
    CONSTITUENCIES_JSON_PATH,
    MANUAL_COLUMNS,
    lookup_key,
    nan_to_none,
    non_empty_text,
)

REQUIRED_SECTIONS = [
    "What happened?",
    "Why it mattered",
    "Factors that may have mattered",
    "Demographic and district context",
    "What to watch next",
    "Notes / caveats",
]

SECTION_ALIASES = {
    "what happened": "What happened?",
    "what happened?": "What happened?",
    "why it mattered": "Why it mattered",
    "factors that may have mattered": "Factors that may have mattered",
    "demographic and district context": "Demographic and district context",
    "what to watch next": "What to watch next",
    "what to watch": "What to watch next",
    "notes / caveats": "Notes / caveats",
    "notes and caveats": "Notes / caveats",
}

REQUIRED_FRONTMATTER = [
    "state",
    "constituency",
    "state_key",
    "constituency_key",
    "manual_confidence",
    "analyst_name",
    "source_notes",
]

ELECTION_MOVEMENT_HINTS = re.compile(
    r"\b(flipped|retained|vote share|margin|percentage points|turnout changed)\b",
    re.IGNORECASE,
)

TYPO_FIXES = {
    "ltanpur": "Sultanpur",
}


@dataclass
class ValidationIssue:
    path: str
    message: str


@dataclass
class ParsedManualNote:
    path: Path
    frontmatter: dict[str, object]
    sections: dict[str, str] = field(default_factory=dict)

    @property
    def state_key(self) -> str:
        return str(self.frontmatter.get("state_key", "")).strip()

    @property
    def constituency_key(self) -> str:
        return str(self.frontmatter.get("constituency_key", "")).strip()


def note_filename(state_key: str, constituency_key: str) -> str:
    safe_state = state_key.replace(" ", "_")
    safe_constituency = constituency_key.replace(" ", "_")
    return f"{safe_state}__{safe_constituency}.md"


def fix_typos(text: str) -> str:
    fixed = text
    for typo, replacement in TYPO_FIXES.items():
        fixed = re.sub(rf"\b{re.escape(typo)}\b", replacement, fixed, flags=re.IGNORECASE)
    return fixed


def load_constituency_lookup() -> dict[str, dict[str, str]]:
    if not CONSTITUENCIES_JSON_PATH.exists():
        return {}
    records = json.loads(CONSTITUENCIES_JSON_PATH.read_text(encoding="utf-8"))
    lookup: dict[str, dict[str, str]] = {}
    for row in records:
        key = lookup_key(str(row["state_key"]), str(row["constituency_key"]))
        lookup[key] = {
            "state": str(row["state"]),
            "constituency": str(row["constituency"]),
            "state_key": str(row["state_key"]),
            "constituency_key": str(row["constituency_key"]),
        }
    return lookup


def load_baseline_lookup() -> dict[str, pd.Series]:
    if not BASELINE_CSV_PATH.exists():
        return {}
    baseline = pd.read_csv(BASELINE_CSV_PATH)
    lookup: dict[str, pd.Series] = {}
    for _, row in baseline.iterrows():
        key = lookup_key(str(row["state_key"]), str(row["constituency_key"]))
        lookup[key] = row
    return lookup


def parse_markdown_note(path: Path) -> ParsedManualNote:
    text = fix_typos(path.read_text(encoding="utf-8"))
    if not text.startswith("---"):
        raise ValueError(f"{path}: missing YAML frontmatter")

    parts = text.split("---", 2)
    if len(parts) < 3:
        raise ValueError(f"{path}: malformed frontmatter")

    frontmatter = yaml.safe_load(parts[1]) or {}
    body = parts[2].strip()
    sections = _parse_sections(body)
    return ParsedManualNote(path=path, frontmatter=frontmatter, sections=sections)


def _parse_sections(body: str) -> dict[str, str]:
    sections: dict[str, str] = {}
    current_heading: str | None = None
    buffer: list[str] = []

    def flush() -> None:
        nonlocal buffer, current_heading
        if current_heading is None:
            return
        content = "\n".join(buffer).strip()
        if content:
            sections[current_heading] = content
        buffer = []

    for line in body.splitlines():
        heading_match = re.match(r"^##\s+(.+?)\s*$", line.strip())
        if heading_match:
            flush()
            raw = heading_match.group(1).strip()
            canonical = SECTION_ALIASES.get(raw.lower(), raw)
            current_heading = canonical
            continue
        if current_heading is not None:
            buffer.append(line)

    flush()
    return sections


def validate_note(note: ParsedManualNote, constituency_lookup: dict[str, dict[str, str]]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    path = str(note.path)

    for field_name in REQUIRED_FRONTMATTER:
        if not non_empty_text(note.frontmatter.get(field_name)):
            issues.append(ValidationIssue(path, f"Missing frontmatter field: {field_name}"))

    key = lookup_key(note.state_key, note.constituency_key)
    if key not in constituency_lookup:
        issues.append(
            ValidationIssue(
                path,
                f"Unknown constituency key {note.state_key}::{note.constituency_key}",
            )
        )
    else:
        expected = constituency_lookup[key]
        if str(note.frontmatter.get("state")) != expected["state"]:
            issues.append(ValidationIssue(path, f"state mismatch: expected {expected['state']!r}"))
        if str(note.frontmatter.get("constituency")) != expected["constituency"]:
            issues.append(
                ValidationIssue(path, f"constituency mismatch: expected {expected['constituency']!r}")
            )

    for section in REQUIRED_SECTIONS:
        if section not in note.sections or not note.sections[section].strip():
            issues.append(ValidationIssue(path, f"Missing or empty section: {section}"))

    confidence = str(note.frontmatter.get("manual_confidence", "")).strip().lower()
    if confidence not in {"low", "medium", "high"}:
        issues.append(ValidationIssue(path, f"Invalid manual_confidence: {confidence!r}"))

    return issues


def has_election_movement(text: str) -> bool:
    return bool(ELECTION_MOVEMENT_HINTS.search(text))


def _summary_from_sections(note: ParsedManualNote) -> str:
    why = note.sections.get("Why it mattered", "").strip()
    if why:
        first_sentence = re.split(r"(?<=[.!?])\s+", why, maxsplit=1)[0].strip()
        if first_sentence:
            return first_sentence
    return why


def _factors_to_key_factors(note: ParsedManualNote) -> str:
    tags = str(note.frontmatter.get("key_factors") or "").strip()
    factors_body = note.sections.get("Factors that may have mattered", "").strip()
    if ";" in factors_body:
        extra = [p.strip() for p in factors_body.split(";") if p.strip()]
    else:
        extra = []
    pieces = [p.strip() for p in tags.split(";") if p.strip()]
    for item in extra:
        if item.lower() not in {p.lower() for p in pieces}:
            pieces.append(item)
    return ";".join(pieces)


def note_to_csv_row(
    note: ParsedManualNote,
    baseline_lookup: dict[str, pd.Series],
    constituency_lookup: dict[str, dict[str, str]],
) -> dict[str, object]:
    key = lookup_key(note.state_key, note.constituency_key)
    baseline = baseline_lookup.get(key)
    constituency = constituency_lookup[key]

    what_happened = note.sections.get("What happened?", "").strip()
    if baseline is not None and not has_election_movement(what_happened):
        electoral_movement = str(baseline.get("electoral_movement", "")).strip()
    else:
        electoral_movement = what_happened

    demographic_section = note.sections.get("Demographic and district context", "").strip()
    if baseline is not None:
        if not demographic_section or demographic_section.startswith("_From baseline"):
            demo = str(baseline.get("demographic_context", "")).strip()
            district = str(baseline.get("district_context", "")).strip()
            demographic_section = demo
            if district:
                demographic_section = f"{demo}\n\n{district}".strip()

    return {
        "state": constituency["state"],
        "constituency": constituency["constituency"],
        "state_key": constituency["state_key"],
        "constituency_key": constituency["constituency_key"],
        "manual_summary": _summary_from_sections(note),
        "manual_electoral_movement": electoral_movement,
        "manual_key_factors": _factors_to_key_factors(note),
        "manual_demographic_context": demographic_section,
        "manual_local_context": note.sections.get("Why it mattered", "").strip(),
        "manual_what_to_watch": note.sections.get("What to watch next", "").strip(),
        "manual_confidence": str(note.frontmatter.get("manual_confidence", "medium")).strip(),
        "analyst_name": str(note.frontmatter.get("analyst_name", "")).strip(),
        "last_reviewed": str(note.frontmatter.get("last_reviewed", "")).strip(),
        "source_notes": str(note.frontmatter.get("source_notes", "")).strip(),
    }


def parse_seed_file(seed_path: Path) -> list[dict[str, str]]:
    """Parse bulk seed markdown into constituency note blocks."""
    if not seed_path.exists():
        return []

    text = fix_typos(seed_path.read_text(encoding="utf-8"))
    lines = text.splitlines()
    blocks: list[dict[str, str]] = []
    current_name: str | None = None
    current_section: str | None = None
    sections: dict[str, list[str]] = {}

    def flush_block() -> None:
        nonlocal current_name, sections
        if not current_name:
            return
        blocks.append(
            {
                "name": current_name.strip(),
                **{k: "\n".join(v).strip() for k, v in sections.items()},
            }
        )
        sections = {}

    def is_constituency_header(index: int, line: str) -> bool:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            return False
        if stripped.endswith(":") or "`" in stripped:
            return False
        if len(stripped) > 60:
            return False
        if re.match(r"^(What happened|Why it mattered|Factors|What to watch)\b", stripped, re.I):
            return False
        # Header lines are short titles; body sentences usually contain a period.
        if "." in stripped:
            return False
        # Next non-empty line should begin a section.
        for j in range(index + 1, len(lines)):
            nxt = lines[j].strip()
            if not nxt:
                continue
            return bool(re.match(r"^What happened:?\s*$", nxt, re.IGNORECASE))
        return False

    for index, raw_line in enumerate(lines):
        line = raw_line.strip()
        if not line:
            continue

        if is_constituency_header(index, raw_line):
            flush_block()
            current_name = line
            current_section = None
            continue

        section_match = re.match(
            r"^(What happened|Why it mattered|Factors that may have mattered|What to watch):?\s*$",
            line,
            re.IGNORECASE,
        )
        if section_match:
            label = section_match.group(1).lower()
            if label.startswith("what happened"):
                current_section = "what_happened"
            elif label.startswith("why"):
                current_section = "why_it_mattered"
            elif label.startswith("factors"):
                current_section = "factors"
            else:
                current_section = "what_to_watch"
            sections.setdefault(current_section, [])
            continue

        if current_section:
            sections.setdefault(current_section, []).append(raw_line.rstrip())

    flush_block()
    return blocks


def match_seed_block_to_constituency(
    name: str,
    constituency_lookup: dict[str, dict[str, str]],
) -> dict[str, str] | None:
    normalized_name = fix_typos(name).strip().lower()
    for record in constituency_lookup.values():
        if record["constituency"].lower() == normalized_name:
            return record
        if record["constituency_key"].lower().replace("_", " ") == normalized_name:
            return record
    return None


def render_note_markdown(
    constituency: dict[str, str],
    *,
    what_happened: str,
    why_it_mattered: str,
    factors: str,
    demographic_context: str,
    what_to_watch: str,
    notes_caveats: str,
    key_factors: str,
    analyst_name: str,
    source_notes: str,
    last_reviewed: str,
    manual_confidence: str = "medium",
) -> str:
    fm = {
        "state": constituency["state"],
        "constituency": constituency["constituency"],
        "state_key": constituency["state_key"],
        "constituency_key": constituency["constituency_key"],
        "manual_confidence": manual_confidence,
        "analyst_name": analyst_name,
        "last_reviewed": last_reviewed,
        "source_notes": source_notes,
        "key_factors": key_factors,
    }
    yaml_block = yaml.safe_dump(fm, sort_keys=False, allow_unicode=True).strip()
    return (
        f"---\n{yaml_block}\n---\n\n"
        f"# {constituency['constituency']}\n\n"
        f"## What happened?\n\n{what_happened.strip()}\n\n"
        f"## Why it mattered\n\n{why_it_mattered.strip()}\n\n"
        f"## Factors that may have mattered\n\n{factors.strip()}\n\n"
        f"## Demographic and district context\n\n{demographic_context.strip()}\n\n"
        f"## What to watch next\n\n{what_to_watch.strip()}\n\n"
        f"## Notes / caveats\n\n{notes_caveats.strip()}\n"
    )


def list_note_files(notes_dir: Path) -> list[Path]:
    if not notes_dir.exists():
        return []
    return sorted(notes_dir.glob("*.md"))
