# Demographic data warehouse

Metadata-driven inventory for demographic variables used in the election
simulator. **Catalog first, ingestion second** — do not scrape all Census
tables or bulk-download NFHS.

## Folder layout

```
data/demographics/
  catalog/          # demographic_variables_master.csv, sources
  raw/
    census_2011/    # preferred location for Census uploads
    nfhs/
    mospi/
    rbi/
    demographics-census-2011/   # optional nested upload folder
  processed/        # cleaned tables + state_demographics_master.csv
  outputs/          # audit reports
```

Legacy uploads under `data/raw/demographics-census-2011/` are still found by
the cleaner and audit.

## Commands

```bash
# 1. Export variable catalog
python -m src.demographics.build_demographic_catalog

# 2. Clean Census 2011 state tables (after uploading raw Excel)
python -m src.demographics.clean_census_state_2011

# 3. Clean Census 2011 district PCA and rebuild split state rows
python -m src.demographics.clean_census_district_2011

# 4. Audit what is still missing
python -m src.demographics.audit_demographic_coverage

# 4b. Audit DHS/NFHS microdata zips in data/raw/dhs_downloads/
python -m src.demographics.dhs.audit_dhs_downloads
python -m src.demographics.dhs.extract_dhs_zips
python -m src.demographics.dhs.build_nfhs_state_features

# 4c. Phase 1 district infrastructure (GE join debug, district master, crosswalk)
python -m src.demographics.dhs.debug_nfhs5_ge_join
python -m src.demographics.build_district_master_table
python -m src.reference.build_district_constituency_crosswalk

# 5. Empty state master template (if starting fresh)
python -m src.demographics.build_state_demographic_master

# 6. NFHS placeholder
python -m src.demographics.merge_nfhs
```

## Current modelling sequence

Build demographics before going deeper into election data:

```text
1. State demographic master
2. State-level Lok Sabha analysis
3. Visual dashboard
4. District/constituency demographic allocation
5. Assembly elections
```

Assembly election data should wait until the state-level demographic and
Lok Sabha analysis spine is trusted.

## Census cleaner outputs

`clean_census_state_2011` writes:

* `processed/census_state_demographics_2011.csv` — Census-only state metrics
* `processed/state_demographics_master.csv` — merged template (Census columns
  filled where parsed; NFHS columns still empty until NFHS cleaners exist)

`clean_census_district_2011` writes:

* `processed/census_district_demographics_2011.csv` — one row per 2011 district
* `processed/census_state_from_districts_2011.csv` — district rollups with
  Telangana and Ladakh split out
* `processed/state_demographics_master.csv` — updated with district-derived
  population, urban/rural, SC/ST, sex ratio, and literacy columns

Known geography caveats:

* Telangana and Ladakh are split from the district PCA workbook.
* Dadra & Nagar Haveli and Daman & Diu are combined for 2024 election analysis
  from two 2011 Census rows.
* District PCA does not contain religion or detailed age; those split-state
  columns stay empty until district religion/age cleaners exist.

These statuses are surfaced in
`data/outputs/state_election_demographic_analysis.csv`.

## Needed Next Files

Highest priority:

* NFHS-5 state fact sheet / state indicator table with household indicators:
  internet access, bank account access, mobile phone access, women with
  secondary education, fertility rate, electricity, LPG, and sanitation.
* Census 2011 district-level religion table, so Telangana, Andhra Pradesh,
  Ladakh, and Jammu & Kashmir can get correct religion shares.
* Census 2011 district-level detailed age table, so split states can get youth,
  working-age, and elderly shares.

Useful next:

* Census 2011 district-level religion table.
* Census 2011 district-level age table.
* MOSPI/RBI state indicators for income, unemployment, poverty, roads,
  banking, agriculture, or other development variables.

Only upload files that map clearly to variables in
`demographic_catalog.py`; avoid bulk dumps without a variable target.

## Roadmap

| Stage | Output |
|-------|--------|
| **Now** | Catalog, Census state cleaner, audit |
| **Next** | NFHS cleaner + `merge_nfhs` |
| **Phase 1 districts** | GE join diagnostics, `district_master_table.csv`, constituency crosswalk |
| **Later** | GIS overlap weights (`district_weight_in_constituency`) |

## Phase 1 district infrastructure

After extracting NFHS Stata files and GE shapefiles:

```bash
python -m src.demographics.dhs.debug_nfhs5_ge_join
python -m src.demographics.build_district_master_table
python -m src.reference.build_district_constituency_crosswalk
```

Outputs:

| File | Description |
|------|-------------|
| `processed/nfhs5_ge_join_diagnostics.csv` | HR vs GE cluster join strategy comparison |
| `processed/district_master_table.csv` | District-level NFHS (+ Census fill where missing) |
| `data/reference/district_constituency_crosswalk.csv` | Many-to-many constituency ↔ district template |

The crosswalk is **approximate** (name matching only). A constituency may map to
multiple districts and vice versa. Future work: compute polygon overlap from
Lok Sabha constituency shapefiles × district shapefiles, then populate
`district_weight_estimate` and `overlap_method`.

## Older modules

* `census_manifest.py` — curated Census *file* checklist
* `build_state_demographics_2011.py` — legacy file inventory script
