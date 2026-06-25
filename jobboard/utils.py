from __future__ import annotations

import hashlib
import html
import re
from datetime import date, datetime, timezone, timedelta
from typing import Any
from urllib.parse import urljoin, urlparse, urlunparse

from bs4 import BeautifulSoup
from dateutil import parser as date_parser


SPACE_RE = re.compile(r"\s+")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def clean_text(value: Any, max_chars: int | None = None) -> str:
    """Convert HTML-ish content to readable, compact plain text."""
    if value is None:
        return ""
    text = str(value)
    if "<" in text and ">" in text:
        text = BeautifulSoup(text, "html.parser").get_text(" ")
    text = html.unescape(text)
    text = SPACE_RE.sub(" ", text).strip()
    if max_chars and len(text) > max_chars:
        return text[: max_chars - 1].rstrip() + "…"
    return text


def normalize_url(url: str) -> str:
    if not url:
        return ""
    try:
        parsed = urlparse(url.strip())
        # Tracking parameters are intentionally removed to improve deduplication.
        return urlunparse((parsed.scheme or "https", parsed.netloc, parsed.path.rstrip("/"), "", "", ""))
    except Exception:
        return url.strip()


def stable_id(*parts: Any) -> str:
    raw = "|".join(clean_text(p).lower() for p in parts if p is not None)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:18]


def parse_date(value: Any, *, now: datetime | None = None) -> str | None:
    """Return an ISO date from timestamps, ISO strings, or ATS relative labels."""
    if value in (None, ""):
        return None
    now = now or utc_now()

    if isinstance(value, (int, float)):
        # Lever uses milliseconds since epoch.
        seconds = float(value) / 1000 if float(value) > 10_000_000_000 else float(value)
        try:
            return datetime.fromtimestamp(seconds, tz=timezone.utc).date().isoformat()
        except (OverflowError, OSError, ValueError):
            return None

    text = clean_text(value).lower()
    if not text:
        return None
    if text in {"today", "posted today"}:
        return now.date().isoformat()
    if text in {"yesterday", "posted yesterday"}:
        return (now.date() - timedelta(days=1)).isoformat()

    relative = re.search(r"(\d+)\+?\s*(day|days|hour|hours|week|weeks|month|months)\s*ago", text)
    if relative:
        amount = int(relative.group(1))
        unit = relative.group(2)
        if unit.startswith("hour"):
            days = 0
        elif unit.startswith("day"):
            days = amount
        elif unit.startswith("week"):
            days = amount * 7
        else:
            days = amount * 30
        return (now.date() - timedelta(days=days)).isoformat()

    try:
        parsed = date_parser.parse(str(value))
        return parsed.date().isoformat()
    except (ValueError, TypeError, OverflowError):
        return None


def days_old(iso_date: str | None, *, today: date | None = None) -> int | None:
    if not iso_date:
        return None
    today = today or utc_now().date()
    try:
        parsed = date.fromisoformat(iso_date[:10])
    except ValueError:
        return None
    return max(0, (today - parsed).days)


def absolute_url(base: str, href: str) -> str:
    return normalize_url(urljoin(base, href))


def truncate_words(text: str, limit: int = 58) -> str:
    words = clean_text(text).split()
    if len(words) <= limit:
        return " ".join(words)
    return " ".join(words[:limit]).rstrip(".,;:") + "…"
