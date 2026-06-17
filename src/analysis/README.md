# Constituency election + demographic analysis

This folder contains the first constituency-level analysis layer for the Indian Election Intelligence Platform.

It joins Lok Sabha 2019/2024 comparison outputs with NFHS constituency demographic levels and NFHS-4 to NFHS-5 change features.

## Commands

Build the master table:

```bash
python -m src.analysis.build_constituency_election_demographic_master
```

Run exploratory driver analysis:

```bash
python -m src.analysis.analyze_vote_share_drivers
```

Diagnose NFHS coverage gaps:

```bash
python -m src.analysis.coverage_diagnostics
```

Audit priority-state coverage breaks end-to-end:

```bash
python -m src.analysis.state_gap_audit
```

## Inputs

Election files are discovered automatically from likely folders:

- `data/outputs/`
- `data/processed/`
- `data/elections/processed/`
- `data/database/`

Demographic inputs:

- `data/demographics/processed/constituency_demographic_panel.csv`
- `data/demographics/processed/constituency_demographic_change_features.csv`
- `data/reference/lok_sabha_district_summary_delimitation.csv`

## Outputs

Written to `data/analysis/`:

| File | Description |
|------|-------------|
| `constituency_election_demographic_master.csv` | One row per constituency with election + demographic fields |
| `vote_share_driver_correlations.csv` | Correlations between swings/turnout/margin and demographic variables |
| `top_swing_constituencies.csv` | Top swing and close-seat tables |
| `analysis_quality_report.csv` | Coverage and quality summary |

Coverage diagnostics are written to `data/analysis/coverage/`:

| File | Description |
|------|-------------|
| `state_coverage.csv` | NFHS coverage by state |
| `variable_coverage.csv` | Non-null counts by demographic variable |
| `constituency_coverage.csv` | Per-constituency coverage flags |
| `missing_coverage_reasons.csv` | Suspected reasons for missing NFHS data |
| `coverage_summary.txt` | Human-readable summary and recommendations |

State gap audits are written to `data/analysis/coverage/state_gap_audits/`:

| File | Description |
|------|-------------|
| `west_bengal_gap_audit.csv` | District + constituency gap audit for West Bengal |
| `tamil_nadu_gap_audit.csv` | District + constituency gap audit for Tamil Nadu |
| `assam_gap_audit.csv` | District + constituency gap audit for Assam |
| `uttarakhand_gap_audit.csv` | District + constituency gap audit for Uttarakhand |
| `all_priority_states_gap_audit.csv` | Combined priority-state audit |
| `state_gap_summary.txt` | Cross-state gap summary and fix order |

## Notes

- Missing values are left blank. The script does not impute demographics.
- Joins use normalized `state_key` and `constituency_key`.
- Telangana election constituencies are matched to delimitation-era Andhra Pradesh demographic rows when needed.
- Correlation output is exploratory only. It does not establish causation.
