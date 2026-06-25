# Census 2011 constituency demographic autofill

District-level Census 2011 approximations for missing constituency core demographic fields. This pipeline **does not** merge values automatically — it produces reviewable candidate files.

## Important principles

- **Census values are district-level approximations**, not exact constituency microdata.
- **Constituency boundaries do not always match districts.** Multi-district seats use population-weighted district estimates.
- **Generated NFHS values remain preferred.** This pipeline only proposes fills for missing core fields.
- **Do not treat district proxies as exact constituency demographics.**
- **Every auto-filled value includes** `source_name`, `source_year`, `method`, `confidence`, and `notes`.
- **Review candidates before merge.** Nothing is appended to `manual_constituency_demographics.csv` automatically.
- **Run `finalize_543_seat_universe` before manual sourcing** so the worklist matches the platform's current Lok Sabha seats.
- **Do not manually source records listed in** `non_543_records_to_exclude.csv` (old names, alias duplicates, geo-only extras).

## Raw inputs

Place official Census 2011 files under:

- `data/demographics/census/raw/`
- or legacy `data/raw/demographics-census-2011/`

Supported files:

| File | Purpose |
|------|---------|
| `India State District Population 2011.xlsx` | District PCA core demographics |
| District-level **C-01** religion tables (`DDWxxC-01 MDDS.XLS`) | District religion shares (required for `religion_hindu_pct`, `religion_muslim_pct`, `religion_christian_pct`, `religion_sikh_pct`) |
| **A-01** or compatible district area Excel/CSV | District area for `population_density` |

**Do not use** `DDW00C-01 MDDS.XLS` for district-level religion — it is all-India/state metadata only.

Download state C-01 files automatically from the official Census NADA catalog:

```bash
python -m src.demographics.census.download_c01_religion_files
```

Files are cached under `data/demographics/census/raw/religion/`. Re-run with `--force` to redownload.

**Telangana note:** Census 2011 has no separate Telangana state code. Telangana constituencies use 2011 Andhra Pradesh (code 28) district rows with post-2011 state reassignment.

If raw PCA is missing, `build_census_district_core` falls back to:

- `data/demographics/processed/census_district_demographics_2011.csv`

`build_district_area_table` scans raw folders for A-01 / area files and writes `census_2011_district_area.csv`. `build_census_district_core` joins that table to compute `population_density` when area is available.

## Commands

Run in this order:

```bash
python -m src.demographics.census.finalize_543_seat_universe
python -m src.demographics.census.diagnose_skipped_autofill_seats
python -m src.demographics.census.clean_completion_worklist_aliases
python -m src.demographics.census.build_district_area_table
python -m src.demographics.census.download_c01_religion_files
python -m src.demographics.census.build_census_district_core
python -m src.demographics.census.build_census_religion_district
python -m src.demographics.census.autofill_constituency_core_demographics
```

After review, append approved rows from:

- `data/demographics/manual/manual_constituency_demographics_autofill_candidates.csv`

into `manual_constituency_demographics.csv`, then run the manual merge workflow:

```bash
python -m src.demographics.manual.validate_manual_demographics
python -m src.demographics.manual.merge_manual_demographics
python -m src.export.build_frontend_data_bundle
cd frontend && npm run build
```

## Outputs

| File | Description |
|------|-------------|
| `final_543_seat_universe.csv` | Current platform Lok Sabha seat universe |
| `non_543_records_to_exclude.csv` | Old names, alias duplicates, and other non-platform records |
| `skipped_autofill_seats_diagnostics.csv` | Per-seat skip reasons and recommended actions |
| `skipped_autofill_seats_markdown.md` | Human-readable skip summary |
| `c01_religion_download_manifest.csv` | NADA catalog crawl and download manifest |
| `c01_religion_missing_priority_states.csv` | Priority-state download coverage check |
| `completion_worklist_alias_repair_report.csv` | Alias / duplicate classification |
| `master_seat_completion_worklist_cleaned.csv` | Deduplicated worklist for autofill |
| `census_2011_district_core.csv` | District core demographics (with density when area joined) |
| `census_2011_district_religion.csv` | District religion shares |
| `constituency_census_autofill_candidates.csv` | Wide candidate summary with mapping metadata |
| `manual_constituency_demographics_autofill_candidates.csv` | Long-format manual entry candidates |

## Autofill rules

- `source_name` = Census 2011
- `source_year` = 2011
- `method` = `district_proxy` (single district) or `district_weighted_estimate` (multiple districts)
- `confidence` = `medium` when district mapping is complete; `low` when mapping is partial
- `population_density` is only filled when district area exists (from A-01 via `build_district_area_table`)
- Religion fields are only filled when **district-level** C-01 religion data is available (`DDWxxC-01`, not `DDW00C-01`)
- Existing generated NFHS values and existing manual rows are never overwritten
- Autofill targets are restricted to seats in `final_543_seat_universe.csv`

## Core fields

`urban_pct`, `literacy_rate`, `female_literacy_pct`, `male_literacy_pct`, `sc_pct`, `st_pct`, `religion_hindu_pct`, `religion_muslim_pct`, `religion_christian_pct`, `religion_sikh_pct`, `population_density`, `sex_ratio`
