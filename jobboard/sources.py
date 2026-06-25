from __future__ import annotations

import logging
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import Any, Callable
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .curated import parse_curated_feed
from .utils import absolute_url, clean_text, normalize_url, parse_date, stable_id

LOGGER = logging.getLogger(__name__)

TITLE_PREFILTER = re.compile(
    r"(?i)(bioinform|computational|genomic|data|analytics|analyst|engineer|software|"
    r"product|program|operations|research|scientist|associate|coordinator|new grad|early career)"
)

EXPIRED_MARKERS = (
    "this vacancy has now expired",
    "this position has been closed",
    "this job has expired",
    "job is no longer available",
    "position is no longer available",
    "no longer accepting applications",
)


class SourceClient:
    def __init__(self, timeout: int = 22) -> None:
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "CelinaJobBoard/2.0 (+personal research job aggregator; respectful daily refresh)",
                "Accept": "application/json,text/plain,text/markdown,text/html;q=0.9,*/*;q=0.8",
            }
        )
        retry = Retry(
            total=3,
            connect=3,
            read=3,
            backoff_factor=0.6,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset({"GET", "POST"}),
        )
        adapter = HTTPAdapter(max_retries=retry, pool_connections=32, pool_maxsize=32)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def get(self, url: str, **kwargs: Any) -> requests.Response:
        response = self.session.get(url, timeout=self.timeout, **kwargs)
        response.raise_for_status()
        return response

    def post(self, url: str, **kwargs: Any) -> requests.Response:
        response = self.session.post(url, timeout=self.timeout, **kwargs)
        response.raise_for_status()
        return response

    def fetch_curated_feed(self, source: dict[str, Any]) -> list[dict[str, Any]]:
        response = self.get(source["url"])
        return parse_curated_feed(response.text, source)

    def fetch_greenhouse(self, source: dict[str, Any]) -> list[dict[str, Any]]:
        board = source["board"]
        url = f"https://boards-api.greenhouse.io/v1/boards/{quote(board, safe='')}/jobs?content=true"
        data = self.get(url).json()
        jobs: list[dict[str, Any]] = []
        for item in data.get("jobs", []):
            location = clean_text((item.get("location") or {}).get("name"))
            description = clean_text(item.get("content"), max_chars=12_000)
            jobs.append(
                {
                    "id": f"greenhouse-{board}-{item.get('id')}",
                    "title": clean_text(item.get("title")),
                    "company": source["name"],
                    "location": location,
                    "workplace": "",
                    "employment_type": "",
                    "salary": "",
                    "url": normalize_url(item.get("absolute_url") or ""),
                    "source": "Greenhouse",
                    "source_type": "greenhouse",
                    "org_type": source.get("org_type", "company"),
                    "research": source.get("org_type") in {"research", "university"},
                    "posted_at": parse_date(item.get("updated_at")),
                    "date_label": "Last updated",
                    "description": description,
                }
            )
        return jobs

    def fetch_lever(self, source: dict[str, Any]) -> list[dict[str, Any]]:
        site = source["site"]
        url = f"https://api.lever.co/v0/postings/{quote(site, safe='')}?mode=json"
        data = self.get(url).json()
        jobs: list[dict[str, Any]] = []
        for item in data if isinstance(data, list) else []:
            categories = item.get("categories") or {}
            list_text = " ".join(
                f"{clean_text(block.get('text'))} {clean_text(block.get('content'))}"
                for block in item.get("lists", [])
            )
            description = clean_text(
                item.get("descriptionPlain") or f"{item.get('description', '')} {list_text}",
                max_chars=12_000,
            )
            jobs.append(
                {
                    "id": f"lever-{site}-{item.get('id')}",
                    "title": clean_text(item.get("text")),
                    "company": source["name"],
                    "location": clean_text(categories.get("location") or item.get("workplaceType")),
                    "workplace": clean_text(item.get("workplaceType")),
                    "employment_type": clean_text(categories.get("commitment")),
                    "salary": clean_text(item.get("salaryRange")),
                    "url": normalize_url(item.get("hostedUrl") or item.get("applyUrl") or ""),
                    "apply_url": normalize_url(item.get("applyUrl") or ""),
                    "source": "Lever",
                    "source_type": "lever",
                    "org_type": source.get("org_type", "company"),
                    "research": source.get("org_type") in {"research", "university"},
                    "posted_at": parse_date(item.get("createdAt")),
                    "date_label": "Posted",
                    "description": description,
                    "team": clean_text(categories.get("team") or categories.get("department")),
                }
            )
        return jobs

    @staticmethod
    def _ashby_salary(item: dict[str, Any]) -> str:
        compensation = item.get("compensation") or {}
        if isinstance(compensation, str):
            return clean_text(compensation)
        for key in ("summary", "compensationSummary", "scrapeableCompensationSalarySummary"):
            if compensation.get(key):
                return clean_text(compensation[key])
        return ""

    def fetch_ashby(self, source: dict[str, Any]) -> list[dict[str, Any]]:
        board = source["board"]
        url = (
            "https://api.ashbyhq.com/posting-api/job-board/"
            f"{quote(board, safe='')}?includeCompensation=true"
        )
        data = self.get(url).json()
        jobs: list[dict[str, Any]] = []
        for item in data.get("jobs", []):
            jobs.append(
                {
                    "id": f"ashby-{board}-{item.get('id') or stable_id(item.get('jobUrl'))}",
                    "title": clean_text(item.get("title")),
                    "company": source["name"],
                    "location": clean_text(item.get("location")),
                    "workplace": clean_text(item.get("workplaceType") or item.get("locationType")),
                    "employment_type": clean_text(item.get("employmentType")),
                    "salary": self._ashby_salary(item),
                    "url": normalize_url(item.get("jobUrl") or item.get("applyUrl") or ""),
                    "apply_url": normalize_url(item.get("applyUrl") or ""),
                    "source": "Ashby",
                    "source_type": "ashby",
                    "org_type": source.get("org_type", "company"),
                    "research": source.get("org_type") in {"research", "university"},
                    "posted_at": parse_date(item.get("publishedAt")),
                    "date_label": "Posted",
                    "description": clean_text(
                        item.get("descriptionPlain") or item.get("descriptionHtml"), max_chars=12_000
                    ),
                    "team": clean_text(item.get("team") or item.get("department")),
                }
            )
        return jobs

    def fetch_workday(self, source: dict[str, Any]) -> list[dict[str, Any]]:
        host = source["host"]
        tenant = source["tenant"]
        site = source["site"]
        search_url = f"https://{host}/wday/cxs/{tenant}/{site}/jobs"
        offset = 0
        limit = 20
        postings: list[dict[str, Any]] = []
        while offset < int(source.get("max_results", 1000)):
            payload = {"appliedFacets": {}, "limit": limit, "offset": offset, "searchText": ""}
            page = self.post(search_url, json=payload).json()
            batch = page.get("jobPostings", [])
            postings.extend(batch)
            offset += len(batch)
            if not batch or offset >= int(page.get("total", 0)):
                break

        jobs: list[dict[str, Any]] = []
        for item in postings:
            title = clean_text(item.get("title"))
            if not TITLE_PREFILTER.search(title):
                continue
            external_path = item.get("externalPath") or ""
            detail_api = f"https://{host}/wday/cxs/{tenant}/{site}{external_path}"
            info: dict[str, Any] = {}
            try:
                detail = self.get(detail_api).json()
                info = detail.get("jobPostingInfo") or detail
            except Exception as exc:  # Detail failures should not discard listing cards.
                LOGGER.debug("Workday detail failed for %s: %s", detail_api, exc)

            public_url = f"https://{host}/{site}{external_path}"
            jobs.append(
                {
                    "id": f"workday-{tenant}-{info.get('jobReqId') or stable_id(public_url)}",
                    "title": clean_text(info.get("title") or title),
                    "company": source["name"],
                    "location": clean_text(info.get("location") or item.get("locationsText")),
                    "workplace": clean_text(info.get("remoteType")),
                    "employment_type": clean_text(info.get("timeType") or ""),
                    "salary": clean_text(info.get("jobCompensation") or ""),
                    "url": normalize_url(info.get("externalUrl") or public_url),
                    "source": "Workday",
                    "source_type": "workday",
                    "org_type": source.get("org_type", "company"),
                    "research": source.get("org_type") in {"research", "university"},
                    "posted_at": parse_date(item.get("postedOn") or info.get("startDate")),
                    "date_label": "Posted",
                    "description": clean_text(info.get("jobDescription"), max_chars=12_000),
                }
            )
        return jobs

    def fetch_html_index(self, source: dict[str, Any]) -> list[dict[str, Any]]:
        index_url = source["url"]
        index_response = self.get(index_url)
        soup = BeautifulSoup(index_response.text, "html.parser")
        link_re = re.compile(source.get("link_regex", r"/job/"))
        title_re = re.compile(source.get("include_title_regex", r"(?i)(data|research|bio)"))
        candidates: dict[str, str] = {}
        for anchor in soup.find_all("a", href=True):
            title = clean_text(anchor.get_text(" "))
            href = anchor.get("href", "")
            if title and link_re.search(href) and title_re.search(title):
                candidates[absolute_url(index_url, href)] = title

        jobs: list[dict[str, Any]] = []
        for url, card_title in list(candidates.items())[:50]:
            try:
                response = self.get(url)
                page = BeautifulSoup(response.text, "html.parser")
                h1 = page.find("h1")
                title = clean_text(h1.get_text(" ") if h1 else card_title)
                main = page.find("main") or page.find(attrs={"role": "main"}) or page.body
                text = clean_text(main.get_text(" ") if main else response.text, max_chars=12_000)
                location_match = re.search(
                    r"(?i)(?:location|located in)[:\s]+([A-Za-z .'-]+,\s*[A-Z]{2})(?:\s|$)", text
                )
                salary_match = re.search(
                    r"\$[\d,]+(?:\.\d+)?\s*(?:-|–|to)\s*\$[\d,]+(?:\.\d+)?(?:\s+per\s+(?:year|hour))?",
                    text,
                )
                posted_match = re.search(
                    r"(?i)(?:posting date|post date|posted)[:\s]+([A-Z][a-z]{2,8}\s+\d{1,2},\s+\d{4})",
                    text,
                )
                jobs.append(
                    {
                        "id": f"html-{stable_id(url)}",
                        "title": title,
                        "company": source["name"],
                        "location": clean_text(location_match.group(1) if location_match else ""),
                        "workplace": "",
                        "employment_type": "",
                        "salary": clean_text(salary_match.group(0) if salary_match else ""),
                        "url": normalize_url(url),
                        "source": f"{source['name']} Careers",
                        "source_type": "html",
                        "org_type": source.get("org_type", "research"),
                        "research": source.get("org_type") in {"research", "university"},
                        "posted_at": parse_date(posted_match.group(1) if posted_match else None),
                        "description": text,
                    }
                )
            except Exception as exc:
                LOGGER.debug("HTML detail failed for %s: %s", url, exc)
        return jobs

    def fetch_remotive(self) -> list[dict[str, Any]]:
        data = self.get("https://remotive.com/api/remote-jobs").json()
        jobs: list[dict[str, Any]] = []
        for item in data.get("jobs", []):
            jobs.append(
                {
                    "id": f"remotive-{item.get('id')}",
                    "title": clean_text(item.get("title")),
                    "company": clean_text(item.get("company_name")),
                    "location": clean_text(item.get("candidate_required_location") or "Remote - US"),
                    "workplace": "Remote",
                    "employment_type": clean_text(item.get("job_type")),
                    "salary": clean_text(item.get("salary")),
                    "url": normalize_url(item.get("url") or ""),
                    "source": "Remotive",
                    "source_type": "remotive",
                    "org_type": "company",
                    "research": False,
                    "posted_at": parse_date(item.get("publication_date")),
                    "description": clean_text(item.get("description"), max_chars=12_000),
                }
            )
        return jobs

    def fetch_adzuna(self, config: dict[str, Any], max_age_days: int) -> list[dict[str, Any]]:
        app_id = os.getenv("ADZUNA_APP_ID", "").strip()
        app_key = os.getenv("ADZUNA_APP_KEY", "").strip()
        if not app_id or not app_key:
            return []
        jobs: list[dict[str, Any]] = []
        for query in config.get("queries", []):
            endpoint = "https://api.adzuna.com/v1/api/jobs/us/search/1"
            params = {
                "app_id": app_id,
                "app_key": app_key,
                "what": query,
                "results_per_page": 50,
                "max_days_old": max_age_days,
                "content-type": "application/json",
            }
            data = self.get(endpoint, params=params).json()
            for item in data.get("results", []):
                salary = ""
                if item.get("salary_min") or item.get("salary_max"):
                    low = item.get("salary_min")
                    high = item.get("salary_max")
                    salary = f"${low:,.0f}–${high:,.0f}" if low and high else f"${(low or high):,.0f}"
                jobs.append(
                    {
                        "id": f"adzuna-{item.get('id')}",
                        "title": clean_text(item.get("title")),
                        "company": clean_text((item.get("company") or {}).get("display_name")),
                        "location": clean_text((item.get("location") or {}).get("display_name")),
                        "workplace": "",
                        "employment_type": clean_text(item.get("contract_time") or item.get("contract_type")),
                        "salary": salary,
                        "url": normalize_url(item.get("redirect_url") or ""),
                        "source": "Adzuna",
                        "source_type": "adzuna",
                        "org_type": "company",
                        "research": "research" in query or "biology" in query or "bioinformatics" in query,
                        "posted_at": parse_date(item.get("created")),
                        "description": clean_text(item.get("description"), max_chars=12_000),
                    }
                )
        return jobs

    def fetch_usajobs(self, config: dict[str, Any], max_age_days: int) -> list[dict[str, Any]]:
        api_key = os.getenv("USAJOBS_API_KEY", "").strip()
        email = os.getenv("USAJOBS_EMAIL", "").strip()
        if not api_key or not email:
            return []
        headers = {
            "Host": "data.usajobs.gov",
            "User-Agent": email,
            "Authorization-Key": api_key,
        }
        jobs: list[dict[str, Any]] = []
        endpoint = "https://data.usajobs.gov/api/search"
        for query in config.get("queries", []):
            params = {
                "Keyword": query,
                "DatePosted": max_age_days,
                "ResultsPerPage": 100,
                "WhoMayApply": "public",
            }
            data = self.get(endpoint, params=params, headers=headers).json()
            items = (data.get("SearchResult") or {}).get("SearchResultItems", [])
            for wrapped in items:
                item = wrapped.get("MatchedObjectDescriptor") or {}
                details = item.get("UserArea", {}).get("Details", {})
                locations = item.get("PositionLocation", [])
                location = "; ".join(clean_text(loc.get("LocationName")) for loc in locations[:3])
                remuneration = item.get("PositionRemuneration", [])
                salary = ""
                if remuneration:
                    pay = remuneration[0]
                    salary = f"${pay.get('MinimumRange')}–${pay.get('MaximumRange')} {pay.get('RateIntervalCode', '')}".strip()
                jobs.append(
                    {
                        "id": f"usajobs-{item.get('PositionID')}",
                        "title": clean_text(item.get("PositionTitle")),
                        "company": clean_text(item.get("OrganizationName") or item.get("DepartmentName")),
                        "location": location,
                        "workplace": clean_text(details.get("TeleworkEligible")),
                        "employment_type": clean_text(item.get("PositionSchedule", [{}])[0].get("Name")),
                        "salary": salary,
                        "url": normalize_url(item.get("PositionURI") or ""),
                        "source": "USAJOBS",
                        "source_type": "usajobs",
                        "org_type": "research" if any(x in query for x in ("bio", "science")) else "government",
                        "research": any(x in query for x in ("bio", "science")),
                        "posted_at": parse_date(item.get("PublicationStartDate")),
                        "description": clean_text(
                            " ".join(
                                [
                                    details.get("JobSummary", ""),
                                    details.get("MajorDuties", []).__str__(),
                                    details.get("Education", ""),
                                    details.get("Requirements", ""),
                                ]
                            ),
                            max_chars=12_000,
                        ),
                    }
                )
        return jobs

    def verify_seed(self, job: dict[str, Any]) -> dict[str, Any] | None:
        url = job.get("url")
        if not url:
            return job
        try:
            response = self.session.get(url, timeout=self.timeout, allow_redirects=True)
            if response.status_code in {404, 410}:
                return None
            if response.status_code >= 500:
                job["verification_status"] = f"Employer page temporarily returned {response.status_code}"
                return job
            text = clean_text(response.text, max_chars=50_000).lower()
            if any(marker in text for marker in EXPIRED_MARKERS):
                return None
            job["verification_status"] = "Link checked"
            job["last_verified_at"] = datetime.now(timezone.utc).date().isoformat()
            return job
        except requests.RequestException as exc:
            job["verification_status"] = "Link could not be checked; verify before applying"
            LOGGER.debug("Seed verification failed for %s: %s", url, exc)
            return job


def collect_live_jobs(
    sources: dict[str, Any],
    *,
    max_age_days: int,
    max_workers: int = 18,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    client = SourceClient()
    tasks: list[tuple[str, Callable[[], list[dict[str, Any]]]]] = []

    for source in sources.get("github_feeds", []):
        if source.get("enabled", True):
            tasks.append((source["name"], lambda s=source: client.fetch_curated_feed(s)))
    for source in sources.get("greenhouse", []):
        tasks.append((source["name"], lambda s=source: client.fetch_greenhouse(s)))
    for source in sources.get("lever", []):
        tasks.append((source["name"], lambda s=source: client.fetch_lever(s)))
    for source in sources.get("ashby", []):
        tasks.append((source["name"], lambda s=source: client.fetch_ashby(s)))
    for source in sources.get("workday", []):
        tasks.append((source["name"], lambda s=source: client.fetch_workday(s)))
    for source in sources.get("html_indexes", []):
        tasks.append((source["name"], lambda s=source: client.fetch_html_index(s)))


    if (sources.get("remotive") or {}).get("enabled"):
        tasks.append(("Remotive", client.fetch_remotive))
    if (sources.get("adzuna") or {}).get("enabled"):
        tasks.append(("Adzuna", lambda: client.fetch_adzuna(sources["adzuna"], max_age_days)))
    if (sources.get("usajobs") or {}).get("enabled"):
        tasks.append(("USAJOBS", lambda: client.fetch_usajobs(sources["usajobs"], max_age_days)))

    jobs: list[dict[str, Any]] = []
    stats: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_map = {executor.submit(fn): name for name, fn in tasks}
        for future in as_completed(future_map):
            name = future_map[future]
            try:
                result = future.result()
                jobs.extend(result)
                stats.append({"source": name, "status": "ok", "fetched": len(result)})
                LOGGER.info("%-34s %4d jobs", name, len(result))
            except Exception as exc:
                stats.append({"source": name, "status": "error", "fetched": 0, "error": str(exc)[:180]})
                LOGGER.warning("%-34s failed: %s", name, exc)
    return jobs, sorted(stats, key=lambda row: row["source"].lower())
