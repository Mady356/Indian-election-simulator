# Election Intelligence Platform — Milestone 1 Backend

FastAPI + PostgreSQL backend for districts, constituencies, demographics, election results, and simple seat simulations.

## Prerequisites

- Python 3.11+
- PostgreSQL **optional** (SQLite is used by default for local dev)

## Setup

```bash
cd /path/to/Election-simulator
python -m venv venv
source venv/bin/activate

pip install -r backend/requirements.txt
python backend/scripts/load_csvs_to_postgres.py
```

The loader creates `backend/data/election_simulator.db` by default (SQLite).
No `createdb` or running Postgres server is required for local development.

### Optional: PostgreSQL

```bash
createdb election_simulator
```

Create `.env` in the project root:

```env
DATABASE_URL=postgresql://localhost/election_simulator
```

Then run the loader again.

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `{"detail":"Not Found"}` at `/` | Open http://127.0.0.1:8000/docs instead |
| `database_unavailable` / 503 | Run `python backend/scripts/load_csvs_to_postgres.py` |
| Postgres `Connection refused` | Either start Postgres, or remove `DATABASE_URL` from `.env` to use SQLite |
| Empty `/districts` | Re-run the loader script |

After changing `.env` or `database.py`, restart uvicorn (`Ctrl+C`, then start again).

## Load CSV data

From the project root:

```bash
python backend/scripts/load_csvs_to_postgres.py
```

Primary sources:

- `data/demographics/processed/district_master_table.csv`
- `data/demographics/processed/nfhs_state_features.csv`
- `data/reference/lok_sabha_district_summary_delimitation.csv`
- `data/reference/lok_sabha_assembly_crosswalk.csv`
- `data/database/constituency_table_2019.csv`
- `data/database/constituency_table_2024.csv`
- `data/database/results_table_2019.csv`
- `data/database/results_table_2024.csv`

## Run the API

```bash
uvicorn backend.app.main:app --reload
```

Open docs at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | API and database status |
| GET | `/districts` | List districts (`state`, `search`) |
| GET | `/districts/{district_id}` | District + demographics |
| GET | `/constituencies` | List constituencies (`state`, `search`, `party_winner`, `year`) |
| GET | `/constituencies/{id}` | Constituency detail + districts + history |
| GET | `/constituencies/{id}/demographics` | Weighted demographic profile |
| GET | `/constituencies/{id}/results` | 2019/2024 results when available |
| POST | `/simulate` | Simple swing + demographic effect simulation |

### Simulation example

```json
{
  "base_year": 2024,
  "party_swings": {"BJP": 2.0, "INC": 1.0},
  "variable_effects": {
    "urban_pct": {"party": "BJP", "effect_per_unit": 0.05},
    "female_literacy_pct": {"party": "INC", "effect_per_unit": 0.03}
  }
}
```

Logic:

1. Start from latest constituency vote shares
2. Apply uniform party swings
3. Apply demographic variable effects
4. Re-normalize shares, pick winners, count seat changes

## Tests

Tests use in-memory SQLite (no Postgres required):

```bash
pytest backend/tests -q
```

## Project layout

```
backend/
  app/
    main.py              # FastAPI entry point
    database.py          # SQLAlchemy engine/session
    models.py            # ORM tables
    schemas.py           # Pydantic models
    routers/             # API routes
    services/            # Demographics + simulation logic
  scripts/
    load_csvs_to_postgres.py
  tests/
```

## Notes

- Existing CSV files are never moved or deleted.
- Constituency demographics are weighted averages across linked districts using `district_segment_share`.
- Delhi district rows in Table A omit district names; the loader assigns district `"Delhi"` for joins.
- State-level NFHS features are stored with `geography_type='state'` on pseudo district rows (`district='__STATE__'`).
