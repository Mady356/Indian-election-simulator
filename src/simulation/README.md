# Simulation Data for The 543

This folder builds static JSON bundles for dashboard simulation features.

## Scenario simulator (deterministic)

```bash
python -m src.simulation.build_simulation_base
```

Output: `frontend/public/data/simulation_base.json`

## Monte Carlo simulator (probabilistic)

```bash
python -m src.simulation.build_monte_carlo_base
```

Output: `frontend/public/data/monte_carlo_base.json`

### Alliance mapping

Party-to-alliance mapping for 2024 lives in:

`data/reference/party_alliance_mapping.csv`

Columns: `party`, `normalized_party`, `alliance_2024`, `notes`

Alliance buckets: `NDA`, `INDIA`, `Others`, `Unknown`

Unknown parties are not invented; they roll into Others only when simulating limited seats.

### Monte Carlo base fields

Each constituency includes:

- 2024 election fields (winner, BJP/INC shares, margin, turnout, nfhs5_coverage_share)
- `party_vote_shares_2024` when ECI results are available
- `alliance_vote_shares_2024` aggregated from the mapping
- `simulation_completeness`:
  - `full_party_shares`
  - `bjp_inc_limited`
  - `winner_margin_only`

Missing party vote shares are not imputed in the base dataset.

## Frontend

- Deterministic engine: `frontend/src/lib/simulator.ts` (legacy scenario tool)
- Monte Carlo engine: `frontend/src/lib/monteCarlo.ts`
- Forecast Lab page: `frontend/src/pages/ForecastPage.tsx` at `/forecast`

The Forecast Lab page runs entirely in the browser. It is an experimental probabilistic simulator, not a calibrated forecast.

## Rebuild workflow

After election pipeline updates:

```bash
python -m src.simulation.build_simulation_base
python -m src.simulation.build_monte_carlo_base
cd frontend && npm run build
```
