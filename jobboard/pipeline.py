from __future__ import annotations

import csv
import json
import logging
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from .emails import generate_cold_email
from .scoring import analyze_job, should_include
from .sources import SourceClient, collect_live_jobs
from .utils import clean_text, days_old, normalize_url, parse_date, stable_id, truncate_words

LOGGER = logging.getLogger(__name__)


def load_yaml(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def normalize_job(raw: dict[str, Any]) -> dict[str, Any]:
    job = deepcopy(raw)
    job["title"] = clean_text(job.get("title"))
    job["company"] = clean_text(job.get("company"))
    job["location"] = clean_text(job.get("location"))
    job["workplace"] = clean_text(job.get("workplace"))
    job["employment_type"] = clean_text(job.get("employment_type"))
    job["salary"] = clean_text(job.get("salary"))
    job["description"] = clean_text(job.get("description"), max_chars=12_000)
    job["url"] = normalize_url(job.get("url") or job.get("apply_url") or "")
    job["apply_url"] = normalize_url(job.get("apply_url") or job["url"])
    job["posted_at"] = parse_date(job.get("posted_at"))
    job["source"] = clean_text(job.get("source") or "Employer careers page")
    job["source_type"] = clean_text(job.get("source_type") or "unknown")
    job["org_type"] = clean_text(job.get("org_type") or "company").lower()
    job["curated_new_grad"] = bool(job.get("curated_new_grad"))
    research_text = f" {job['title']} {job['company']} {job['description']} ".lower()
    research_signal = any(term in research_text for term in (
        "bioinformatics", "computational biology", "genomics", "research assistant",
        "research associate", "research coordinator", "research technician",
        "laboratory", " lab ", "cancer institute", "medical school", "university",
    ))
    job["research"] = bool(
        job.get("research") or job["org_type"] in {"research", "university"} or research_signal
    )
    job["id"] = clean_text(job.get("id")) or stable_id(
        job["source_type"], job["company"], job["title"], job["location"], job["url"]
    )
    job["fetched_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    job["age_days"] = days_old(job["posted_at"])
    job["summary"] = truncate_words(job["description"], 48)
    return job


def _fingerprint_text(value: Any) -> str:
    text = clean_text(value).lower()
    text = re.sub(r"\b(?:new grad(?:uate)?|early career|entry level|entry-level|2025|2026|2027)\b", " ", text)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(text.split())


def _job_key(job: dict[str, Any]) -> str:
    url = normalize_url(job.get("url") or "")
    parsed_host = ""
    try:
        from urllib.parse import urlparse
        parsed_host = urlparse(url).netloc.lower()
    except Exception:
        pass
    aggregator = job.get("source_type") == "curated_feed" or any(
        host in parsed_host for host in ("simplify.jobs", "jobright.ai", "github.com")
    )
    if url and not aggregator:
        return f"url:{url.lower()}"
    company = _fingerprint_text(job.get("company"))
    title = _fingerprint_text(job.get("title"))
    location = _fingerprint_text(job.get("location"))
    return "key:" + stable_id(company, title, location)


def _merge_jobs(existing: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    """Merge duplicates, preferring official employer records over aggregator cards."""
    existing_is_feed = existing.get("source_type") == "curated_feed"
    incoming_is_feed = incoming.get("source_type") == "curated_feed"
    if existing_is_feed and not incoming_is_feed:
        merged = deepcopy(incoming)
        fallback = existing
    else:
        merged = deepcopy(existing)
        fallback = incoming

    for field in (
        "salary", "employment_type", "workplace", "location", "posted_at", "apply_url",
        "lab_or_team", "recipient", "verification_status", "last_verified_at", "category_hint",
    ):
        if not merged.get(field) and fallback.get(field):
            merged[field] = fallback[field]
    if len(fallback.get("description", "")) > len(merged.get("description", "")):
        merged["description"] = fallback["description"]
    merged["research"] = bool(merged.get("research") or fallback.get("research"))
    merged["curated_new_grad"] = bool(merged.get("curated_new_grad") or fallback.get("curated_new_grad"))
    sources = []
    for record in (existing, incoming):
        source = clean_text(record.get("source"))
        if source and source not in sources:
            sources.append(source)
    merged["also_seen_on"] = sources
    return merged


def deduplicate(jobs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_key: dict[str, dict[str, Any]] = {}
    for job in jobs:
        key = _job_key(job)
        if key in by_key:
            by_key[key] = _merge_jobs(by_key[key], job)
        else:
            by_key[key] = job
    return list(by_key.values())


def verify_seed_jobs(seed_jobs: list[dict[str, Any]], max_workers: int = 8) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    client = SourceClient()
    verified: list[dict[str, Any]] = []
    stats: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_map = {executor.submit(client.verify_seed, deepcopy(job)): job for job in seed_jobs}
        for future in as_completed(future_map):
            original = future_map[future]
            try:
                result = future.result()
                if result is None:
                    stats.append({"source": original.get("company", "seed"), "status": "expired", "fetched": 0})
                else:
                    verified.append(result)
                    stats.append({"source": original.get("company", "seed"), "status": "ok", "fetched": 1})
            except Exception as exc:
                fallback = deepcopy(original)
                fallback["verification_status"] = "Link could not be checked; verify before applying"
                verified.append(fallback)
                stats.append(
                    {
                        "source": original.get("company", "seed"),
                        "status": "error",
                        "fetched": 1,
                        "error": str(exc)[:180],
                    }
                )
    return verified, stats


def _counts(jobs: list[dict[str, Any]], field: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for job in jobs:
        value = clean_text(job.get(field) or "Unknown")
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items(), key=lambda item: (-item[1], item[0])))


def _load_previous_board(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as handle:
            value = json.load(handle)
        return value if isinstance(value, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _apply_history(
    jobs: list[dict[str, Any]], previous_board: dict[str, Any], generated_at: str
) -> tuple[int, int]:
    previous_jobs = previous_board.get("jobs", []) if isinstance(previous_board, dict) else []
    previous_by_key = {_job_key(job): job for job in previous_jobs if isinstance(job, dict)}
    current_keys: set[str] = set()
    new_count = 0
    for job in jobs:
        key = _job_key(job)
        current_keys.add(key)
        previous = previous_by_key.get(key)
        job["first_seen_at"] = (previous or {}).get("first_seen_at") or (previous or {}).get("fetched_at") or generated_at
        job["last_seen_at"] = generated_at
        job["is_new"] = previous is None
        if job["is_new"]:
            new_count += 1
    removed_count = sum(1 for key in previous_by_key if key not in current_keys)
    return new_count, removed_count


def build_board(
    root: Path,
    *,
    offline: bool = False,
    max_age_days: int = 60,
    min_score: int = 25,
) -> dict[str, Any]:
    profile = load_yaml(root / "config" / "profile.yml")
    source_config = load_yaml(root / "config" / "sources.yml") or {}
    seed_jobs = load_yaml(root / "config" / "seed_jobs.yml") or []

    source_stats: list[dict[str, Any]] = []
    if offline:
        working_seeds = seed_jobs
        source_stats.append({"source": "Verified starter snapshot", "status": "offline", "fetched": len(seed_jobs)})
        live_jobs: list[dict[str, Any]] = []
    else:
        working_seeds, verification_stats = verify_seed_jobs(seed_jobs)
        source_stats.extend(verification_stats)
        live_jobs, live_stats = collect_live_jobs(source_config, max_age_days=max_age_days)
        source_stats.extend(live_stats)

    normalized = [normalize_job(job) for job in [*working_seeds, *live_jobs] if job.get("title") and job.get("company")]
    unique = deduplicate(normalized)

    analyzed: list[dict[str, Any]] = []
    for job in unique:
        job = analyze_job(job, profile)
        if not should_include(job, max_age_days=max_age_days, min_score=min_score):
            continue
        email = generate_cold_email(job, profile)
        if email:
            job["cold_email"] = email
        job["summary"] = truncate_words(job.get("description", ""), 48)
        job["age_days"] = days_old(job.get("posted_at"))
        analyzed.append(job)

    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    previous_board = _load_previous_board(root / "site" / "data" / "jobs.json")
    new_since_previous, removed_since_previous = _apply_history(analyzed, previous_board, generated_at)

    analyzed.sort(
        key=lambda job: (
            job.get("match_score", 0),
            job.get("posted_at") or "0000-00-00",
            job.get("company", ""),
        ),
        reverse=True,
    )

    board = {
        "meta": {
            "title": profile.get("board_title", "New-Grad Job Board"),
            "candidate": profile.get("name"),
            "generated_at": generated_at,
            "offline_snapshot": offline,
            "max_age_days": max_age_days,
            "minimum_match_score": min_score,
            "total_jobs": len(analyzed),
            "new_since_previous": new_since_previous,
            "curated_feed_jobs": sum(1 for job in analyzed if job.get("curated_new_grad")),
            "official_source_jobs": sum(1 for job in analyzed if job.get("source_type") not in {"curated_feed", "seed"}),
            "successful_sources": sum(1 for row in source_stats if row.get("status") in {"ok", "offline"}),
            "removed_since_previous": removed_since_previous,
            "previous_total_jobs": len(previous_board.get("jobs", [])) if isinstance(previous_board, dict) else 0,
            "strong_matches": sum(1 for job in analyzed if job.get("fit_tier") == "Strong"),
            "research_jobs": sum(1 for job in analyzed if job.get("research")),
            "posted_last_7_days": sum(1 for job in analyzed if job.get("age_days") is not None and job["age_days"] <= 7),
            "counts_by_category": _counts(analyzed, "category"),
            "counts_by_location": _counts(analyzed, "location_group"),
            "counts_by_fit": _counts(analyzed, "fit_tier"),
            "source_health": sorted(source_stats, key=lambda row: clean_text(row.get("source")).lower()),
            "disclaimer": (
                "This board merges high-volume new-grad feeds with official employer and research-institution sources. "
                "Coverage is broad but not literally exhaustive; always confirm posting status, work authorization, degree, and experience requirements on the employer site."
            ),
        },
        "profile": {
            "name": profile.get("name"),
            "degree": profile.get("education", {}).get("degree"),
            "school": profile.get("education", {}).get("school"),
            "summary": profile.get("summary"),
            "linkedin": profile.get("linkedin"),
        },
        "jobs": analyzed,
    }
    return board


def write_board(board: dict[str, Any], site_dir: Path) -> None:
    data_dir = site_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    json_path = data_dir / "jobs.json"
    json_tmp = json_path.with_suffix(".json.tmp")
    with json_tmp.open("w", encoding="utf-8") as handle:
        json.dump(board, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    json_tmp.replace(json_path)

    new_jobs_path = data_dir / "new_jobs.json"
    new_jobs_tmp = new_jobs_path.with_suffix(".json.tmp")
    with new_jobs_tmp.open("w", encoding="utf-8") as handle:
        json.dump({"generated_at": board.get("meta", {}).get("generated_at"), "jobs": [job for job in board.get("jobs", []) if job.get("is_new")]}, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    new_jobs_tmp.replace(new_jobs_path)

    js_path = data_dir / "jobs.js"
    js_tmp = js_path.with_suffix(".js.tmp")
    with js_tmp.open("w", encoding="utf-8") as handle:
        handle.write("window.JOB_BOARD_DATA = ")
        json.dump(board, handle, ensure_ascii=False, separators=(",", ":"))
        handle.write(";\n")
    js_tmp.replace(js_path)

    csv_path = data_dir / "jobs.csv"
    csv_tmp = csv_path.with_suffix(".csv.tmp")
    fields = [
        "is_new",
        "first_seen_at",
        "match_score",
        "fit_tier",
        "title",
        "company",
        "location",
        "location_group",
        "category",
        "research",
        "entry_level",
        "posted_at",
        "salary",
        "employment_type",
        "url",
        "matched_skills",
        "warnings",
    ]
    with csv_tmp.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for job in board.get("jobs", []):
            row = {field: job.get(field, "") for field in fields}
            row["matched_skills"] = "; ".join(job.get("matched_skills", []))
            row["warnings"] = "; ".join(job.get("warnings", []))
            writer.writerow(row)
    csv_tmp.replace(csv_path)

    email_path = data_dir / "cold-emails.md"
    email_tmp = email_path.with_suffix(".md.tmp")
    lines = [
        f"# Research cold-email drafts for {board.get('profile', {}).get('name', 'the candidate')}",
        "",
        "Review the employer posting and lab website before sending. Replace generic recipients with a specific PI or hiring manager when possible.",
        "",
    ]
    for job in board.get("jobs", []):
        email = job.get("cold_email")
        if not email:
            continue
        lines.extend([
            f"## {job.get('company', '')} — {job.get('title', '')}",
            "",
            f"**Subject:** {email.get('subject', '')}",
            "",
            email.get("body", ""),
            "",
            f"Posting: {job.get('url', '')}",
            "",
            "---",
            "",
        ])
    email_tmp.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    email_tmp.replace(email_path)

    # A single-file preview is convenient for sharing or opening without a web server.
    index_path = site_dir / "index.html"
    css_path = site_dir / "styles.css"
    app_path = site_dir / "app.js"
    live_path = site_dir / "live_sources.js"
    if index_path.exists() and css_path.exists() and app_path.exists() and live_path.exists():
        html = index_path.read_text(encoding="utf-8")
        css = css_path.read_text(encoding="utf-8")
        app = app_path.read_text(encoding="utf-8")
        live = live_path.read_text(encoding="utf-8")
        payload = json.dumps(board, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
        html = html.replace(
            '<link rel="stylesheet" href="styles.css">',
            f"<style>\n{css}\n</style>",
        )
        html = html.replace(
            '<script src="data/jobs.js"></script>',
            f"<script>window.JOB_BOARD_DATA = {payload};</script>",
        )
        html = html.replace('<script src="live_sources.js" defer></script>', "")
        html = html.replace('<script src="app.js" defer></script>', "")
        html = html.replace("</body>", f"<script>\n{live}\n</script>\n<script>\n{app}\n</script>\n</body>")
        standalone_path = site_dir / "standalone.html"
        standalone_tmp = standalone_path.with_suffix(".html.tmp")
        standalone_tmp.write_text(html, encoding="utf-8")
        standalone_tmp.replace(standalone_path)


def run(
    root: Path,
    *,
    offline: bool = False,
    max_age_days: int | None = None,
    min_score: int | None = None,
) -> dict[str, Any]:
    resolved_max_age = max_age_days if max_age_days is not None else int(os.getenv("JOB_BOARD_MAX_AGE_DAYS", "60"))
    resolved_min_score = min_score if min_score is not None else int(os.getenv("JOB_BOARD_MIN_SCORE", "25"))
    board = build_board(
        root,
        offline=offline,
        max_age_days=resolved_max_age,
        min_score=resolved_min_score,
    )
    write_board(board, root / "site")
    LOGGER.info("Wrote %d jobs to %s", len(board["jobs"]), root / "site" / "data" / "jobs.json")
    return board
