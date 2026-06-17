# Project Guide

This project is a research pipeline for Indian Lok Sabha election analysis.
It turns raw ECI files into cleaned tables, derived constituency features,
historical comparison outputs, and scenario simulations.

If you are trying to understand the project, start here.

## Where You Are

You have a working 2019 and 2024 election data pipeline.

The project can currently:

* Clean raw ECI election files for 2019 and 2024.
* Build candidate, party, constituency, and alliance tables.
* Compare 2019 vs 2024 winners and party vote-share swings.
* Reconcile most renamed or respelled constituencies across years.
* Score constituency volatility.
* Run a scenario simulator from editable state/party swing assumptions.
* Build a Census-based state demographic master table.
* Join state-level demographics to state-level 2019/2024 Lok Sabha outcomes.

The project is not yet a forecasting product. It is at the stage where the
data spine is becoming solid enough to support better models. The preferred
next direction is state-first: finish the state demographic spine, analyse
Lok Sabha outcomes state by state, then aggregate national patterns from those
state blocks.

## First Files To Open

Open these in this order:

1. [README.md](../README.md)  
   High-level project description and commands.

2. [src/config.py](../src/config.py)  
   Shows the active single-year election setting. Right now `ACTIVE_YEAR` is
   set to 2019. Change this when rebuilding one year at a time.

3. [data/outputs/README.md](../data/outputs/README.md)  
   Explains which generated CSVs matter and how to read them.

4. [data/scenarios/README.md](../data/scenarios/README.md)  
   Explains how simulator assumptions are stored.

5. [src/analysis/compare_2019_2024.py](../src/analysis/compare_2019_2024.py)  
   The main historical comparison script.

6. [src/simulation/election_simulator_v1.py](../src/simulation/election_simulator_v1.py)  
   The current full scenario simulator.

## Mental Model

The project has four layers:

```text
raw ECI files
  -> cleaned processed CSVs
  -> database tables
  -> analysis and simulation outputs
```

Use `data/processed/` when you want intermediate single-year pipeline outputs.
Use `data/database/` when you want cleaner analytical tables.
Use `data/outputs/` when you want final report-style results.
Use `data/scenarios/` when you want to edit simulator assumptions.

## The Main Pipeline

Single-year rebuild:

```bash
venv/bin/python -m src.clean.clean_eci
venv/bin/python -m src.metadata.build_party_metadata
venv/bin/python -m src.features.build_winners_table
venv/bin/python -m src.features.build_constituency_top2
venv/bin/python -m src.features.build_constituency_features
venv/bin/python -m src.analysis.vote_seat_distortion
venv/bin/python -m src.analysis.constituency_similarity
venv/bin/python -m src.database.database_layer
```

Historical comparison after both 2019 and 2024 database tables exist:

```bash
venv/bin/python -m src.analysis.compare_2019_2024
venv/bin/python -m src.analysis.build_constituency_volatality
```

Scenario simulation:

```bash
venv/bin/python -m src.simulation.election_simulator_v1
```

State election-demographic bridge:

```bash
venv/bin/python -m src.demographics.clean_census_state_2011
venv/bin/python -m src.demographics.clean_census_district_2011
venv/bin/python -m src.demographics.audit_demographic_coverage
venv/bin/python -m src.analysis.build_state_election_demographic_analysis
```

## How To Read The Current Results

Start with these three outputs:

0. [state_election_demographic_analysis.csv](../data/outputs/state_election_demographic_analysis.csv)  
   One row per state/UT. This is the main bridge between state demographics
   and state-level Lok Sabha outcomes. Use it for demographic-vs-election
   charts and state-first analysis.

1. [winner_comparison_2019_2024.csv](../data/outputs/winner_comparison_2019_2024.csv)  
   One row per matched constituency. This tells you whether the winning party
   changed between 2019 and 2024.

2. [constituency_volatility_2019_2024.csv](../data/outputs/constituency_volatility_2019_2024.csv)  
   Adds volatility features to the comparison table. Use this to find seats
   that changed parties, had close margins, fragmented competition, or large
   swings.

3. [sim_v1_flip_report.csv](../data/outputs/sim_v1_flip_report.csv)  
   Compares actual 2024 winners against the winners under your scenario swing
   assumptions.

Important current numbers:

* Matched 2019-to-2024 constituencies: 542
* Actual 2019-to-2024 seat flips: 214
* Remaining unmatched rows: 1
* Scenario simulator seats: 542
* Scenario simulator flips: 21

## How To Read Key Columns

In `winner_comparison_2019_2024.csv`:

* `constituency_id` is the reconciled cross-year key.
* `constituency_id_2019` is the original 2019 key.
* `constituency_id_2024` is the original 2024 key.
* `party_2019` and `party_2024` are the winning parties.
* `seat_flipped` is `True` when the winning party changed.

In `constituency_volatility_2019_2024.csv`:

* `top2_margin_pct` is the 2024 winner-vs-runner-up margin.
* `effective_num_parties` measures how fragmented the seat was.
* `avg_abs_swing` measures average party movement between 2019 and 2024.
* `volatility_score` is a rough composite score for seat instability.

In `sim_v1_flip_report.csv`:

* `actual_party` is the real 2024 winner's party.
* `sim_party` is the projected winner under the scenario.
* `flipped` is `True` when the scenario changes the seat winner.
* `sim_vote_share` is the projected winner's simulated vote share.

In `state_election_demographic_analysis.csv`:

* `state` is the 2024 election state/UT name.
* `demography_match_status` tells whether the demographic row is an exact
  state match, a composite 2011 UT match, legacy 2011 geography, or missing.
* `flip_rate`, `close_seat_rate_5pct`, and `avg_volatility_score` summarize
  state-level seat instability.
* `bjp_avg_swing` and `inc_avg_swing` are quick party-specific swing columns.
* Census columns such as `urban_pct`, `sc_pct`, `st_pct`, `muslim_pct`,
  `literacy_rate`, and `youth_pct` provide state context.

## What To Do Next

Recommended next sequence:

1. Finish the state demographic spine.
   Census 2011 state variables are partially populated. District PCA now
   splits Telangana and Ladakh for population/literacy/SC/ST/urbanisation.
   Add NFHS-5 state indicators and district religion/age next.

2. Build the state election-demographic bridge.
   Run `src.analysis.build_state_election_demographic_analysis` and use the
   output as the first visual-analysis table.

3. Validate the constituency alias map.
   The matching now covers 542 seats. Review the renamed-seat mappings in
   `src/analysis/compare_2019_2024.py` and keep the unmatched audit file.

4. Clean up party continuity.
   Some swings are noisy because party IDs change across years or because
   factions split. Build a party/faction continuity map before treating every
   party swing as a clean like-for-like comparison.

5. Improve simulator scenarios.
   Add more scenario CSVs under `data/scenarios/`, then let the simulator pick
   a scenario file by argument instead of always using `sim_v1_state_party_swings.csv`.

6. Add visual exploration.
   Start with state-level charts: flip rate by state, party swing by state,
   volatility by demographic variable, and scenario flips.

7. Add Monte Carlo simulation.
   Move from one deterministic scenario to many sampled scenarios, producing
   win probabilities per constituency.

8. Add assembly elections later.
   Assembly elections should come after the state-level Lok Sabha workflow is
   stable. They are the right tool for within-state political geography, but
   they add more constituency, alliance, year, and candidate complexity.

## Suggested Near-Term Milestone

The next meaningful milestone is:

> A clean state-first analytical spine: state demographics, state-level
> 2019-to-2024 Lok Sabha outcomes, party swings, volatility, and scenario
> outputs all connected in one visual-ready table.

After that, the project is ready for visual dashboards, constituency-level
demographic allocation, and then probabilistic modeling.
