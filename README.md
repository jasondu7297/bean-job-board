# Celina's Comprehensive New-Grad Job Board

A resume-matched U.S. job board for new-graduate and early-career opportunities across:

- bioinformatics, computational biology, genomics, biology, and university research;
- data analysis, data science, data engineering, software, and automation;
- product, program, operations, business analysis, and broadly relevant new-grad roles.

The board is built around Celina's Biology/Bioinformatics degree and experience with Python, R, SQL, Bash, Linux, Snakemake, Nextflow, genomics workflows, data pipelines, and technical communication.

## Why this version contains hundreds rather than ten

The original preview contained only a ten-role offline seed snapshot. Version 2 keeps that snapshot solely as an instant fallback, then merges a much larger inventory from:

- Simplify's daily-maintained new-grad list;
- SpeedyApply's U.S. software and AI/data new-grad lists;
- Jobright's daily feeds for data analysis, software, product, business analysis, engineering, research/consulting, education, public sector, management, marketing, HR, support, and design;
- official Greenhouse, Lever, Ashby, Workday, and selected university/research-institution career sources;
- optional Adzuna and USAJOBS APIs.

The browser refresh normally produces several hundred unique U.S. roles after location filtering and deduplication. The exact total changes as sources add, remove, or close postings.

## What the board does

- Fetches high-volume live feeds whenever the page opens, with a second CDN endpoint as a fallback.
- Runs a scheduled GitHub Action every day to rebuild and deploy a persistent snapshot.
- Stores `first_seen_at`, `last_seen_at`, and `is_new` fields so daily runs can identify net-new roles.
- Tracks a browser-local comparison baseline for the **New since last sync** filter.
- Deduplicates by normalized application URL, then by company/title/location.
- Filters to U.S. roles and removes internships, postdoctoral positions, obviously senior roles, and out-of-scope listings.
- Scores every job against the resume and groups it into Strong, Good, or Stretch fit tiers.
- Generates a tailored cold-email draft for likely university, lab, clinical-research, bioinformatics, genomics, and research-data positions.
- Supports search, category/location/source/recency filters, saved jobs, pagination, and CSV export.

No job aggregator can guarantee every posting, and no source can guarantee ten genuinely new openings on every calendar day. The architecture is deliberately broad enough that active hiring days will often add many roles, while accurately reporting zero or fewer additions when posting volume is lower.

## Open the standalone board

`site/standalone.html` is a single self-contained page. Open it while connected to the internet; the ten-role fallback appears immediately and the comprehensive live inventory is merged in automatically.

The multi-file site can also be served locally:

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python scripts/update_jobs.py --offline
python -m http.server 8000 -d site
```

Then open `http://localhost:8000`.

A full server-side refresh is:

```bash
python scripts/update_jobs.py --max-age-days 120 --min-score 0
```

Generated outputs:

```text
site/data/jobs.json
site/data/jobs.js
site/data/jobs.csv
site/data/cold-emails.md
site/standalone.html
```

## Deploy with automatic daily refresh

1. Create a GitHub repository and upload the project.
2. Open **Settings → Pages** and choose **GitHub Actions** as the source.
3. Open **Actions → Refresh and deploy job board → Run workflow** for the first deployment.
4. Leave the included schedule enabled.

The action refreshes all configured sources, runs the tests, commits the new snapshot so history persists, and deploys the `site/` directory to GitHub Pages. GitHub may start scheduled workflows several minutes after the listed cron time.

## Optional API secrets

The high-volume feeds and public ATS connectors require no API key. For extra coverage, add repository secrets under **Settings → Secrets and variables → Actions**:

| Secret | Purpose |
|---|---|
| `ADZUNA_APP_ID` | Adzuna application ID |
| `ADZUNA_APP_KEY` | Adzuna application key |
| `USAJOBS_API_KEY` | USAJOBS developer key |
| `USAJOBS_EMAIL` | Email used in the USAJOBS API header |

The workflow continues when these optional secrets are absent.

## Customize coverage

- `config/profile.yml` controls resume skills, target locations, experience highlights, and cold-email language.
- `config/sources.yml` contains the high-volume feeds, employer ATS boards, university/research pages, and optional API queries.
- `config/seed_jobs.yml` is only the verified fallback snapshot.
- `JOB_BOARD_MAX_AGE_DAYS` and `JOB_BOARD_MIN_SCORE` tune recency and score filtering.

Example employer additions:

```yaml
greenhouse:
  - name: Example Biotech
    board: examplebiotech
    org_type: research

lever:
  - name: Example Data Company
    site: exampledata
    org_type: company
```

A broken or renamed source is logged and skipped independently rather than breaking the full refresh.

## Cold-email behavior

Research-oriented jobs receive a draft that:

- introduces Celina's Biology/Bioinformatics background;
- references the BRCA1/BRCA2 population-genomics workflow and OICR internships;
- connects Python, R, SQL, Linux, workflow automation, and biological context to the role;
- asks for a 15–20 minute conversation about the lab, its current work, and the position.

Before sending, replace the generic recipient, read the lab website, and add one accurate sentence about a current paper, project, or research direction.

## Privacy

The public page does not expose a phone number or email address. Saved jobs and browser comparison history remain in `localStorage` on the current device.

## Tests

```bash
python -m unittest discover -s tests -v
node --check site/live_sources.js
node --check site/app.js
```

## Project layout

```text
config/                  profile, source inventory, fallback jobs
jobboard/                parsers, fetchers, scoring, normalization, email generation
scripts/update_jobs.py   refresh CLI
site/                    static UI, browser live-loader, generated data
.github/workflows/       scheduled refresh and GitHub Pages deployment
tests/                   parser, scoring, location, and email tests
```
