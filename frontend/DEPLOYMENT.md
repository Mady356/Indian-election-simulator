# Deploying The 543 to Vercel

Production site: [the543.org](https://the543.org)  
Also configure: [www.the543.org](https://www.the543.org)

## Deployment target

**Vercel** — static Vite build from `frontend/`.

## Vercel project settings

| Setting | Value |
|---------|--------|
| Root Directory | `frontend` |
| Framework Preset | Vite |
| Install Command | `npm install` |
| Build Command | `npm run build` |
| Output Directory | `dist` |

## Pre-deploy: build the data bundle

From the **repository root** (not `frontend/`):

```bash
python -m src.export.build_frontend_data_bundle
python scripts/check_deploy_safety.py
```

This writes JSON to `frontend/public/data/`. Commit those files or run the command in a Vercel build step before `npm run build` if you add a monorepo build script later.

## Local production check

```bash
python scripts/production_check.py
```

Or manually:

```bash
cd frontend
npm install
npm run build
npm run preview
```

Open the URL shown by `npm run preview` (usually http://localhost:4173).

## Import from GitHub

1. Push the repo to GitHub.
2. In [Vercel](https://vercel.com), **Add New Project** → import the repository.
3. Set **Root Directory** to `frontend`.
4. Confirm build settings above and deploy.

## Custom domain (the543.org)

After the first deploy:

1. Open **Project Settings → Domains**.
2. Add:
   - `the543.org`
   - `www.the543.org`
3. At your domain registrar, add the DNS records Vercel shows (typically `A` / `CNAME` for apex and `www`).
4. Wait for DNS propagation; Vercel will issue HTTPS automatically.

## What must not be deployed

The static app should only ship:

- `frontend/dist/` (built assets)
- `frontend/public/data/*.json`
- `frontend/public/geo/*.geojson`

Do **not** put raw DHS, NFHS, CSDS, DTA, SAV, ZIP, or PDF files under `frontend/public/`. Run `python scripts/check_deploy_safety.py` before each release.

## SPA routing

`frontend/vercel.json` rewrites all routes to `index.html` so deep links work:

- `/compare`
- `/insights`
- `/methodology`
- `/state/:stateKey`
- `/constituency/:stateKey/:constituencyKey`
