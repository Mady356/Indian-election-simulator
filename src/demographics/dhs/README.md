# DHS / NFHS Demographic Pipeline

Aggregates DHS/NFHS microdata into **state and district features** and a
**cluster geospatial layer**. Raw microdata stays local and is gitignored.

## Privacy rules

- Never commit raw DHS microdata (`data/raw/dhs_downloads/`, `data/demographics/raw/dhs_extracted/`).
- Never export household or person rows to the visualizer.
- Only aggregated CSVs and anonymized cluster points are published.
- GPS coordinates are displaced by DHS; do not use for exact matching.

## Commands

Run from project root:

```bash
python -m src.demographics.dhs.audit_dhs_downloads
python -m src.demographics.dhs.extract_dhs_zips
python -m src.demographics.dhs.inspect_dhs_variables
python -m src.demographics.dhs.build_nfhs_state_features
python -m src.demographics.dhs.build_nfhs_district_features
python -m src.demographics.dhs.build_dhs_geospatial_layer
python -m src.demographics.dhs.debug_nfhs5_ge_join
python -m src.demographics.build_district_master_table
python -m src.reference.build_district_constituency_crosswalk
```

## Outputs

| File | Description |
|------|-------------|
| `data/demographics/processed/nfhs_state_features.csv` | State-level NFHS-4/5 indicators + trends |
| `data/demographics/processed/nfhs_district_features.csv` | District-level (when join succeeds) |
| `data/demographics/processed/nfhs5_ge_join_diagnostics.csv` | NFHS-5 HR↔GE cluster join strategy tests |
| `data/demographics/processed/district_master_table.csv` | Unified district demographic master |
| `data/reference/district_constituency_crosswalk.csv` | Many-to-many constituency↔district mapping |
| `data/demographics/processed/dhs_cluster_geospatial.csv` | Cluster lat/lon (internal aggregated) |
| `data/demographics/processed/dhs_feature_dictionary.csv` | Variable labels from Stata metadata |
| `visualizer/data/dhs_geospatial_clusters_public.csv` | Public-safe map layer |

## Visualizer

```bash
cd visualizer && python3 -m http.server 8080
```

Open http://localhost:8080 and toggle **Show DHS clusters**.

## Notes

- Uses Stata (`DT`) zips only in extraction step.
- Weights (`hv005`, `v005`, `mv005`) are divided by 1,000,000 when needed.
- `internet_pct` may be NA if no internet variable exists in the recode file.
- District features require a district column or successful GE cluster join.
- Run `debug_nfhs5_ge_join` if NFHS-5 GE match rate is low (~5%); GE `DHSCLUST`
  often encodes clusters as `hv001 * 10` (e.g. HR 1001 → GE 10001).
- The constituency crosswalk is name-based only; use GIS overlap for production weights.
