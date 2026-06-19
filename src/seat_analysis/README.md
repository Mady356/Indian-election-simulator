# Seat Intelligence Notes v1

Structured seat-by-seat analysis for **The 543**, generated from existing election and demographic data, with optional manual analyst overrides.

## What this layer does

- **Baseline notes** are auto-generated for every Lok Sabha constituency in the master dataset.
- **Priority seats** are flagged for manual review based on flips, close contests, large swings, and major constituencies.
- **Manual notes** can override generated text where analysts add higher-quality context.
- **Final output** is exported to CSV and `frontend/public/data/seat_analysis.json` for dashboard use.

## Principles

- Use only available structured data.
- Do not invent local facts, caste/religion claims, or constituency folklore.
- Do not make causal claims. Generated language uses cautious phrasing such as “available data indicates” and “may suggest”.
- Clearly separate election movement from demographic interpretation.
- Missing demographic values are **not** imputed.

## Data folders

| Path | Purpose |
|------|---------|
| `data/seat_analysis/generated/` | Machine-generated baseline and priority lists |
| `data/seat_analysis/manual/` | Analyst templates and working manual notes |
| `data/seat_analysis/processed/` | Merged final seat analysis CSV |
| `frontend/public/data/` | Deployable `seat_analysis.json` |

## Inputs

- `data/analysis/constituency_election_demographic_master.csv`
- `data/analysis/top_swing_constituencies.csv`
- `data/analysis/coverage/constituency_coverage.csv` (referenced in project docs; baseline uses master fields)
- `frontend/public/data/constituencies.json`
- `frontend/public/data/states.json`

## Commands

Run from the repository root:

```bash
python -m src.seat_analysis.build_seat_analysis_baseline
python -m src.seat_analysis.build_priority_seat_list
python -m src.seat_analysis.merge_manual_seat_notes
```

Recommended order:

1. Build baseline notes for all seats.
2. Build priority list and manual template.
3. Merge baseline + manual notes into final outputs.

## Outputs

| File | Description |
|------|-------------|
| `data/seat_analysis/generated/seat_analysis_baseline.csv` | Generated notes for all constituencies |
| `data/seat_analysis/generated/priority_seat_list.csv` | Ranked seats for manual review |
| `data/seat_analysis/manual/manual_seat_notes_template.csv` | Blank manual fields for priority seats |
| `data/seat_analysis/processed/seat_analysis_final.csv` | Merged final notes |
| `frontend/public/data/seat_analysis.json` | Frontend-ready JSON keyed by `STATE_KEY::CONSTITUENCY_KEY` |

## Manual analyst workflow

1. Run the baseline and priority scripts.
2. Copy `manual_seat_notes_template.csv` to `manual_seat_notes.csv` if you want a working file separate from the template.
3. Fill only the `manual_*` columns where you want to override generated text.
4. Leave fields blank to keep generated baseline content.
5. Re-run `merge_manual_seat_notes`.

### Manual columns

- `manual_summary`
- `manual_electoral_movement`
- `manual_key_factors`
- `manual_demographic_context`
- `manual_local_context`
- `manual_what_to_watch`
- `manual_confidence`
- `analyst_name`
- `last_reviewed`
- `source_notes`

Manual overrides apply **only** where a manual field is non-empty.

## JSON object shape

Each seat is keyed as:

```text
NORMALIZED_STATE_KEY::NORMALIZED_CONSTITUENCY_KEY
```

Example fields:

- `summary`
- `electoral_movement`
- `key_factors`
- `demographic_context`
- `district_context`
- `local_context`
- `what_to_watch`
- `confidence`
- `data_quality_note`
- `analysis_source` (`generated`, `manual`, or `mixed`)

## Key factor tags

Baseline generation may assign tags such as:

- `seat_flip`
- `close_contest_2024`
- `large_bjp_gain` / `large_bjp_loss`
- `large_inc_gain` / `large_inc_loss`
- `high_turnout_change`
- `urban_profile` / `rural_profile`
- `high_demographic_coverage` / `low_demographic_coverage`
- `election_only_profile`
- `district_coverage_gap`

Thresholds:

- large swing: absolute value ≥ 10 percentage points
- close contest: `margin_2024` ≤ 5 percentage points
- high coverage: `nfhs5_coverage_share` ≥ 0.75
- low coverage: `nfhs5_coverage_share` < 0.5

## Rebuilding frontend JSON

After updating manual notes:

```bash
python -m src.seat_analysis.merge_manual_seat_notes
```

If upstream election/demographic data changes, rebuild baseline first:

```bash
python -m src.seat_analysis.build_seat_analysis_baseline
python -m src.seat_analysis.build_priority_seat_list
python -m src.seat_analysis.merge_manual_seat_notes
```

## Editorial guidance

Manual notes should still avoid unsupported causal claims. Use `manual_local_context` only when backed by cited sources recorded in `source_notes`.
