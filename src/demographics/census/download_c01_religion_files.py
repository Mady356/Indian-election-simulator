"""Download Census 2011 C-01 district religion tables from the official NADA catalog."""

from __future__ import annotations

import argparse
import hashlib
import re
import time
import urllib.parse
import warnings
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup

from src.demographics.census.common import (
    C01_RELIGION_MANIFEST_PATH,
    C01_RELIGION_MISSING_PRIORITY_PATH,
    CENSUS_RELIGION_RAW_DIR,
    CENSUS_REPORTS_DIR,
    ensure_dirs,
)

NADA_CATALOG_BASE = "https://censusindia.gov.in/nada/index.php/catalog/{catalog_id}"
USER_AGENT = "Mozilla/5.0 (compatible; ElectionSimulator-CensusBot/1.0; +research)"
DEFAULT_CATALOG_START = 11350
DEFAULT_CATALOG_END = 11420
DEFAULT_REQUEST_DELAY_SEC = 0.75

DDW_FILENAME_RE = re.compile(r"(DDW\d{2}C-01)\s*MDDS\.(XLS|XLSX)", re.IGNORECASE)
C01_PAGE_RE = re.compile(r"C-01.*religious community", re.IGNORECASE)

CENSUS_2011_STATE_CODES: dict[str, str] = {
    "00": "India",
    "01": "Jammu & Kashmir",
    "02": "Himachal Pradesh",
    "03": "Punjab",
    "04": "Chandigarh",
    "05": "Uttarakhand",
    "06": "Haryana",
    "07": "NCT of Delhi",
    "08": "Rajasthan",
    "09": "Uttar Pradesh",
    "10": "Bihar",
    "11": "Sikkim",
    "12": "Arunachal Pradesh",
    "13": "Nagaland",
    "14": "Manipur",
    "15": "Mizoram",
    "16": "Tripura",
    "17": "Meghalaya",
    "18": "Assam",
    "19": "West Bengal",
    "20": "Jharkhand",
    "21": "Odisha",
    "22": "Chhattisgarh",
    "23": "Madhya Pradesh",
    "24": "Gujarat",
    "25": "Daman & Diu",
    "26": "Dadra & Nagar Haveli",
    "27": "Maharashtra",
    "28": "Andhra Pradesh",
    "29": "Karnataka",
    "30": "Goa",
    "31": "Lakshadweep",
    "32": "Kerala",
    "33": "Tamil Nadu",
    "34": "Puducherry",
    "35": "Andaman & Nicobar Islands",
}

PRIORITY_STATE_CODES = [
    "05",
    "07",
    "09",
    "18",
    "19",
    "21",
    "27",
    "28",
    "29",
    "32",
    "33",
    "34",
    "35",
]

TELANGANA_NOTE = (
    "Census 2011 has no separate Telangana state code. Telangana constituencies should use "
    "2011 Andhra Pradesh (state code 28) district religion rows, with post-2011 state reassignment "
    "for Telangana districts handled by assign_post_2011_state() in the religion build pipeline."
)


def _safe_local_filename(raw_name: str) -> str:
    match = DDW_FILENAME_RE.search(raw_name)
    if match:
        ext = match.group(2).upper()
        return f"{match.group(1).upper()}_MDDS.{ext}"
    cleaned = re.sub(r"\s+", "_", raw_name.strip())
    return cleaned


def _state_code_from_filename(filename: str) -> str:
    match = re.search(r"DDW(\d{2})C-01", filename, re.IGNORECASE)
    return match.group(1) if match else ""


def _state_name_guess(page_title: str, state_code: str) -> str:
    if state_code and state_code in CENSUS_2011_STATE_CODES:
        mapped = CENSUS_2011_STATE_CODES[state_code]
        if mapped != "India":
            return mapped
    match = re.search(r"religious community,\s*(.+?)\s*-\s*20\d{2}", page_title, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return ""


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _make_session(verify_ssl: bool) -> requests.Session:
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    session.verify = verify_ssl
    return session


def _absolute_url(base_url: str, href: str) -> str:
    if href.startswith("http://") or href.startswith("https://"):
        return href
    parsed = urllib.parse.urlparse(base_url)
    return urllib.parse.urlunparse(
        (parsed.scheme, parsed.netloc, urllib.parse.urljoin(base_url, href), "", "", "")
    )


def _parse_catalog_page(catalog_id: int, html: str, catalog_url: str) -> list[dict[str, str]]:
    soup = BeautifulSoup(html, "html.parser")
    title = (soup.title.string or "").strip() if soup.title else ""
    if not C01_PAGE_RE.search(title):
        return []

    downloads: list[dict[str, str]] = []
    seen_urls: set[str] = set()
    for anchor in soup.find_all("a", href=True):
        text = anchor.get_text(" ", strip=True)
        href = anchor["href"]
        label = text or href
        if not DDW_FILENAME_RE.search(label) and not DDW_FILENAME_RE.search(href):
            continue
        match = DDW_FILENAME_RE.search(label) or DDW_FILENAME_RE.search(href)
        if not match:
            continue
        filename = f"{match.group(1).upper()} MDDS.{match.group(2).upper()}"
        if filename.upper().startswith("DDW00C-01"):
            continue
        download_url = _absolute_url(catalog_url, href)
        if download_url in seen_urls:
            continue
        seen_urls.add(download_url)
        state_code = _state_code_from_filename(filename)
        downloads.append(
            {
                "catalog_id": str(catalog_id),
                "catalog_url": catalog_url,
                "state_code": state_code,
                "state_name_guess": _state_name_guess(title, state_code),
                "filename": filename,
                "download_url": download_url,
            }
        )
    return downloads


def _download_file(
    session: requests.Session,
    download_url: str,
    local_path: Path,
    force: bool,
) -> tuple[str, int, str, str]:
    if local_path.exists() and not force:
        return "cached", local_path.stat().st_size, _sha256_file(local_path), ""

    try:
        response = session.get(download_url, timeout=120, stream=True)
        response.raise_for_status()
        local_path.parent.mkdir(parents=True, exist_ok=True)
        with local_path.open("wb") as handle:
            for chunk in response.iter_content(chunk_size=1024 * 64):
                if chunk:
                    handle.write(chunk)
        return "downloaded", local_path.stat().st_size, _sha256_file(local_path), ""
    except requests.RequestException as exc:
        return "error", 0, "", str(exc)


def crawl_and_download_c01_files(
    catalog_start: int = DEFAULT_CATALOG_START,
    catalog_end: int = DEFAULT_CATALOG_END,
    delay_sec: float = DEFAULT_REQUEST_DELAY_SEC,
    force: bool = False,
    verify_ssl: bool = False,
) -> pd.DataFrame:
    ensure_dirs()
    if not verify_ssl:
        warnings.filterwarnings("ignore", message="Unverified HTTPS request")

    session = _make_session(verify_ssl=verify_ssl)
    manifest_rows: list[dict[str, object]] = []

    for catalog_id in range(catalog_start, catalog_end + 1):
        catalog_url = NADA_CATALOG_BASE.format(catalog_id=catalog_id)
        try:
            response = session.get(catalog_url, timeout=30)
            if response.status_code != 200:
                manifest_rows.append(
                    {
                        "catalog_id": catalog_id,
                        "catalog_url": catalog_url,
                        "state_code": "",
                        "state_name_guess": "",
                        "filename": "",
                        "download_url": "",
                        "local_path": "",
                        "status": "catalog_not_found",
                        "file_size_bytes": 0,
                        "sha256": "",
                        "error": f"HTTP {response.status_code}",
                    }
                )
                time.sleep(delay_sec)
                continue

            entries = _parse_catalog_page(catalog_id, response.text, catalog_url)
            if not entries:
                time.sleep(delay_sec)
                continue

            for entry in entries:
                local_name = _safe_local_filename(entry["filename"])
                local_path = CENSUS_RELIGION_RAW_DIR / local_name
                status, size, sha256, error = _download_file(
                    session,
                    entry["download_url"],
                    local_path,
                    force=force,
                )
                manifest_rows.append(
                    {
                        **entry,
                        "local_path": str(local_path),
                        "status": status,
                        "file_size_bytes": size,
                        "sha256": sha256,
                        "error": error,
                    }
                )
                print(f"  [{status}] {entry['filename']} -> {local_path}")
                time.sleep(delay_sec)
        except requests.RequestException as exc:
            manifest_rows.append(
                {
                    "catalog_id": catalog_id,
                    "catalog_url": catalog_url,
                    "state_code": "",
                    "state_name_guess": "",
                    "filename": "",
                    "download_url": "",
                    "local_path": "",
                    "status": "catalog_error",
                    "file_size_bytes": 0,
                    "sha256": "",
                    "error": str(exc),
                }
            )
            time.sleep(delay_sec)

    manifest = pd.DataFrame(manifest_rows)
    if not manifest.empty:
        manifest = manifest.sort_values(["state_code", "filename"]).reset_index(drop=True)
    manifest.to_csv(C01_RELIGION_MANIFEST_PATH, index=False)
    _write_missing_priority_report(manifest)
    _write_telangana_note()
    return manifest


def _write_missing_priority_report(manifest: pd.DataFrame) -> None:
    downloaded_codes: set[str] = set()
    if not manifest.empty:
        ok = manifest["status"].isin(["downloaded", "cached"])
        downloaded_codes = set(manifest.loc[ok, "state_code"].astype(str).str.zfill(2))

    rows: list[dict[str, object]] = []
    for code in PRIORITY_STATE_CODES:
        rows.append(
            {
                "state_code": code,
                "state_name": CENSUS_2011_STATE_CODES.get(code, ""),
                "priority": True,
                "file_present": code in downloaded_codes,
                "notes": "",
            }
        )
    missing = pd.DataFrame(rows)
    missing.to_csv(C01_RELIGION_MISSING_PRIORITY_PATH, index=False)


def _write_telangana_note() -> None:
    note_path = CENSUS_REPORTS_DIR / "c01_religion_telangana_note.md"
    note_path.write_text(f"# Telangana religion mapping note\n\n{TELANGANA_NOTE}\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog-start", type=int, default=DEFAULT_CATALOG_START)
    parser.add_argument("--catalog-end", type=int, default=DEFAULT_CATALOG_END)
    parser.add_argument("--delay", type=float, default=DEFAULT_REQUEST_DELAY_SEC)
    parser.add_argument("--force", action="store_true", help="Redownload files even if cached locally")
    parser.add_argument(
        "--verify-ssl",
        action="store_true",
        help="Verify TLS certificates (censusindia.gov.in may fail on some systems)",
    )
    args = parser.parse_args()

    print(
        f"Crawling Census NADA catalog IDs {args.catalog_start}-{args.catalog_end} "
        f"for C-01 religion files..."
    )
    manifest = crawl_and_download_c01_files(
        catalog_start=args.catalog_start,
        catalog_end=args.catalog_end,
        delay_sec=args.delay,
        force=args.force,
        verify_ssl=args.verify_ssl,
    )

    if manifest.empty:
        print("No C-01 religion catalog entries found.")
    else:
        file_rows = manifest[manifest["filename"].astype(str).str.len() > 0]
        ok = file_rows[file_rows["status"].isin(["downloaded", "cached"])]
        print(f"\nC-01 religion download summary")
        print(f"  Catalog entries with files: {len(file_rows)}")
        print(f"  Downloaded/cached: {len(ok)}")
        print(f"  Errors: {len(file_rows[file_rows['status'] == 'error'])}")
        print(f"  Manifest: {C01_RELIGION_MANIFEST_PATH}")
        print(f"  Priority check: {C01_RELIGION_MISSING_PRIORITY_PATH}")
        print(f"\n{TELANGANA_NOTE}")


if __name__ == "__main__":
    main()
