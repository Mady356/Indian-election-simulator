# Manual constituency demographic overrides

Safe, source-tracked manual demographic entry for constituencies where the NFHS/Census-linked pipeline has missing or low coverage.

## Principles

- **Use real public sources only.** Census tables, NFHS reports, state statistical abstracts, election commission handbooks, and other verifiable documents.
- **Do not invent demographic data.** If a value cannot be sourced, leave the template row blank.
- **Generated pipeline values are preferred.** Manual values fill gaps; they do not silently replace NFHS/Census-linked estimates unless `override_allowed=true`.
- **Every manual value needs provenance:** `source_name`, `source_year`, `method`, `confidence`, and `notes` (required for proxies/estimates).
- **State averages and proxies must be marked `low` confidence** and explained in `notes`.
- **Do not fill all 3,801 template rows at once.** Work in daily batches and complete core fields first.
- **Do not invent election results.** If election data is missing, mark the seat for election result research.

## Core fields (fill these first)

`urban_pct`, `literacy_rate`, `sc_pct`, `st_pct`, `religion_hindu_pct`, `religion_muslim_pct`, `population_density`, `sex_ratio`

## Census 2011 autofill (review before merge)

District-level Census approximations for missing core fields. **Candidates are not merged automatically.**

```bash
python -m src.demographics.census.clean_completion_worklist_aliases
python -m src.demographics.census.build_census_district_core
python -m src.demographics.census.build_census_religion_district
python -m src.demographics.census.autofill_constituency_core_demographics
```

Review `manual_constituency_demographics_autofill_candidates.csv`, then append approved rows to `manual_constituency_demographics.csv`.

See `src/demographics/census/README.md` for full details.

## Manual demographic workflow

1. **Build master completion worklist** — canonical seat universe and gap classification
2. **Build completion batch** — export the next 50 incomplete seats (core fields first)
3. **Track progress** — see what is missing by state, seat, and variable
4. **Fill values** from real public sources in the batch CSV or `manual_constituency_demographics.csv`
5. **Validate** manual demographics
6. **Merge** manual demographics into the master panel
7. **Rebuild** frontend bundle
8. **Run** frontend build
9. **Deploy**

## Commands

```bash
python -m src.demographics.manual.build_master_completion_worklist
python -m src.demographics.manual.build_manual_completion_batch
python -m src.demographics.manual.manual_progress_tracker
python -m src.demographics.manual.build_daily_manual_batch
python -m src.demographics.manual.validate_manual_demographics
python -m src.demographics.manual.merge_manual_demographics
python -m src.export.build_frontend_data_bundle
cd frontend && npm run build
```

Supporting commands:

```bash
python -m src.demographics.manual.build_manual_demographic_template
```

## Progress reports

`build_master_completion_worklist` writes:

- `data/demographics/manual/reports/master_seat_completion_worklist.csv`
- `data/demographics/manual/reports/master_seat_completion_by_state.csv`
- `data/demographics/manual/reports/master_seat_completion_checklist.md`

`build_manual_completion_batch` writes:

- `data/demographics/manual/daily_batches/manual_completion_batch_YYYY_MM_DD.csv`

`manual_progress_tracker` writes:

- `data/demographics/manual/reports/manual_demographic_progress_by_state.csv`
- `data/demographics/manual/reports/manual_demographic_progress_by_constituency.csv`
- `data/demographics/manual/reports/manual_demographic_progress_by_variable.csv`

## Daily batches

`build_daily_manual_batch` writes:

- `data/demographics/manual/daily_batches/manual_batch_YYYY_MM_DD.csv`

Batch prioritization:

1. Priority seats with `election_only` demographic coverage
2. States with zero or low demographic coverage
3. Seats with manual seat notes already written
4. High political importance (priority seat list score)

After filling a batch, append completed rows to `manual_constituency_demographics.csv` and run validate → merge → bundle.

## Enter manual values

Edit `data/demographics/manual/manual_constituency_demographics.csv`.

Required columns for each filled row:

| Column | Notes |
|--------|-------|
| `state_key`, `constituency_key` | Must match `constituencies.json` |
| `variable` | One of the allowed variables (see below) |
| `value` | Numeric |
| `source_name` | Publication or dataset name |
| `source_year` | Year of the source |
| `method` | How the value was derived |
| `confidence` | `high`, `medium`, or `low` |
| `notes` | Required for estimates, proxies, district/state roll-ups |

Set `override_allowed=true` only when you deliberately want a manual value to replace an existing generated NFHS value (rare; use with caution).

## Validation

```bash
python -m src.demographics.manual.validate_manual_demographics
```

Writes `data/demographics/manual/manual_demographic_quality_report.csv` with statuses:

- `valid`
- `missing_source`
- `invalid_value`
- `missing_method`
- `duplicate_conflict`
- `needs_review`

## Merge

```bash
python -m src.demographics.manual.merge_manual_demographics
```

Inputs:

- `data/analysis/constituency_election_demographic_master.csv`
- `data/demographics/manual/manual_constituency_demographics.csv`

Outputs:

- `data/analysis/constituency_election_demographic_master_with_manual.csv`
- `data/demographics/processed/constituency_demographic_panel_with_manual.csv`

Merge rules:

- Missing generated values are filled from valid manual rows.
- Existing generated values are kept; manual alternatives are stored as `manual_{variable}` reference columns unless `override_allowed=true`.
- Per-field metadata columns: `{variable}_source`, `{variable}_source_year`, `{variable}_method`, `{variable}_confidence`.
- Constituency summary fields: `manual_demographic_fields_count`, `manual_demographic_source_count`, `demographic_source_type` (`generated`, `manual`, `mixed`, `election_only`).

## Frontend bundle

```bash
python -m src.export.build_frontend_data_bundle
cd frontend && npm run build
```

Exports manual demographic metadata to `frontend/public/data/constituencies.json` and `frontend/public/data/manual_demographic_sources.json`.

## Allowed variables

`urban_pct`, `literacy_rate`, `female_literacy_pct`, `male_literacy_pct`, `sc_pct`, `st_pct`, `religion_hindu_pct`, `religion_muslim_pct`, `religion_christian_pct`, `religion_sikh_pct`, `population_density`, `sex_ratio`, `electricity_pct`, `lpg_pct`, `improved_sanitation_pct`, `mobile_phone_pct`, `bank_account_pct`, `wealth_index_mean`, `fertility_rate`

## Allowed confidence

`high`, `medium`, `low`

## Allowed geography_level

`constituency`, `district`, `subdistrict`, `municipal`, `district_weighted_estimate`, `state_average_proxy`
