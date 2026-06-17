# Outputs Guide

This folder contains report-style outputs. These are the files to open when
you want to understand results, not rebuild the pipeline.

## Start Here

### `state_election_demographic_analysis.csv`

The main state-level bridge table.

Read it as:

* One row = one 2024 election state/UT.
* Election columns summarize 2019-to-2024 Lok Sabha outcomes by state.
* Demographic columns come from `data/demographics/processed/state_demographics_master.csv`.
* `demography_match_status` tells whether the demographic geography is exact,
  composite, legacy 2011 geography, or missing.

Use this file first when asking state-level questions like whether volatility,
seat flips, close seats, or party swings relate to urbanisation, literacy,
religion share, SC/ST share, or youth share.

### `state_party_swing_analysis.csv`

State-party swing table.

Read it as:

* One row = one `(state, party_id)` pair.
* `avg_swing` = average constituency-level party vote-share swing from 2019 to 2024.
* `seats_2019`, `seats_2024`, and `seat_change` summarize seat outcomes.
* `alliance_2024` gives the current alliance bucket where known.

Use this file for state-by-state party analysis and dashboard filters.

### `winner_comparison_2019_2024.csv`

The main historical comparison file.

Read it as:

* One row = one matched Lok Sabha constituency.
* `party_2019` = winning party in 2019.
* `party_2024` = winning party in 2024.
* `seat_flipped` = whether the winning party changed.
* `constituency_id` = reconciled cross-year ID.
* `constituency_id_2019` and `constituency_id_2024` = original source IDs.

Current shape: 542 matched constituencies.

### `unmatched_constituencies_2019_2024.csv`

Audit file for seats that still do not match after reconciliation.

This should stay small. If it grows after future changes, inspect it before
trusting cross-year outputs.

Current shape: 1 row.

### `constituency_volatility_2019_2024.csv`

The main seat-risk / instability file.

Read it as:

* One row = one matched constituency.
* `seat_flipped` tells whether the seat changed winner party.
* `top2_margin_pct` tells how close the 2024 result was.
* `effective_num_parties` tells how fragmented the seat was.
* `avg_abs_swing` summarizes party movement.
* `volatility_score` is a rough composite instability score.

Use this file to rank battleground or unstable seats.

### `sim_v1_flip_report.csv`

The main scenario-simulation comparison file.

Read it as:

* One row = one 2024 constituency.
* `actual_party` = real 2024 winner party.
* `sim_party` = projected winner party after scenario swings.
* `flipped` = whether the scenario changes the winner.
* `sim_vote_share` = projected winner vote share.

Current shape: 542 constituencies, 21 simulated flips.

## Projection Files

### `sim_v1_party_projection.csv`

Projected seats by party under the scenario.

### `sim_v1_alliance_projection.csv`

Projected seats by alliance under the scenario.

### `sim_v1_state_projection.csv`

Projected seats by state and party under the scenario.

### `sim_v1_battlegrounds.csv`

Scenario flip report enriched with volatility fields where available.

## Lower-Level Files

### `party_swings_2019_2024.csv`

Party-level vote-share movement by constituency. Treat this carefully until a
party/faction continuity map exists.

### `state_swing_summary_2019_2024.csv`

Average party swing by state.

### `sim_v1_full_results.csv`

Candidate-level simulated results. Large and detailed; usually not the first
file to open.

## Recommended Workflow

1. Build or audit the demographic spine:
   `venv/bin/python -m src.demographics.clean_census_state_2011`
   `venv/bin/python -m src.demographics.clean_census_district_2011`
2. Build historical Lok Sabha comparison:
   `venv/bin/python -m src.analysis.compare_2019_2024`
3. Build volatility:
   `venv/bin/python -m src.analysis.build_constituency_volatality`
4. Build the state bridge:
   `venv/bin/python -m src.analysis.build_state_election_demographic_analysis`
5. Visualise `state_election_demographic_analysis.csv` and
   `state_party_swing_analysis.csv`.
