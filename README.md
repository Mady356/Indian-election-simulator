# The 543

**Indian Election Intelligence** — explore Lok Sabha elections at [the543.org](https://the543.org).

## Quick start

### Frontend (static MVP — deployable to Vercel)

```bash
python -m src.export.build_frontend_data_bundle
python scripts/check_deploy_safety.py
cd frontend
npm install
npm run dev
```

See [frontend/DEPLOYMENT.md](frontend/DEPLOYMENT.md) for Vercel + `the543.org` setup.

### Backend API (optional)

```bash
source venv/bin/activate
pip install -r requirements.txt
uvicorn backend.app.main:app --reload
```

See [backend/README.md](backend/README.md).

## Data

Large raw files (DHS microdata, CSDS PDFs) are **not** in git. Processed analysis outputs live under `data/analysis/` and `frontend/public/data/`.

## Pipelines

| Module | Path |
|--------|------|
| Delimitation / crosswalks | `src/reference/` |
| NFHS demographics | `src/demographics/` |
| Swing & correlation analysis | `src/analysis/` |
| CSDS post-poll extraction | `src/postpoll/` |
| Frontend data bundle | `src/export/` |

## License

Research / educational use. Verify election figures against official ECI publications.
