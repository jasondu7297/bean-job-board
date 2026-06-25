# Celina's New-Grad Job Board

A resume-matched U.S. job board for new-grad and early-career roles across bioinformatics, computational biology, genomics, biology research, data analysis, data engineering, software, product, operations, and other broadly relevant roles.

## What it does

- Pulls roles from high-volume new-grad feeds, public ATS sources, university/research career pages, and optional Adzuna/USAJOBS APIs.
- Deduplicates jobs by application URL, company, title, and location.
- Filters for U.S. roles and removes internships, postdocs, senior roles, and clearly out-of-scope postings.
- Generates tailored cold-email drafts for research, lab, university, bioinformatics, genomics, and research-data roles.
- Supports search, filters, saved jobs, pagination, and CSV export.
- Refreshes daily through GitHub Actions.

## Open the board

Use the standalone version:

```text
site/standalone.html
```

Open it in a browser while connected to the internet. The fallback snapshot loads immediately, then live sources are merged in automatically.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python scripts/update_jobs.py --offline
python -m http.server 8000 -d site
```

Then open:

```text
http://localhost:8000
```

To run a full refresh:

```bash
python scripts/update_jobs.py --max-age-days 120 --min-score 0
```

Generated files:

```text
site/data/jobs.json
site/data/jobs.js
site/data/jobs.csv
site/data/cold-emails.md
site/standalone.html
```

## Deploy with daily refresh

1. Create a GitHub repository and upload the project.
2. Go to **Settings → Pages** and select **GitHub Actions** as the source.
3. Go to **Actions → Refresh and deploy job board → Run workflow**.
4. Keep the included schedule enabled for automatic daily refreshes.

The workflow refreshes jobs, updates the snapshot, runs tests, and deploys the `site/` folder to GitHub Pages.

## Optional API keys

The main sources work without API keys. For extra coverage, add these GitHub repository secrets:

| Secret            | Purpose                              |
| ----------------- | ------------------------------------ |
| `ADZUNA_APP_ID`   | Adzuna application ID                |
| `ADZUNA_APP_KEY`  | Adzuna application key               |
| `USAJOBS_API_KEY` | USAJOBS developer key                |
| `USAJOBS_EMAIL`   | Email used in the USAJOBS API header |

## Customize

- `config/profile.yml` — resume details, skills, target locations, and cold-email language.
- `config/sources.yml` — job feeds, ATS boards, university pages, and optional APIs.
- `config/seed_jobs.yml` — fallback snapshot roles.
- `JOB_BOARD_MAX_AGE_DAYS` — maximum posting age.
- `JOB_BOARD_MIN_SCORE` — minimum resume-match score.

## Tests

```bash
python -m unittest discover -s tests -v
node --check site/live_sources.js
node --check site/app.js
```
