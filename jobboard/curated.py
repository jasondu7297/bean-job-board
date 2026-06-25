from __future__ import annotations

import re
from datetime import date, datetime, timedelta, timezone
from typing import Any, Iterable
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup, Tag
from dateutil import parser as date_parser

from .utils import clean_text, normalize_url, stable_id

_HEADER_ALIASES = {
    "company": ("company", "employer", "organization", "organisation"),
    "title": ("role", "job title", "position", "title", "job"),
    "location": ("location", "city", "office"),
    "application": ("application", "apply", "link", "posting"),
    "date": ("date posted", "posted", "posting age", "age", "date"),
    "workplace": ("work model", "workplace", "work type", "remote"),
    "salary": ("salary", "compensation", "pay"),
}

_RESEARCH_TERMS = (
    "bioinform", "computational biology", "genomic", "sequencing", "omics",
    "research assistant", "research associate", "research technician", "research coordinator",
    "clinical research", "laboratory", " lab ", "scientific programmer", "biostat",
    "university", "institute", "hospital", "medical school", "cancer center", "cancer centre",
)


_RESTRICTED_ROLE_RE = re.compile(
    r"(?i)\b(firearm|ammunition|munition|weapon|missile|ordnance|explosive|"
    r"sportsbook|sports betting|casino|poker|gambling|draftkings|fanduel|betmgm|"
    r"bet365|betrivers|caesars entertainment|penn entertainment|hard rock bet|pointsbet)\b"
)

_NON_US_MARKERS = (
    "canada", "toronto", "vancouver", "montreal", "ottawa", "calgary", "waterloo",
    "united kingdom", " uk", "london", "edinburgh", "glasgow", "cardiff", "manchester",
    "india", "singapore", "australia", "germany", "france", "spain", "italy", "poland",
    "netherlands", "ireland", "israel", "japan", "china", "hong kong", "taiwan", "europe",
)

_US_MARKERS = (
    "united states", "usa", "u.s.", "remote in us", "remote - us", "remote, us", "nationwide",
    "alabama", "alaska", "arizona", "arkansas", "california", "colorado", "connecticut",
    "delaware", "florida", "georgia", "hawaii", "idaho", "illinois", "indiana", "iowa",
    "kansas", "kentucky", "louisiana", "maine", "maryland", "massachusetts", "michigan",
    "minnesota", "mississippi", "missouri", "montana", "nebraska", "nevada",
    "new hampshire", "new jersey", "new mexico", "north carolina", "north dakota",
    "ohio", "oklahoma", "oregon", "pennsylvania", "rhode island", "south carolina",
    "south dakota", "tennessee", "texas", "utah", "vermont", "virginia",
    "washington", "west virginia", "wisconsin", "wyoming",
    "new york", "nyc", "brooklyn", "manhattan", "bronx", "queens",
    "san francisco", "sf", "south san francisco", "bay area", "palo alto", "menlo park",
    "mountain view", "sunnyvale", "san mateo", "redwood city", "oakland", "berkeley",
    "boston", "cambridge", "somerville", "brookline", "waltham", "watertown",
    "seattle", "bellevue", "san diego", "la jolla", "los angeles", "washington, dc",
    "district of columbia", "philadelphia", "chicago", "raleigh", "durham", "chapel hill",
    "austin", "dallas", "houston", "atlanta", "denver", "phoenix", "portland", "miami",
    "minneapolis", "detroit", "baltimore", "pittsburgh", "columbus", "cleveland",
)

_US_STATE_RE = re.compile(
    r"(?:^|[\s,/(])(?:AL|AK|AZ|AR|CA|CO|CT|DE|FL|GA|HI|ID|IL|IN|IA|KS|KY|LA|ME|MD|MA|MI|MN|MS|MO|MT|NE|NV|NH|NJ|NM|NY|NC|ND|OH|OK|OR|PA|RI|SC|SD|TN|TX|UT|VT|VA|WA|WV|WI|WY|DC)(?:$|[\s,/)])",
    re.IGNORECASE,
)


def _now_date(now: datetime | date | None = None) -> date:
    if isinstance(now, datetime):
        return now.date()
    return now or datetime.now(timezone.utc).date()


def parse_posted_date(value: Any, now: datetime | date | None = None) -> str | None:
    """Parse relative ages ("3d", "2mo") and ordinary dates into ISO format."""
    text = clean_text(value).lower()
    if not text or text in {"n/a", "unknown", "—", "-"}:
        return None
    today = _now_date(now)
    if text in {"today", "new", "just posted"}:
        return today.isoformat()
    if text in {"yesterday", "1 day ago"}:
        return (today - timedelta(days=1)).isoformat()

    compact = text.replace(" ", "")
    match = re.fullmatch(r"(\d+)(h|hr|hrs|d|day|days|w|wk|wks|mo|mos|month|months)", compact)
    if match:
        amount = int(match.group(1))
        unit = match.group(2)
        if unit in {"h", "hr", "hrs"}:
            days = 0
        elif unit in {"d", "day", "days"}:
            days = amount
        elif unit in {"w", "wk", "wks"}:
            days = amount * 7
        else:
            days = amount * 30
        return (today - timedelta(days=days)).isoformat()

    ago_match = re.search(r"(\d+)\s+(hour|day|week|month)s?\s+ago", text)
    if ago_match:
        amount = int(ago_match.group(1))
        unit = ago_match.group(2)
        days = 0 if unit == "hour" else amount if unit == "day" else amount * 7 if unit == "week" else amount * 30
        return (today - timedelta(days=days)).isoformat()

    try:
        parsed = date_parser.parse(text, fuzzy=True, default=datetime(today.year, 1, 1))
        candidate = parsed.date()
        # Month/day lists usually omit year. Do not assign a future date to an old December posting.
        if not re.search(r"\b(?:19|20)\d{2}\b", text) and candidate > today + timedelta(days=7):
            candidate = candidate.replace(year=candidate.year - 1)
        return candidate.isoformat()
    except (ValueError, TypeError, OverflowError):
        return None


def looks_like_us_location(location: str, *, allow_unknown: bool = False) -> bool:
    text = f" {clean_text(location).lower()} "
    if not text.strip():
        return allow_unknown
    has_us = (
        any(marker in text for marker in _US_MARKERS)
        or bool(_US_STATE_RE.search(location))
        or bool(re.search(r"(?:^|[\s,/(])(?:US|USA|SF)(?:$|[\s,/)])", location, flags=re.IGNORECASE))
    )
    has_non_us = any(marker in text for marker in _NON_US_MARKERS)
    if has_us:
        return True
    if has_non_us:
        return False
    # Generic remote listings are retained only when they explicitly indicate the United States.
    if "remote" in text:
        return any(token in text for token in ("us", "usa", "united states", "north america"))
    # Curated USA-only feeds can opt into unknown/ambiguous locations.
    return allow_unknown


def _header_index(headers: list[str], field: str) -> int | None:
    for index, header in enumerate(headers):
        normalized = clean_text(header).lower()
        if any(alias in normalized for alias in _HEADER_ALIASES[field]):
            return index
    return None


def _markdown_links(text: str) -> tuple[str, list[str]]:
    links = re.findall(r"\[[^\]]*\]\(([^)]+)\)", text)
    cleaned = re.sub(r"!\[[^\]]*\]\([^)]+\)", "", text)
    cleaned = re.sub(r"\[([^\]]*)\]\([^)]+\)", r"\1", cleaned)
    cleaned = re.sub(r"<br\s*/?>", " / ", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"<[^>]+>", " ", cleaned)
    cleaned = re.sub(r"(?:\*\*|__|`)", "", cleaned)
    return clean_text(cleaned), links


def _url_score(url: str, *, application_cell: bool = False) -> int:
    lowered = url.lower()
    if not lowered or lowered.startswith(("#", "mailto:", "javascript:")):
        return -1000
    if any(x in lowered for x in ("raw.githubusercontent.com", ".svg", ".png", ".jpg", "github.com/sponsors")):
        return -500
    score = 10 if application_cell else 0
    if any(x in lowered for x in (
        "simplify.jobs/p/", "jobright.ai/jobs", "myworkdayjobs.com", "greenhouse.io", "lever.co",
        "ashbyhq.com", "smartrecruiters.com", "icims.com", "workable.com", "careers.", "/jobs/", "/job/",
    )):
        score += 50
    if any(x in lowered for x in ("linkedin.com/company", "/about", "/company/", "wikipedia.org")):
        score -= 30
    return score


def _choose_url(urls: Iterable[str], source_url: str, *, application_cell: bool = False) -> str:
    normalized: list[str] = []
    for candidate in urls:
        candidate = candidate.strip()
        if not candidate:
            continue
        absolute = urljoin(source_url, candidate)
        normalized.append(normalize_url(absolute))
    if not normalized:
        return ""
    return max(normalized, key=lambda item: _url_score(item, application_cell=application_cell))


def _research_flag(title: str, company: str, source: dict[str, Any]) -> bool:
    text = f" {title} {company} ".lower()
    title_signal = any(term in text for term in _RESEARCH_TERMS)
    return bool(title_signal or source.get("org_type") in {"research", "university"})


def _make_job(
    source: dict[str, Any],
    *,
    company: str,
    title: str,
    location: str,
    url: str,
    posted_text: str = "",
    workplace: str = "",
    salary: str = "",
    now: datetime | date | None = None,
) -> dict[str, Any] | None:
    company = clean_text(company).lstrip("↳").strip()
    title = clean_text(title).lstrip("↳").strip()
    location = clean_text(location)
    if not company or not title or len(title) < 3:
        return None
    if _RESTRICTED_ROLE_RE.search(f"{title} {company}"):
        return None

    scope = source.get("scope", "us")
    if scope != "all" and not looks_like_us_location(
        location,
        allow_unknown=bool(source.get("allow_unknown_location") or scope == "usa_only"),
    ):
        return None

    posted_at = parse_posted_date(posted_text, now=now)
    research = _research_flag(title, company, source)
    category_hint = clean_text(source.get("category_hint") or "General New Grad")
    source_name = clean_text(source.get("name") or "Curated new-grad feed")
    source_url = clean_text(source.get("page_url") or source.get("url"))
    return {
        "id": f"feed-{stable_id(source_name, company, title, location, url)}",
        "title": title,
        "company": company,
        "location": location,
        "workplace": clean_text(workplace),
        "employment_type": "Full-time",
        "salary": clean_text(salary),
        "url": normalize_url(url or source_url),
        "source": source_name,
        "source_type": "curated_feed",
        "source_feed_url": normalize_url(source_url),
        "org_type": "research" if research else clean_text(source.get("org_type") or "company"),
        "research": research,
        "posted_at": posted_at,
        "posted_text": clean_text(posted_text),
        "date_label": "Posted",
        "description": clean_text(
            f"Curated new-graduate listing from {source_name}. Category: {category_hint}. "
            f"Role: {title}. Location: {location}."
        ),
        "category_hint": category_hint,
        "curated_new_grad": True,
    }


def _parse_html_tables(text: str, source: dict[str, Any], now: datetime | date | None) -> list[dict[str, Any]]:
    soup = BeautifulSoup(text, "html.parser")
    jobs: list[dict[str, Any]] = []
    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        if len(rows) < 2:
            continue
        header_cells = rows[0].find_all(["th", "td"])
        headers = [clean_text(cell.get_text(" ")) for cell in header_cells]
        company_idx = _header_index(headers, "company")
        title_idx = _header_index(headers, "title")
        location_idx = _header_index(headers, "location")
        application_idx = _header_index(headers, "application")
        date_idx = _header_index(headers, "date")
        workplace_idx = _header_index(headers, "workplace")
        salary_idx = _header_index(headers, "salary")
        if title_idx is None or company_idx is None:
            continue

        previous_company = ""
        for row in rows[1:]:
            cells: list[Tag] = row.find_all("td", recursive=False) or row.find_all("td")
            if not cells:
                continue
            # Some lists omit the company cell for an arrow/continuation row.
            missing_company = len(cells) == len(headers) - 1
            def cell_at(index: int | None) -> Tag | None:
                if index is None:
                    return None
                adjusted = index - 1 if missing_company and index > company_idx else index
                if missing_company and index == company_idx:
                    return None
                return cells[adjusted] if 0 <= adjusted < len(cells) else None

            company_cell = cell_at(company_idx)
            title_cell = cell_at(title_idx)
            location_cell = cell_at(location_idx)
            app_cell = cell_at(application_idx)
            date_cell = cell_at(date_idx)
            workplace_cell = cell_at(workplace_idx)
            salary_cell = cell_at(salary_idx)

            company = clean_text(company_cell.get_text(" ") if company_cell else "")
            if not company or company in {"↳", "↪", "→"}:
                company = previous_company
            else:
                previous_company = company
            title = clean_text(title_cell.get_text(" ") if title_cell else "")
            location = clean_text(location_cell.get_text(" / ") if location_cell else "")
            posted_text = clean_text(date_cell.get_text(" ") if date_cell else "")
            workplace = clean_text(workplace_cell.get_text(" ") if workplace_cell else "")
            salary = clean_text(salary_cell.get_text(" ") if salary_cell else "")

            app_urls = [anchor.get("href", "") for anchor in app_cell.find_all("a", href=True)] if app_cell else []
            row_urls = [anchor.get("href", "") for anchor in row.find_all("a", href=True)]
            url = _choose_url(app_urls, source.get("page_url") or source["url"], application_cell=True)
            if not url:
                # Skip the first (usually company) link when possible.
                url = _choose_url(row_urls[1:] or row_urls, source.get("page_url") or source["url"])
            job = _make_job(
                source,
                company=company,
                title=title,
                location=location,
                url=url,
                posted_text=posted_text,
                workplace=workplace,
                salary=salary,
                now=now,
            )
            if job:
                jobs.append(job)
    return jobs


def _split_markdown_row(line: str) -> list[str]:
    stripped = line.strip().strip("|")
    return [part.strip() for part in re.split(r"(?<!\\)\|", stripped)]


def _parse_markdown_tables(text: str, source: dict[str, Any], now: datetime | date | None) -> list[dict[str, Any]]:
    lines = text.splitlines()
    jobs: list[dict[str, Any]] = []
    previous_company = ""
    index = 0
    while index + 1 < len(lines):
        line = lines[index]
        separator = lines[index + 1]
        if "|" not in line or not re.match(r"^\s*\|?\s*:?-{2,}", separator):
            index += 1
            continue
        headers = [clean_text(cell) for cell in _split_markdown_row(line)]
        company_idx = _header_index(headers, "company")
        title_idx = _header_index(headers, "title")
        location_idx = _header_index(headers, "location")
        application_idx = _header_index(headers, "application")
        date_idx = _header_index(headers, "date")
        workplace_idx = _header_index(headers, "workplace")
        salary_idx = _header_index(headers, "salary")
        index += 2
        if company_idx is None or title_idx is None:
            continue
        while index < len(lines) and "|" in lines[index]:
            cells = _split_markdown_row(lines[index])
            index += 1
            if len(cells) < 2:
                continue
            def raw_at(i: int | None) -> str:
                return cells[i] if i is not None and i < len(cells) else ""
            company, company_links = _markdown_links(raw_at(company_idx))
            title, title_links = _markdown_links(raw_at(title_idx))
            location, location_links = _markdown_links(raw_at(location_idx))
            posted_text, _ = _markdown_links(raw_at(date_idx))
            workplace, _ = _markdown_links(raw_at(workplace_idx))
            salary, _ = _markdown_links(raw_at(salary_idx))
            _, app_links = _markdown_links(raw_at(application_idx))
            if not company or company in {"↳", "↪", "→"}:
                company = previous_company
            else:
                previous_company = company
            url = _choose_url(app_links, source.get("page_url") or source["url"], application_cell=True)
            if not url:
                url = _choose_url(title_links + location_links + company_links, source.get("page_url") or source["url"])
            job = _make_job(
                source,
                company=company,
                title=title,
                location=location,
                url=url,
                posted_text=posted_text,
                workplace=workplace,
                salary=salary,
                now=now,
            )
            if job:
                jobs.append(job)
    return jobs


def parse_curated_feed(text: str, source: dict[str, Any], now: datetime | date | None = None) -> list[dict[str, Any]]:
    """Parse GitHub-style HTML/Markdown job tables into normalized job dictionaries."""
    jobs = [*_parse_html_tables(text, source, now), *_parse_markdown_tables(text, source, now)]
    deduped: dict[str, dict[str, Any]] = {}
    for job in jobs:
        key = normalize_url(job.get("url") or "") or stable_id(job.get("company"), job.get("title"), job.get("location"))
        deduped[key.lower()] = job
    max_rows = int(source.get("max_rows") or 5000)
    return list(deduped.values())[:max_rows]

# Backward-compatible names used by tests and older configurations.
def parse_curated_markdown(text: str, source: dict[str, Any], now: datetime | date | None = None) -> list[dict[str, Any]]:
    return parse_curated_feed(text, source, now=now)


def parse_speedyapply_markdown(text: str, source: dict[str, Any], now: datetime | date | None = None) -> list[dict[str, Any]]:
    configured = {"scope": "usa_only", "allow_unknown_location": True, **source}
    return parse_curated_feed(text, configured, now=now)


def parse_jobright_markdown(text: str, source: dict[str, Any], now: datetime | date | None = None) -> list[dict[str, Any]]:
    configured = {"scope": "us", **source}
    return parse_curated_feed(text, configured, now=now)


is_us_location = looks_like_us_location

