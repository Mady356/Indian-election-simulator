"""
Render HTML review pages for high-potential taxonomy extraction tables.

Run:
    python -m src.postpoll.render_taxonomy_review_pages
"""

from __future__ import annotations

import html
import json
from pathlib import Path

import pandas as pd

from src.postpoll.csds_manifest import BEHAVIOUR_ANALYSIS_DIR, EXTRACTED_DIR
from src.postpoll.csds_taxonomy import (
    EXTRACTED_CANDIDATES_PATH,
    MANUAL_REVIEW_PAGES_DIR,
    REVIEW_PATH,
    TABLE_LABEL_INVENTORY_PATH,
    TAXONOMY_REVIEW_INDEX_PATH,
    ensure_taxonomy_dirs,
)

TOP_N = 100


def _load_csv_preview(path: Path, max_rows: int = 12) -> str:
    if not path.exists():
        return "<em>CSV not found</em>"
    try:
        df = pd.read_csv(path)
    except Exception as exc:
        return f"<em>Could not read CSV: {html.escape(str(exc))}</em>"
    preview = df.head(max_rows)
    table_html = preview.to_html(index=False, classes="csv-preview", border=0)
    if len(df) > max_rows:
        table_html += f"<p><em>Showing {max_rows} of {len(df)} rows.</em></p>"
    return table_html


def _candidate_rows_for_table(candidates: pd.DataFrame, table_file: str) -> pd.DataFrame:
    if candidates.empty:
        return candidates
    mask = candidates["notes"].astype(str).str.contains("marginal|layout", case=False, na=False)
    title_mask = candidates.get("source_table_title", pd.Series(dtype=str)).astype(str) == table_file
    page_mask = candidates["source_table_index"].astype(str).str.zfill(3) == table_file.split("_")[-1].replace(".csv", "")
    subset = candidates[title_mask | (mask & page_mask)]
    if subset.empty:
        table_index = table_file.split("_")[-1].replace(".csv", "")
        subset = candidates[candidates["source_table_index"].astype(str).str.zfill(3) == table_index]
    return subset


def _render_page_image(source_file: str, source_page: object) -> str:
    if not source_file or pd.isna(source_page):
        return "<p><em>Page image unavailable (missing source mapping).</em></p>"
    pdf_path = BEHAVIOUR_ANALYSIS_DIR / str(source_file)
    if not pdf_path.exists():
        return f"<p><em>PDF not found: {html.escape(str(pdf_path))}</em></p>"
    try:
        import pdfplumber
    except ImportError:
        return "<p><em>Install pdfplumber to render page images.</em></p>"

    page_num = int(source_page)
    out_dir = MANUAL_REVIEW_PAGES_DIR / "images"
    out_dir.mkdir(parents=True, exist_ok=True)
    image_name = f"{pdf_path.stem}_p{page_num:04d}.png"
    image_path = out_dir / image_name
    if not image_path.exists():
        with pdfplumber.open(pdf_path) as pdf:
            if page_num < 1 or page_num > len(pdf.pages):
                return f"<p><em>Page {page_num} out of range.</em></p>"
            page = pdf.pages[page_num - 1]
            image = page.to_image(resolution=120)
            image.save(image_path, format="PNG")
    rel = Path("images") / image_name
    return f'<img src="{html.escape(rel.as_posix())}" alt="page {page_num}" class="page-image" />'


def build_review_index() -> Path:
    ensure_taxonomy_dirs()
    inventory = pd.read_csv(TABLE_LABEL_INVENTORY_PATH)
    candidates = (
        pd.read_csv(EXTRACTED_CANDIDATES_PATH) if EXTRACTED_CANDIDATES_PATH.exists() else pd.DataFrame()
    )

    top = inventory.sort_values("extraction_potential_score", ascending=False).head(TOP_N)
    sections: list[str] = []

    for rank, (_, row) in enumerate(top.iterrows(), start=1):
        table_file = str(row["table_file"])
        csv_path = EXTRACTED_DIR / table_file
        table_candidates = _candidate_rows_for_table(candidates, table_file)

        candidate_html = "<p><em>No candidate rows extracted for this table yet.</em></p>"
        if not table_candidates.empty:
            display_cols = [
                "party_or_alliance",
                "voter_group_type",
                "voter_group",
                "vote_share",
                "extraction_confidence",
                "raw_row_label",
                "raw_column_label",
                "raw_cell_value",
            ]
            cols = [c for c in display_cols if c in table_candidates.columns]
            candidate_html = table_candidates[cols].to_html(index=False, classes="candidate-preview", border=0)

        party_labels = html.escape(str(row.get("recognized_party_labels", "")))
        group_labels = html.escape(str(row.get("recognized_group_labels", "")))
        layout = html.escape(str(row.get("likely_layout", "")))
        table_type = html.escape(str(row.get("table_type", "")))
        score = row.get("extraction_potential_score", "")
        source_file = html.escape(str(row.get("source_file", "")))
        source_page = row.get("source_page", "")

        sections.append(
            f"""
            <section class="review-card" id="table-{rank}">
              <h2>#{rank} — {html.escape(table_file)}</h2>
              <div class="meta">
                <span>Score: {score}</span>
                <span>Layout: {layout}</span>
                <span>Type: {table_type}</span>
                <span>Parties: {party_labels or "-"}</span>
                <span>Groups: {group_labels or "-"}</span>
                <span>Source: {source_file}</span>
                <span>Page: {html.escape(str(source_page))}</span>
              </div>
              <div class="grid">
                <div>
                  <h3>Page image</h3>
                  {_render_page_image(str(row.get("source_file", "")), source_page)}
                </div>
                <div>
                  <h3>Extracted table preview</h3>
                  {_load_csv_preview(csv_path)}
                </div>
              </div>
              <h3>Candidate rows</h3>
              {candidate_html}
            </section>
            """
        )

    review_path = REVIEW_PATH
    review_note = (
        f"<code>{html.escape(str(review_path))}</code>"
        if review_path.exists()
        else "<em>Review file will be created after validation.</em>"
    )

    doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>CSDS Taxonomy Review Index</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 24px; color: #1f2937; }}
    h1 {{ margin-bottom: 0.2rem; }}
    .instructions {{ background: #f8fafc; border: 1px solid #dbe3ee; padding: 16px; border-radius: 8px; margin: 16px 0 24px; }}
    .review-card {{ border: 1px solid #dbe3ee; border-radius: 10px; padding: 16px; margin-bottom: 24px; }}
    .meta {{ display: flex; flex-wrap: wrap; gap: 10px; margin: 8px 0 16px; font-size: 0.92rem; color: #475569; }}
    .meta span {{ background: #eef2ff; padding: 4px 8px; border-radius: 999px; }}
    .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }}
    .page-image {{ max-width: 100%; border: 1px solid #cbd5e1; border-radius: 6px; }}
    table.csv-preview, table.candidate-preview {{ width: 100%; border-collapse: collapse; font-size: 0.85rem; }}
    table.csv-preview th, table.csv-preview td, table.candidate-preview th, table.candidate-preview td {{
      border: 1px solid #e2e8f0; padding: 4px 6px; vertical-align: top;
    }}
    @media (max-width: 960px) {{ .grid {{ grid-template-columns: 1fr; }} }}
  </style>
</head>
<body>
  <h1>CSDS Taxonomy Review Index</h1>
  <p>Top {TOP_N} high-potential tables from <code>csds_table_label_inventory.csv</code>.</p>
  <div class="instructions">
    <h3>Review instructions</h3>
    <ol>
      <li>Open the source PDF page and compare against the extracted CSV preview.</li>
      <li>Check whether candidate rows map real vote shares to the correct voter group and party.</li>
      <li>Record decisions in {review_note} with <code>review_decision</code> = <code>approve</code>, <code>reject</code>, or <code>edit</code>.</li>
      <li>Re-run <code>python -m src.postpoll.approve_taxonomy_candidates</code> after editing review decisions.</li>
      <li>Only approved taxonomy rows belong in dashboard JSON. Do not use pending candidates for analysis.</li>
    </ol>
  </div>
  {''.join(sections)}
</body>
</html>
"""
    TAXONOMY_REVIEW_INDEX_PATH.write_text(doc, encoding="utf-8")
    return TAXONOMY_REVIEW_INDEX_PATH


def main() -> None:
    if not TABLE_LABEL_INVENTORY_PATH.exists():
        raise FileNotFoundError(
            f"Missing {TABLE_LABEL_INVENTORY_PATH}. Run python -m src.postpoll.csds_table_label_miner first."
        )
    out = build_review_index()
    print("CSDS taxonomy review pages")
    print(f"  Tables rendered: {TOP_N}")
    print(f"  Saved: {out}")


if __name__ == "__main__":
    main()
