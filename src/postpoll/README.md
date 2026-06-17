# CSDS-Lokniti Pre-Poll / Post-Poll Pipeline

This module ingests CSDS-Lokniti National Election Study PDFs and builds a
traceable voter-behavior layer for the Indian Election Intelligence Platform.

It compares:

1. **Pre-poll expectations** — what voters said they intended to do before the election
2. **Post-poll reported behavior** — what voters reported after the election
3. **Actual election results** — from existing ECI result tables in this repo

The outputs will power **Opinion Poll Lab** and **Vote Bank Analysis** in the dashboard.

---

## Where to put raw files

CSDS PDFs belong under `data/behaviour-analysis/`:

```
data/behaviour-analysis/
  post-poll/
    2019/
      postpoll_results_2019.pdf
      postpoll_method_2019.pdf
      postpoll_question_2019.pdf
    2024/
      postpoll_study_2024.pdf
      postpoll_methodnote_2024.pdf
      2024_questionnaire_post_poll.pdf
  pre-poll/
    2019/
      prepoll_2019_results.pdf
      prepoll_2019_method.pdf
      prepoll_2019_questionnaire.pdf
    2024/
      prepoll_report_2024.pdf
      prepoll_method_2024.pdf
      prepoll_questionnaire_2024.pdf
```

The pipeline also auto-discovers PDFs in each `{post-poll,pre-poll}/{year}/` folder
by filename keywords (`results`/`report`/`study`, `method`, `questionnaire`) if
names differ slightly.

Processed outputs (extracted tables, CSVs, JSON) are written to `data/postpoll/`.

---

## Command order

```bash
source venv/bin/activate
pip install pdfplumber   # if not already installed

python -m src.postpoll.csds_manifest
python -m src.postpoll.extract_csds_tables
python -m src.postpoll.clean_csds_tables
python -m src.postpoll.analyze_pre_post_shift
python -m src.postpoll.build_vote_behavior_database
```

### QA and deduplication (run after cleaning)

```bash
python -m src.postpoll.validate_csds_outputs
python -m src.postpoll.deduplicate_vote_behavior
python -m src.postpoll.prioritize_manual_tables
```

Use **deduped** outputs for dashboard and analysis:

- `csds_vote_behavior_tables_deduped.csv`
- `csds_pre_post_comparison_deduped.csv`
- `frontend/public/data/csds_*.json` (updated by deduplicate step)

The original `csds_pre_post_comparison.csv` can inflate row counts via many-to-many
duplicate joins. The deduped comparison rebuilds one-to-one pre/post matches only.

### Taxonomy-guided extraction (recommended)

Generic table extraction pulls questionnaire grids, newspaper codes, and
methodology pages into the vote-behavior database. The taxonomy-guided pipeline
searches only for pages and tables that match a voter-behavior taxonomy.

```bash
python -m src.postpoll.csds_table_label_miner
python -m src.postpoll.taxonomy_guided_search
python -m src.postpoll.taxonomy_guided_extract
python -m src.postpoll.validate_taxonomy_candidates
python -m src.postpoll.approve_taxonomy_candidates
python -m src.postpoll.render_taxonomy_review_pages
```

Or run the full improved pipeline in one step:

```bash
python -m src.postpoll.improve_taxonomy_extraction
```

**Table label mining** (`csds_table_label_miner`) scans every extracted CSV in
`data/postpoll/extracted/`, detects likely layouts (groups×parties, parties×groups,
party marginals with `%` columns, questionnaire grids), and writes
`data/postpoll/reports/csds_table_label_inventory.csv` ranked by
`extraction_potential_score`.

**Improved extraction logic** (`taxonomy_guided_extract`) uses the label inventory
and page candidates to extract from pre-extracted CSV tables (not PDF-only). It
handles:

- Layout A: voter groups as rows, parties as columns
- Layout B: parties as rows, voter groups as columns
- Layout C/D: multi-row or shifted headers (CSDS `001: Congress` codes)
- Layout E: vote shares as `45`, `45%`, `45.0`, `45 (n=...)`, `45 per cent`
- Party marginals: coded party rows with a `%` column plus page-context voter group

Page text raises confidence for vote-choice questions and lowers it for
questionnaire/methodology pages. Every value traces to `source_file`,
`source_page`, `source_table_index`, `raw_row_label`, `raw_column_label`, and
`raw_cell_value`.

**Review UI**: open `data/postpoll/manual/review_pages/taxonomy_review_index.html`
in a browser after `render_taxonomy_review_pages`. It shows the top 100
high-potential tables with page images, CSV previews, and extracted candidate rows.
Approve / reject / edit in `data/postpoll/manual/entered/csds_taxonomy_candidate_review.csv`.

**Why taxonomy-guided extraction is still reviewed before dashboard use**

CSDS PDFs mix real vote tables with campaign-contact grids, issue batteries, and
codebooks. Even with taxonomy filters, some party-marginal tables require human
confirmation of the voter group implied by page context. Non-approved taxonomy
rows must not enter dashboard JSON. Do not average conflicting duplicates or
impute missing cells.

Use **curated** outputs for dashboard and analysis:

- `data/postpoll/processed/csds_vote_behavior_curated.csv`
- `data/postpoll/processed/csds_pre_post_comparison_curated.csv`
- `frontend/public/data/csds_vote_behavior_curated.json`
- `frontend/public/data/csds_pre_post_comparison_curated.json`

Edit `data/postpoll/taxonomy/csds_voter_behavior_taxonomy.yml` to tune keywords
and canonical voter groups. Review pending candidates in
`data/postpoll/manual/entered/csds_taxonomy_candidate_review.csv`.

**Do not use non-approved taxonomy candidates or legacy generic rows for analysis.**

---

## Output files

### Processed data (`data/postpoll/processed/`)

| File | Description |
|------|-------------|
| `csds_study_metadata.csv` | Study manifest (sample size, coverage, weighting flags) |
| `csds_vote_behavior_tables.csv` | Long-format voter-group vote shares (raw cleaned) |
| `csds_vote_behavior_tables_deduped.csv` | Deduplicated vote-behavior rows (**use for dashboard**) |
| `csds_pre_post_comparison.csv` | Raw pre/post comparison (may include duplicate-join inflation) |
| `csds_pre_post_comparison_deduped.csv` | Trustworthy one-to-one pre/post comparison (**use for dashboard**) |
| `csds_vote_behavior_curated.csv` | Taxonomy-approved curated database (**preferred for dashboard**) |
| `csds_pre_post_comparison_curated.csv` | Curated one-to-one pre/post comparison (**preferred for dashboard**) |
| `csds_vs_actual_results.csv` | Survey vs actual election vote share |

### Reports (`data/postpoll/reports/`)

| File | Description |
|------|-------------|
| `manual_extraction_needed.csv` | Tables/pages needing human review |
| `manual_extraction_priority.csv` | Ranked manual tables by likely voter-behavior value |
| `csds_vote_behavior_quality_report.csv` | Per-row QA flags for cleaned vote-behavior data |
| `csds_duplicate_keys.csv` | Duplicate analytical keys and dedupe recommendations |
| `csds_pre_post_join_audit.csv` | Pre/post join diagnostics (one-to-one vs missing vs conflict) |
| `csds_pre_post_shift_summary.csv` | Interpretable pre-to-post shift summaries |
| `csds_poll_accuracy_summary.csv` | Survey vs actual national accuracy summary |
| `csds_taxonomy_candidate_quality_report.csv` | Taxonomy candidate validation flags |
| `csds_taxonomy_duplicate_candidates.csv` | Duplicate taxonomy candidate keys |
| `csds_table_label_inventory.csv` | Mined row/column labels and layout scores for extracted tables |
| `csds_table_page_index.csv` | Maps `{year}_{poll_type}_table_NNN.csv` to PDF page numbers |
| `manual_extraction_priority.csv` | Ranked manual tables by likely voter-behavior value |

### Extracted audit trail (`data/postpoll/extracted/`)

| Pattern | Description |
|---------|-------------|
| `{year}_{poll_type}_table_{NNN}.csv` | Raw extracted tables (one per detected table) |
| `{year}_{poll_type}_text.txt` | Full page text for audit |

### Dashboard JSON (`frontend/public/data/`)

| File | Description |
|------|-------------|
| `csds_vote_behavior.json` | Vote-behavior rows + study metadata |
| `csds_pre_post_comparison.json` | Pre/post comparison rows |
| `csds_poll_accuracy_summary.json` | Survey vs actual summary rows |

---

## Schema notes

### `csds_vote_behavior_tables.csv`

Key columns: `year`, `poll_type`, `voter_group_type`, `voter_group`,
`party_or_alliance`, `vote_share`, `source_table`, `source_page`, `original_label`.

Normalized `poll_type` values: `pre_poll`, `post_poll`.

Normalized `party_or_alliance` values: `BJP`, `INC`, `NDA`, `INDIA`, `UPA`,
`Others`, `Regional`, `Unknown`.

Normalized `voter_group_type` values: `gender`, `age`, `religion`, `caste`,
`class`, `education`, `rural_urban`, `region`, `state`, `other`.

### Pre-to-post shift

`pre_to_post_shift = post_poll_vote_share - pre_poll_vote_share`

`shift_direction`:

- `increased_post_poll`
- `decreased_post_poll`
- `unchanged`
- `unavailable`

**This is not called "polling error."** A pre-to-post shift may reflect late
swing, turnout differences, sampling differences, undecided voters moving,
or methodology differences between the two surveys. It is **not** causal inference.

### Post-poll vs pre-poll usage

| Survey | Primary use in this platform |
|--------|------------------------------|
| **Post-poll** | Reported voter behavior by social group — best for vote-bank analysis |
| **Pre-poll** | Stated preferences before the election — best for opinion-poll calibration |

### Survey vs actual

`csds_vs_actual_results.csv` joins survey estimates to actual vote shares
discovered from `data/database/results_table_{year}.csv` and
`data/database/alliance_table_{year}.csv`. National comparison is computed
when overall survey rows exist; state-level comparison is added when state
breakdowns are present in cleaned survey data.

---

## Design rules

- **Do not fake values** — only extracted table cells become vote shares
- **Do not silently impute** — missing cells stay missing
- **Do not treat pre-to-post shift as pure error** — use descriptive language
- **Keep raw extracted tables** for auditability
- **Trace every cleaned value** to `source_table` (and `source_page` when known)
- **Prefer manual review** over guessing when table structure is ambiguous

---

## QA: duplicate analytical keys

Analytical key (unique voter-behavior estimate):

```
year + poll_type + geography_level + state + voter_group_type + voter_group + party_or_alliance
```

Pre/post comparison join key (cross-survey match):

```
year + geography_level + state + voter_group_type + voter_group + party_or_alliance
```

If the same analytical key appears multiple times (e.g. the auto-cleaner misparsed
several source tables onto `voter_group=nan`), joining pre-poll to post-poll without
deduplication creates a **many-to-many cross product**. That is why the raw
comparison file can have more rows than the vote-behavior database.

Deduplication rules:

- Same `vote_share` duplicates → keep one row
- Different `vote_share` values → keep highest-confidence row
- Tied confidence with conflicting values → `conflict_flag=true`, excluded from comparison

---

## Taxonomy-guided extraction

The taxonomy YAML at `data/postpoll/taxonomy/csds_voter_behavior_taxonomy.yml`
defines:

- canonical voter groups (gender, age, religion, caste, etc.)
- party/alliance labels
- search keywords per group type
- table-type keywords (vote tables vs questionnaire vs methodology)

**Why taxonomy is better than generic extraction**

CSDS reports mix voter-behavior tables with questionnaire codebooks, newspaper
readership grids, and fieldwork notes. Generic pdfplumber extraction treated
many of these as party vote shares. Taxonomy-guided search scores pages first,
then extracts only tables where row/column labels match known voter groups and
parties.

**Review workflow**

1. `csds_table_label_miner` inventories extracted tables and scores extraction potential
2. `taxonomy_guided_search` writes page candidates with `recommended_action`
3. `taxonomy_guided_extract` creates candidate rows from high-potential CSV tables and candidate pages
4. `validate_taxonomy_candidates` flags invalid/duplicate rows
5. `approve_taxonomy_candidates` auto-approves high-confidence non-conflict rows
6. `render_taxonomy_review_pages` builds `taxonomy_review_index.html` for manual QA
7. Edit `data/postpoll/manual/entered/csds_taxonomy_candidate_review.csv` for
   `review_decision` = `approve`, `reject`, or `edit`
8. Re-run `approve_taxonomy_candidates` after editing review decisions

Only rows with `approval_status=approved` and
`curation_status` in (`trusted`, `usable_with_caution`) reach the dashboard JSON.

---

## Manual review workflow

When `manual_extraction_needed.csv` has rows, start with
`manual_extraction_priority.csv` for high-value tables:

1. Open the cited PDF page or extracted CSV in `data/postpoll/extracted/`
2. Transcribe the table into a CSV matching the extracted naming convention
3. Rerun `clean_csds_tables` through `deduplicate_vote_behavior`

---

## Election result discovery

Actual results are auto-discovered from:

- `data/outputs/`
- `data/processed/`
- `data/elections/processed/`
- `data/database/`

The builder prefers `results_table_{year}.csv` and `alliance_table_{year}.csv`.
