"""
Shared helpers for parsing the 2008 Delimitation Order PDF text.

The order uses several layout conventions across states (numbered-dot,
number-dash, wrapped reservation tags). Parsers here favour retaining
low-confidence rows over silent drops.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass, field

import pandas as pd

from src.reference.delimitation_paths import DELIMITATION_PDF

# Roman schedule → state/UT (Schedules I–II are seat-allocation tables, not parsed here).
ROMAN_TO_STATE: dict[str, str] = {
    "III": "Andhra Pradesh",
    "IV": "Arunachal Pradesh",
    "V": "Assam",
    "VI": "Bihar",
    "VII": "Chhattisgarh",
    "VIII": "Goa",
    "IX": "Gujarat",
    "X": "Haryana",
    "XI": "Himachal Pradesh",
    "XII": "Jammu and Kashmir",
    "XIII": "Jharkhand",
    "XIV": "Karnataka",
    "XV": "Kerala",
    "XVI": "Madhya Pradesh",
    "XVII": "Maharashtra",
    "XVIII": "Manipur",
    "XIX": "Meghalaya",
    "XX": "Mizoram",
    "XXI": "Nagaland",
    "XXII": "Orissa",
    "XXIII": "Punjab",
    "XXIV": "Rajasthan",
    "XXV": "Sikkim",
    "XXVI": "Tamil Nadu",
    "XXVII": "Tripura",
    "XXVIII": "Uttar Pradesh",
    "XXIX": "Uttarakhand",
    "XXX": "West Bengal",
    "XXXI": "Delhi",
    "XXXII": "Puducherry",
}

EXPECTED_LS_SEATS = 543
EXPECTED_AC_SEATS = 4120

SCHEDULE_RE = re.compile(r"SCHEDULE\s*[-–]\s*([IVXLC]+)", re.I)
DISTRICT_RE = re.compile(r"^\s*(\d+)\s*[–—\-]\s*DISTRICT\s*:\s*(.+?)\s*$", re.I)
AC_DOT_RE = re.compile(r"^\s*(\d+)\.\s+(.+?)(?:\s*\((SC|ST)\))?\s*$", re.I)
AC_DASH_NAME_RE = re.compile(r"^\s*(\d+)\s*-\s*(.+?)(?:\s*\((SC|ST)\))?\s*$")
AC_NUM_ONLY_RE = re.compile(r"^\s*(\d+)\.?\s*$")
RESERVATION_ONLY_RE = re.compile(r"^\((SC|ST)\)\s*$", re.I)
AC_SPACE_NAME_RE = re.compile(
    r"^\s*(\d+)\s{2,}(.+?)(?:\s*\((SC|ST)\))?\s*$",
    re.I,
)
AC_SEGMENT_SPACE_RE = re.compile(
    r"(\d+)\s+([A-Za-z][A-Za-z0-9 \-/\.&']+?)"
    r"(?:\s*\((SC|ST)\))?(?=\s*,|\s*$|\s+and\s+\d+\s|\s+\d+\s+[A-Za-z])",
    re.I,
)
LS_HEADER_DASH_RE = re.compile(r"^\s*(\d+)\s*-\s*(.+?)(?:\s*\((SC|ST)\))?\s*$")
LS_HEADER_DOT_RE = re.compile(r"^\s*(\d+)\.\s+(.+?)(?:\s*\((SC|ST)\))?\s*$")
AC_DASH = r"[-—–~]"
AC_LEAD = rf"(?:{AC_DASH}|\.)\s*"
AC_SEGMENT_RE = re.compile(
    rf"(\d+)\s*{AC_DASH}\s*([A-Za-z][A-Za-z0-9 \-/\.&']+?)"
    rf"(?:\s*\((SC|ST)\))?(?=\s*,|\s*$|\s+\d+\s*{AC_DASH}|\s+\d+\.\s|\s+and\s+\d+\s*{AC_DASH})",
    re.I,
)
AC_SEGMENT_DOT_RE = re.compile(
    r"(\d+)\.\s*([A-Za-z][A-Za-z0-9 \-/\.&']+?)"
    r"(?:\s*\((SC|ST)\))?(?=\s*,|\s*$|\s+\d+\.\s|\s+\d+\s*[-—–~]|\s+&|\s+and\s+\d+)",
    re.I,
)
LS_HEADER_DOT_RE = re.compile(r"^\s*(\d+)\.\s+(.+?)(?:\s*\((SC|ST)\))?\s*\.?\s*$")

SKIP_LINE_PATTERNS = (
    re.compile(r"^Sl\.?\s*No", re.I),
    re.compile(r"^Extent of", re.I),
    re.compile(r"^Serial no", re.I),
    re.compile(r"^NOTE", re.I),
    re.compile(r"^Note\.?", re.I),
    re.compile(r"^Any reference", re.I),
    re.compile(r"^The entire area", re.I),
    re.compile(r"^Delimitation Order", re.I),
    re.compile(r"^TABLE OF CONTENTS", re.I),
    re.compile(r"^Contents$", re.I),
    re.compile(r"^PAGE$", re.I),
)


def normalize_key(value: object) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    text = str(value).strip().upper()
    text = text.replace("&", " AND ")
    text = re.sub(r"[–—\-/]", " ", text)
    text = re.sub(r"[^A-Z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def clean_display_name(value: object) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    text = str(value).strip()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\s*\((SC|ST)\)\s*$", "", text, flags=re.I)
    return text.strip(" .,-")


def split_reservation(name: str) -> tuple[str, str]:
    match = re.search(r"\((SC|ST)\)\s*$", name.strip(), re.I)
    if match:
        base = re.sub(r"\s*\((SC|ST)\)\s*$", "", name.strip(), flags=re.I).strip()
        return base, match.group(1).upper()
    return name.strip(), ""


def pdf_page_count(pdf_path: str | None = None) -> int:
    path = pdf_path or str(DELIMITATION_PDF)
    result = subprocess.run(
        ["pdfinfo", path],
        capture_output=True,
        text=True,
        check=True,
    )
    for line in result.stdout.splitlines():
        if line.startswith("Pages:"):
            return int(line.split(":", 1)[1].strip())
    raise RuntimeError("Could not read page count from pdfinfo")


def extract_pdf_pages(pdf_path: str | None = None) -> pd.DataFrame:
    """Extract one row per PDF page using pdftotext."""
    path = str(pdf_path or DELIMITATION_PDF)
    pages = pdf_page_count(path)
    rows: list[dict[str, object]] = []
    for page_num in range(1, pages + 1):
        result = subprocess.run(
            ["pdftotext", "-layout", "-f", str(page_num), "-l", str(page_num), path, "-"],
            capture_output=True,
            text=True,
            check=True,
        )
        rows.append({"page_number": page_num, "text": result.stdout})
    return pd.DataFrame(rows)


def _should_skip_line(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return True
    if stripped.isdigit() and len(stripped) <= 3:
        return True
    return any(p.search(stripped) for p in SKIP_LINE_PATTERNS)


def _extract_schedule_roman(line: str) -> str | None:
    match = SCHEDULE_RE.search(line)
    return match.group(1).upper() if match else None


def _is_appendix_header(line: str) -> bool:
    """True only for standalone APPENDIX section headers, not extent references."""
    upper = line.strip().upper()
    if not upper.startswith("APPENDIX"):
        return False
    # Wrapped extent lines: "Appendix] in Karimganj sub-division."
    if re.search(r"APPENDIX\]", upper):
        return False
    # Inline references: "item (3) of the Appendix in …"
    if re.search(r"\b(?:OF |THE )APPENDIX\b", upper) and not re.match(r"^APPENDIX(?:\s|$)", upper):
        return False
    return bool(re.match(r"^APPENDIX(?:\s*-\s*DISTRICT)?\s*$", upper))


def _detect_section(line: str) -> str | None:
    upper = line.upper()
    if "TABLE A" in upper and "ASSEMBLY" in upper:
        return "table_a"
    if "PART A" in upper and "ASSEMBLY" in upper:
        return "table_a"
    if "TABLE B" in upper and "PARLIAMENTARY" in upper:
        return "table_b"
    if "PART B" in upper and "PARLIAMENTARY" in upper:
        return "table_b"
    if "PART - B" in upper and "PARLIAMENTARY" in upper:
        return "table_b"
    if "PARLIAMENTARY CONSTITUENCIES" in upper and "SERIAL" in upper:
        return "table_b"
    if "ANNEXURE" in upper and "ASSEMBLY" in upper:
        return "table_a"
    if _is_appendix_header(line):
        return "appendix"
    return None


def _is_appendix_village_line(line: str) -> bool:
    stripped = line.strip()
    if not re.match(r"^\d+\.\s+[A-Za-z]", stripped):
        return False
    if re.search(r"(thana|sub-division|mouza|district|constituency|taluk)", stripped, re.I):
        return False
    return True


def _is_ls_header_line(line: str, section: str) -> bool:
    if section != "table_b":
        return False
    stripped = line.strip()
    if AC_SEGMENT_RE.fullmatch(stripped.rstrip(",")):
        return False
    match = LS_HEADER_DASH_RE.match(stripped)
    if match and match.group(1).isdigit():
        name = match.group(2).strip()
        if len(name) >= 3 and name[0].isupper():
            return True
    match = LS_HEADER_DOT_RE.match(stripped)
    if match and not stripped.lower().startswith("ward"):
        name = match.group(2).strip()
        if len(name) >= 3:
            return True
    return False


def _parse_ls_header(line: str) -> tuple[int, str, str] | None:
    stripped = line.strip()
    for pattern in (LS_HEADER_DASH_RE, LS_HEADER_DOT_RE):
        match = pattern.match(stripped)
        if match:
            num = int(match.group(1))
            name, reservation = split_reservation(match.group(2).strip())
            if pattern is LS_HEADER_DOT_RE and reservation == "" and match.lastindex >= 3 and match.group(3):
                reservation = match.group(3).upper()
            return num, clean_display_name(name), reservation
    return None


def _preprocess_ac_segment_text(text: str) -> str:
    """Fix glued AC numbers (e.g. 22Virugambakkam) before segment extraction."""
    normalized = re.sub(r"\band\b", ",", text, flags=re.I)
    normalized = re.sub(r"\s*&\s*", ",", normalized)
    normalized = re.sub(r"(\d)([A-Za-z])", r"\1 \2", normalized)
    return normalized


def _extract_ac_segments(text: str) -> list[tuple[int, str, str]]:
    segments: list[tuple[int, str, str]] = []
    seen: set[int] = set()
    normalized = _preprocess_ac_segment_text(text)
    for pattern in (AC_SEGMENT_RE, AC_SEGMENT_DOT_RE, AC_SEGMENT_SPACE_RE):
        for match in pattern.finditer(normalized):
            ac_no = int(match.group(1))
            if ac_no in seen:
                continue
            name = clean_display_name(match.group(2))
            if not name or len(name) < 2:
                continue
            reservation = (match.group(3) or "").upper()
            segments.append((ac_no, name, reservation))
            seen.add(ac_no)
    return segments


def _split_ls_line(line: str) -> tuple[tuple[int, str, str] | None, str]:
    """
    Split a Table B line into (LS header, AC segment text).

    Supports both dash and dot LS numbering, e.g.:
      1-ADILABAD (ST)      1-Sirpur, ...
      1. Valmiki Nagar     1- Valmiki Nagar, ...
    """
    stripped = line.strip()
    for lead_pattern in (r"^(\d+)\s*-\s*(.+)$", r"^(\d+)\.\s*(.+)$"):
        match = re.match(lead_pattern, stripped)
        if not match:
            continue
        ls_no = int(match.group(1))
        rest = match.group(2)
        split = re.search(rf"\s{{2,}}(\d+\s*{AC_LEAD}.*)$", rest)
        if not split:
            split = re.search(r"\s{2,}(\d+\s+[A-Za-z].*)$", rest)
        if split:
            ls_name_part = rest[: split.start()].strip()
            ac_text = rest[split.start() :].strip()
        else:
            ls_name_part = rest.strip()
            ac_text = ""

        ls_name_part = ls_name_part.rstrip(".")
        ls_name, reservation = split_reservation(ls_name_part)
        return (ls_no, clean_display_name(ls_name), reservation), ac_text
    return None, stripped


def _is_table_b_continuation(line: str) -> bool:
    """Indented lines in Table B continue AC segments for the current LS seat."""
    leading = len(line) - len(line.lstrip(" "))
    return leading >= 5


def _is_table_b_name_wrap(line: str) -> bool:
    """Wrapped LS constituency names (e.g. Paschim / Champaran) with optional AC tail."""
    stripped = line.strip()
    if not stripped or re.match(r"^\d+\s*[-\.]", stripped):
        return False
    leading = len(line) - len(line.lstrip(" "))
    return 0 < leading < 5


def _handle_table_b_name_wrap(ctx: ParseContext, line: str) -> None:
    stripped = line.strip()
    split = re.search(rf"\s{{2,}}(\d+\s*{AC_LEAD}.*)$", stripped)
    if split:
        name_part = stripped[: split.start()].strip()
        ac_text = stripped[split.start() :].strip()
        if name_part:
            ctx.current_ls_name = f"{ctx.current_ls_name} {name_part}".strip()
        if ac_text:
            ctx.ls_buffer_lines.append(ac_text)
    elif ctx.current_ls_name:
        ctx.current_ls_name = f"{ctx.current_ls_name} {stripped}".strip()


def _is_table_b_ls_start(line: str) -> bool:
    stripped = line.strip()
    if not re.match(r"^\d+\s*[-\.]", stripped):
        return False
    if _is_table_b_continuation(line):
        return False
    body_match = re.match(r"^\d+\s*[-\.]\s*(.+)$", stripped)
    if not body_match:
        return False
    body = body_match.group(1)
    if re.search(rf"\s{{2,}}\d+\s*(?:{AC_DASH}|\\.)", body):
        return True
    if re.search(r"\s{2,}\d+\s+[A-Za-z]", body):
        return True
    if not re.search(rf"\d+\s*(?:{AC_DASH}|\\.)", body):
        return True
    return False


@dataclass
class ParseContext:
    state: str | None = None
    section: str | None = None
    district: str | None = None
    appendix_skip: bool = False
    current_ls_no: int | None = None
    current_ls_name: str | None = None
    current_ls_reservation: str = ""
    pending_ac_no: int | None = None
    pending_ac_name: str | None = None
    pending_ac_reservation: str = ""
    extent_lines: list[str] = field(default_factory=list)
    ls_buffer_lines: list[str] = field(default_factory=list)


def _flush_assembly(
    ctx: ParseContext,
    page_num: int,
    rows: list[dict[str, object]],
    confidence: str = "high",
) -> None:
    if ctx.pending_ac_no is None or not ctx.pending_ac_name or not ctx.state:
        return
    name = clean_display_name(ctx.pending_ac_name)
    reservation = ctx.pending_ac_reservation
    if not reservation:
        name, reservation = split_reservation(name)
    rows.append(
        {
            "state": ctx.state,
            "assembly_no": ctx.pending_ac_no,
            "assembly_constituency": name,
            "district": ctx.district or "",
            "reservation_status": reservation,
            "raw_extent_text": " ".join(ctx.extent_lines).strip(),
            "source_page": page_num,
            "parse_confidence": confidence,
        }
    )
    ctx.pending_ac_no = None
    ctx.pending_ac_name = None
    ctx.pending_ac_reservation = ""
    ctx.extent_lines = []


def _is_table_a_ac_start(stripped: str) -> bool:
    return bool(
        AC_DOT_RE.match(stripped)
        or (AC_DASH_NAME_RE.match(stripped) and not stripped.endswith(","))
        or AC_SPACE_NAME_RE.match(stripped)
        or AC_NUM_ONLY_RE.match(stripped)
    )


def _start_table_a_ac_line(ctx: ParseContext, stripped: str) -> None:
    """Start a new Table A AC row from a numbered constituency line."""
    ac_dot = AC_DOT_RE.match(stripped)
    if ac_dot:
        name = ac_dot.group(2).strip()
        reservation = (ac_dot.group(3) or "").upper()
        ctx.pending_ac_no = int(ac_dot.group(1))
        ctx.pending_ac_name = name
        ctx.pending_ac_reservation = reservation
        if not reservation:
            _, ctx.pending_ac_reservation = split_reservation(name)
        return

    ac_dash = AC_DASH_NAME_RE.match(stripped)
    if ac_dash and not stripped.endswith(","):
        name = ac_dash.group(2).strip()
        reservation = (ac_dash.group(3) or "").upper()
        ctx.pending_ac_no = int(ac_dash.group(1))
        ctx.pending_ac_name = name
        ctx.pending_ac_reservation = reservation
        return

    ac_space = AC_SPACE_NAME_RE.match(stripped)
    if ac_space:
        rest = ac_space.group(2).strip()
        name_part = re.split(r"\s{2,}", rest, maxsplit=1)[0].strip()
        reservation = (ac_space.group(3) or "").upper()
        ctx.pending_ac_no = int(ac_space.group(1))
        ctx.pending_ac_name = name_part
        ctx.pending_ac_reservation = reservation
        if not reservation:
            _, ctx.pending_ac_reservation = split_reservation(name_part)
        extent_tail = re.split(r"\s{2,}", rest, maxsplit=1)
        if len(extent_tail) > 1:
            ctx.extent_lines = [extent_tail[1].strip()]
        return

    ac_num = AC_NUM_ONLY_RE.match(stripped)
    if ac_num:
        ctx.pending_ac_no = int(ac_num.group(1))
        ctx.pending_ac_name = None
        ctx.pending_ac_reservation = ""


def _flush_ls_segments(
    ctx: ParseContext,
    page_num: int,
    rows: list[dict[str, object]],
) -> None:
    if ctx.current_ls_no is None or not ctx.current_ls_name or not ctx.state:
        ctx.ls_buffer_lines = []
        return
    buffer_text = "\n".join(ctx.ls_buffer_lines)
    segments = _extract_ac_segments(buffer_text)
    if not segments:
        rows.append(
            {
                "state": ctx.state,
                "lok_sabha_no": ctx.current_ls_no,
                "lok_sabha_constituency": ctx.current_ls_name,
                "reservation_status": ctx.current_ls_reservation,
                "assembly_no": pd.NA,
                "assembly_constituency": "",
                "source_page": page_num,
                "raw_text": buffer_text.strip(),
                "parse_confidence": "low",
            }
        )
    else:
        for ac_no, ac_name, ac_res in segments:
            rows.append(
                {
                    "state": ctx.state,
                    "lok_sabha_no": ctx.current_ls_no,
                    "lok_sabha_constituency": ctx.current_ls_name,
                    "reservation_status": ctx.current_ls_reservation,
                    "assembly_no": ac_no,
                    "assembly_constituency": ac_name,
                    "source_page": page_num,
                    "raw_text": buffer_text.strip()[:500],
                    "parse_confidence": "high" if ac_name else "medium",
                }
            )
    ctx.ls_buffer_lines = []


def _handle_table_b_line(
    ctx: ParseContext,
    line: str,
    page_num: int,
    rows: list[dict[str, object]],
) -> None:
    stripped = line.strip()

    if RESERVATION_ONLY_RE.match(stripped) and ctx.current_ls_no is not None:
        if not ctx.ls_buffer_lines:
            ctx.current_ls_reservation = stripped.strip("()").upper()
            return
        ctx.ls_buffer_lines.append(stripped)
        return

    if _is_table_b_continuation(line):
        ctx.ls_buffer_lines.append(stripped)
        return

    if _is_table_b_name_wrap(line) and ctx.current_ls_no is not None:
        _handle_table_b_name_wrap(ctx, line)
        return

    if _is_table_b_ls_start(line):
        _flush_ls_segments(ctx, page_num, rows)
        header, ac_text = _split_ls_line(line)
        if header:
            ctx.current_ls_no, ctx.current_ls_name, ctx.current_ls_reservation = header
            ctx.ls_buffer_lines = [ac_text] if ac_text else []
        return

    if ctx.current_ls_no is not None:
        ctx.ls_buffer_lines.append(stripped)


def parse_delimitation_pages(pages_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (assembly_district_df, lok_sabha_assembly_df)."""
    assembly_rows: list[dict[str, object]] = []
    ls_rows: list[dict[str, object]] = []
    ctx = ParseContext()

    for _, page_row in pages_df.sort_values("page_number").iterrows():
        page_num = int(page_row["page_number"])
        text = str(page_row["text"])
        lines = text.splitlines()
        lookahead_state: str | None = None

        for idx, line in enumerate(lines):
            stripped = line.strip()
            if not stripped:
                continue

            roman = _extract_schedule_roman(stripped)
            if roman and roman in ROMAN_TO_STATE:
                _flush_assembly(ctx, page_num, assembly_rows)
                _flush_ls_segments(ctx, page_num, ls_rows)
                ctx.state = ROMAN_TO_STATE[roman]
                ctx.section = None
                ctx.district = None
                ctx.appendix_skip = False
                ctx.current_ls_no = None
                ctx.current_ls_name = None
                continue

            if "ANNEXURE" in stripped.upper() and idx + 1 < len(lines):
                nxt = lines[idx + 1].strip().upper()
                if "JAMMU" in nxt or "KASHMIR" in nxt:
                    _flush_assembly(ctx, page_num, assembly_rows)
                    ctx.state = "Jammu and Kashmir"
                    ctx.section = "table_a"
                    ctx.district = None
                    continue

            section = _detect_section(stripped)
            if section:
                _flush_assembly(ctx, page_num, assembly_rows)
                _flush_ls_segments(ctx, page_num, ls_rows)
                if section == "appendix":
                    ctx.appendix_skip = True
                else:
                    ctx.section = section
                    ctx.appendix_skip = False
                ctx.district = None
                ctx.current_ls_no = None
                ctx.current_ls_name = None
                continue

            if ctx.state is None:
                continue

            if _should_skip_line(stripped):
                continue

            district_match = DISTRICT_RE.match(stripped)
            if district_match and ctx.section == "table_a":
                _flush_assembly(ctx, page_num, assembly_rows)
                ctx.district = clean_display_name(district_match.group(2))
                ctx.appendix_skip = False
                continue

            if ctx.appendix_skip and _is_appendix_village_line(stripped):
                continue

            if ctx.section == "table_b":
                _handle_table_b_line(ctx, line, page_num, ls_rows)
                continue

            if ctx.section == "table_a":
                if RESERVATION_ONLY_RE.match(stripped):
                    ctx.pending_ac_reservation = stripped.strip("()").upper()
                    continue

                if _is_table_a_ac_start(stripped):
                    _flush_assembly(ctx, page_num, assembly_rows)
                    _start_table_a_ac_line(ctx, stripped)
                    continue

                if ctx.pending_ac_no is not None and ctx.pending_ac_name is None:
                    if not RESERVATION_ONLY_RE.match(stripped) and not DISTRICT_RE.match(stripped):
                        ctx.pending_ac_name = stripped
                        continue

                if ctx.pending_ac_no is not None and ctx.pending_ac_name:
                    if _is_table_a_ac_start(stripped):
                        _flush_assembly(ctx, page_num, assembly_rows)
                        _start_table_a_ac_line(ctx, stripped)
                        continue
                    if not _detect_section(stripped) and not DISTRICT_RE.match(stripped):
                        ctx.extent_lines.append(stripped)
                    continue

        _flush_assembly(ctx, page_num, assembly_rows)
        _flush_ls_segments(ctx, page_num, ls_rows)

    ac_df = pd.DataFrame(assembly_rows)
    ls_df = pd.DataFrame(ls_rows)
    if not ac_df.empty:
        ac_df["_extent_len"] = ac_df["raw_extent_text"].astype(str).str.len()
        ac_df = ac_df.sort_values("_extent_len", ascending=False).drop_duplicates(
            subset=["state", "assembly_no", "assembly_constituency", "district"],
            keep="first",
        )
        ac_df = ac_df.drop(columns=["_extent_len"])
    if not ls_df.empty:
        ls_df = ls_df.drop_duplicates(
            subset=["state", "lok_sabha_no", "assembly_no", "assembly_constituency"],
            keep="last",
        )
    return ac_df, ls_df
