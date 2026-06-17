"""
CSDS-Lokniti study manifest.

Raw PDFs live under data/behaviour-analysis/{post-poll,pre-poll}/{year}/.
Pipeline outputs stay under data/postpoll/.

Run:
    python -m src.postpoll.csds_manifest
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]

# Source PDFs (user-provided CSDS downloads)
BEHAVIOUR_ANALYSIS_DIR = ROOT / "data" / "behaviour-analysis"
POST_POLL_SOURCE_DIR = BEHAVIOUR_ANALYSIS_DIR / "post-poll"
PRE_POLL_SOURCE_DIR = BEHAVIOUR_ANALYSIS_DIR / "pre-poll"

# Pipeline outputs (extracted tables, processed CSVs, reports, JSON)
POSTPOLL_DIR = ROOT / "data" / "postpoll"
EXTRACTED_DIR = POSTPOLL_DIR / "extracted"
PROCESSED_DIR = POSTPOLL_DIR / "processed"
REPORTS_DIR = POSTPOLL_DIR / "reports"
FRONTEND_DATA_DIR = ROOT / "frontend" / "public" / "data"

# Legacy alias — raw inputs are no longer expected here
RAW_DIR = BEHAVIOUR_ANALYSIS_DIR

MANIFEST_PATH = PROCESSED_DIR / "csds_study_metadata.csv"

STUDIES: list[dict[str, object]] = [
    {
        "year": 2024,
        "poll_type": "post_poll",
        "source": "CSDS-Lokniti National Election Study",
        "report_path": "post-poll/2024/postpoll_study_2024.pdf",
        "method_note_path": "post-poll/2024/postpoll_methodnote_2024.pdf",
        "questionnaire_path": "post-poll/2024/2024_questionnaire_post_poll.pdf",
    },
    {
        "year": 2024,
        "poll_type": "pre_poll",
        "source": "CSDS-Lokniti National Election Study",
        "report_path": "pre-poll/2024/prepoll_report_2024.pdf",
        "method_note_path": "pre-poll/2024/prepoll_method_2024.pdf",
        "questionnaire_path": "pre-poll/2024/prepoll_questionnaire_2024.pdf",
    },
    {
        "year": 2019,
        "poll_type": "post_poll",
        "source": "CSDS-Lokniti National Election Study",
        "report_path": "post-poll/2019/postpoll_results_2019.pdf",
        "method_note_path": "post-poll/2019/postpoll_method_2019.pdf",
        "questionnaire_path": "post-poll/2019/postpoll_question_2019.pdf",
    },
    {
        "year": 2019,
        "poll_type": "pre_poll",
        "source": "CSDS-Lokniti National Election Study",
        "report_path": "pre-poll/2019/prepoll_2019_results.pdf",
        "method_note_path": "pre-poll/2019/prepoll_2019_method.pdf",
        "questionnaire_path": "pre-poll/2019/prepoll_2019_questionnaire.pdf",
    },
]

MANIFEST_COLUMNS = [
    "year",
    "poll_type",
    "source",
    "raw_report_file",
    "method_note_file",
    "questionnaire_file",
    "sample_size",
    "states_covered",
    "constituencies_covered",
    "is_weighted_report",
    "notes",
]

REPORT_KEYWORDS = ("results", "report", "study")
METHOD_KEYWORDS = ("method", "methodnote")
QUESTIONNAIRE_KEYWORDS = ("question", "questionnaire")


def _poll_source_dir(poll_type: str) -> Path:
    return POST_POLL_SOURCE_DIR if poll_type == "post_poll" else PRE_POLL_SOURCE_DIR


def _relative_path(path: Path) -> str:
    try:
        return str(path.relative_to(BEHAVIOUR_ANALYSIS_DIR))
    except ValueError:
        return str(path)


def _score_filename(name: str, keywords: tuple[str, ...]) -> int:
    lower = name.lower()
    return sum(1 for keyword in keywords if keyword in lower)


def _discover_pdf(year: int, poll_type: str, keywords: tuple[str, ...]) -> Path | None:
    folder = _poll_source_dir(poll_type) / str(year)
    if not folder.is_dir():
        return None
    candidates = sorted(folder.glob("*.pdf"))
    if not candidates:
        return None
    ranked = sorted(
        candidates,
        key=lambda path: (_score_filename(path.name, keywords), path.name),
        reverse=True,
    )
    best = ranked[0]
    return best if _score_filename(best.name, keywords) > 0 else None


def resolve_study_file(study: dict[str, object], file_kind: str) -> Path:
    """
    Resolve a study PDF path.

    file_kind: report | method_note | questionnaire
    """
    key_map = {
        "report": ("report_path", REPORT_KEYWORDS),
        "method_note": ("method_note_path", METHOD_KEYWORDS),
        "questionnaire": ("questionnaire_path", QUESTIONNAIRE_KEYWORDS),
    }
    path_key, keywords = key_map[file_kind]
    configured = study.get(path_key)
    if configured:
        path = BEHAVIOUR_ANALYSIS_DIR / str(configured)
        if path.exists():
            return path

    discovered = _discover_pdf(int(study["year"]), str(study["poll_type"]), keywords)
    return discovered if discovered else Path(str(configured or ""))


def resolve_report_path(study: dict[str, object]) -> Path:
    return resolve_study_file(study, "report")


def resolve_method_path(study: dict[str, object]) -> Path:
    return resolve_study_file(study, "method_note")


def resolve_questionnaire_path(study: dict[str, object]) -> Path:
    return resolve_study_file(study, "questionnaire")


def _read_pdf_text(path: Path) -> str:
    if not path.exists():
        return ""
    try:
        import pdfplumber
    except ImportError:
        return ""
    chunks: list[str] = []
    try:
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                text = page.extract_text() or ""
                if text.strip():
                    chunks.append(text)
    except Exception:
        return ""
    return "\n".join(chunks)


def _extract_sample_size(text: str) -> str:
    patterns = [
        r"sample\s+(?:size|of)\s+(?:was\s+)?(?:about\s+)?([\d,]+)",
        r"([\d,]{3,})\s+respondents",
        r"total\s+sample\s*[:=]?\s*([\d,]+)",
        r"\bn\s*[=:]\s*([\d,]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.I)
        if match:
            return match.group(1).replace(",", "")
    return ""


def _extract_states_covered(text: str) -> str:
    match = re.search(r"(\d{1,2})\s+states?(?:\s+and\s+union\s+territor(?:y|ies))?", text, re.I)
    if match:
        return match.group(1)
    match = re.search(r"cover(?:ed|ing)\s+(\d{1,2})\s+states?", text, re.I)
    if match:
        return match.group(1)
    return ""


def _extract_constituencies_covered(text: str) -> str:
    patterns = [
        r"(\d{2,3})\s+(?:lok\s+sabha\s+)?constituenc",
        r"(\d{2,3})\s+parliamentary\s+constituenc",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.I)
        if match:
            return match.group(1)
    return ""


def _extract_weighted_flag(text: str) -> str:
    if not text.strip():
        return ""
    if re.search(r"\bweighted\b", text, re.I):
        return "yes"
    if re.search(r"\bunweighted\b", text, re.I):
        return "no"
    return ""


def build_manifest_row(study: dict[str, object]) -> dict[str, object]:
    report_path = resolve_report_path(study)
    method_path = resolve_method_path(study)
    questionnaire_path = resolve_questionnaire_path(study)
    notes: list[str] = []

    if not report_path.exists():
        notes.append("report PDF missing")
    if not method_path.exists():
        notes.append("method note PDF missing")
    if not questionnaire_path.exists():
        notes.append("questionnaire PDF missing")

    method_text = _read_pdf_text(method_path)
    report_text = _read_pdf_text(report_path) if report_path.exists() else ""
    combined = "\n".join([method_text, report_text]).strip()

    sample_size = _extract_sample_size(method_text) or _extract_sample_size(report_text)
    states_covered = _extract_states_covered(combined)
    constituencies_covered = _extract_constituencies_covered(combined)
    weighted = _extract_weighted_flag(combined)

    if not combined and (report_path.exists() or method_path.exists()):
        notes.append("metadata not auto-extracted; review method note manually")
    if not sample_size and combined:
        notes.append("sample_size not found in text")

    return {
        "year": study["year"],
        "poll_type": study["poll_type"],
        "source": study["source"],
        "raw_report_file": _relative_path(report_path) if report_path else "",
        "method_note_file": _relative_path(method_path) if method_path else "",
        "questionnaire_file": _relative_path(questionnaire_path) if questionnaire_path else "",
        "sample_size": sample_size,
        "states_covered": states_covered,
        "constituencies_covered": constituencies_covered,
        "is_weighted_report": weighted,
        "notes": "; ".join(notes),
    }


def build_manifest() -> pd.DataFrame:
    rows = [build_manifest_row(study) for study in STUDIES]
    return pd.DataFrame(rows, columns=MANIFEST_COLUMNS)


def main() -> None:
    for directory in (BEHAVIOUR_ANALYSIS_DIR, EXTRACTED_DIR, PROCESSED_DIR, REPORTS_DIR):
        directory.mkdir(parents=True, exist_ok=True)

    manifest = build_manifest()
    manifest.to_csv(MANIFEST_PATH, index=False)

    found_reports = sum(1 for study in STUDIES if resolve_report_path(study).exists())
    found_method = sum(1 for study in STUDIES if resolve_method_path(study).exists())
    found_questionnaires = sum(
        1 for study in STUDIES if resolve_questionnaire_path(study).exists()
    )

    print("CSDS study manifest")
    print(f"  Source directory: {BEHAVIOUR_ANALYSIS_DIR}")
    print(f"  Studies configured: {len(STUDIES)}")
    print(f"  Report PDFs found: {found_reports}/{len(STUDIES)}")
    print(f"  Method notes found: {found_method}/{len(STUDIES)}")
    print(f"  Questionnaires found: {found_questionnaires}/{len(STUDIES)}")
    print(f"  Saved: {MANIFEST_PATH}")
    if found_reports == 0:
        print(
            "  Place PDFs in data/behaviour-analysis/post-poll/{year}/ "
            "and data/behaviour-analysis/pre-poll/{year}/"
        )


if __name__ == "__main__":
    main()
