# The 543 — Frontend

**Indian Election Intelligence** — static React dashboard for [the543.org](https://the543.org).

## Prerequisites

- Node.js 18+
- Python 3.12+ (to build the data bundle)

## Build data bundle

From the repository root:

```bash
python -m src.export.build_frontend_data_bundle
```

Outputs:

| File | Description |
|------|-------------|
| `public/data/constituencies.json` | 542 constituency records (election + demographics) |
| `public/data/states.json` | State-level summaries |
| `public/data/insights.json` | Correlation insights for Insights Lab |
| `public/data/coverage_summary.json` | Coverage diagnostics |
| `public/data/top_swing_constituencies.json` | Ranked swing / flip tables |
| `public/data/variable_coverage.json` | Per-variable coverage stats |

## Run locally

```bash
cd frontend
npm install
npm run dev
```

Open **http://127.0.0.1:5173**

## Production build

```bash
cd frontend
npm run build
npm run preview
```

Deploy the `frontend/dist` folder to Vercel (or any static host). Ensure `public/geo/` symlinks or copies resolve at build time.

## Pages

| Route | Description |
|-------|-------------|
| `/` | Explore — India map, search, constituency panel |
| `/compare` | 2019 vs 2024 national comparison |
| `/insights` | Insights Lab — exploratory correlations |
| `/methodology` | Data sources, coverage, limitations |
| `/state/:stateKey` | State overview |
| `/constituency/:stateKey/:constituencyKey` | Constituency profile |

Coming soon (disabled in nav): Forecast, Vote Bank Analysis, Opinion Poll Lab.

## Optional backend

The Vite dev server proxies `/api/*` to `http://127.0.0.1:8000` if you run the FastAPI backend (`backend/README.md`). The MVP dashboard does **not** depend on the API.

## Stack

- React 18 + TypeScript
- Vite
- Tailwind CSS
- TanStack React Query (static JSON loader)
- MapLibre GL
- Recharts

## Design

Dark analytical theme (`#0B1020` background). All numbers come from the JSON bundle — no hardcoded statistics. Missing demographics are shown transparently with coverage warnings.
