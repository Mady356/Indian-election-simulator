# Scenario Guide

This folder contains editable simulator assumptions.

## Current Scenario

### `sim_v1_state_party_swings.csv`

This is the default input for:

```bash
venv/bin/python -m src.simulation.election_simulator_v1
```

Columns:

* `state` = state name exactly as it appears in the 2024 database table.
* `party_id` = normalized party ID.
* `swing` = vote-share percentage-point shift to apply.

Example:

```csv
state,party_id,swing
Maharashtra,BJP,-3.0
Maharashtra,INC,2.0
```

That means BJP loses 3 percentage points in Maharashtra and INC gains 2.
The simulator then renormalizes constituency vote shares back to 100%.

## How To Experiment

For now, edit `sim_v1_state_party_swings.csv` and rerun:

```bash
venv/bin/python -m src.simulation.election_simulator_v1
```

Recommended next improvement: add a command-line argument so the simulator can
run any scenario CSV without renaming files.
