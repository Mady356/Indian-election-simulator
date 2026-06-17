# NFHS-4 / NFHS-5 demographic panel pipeline

Build district-level and constituency-level NFHS panels with cross-round change
features for the Indian Election Intelligence Platform.

## Inputs

| Path | Role |
|------|------|
| `data/demographics/processed/nfhs_district_features.csv` | District NFHS aggregates (from DHS microdata pipeline) |
| `data/reference/lok_sabha_district_summary_delimitation.csv` | LS constituency → district weights (`district_segment_share`) |
| `data/raw/NHFS-DATA/` | Reference NFHS tables (state summary + NFHS-5 micro extract); **not overwritten** |

Upstream (if district features missing):

```bash
python -m src.demographics.dhs.build_nfhs_district_features
```

## Outputs

| File | Description |
|------|-------------|
| `nfhs_district_panel.csv` | NFHS-4 and NFHS-5 district rows (separate rows per survey) |
| `nfhs_district_change_features.csv` | District-level NFHS-4 → NFHS-5 changes |
| `constituency_demographic_panel.csv` | Weighted constituency aggregates per survey |
| `constituency_demographic_change_features.csv` | Constituency-level changes |
| `nfhs4_district_code_crosswalk.csv` | NFHS-4 `sdist` code → district name mapping |
| `nfhs_panel_quality_report.csv` | Validation summary |

## NFHS-4 district code crosswalk

NFHS-4 stores districts as numeric `sdist` codes. Resolve them before change
features or constituency aggregation:

```bash
python -m src.demographics.nfhs.build_nfhs4_district_crosswalk
```

Output: `data/demographics/processed/nfhs4_district_code_crosswalk.csv`

The district panel builder applies this crosswalk automatically when census
2011 districts are available.

## Run order

```bash
python -m src.demographics.nfhs.build_nfhs4_district_crosswalk   # optional; panel rebuilds if missing
python -m src.demographics.nfhs.build_nfhs_district_panel
python -m src.demographics.nfhs.build_nfhs_change_features
python -m src.demographics.nfhs.build_constituency_demographic_panel
python -m src.demographics.nfhs.validate_nfhs_panel
```

## Panel rules

- **No imputation** — missing values stay missing.
- **NFHS-4 year = 2016**, **NFHS-5 year = 2021** for annualized change:
  `feature_annual_change = (NFHS5 − NFHS4) / 5`
- **Constituency aggregation**: weighted sum using `district_segment_share`; weights
  renormalized within constituency if they do not sum to 1; districts without NFHS
  data are excluded and `coverage_share` is reduced.
- **change_quality_flag**:
  - `high` — both rounds, reasonable household sample, all change features present
  - `medium` — both rounds, reasonable sample, some features missing
  - `low` — one round missing, weak sample, or unmapped numeric code

Crosswalk methods (see `build_nfhs4_district_crosswalk.py`):

1. Census 2011 rank within state → district name
2. NFHS-5 label validation (exact / fuzzy)
3. Feature-vector Hungarian fallback

Re-run the panel pipeline after updating crosswalk or `nfhs_district_features.csv`.

## Andhra Pradesh / Telangana bifurcation (2014)

The 2008 delimitation order lists Telangana districts under schedule **Andhra
Pradesh** (`RANGAREDDI`, `HYDERABAD`, etc.). Census 2011 and NFHS-4 use undivided
AP labels; NFHS-5 reports **Telangana** as a separate state.

| Layer | Behaviour |
|-------|-----------|
| `delimitation_census_district_alias.csv` | `nfhs4_state=Andhra Pradesh`, `nfhs5_state=Telangana` for Telangana-region districts |
| NFHS-5 GE join | Hybrid `IAGE71FL` + `IAGE7AFL` (Telangana clusters only resolve on 7AFL) |
| Constituency panel | Looks up NFHS-5 under Telangana; falls back to NFHS-4 AP district rows when NFHS-5 district GE data is missing (`_nfhs4_telangana_proxy`) |

Logic: `src/reference/ap_telangana_bifurcation.py`. Rebuild alias table after
district features update:

```bash
python -m src.reference.build_delimitation_census_district_alias
```

States missing NFHS-5 district extracts (Tamil Nadu, Assam, West Bengal, etc.)
still get census names but cannot produce cross-round district changes until
NFHS-5 district features are rebuilt for those states.
