from __future__ import annotations

import re
from typing import Any

from .curated import looks_like_us_location
from .utils import clean_text, days_old


CATEGORY_KEYWORDS: dict[str, tuple[str, ...]] = {
    "Bioinformatics / Computational Biology": (
        "bioinformatics", "computational biology", "computational biologist",
        "genomics", "genomic", "transcriptomics", "proteomics", "multi-omics",
        "single-cell", "single cell", "rna-seq", "dna-seq", "sequencing",
        "biostatistics", "biological data", "scientific programmer",
    ),
    "Data Analysis / Data Science": (
        "data analyst", "data scientist", "analytics", "insights analyst",
        "research data analyst", "biostatistician", "quantitative analyst",
        "business intelligence", "statistical analyst", "data visualization",
    ),
    "Data Engineering / Software": (
        "data engineer", "analytics engineer", "software engineer", "software developer",
        "bioinformatics engineer", "data platform", "etl", "pipeline engineer",
        "database", "backend engineer", "machine learning engineer", "automation engineer",
    ),
    "Product / Program / Operations": (
        "associate product manager", "product analyst", "product operations",
        "program coordinator", "program associate", "project coordinator",
        "technical program", "business operations", "strategy and operations",
        "operations analyst", "implementation analyst", "customer success analyst",
    ),
    "University / Research": (
        "research assistant", "research associate", "research technician",
        "lab technician", "laboratory technician", "officer of research",
        "computational associate", "academic", "university", "institute",
        "laboratory", "lab ", "scientific analyst",
    ),
    "General New Grad": (
        "new grad", "new graduate", "recent graduate", "university graduate",
        "early career", "entry level", "entry-level", "junior", "analyst i",
        "engineer i", "scientist i", "associate", "coordinator",
    ),
}

ENTRY_TERMS = (
    "new grad", "new graduate", "recent graduate", "university graduate", "early career",
    "entry level", "entry-level", "junior", "0-2 years", "0–2 years", "0 to 2 years",
    "no prior experience", "no experience necessary", "bachelor's degree", "bachelors degree",
    "associate computational", "research assistant", "analyst i", "engineer i", "scientist i",
    "training to become", "mentored training position",
)

EXCLUDE_TITLE_TERMS = (
    "postdoctoral", "postdoc", "post-doc", "faculty", "professor", "physician", "nurse",
    "medical doctor", "phd student", "graduate student", "internship", "intern ", "co-op", "coop",
    "sales representative", "account executive", "retail", "warehouse", "security guard",
    "firearm", "ammunition", "munition", "weapon", "missile", "ordnance", "explosive",
    "sportsbook", "sports betting", "casino", "poker", "gambling", "draftkings",
    "fanduel", "betmgm", "bet365", "betrivers", "caesars entertainment",
    "penn entertainment", "hard rock bet", "pointsbet",
)

SENIOR_TITLE_TERMS = (
    "senior", "sr.", "principal", "director", "head of", "vice president", "vp ",
    "manager ii", "manager iii", "staff software", "staff data", "lead engineer",
)

RESTRICTED_SECTOR_TERMS = (
    "firearm", "ammunition", "munition", "weapon", "missile", "ordnance", "explosive",
    "sportsbook", "sports betting", "casino", "poker", "lottery", "gambling",
    "ts/sci", "polygraph required", "active security clearance",
)

RESTRICTED_ORGANIZATIONS = (
    "anduril", "aerovironment", "agile defense", "amentum", "bae systems",
    "belay technologies", "caci", "captivation software", "constellation technologies",
    "general dynamics mission systems", "kbr", "l3harris", "leidos", "lockheed martin",
    "northrop grumman", "peraton", "raytheon", "saalex", "simventions",
    "light & wonder", "draftkings", "fanduel", "betmgm", "caesars entertainment",
    "penn entertainment", "hard rock digital", "flutter entertainment", "kalshi",
)


US_STATE_OR_CITY_TERMS = (
    " alabama", " alaska", " arizona", " arkansas", " california", " colorado",
    " connecticut", " delaware", " florida", " georgia", " hawaii", " idaho",
    " illinois", " indiana", " iowa", " kansas", " kentucky", " louisiana",
    " maine", " maryland", " massachusetts", " michigan", " minnesota",
    " mississippi", " missouri", " montana", " nebraska", " nevada",
    " new hampshire", " new jersey", " new mexico", " new york",
    " north carolina", " north dakota", " ohio", " oklahoma", " oregon",
    " pennsylvania", " rhode island", " south carolina", " south dakota",
    " tennessee", " texas", " utah", " vermont", " virginia", " washington",
    " west virginia", " wisconsin", " wyoming", " district of columbia",
)
US_STATE_CODE_RE = re.compile(
    r"\b(?:AL|AK|AZ|AR|CA|CO|CT|DE|FL|GA|HI|ID|IL|IN|IA|KS|KY|LA|ME|MD|MA|MI|MN|MS|MO|MT|NE|NV|NH|NJ|NM|NY|NC|ND|OH|OK|OR|PA|RI|SC|SD|TN|TX|UT|VT|VA|WA|WV|WI|WY|DC)\b",
    re.I,
)
FOREIGN_LOCATION_TERMS = (
    "canada", "united kingdom", "england", "ireland", "india", "singapore",
    "australia", "germany", "france", "spain", "italy", "mexico", "brazil",
    "argentina", "colombia", "poland", "netherlands", "sweden", "denmark",
    "japan", "china", "hong kong", "taiwan", "israel", "philippines",
)

SKILL_ALIASES: dict[str, tuple[str, ...]] = {
    "Python": ("python",),
    "R": (" r ", "r programming", "statistical programming using r", "r/bash", "r and bash"),
    "SQL": ("sql", "mysql", "database query"),
    "Bash": ("bash", "shell scripting"),
    "Linux": ("linux", "unix"),
    "Snakemake": ("snakemake",),
    "Nextflow": ("nextflow",),
    "Pandas": ("pandas",),
    "TensorFlow": ("tensorflow",),
    "Git": ("git", "github", "version control"),
    "APIs": ("api", "apis"),
    "ETL / pipelines": ("etl", "data pipeline", "processing pipeline", "workflow"),
    "Genomics": ("genomics", "genomic", "sequencing", "rna-seq", "dna-seq"),
    "Machine learning": ("machine learning", "ml ", "artificial intelligence", " ai "),
}


def location_group(location: str) -> str:
    text = clean_text(location).lower()
    if not text:
        return "Location not listed"
    if any(x in text for x in ("remote", "united states", "usa", "u.s.")) and not any(
        city in text for city in ("london", "toronto", "canada", "europe", "india", "singapore")
    ):
        return "Remote - US"
    if any(x in text for x in (
        "san francisco", "south san francisco", "bay area", "palo alto", "redwood city",
        "menlo park", "berkeley", "oakland", "san mateo", "mountain view", "sunnyvale",
        "foster city", "emeryville",
    )):
        return "San Francisco Bay Area"
    if any(x in text for x in (
        "new york", "brooklyn", "bronx", "queens", "manhattan", "jersey city",
    )):
        return "New York City"
    if any(x in text for x in (
        "boston", "cambridge", "somerville", "brookline", "watertown", "waltham",
        "lexington", "newton", "allston",
    )):
        return "Boston / Cambridge"
    if "seattle" in text or "bellevue" in text:
        return "Seattle"
    if "san diego" in text or "la jolla" in text:
        return "San Diego"
    if any(x in text for x in ("washington, dc", "washington, d.c", "district of columbia", "bethesda", "rockville")):
        return "Washington, DC"
    if "philadelphia" in text:
        return "Philadelphia"
    if any(x in text for x in ("raleigh", "durham", "chapel hill", "research triangle")):
        return "Research Triangle"
    if "chicago" in text:
        return "Chicago"
    if any(term in text for term in FOREIGN_LOCATION_TERMS):
        return "Outside U.S."
    if US_STATE_CODE_RE.search(clean_text(location)) or any(term in f" {text}" for term in US_STATE_OR_CITY_TERMS):
        return "Other U.S."
    if looks_like_us_location(location):
        return "Other U.S."
    return "Other / verify location"


def _category_scores(title: str, description: str, org_type: str) -> dict[str, int]:
    title_l = f" {title.lower()} "
    body_l = f" {description.lower()} "
    scores: dict[str, int] = {}
    for category, keywords in CATEGORY_KEYWORDS.items():
        score = 0
        for keyword in keywords:
            kw = keyword.lower()
            if kw in title_l:
                score += 8
            elif kw in body_l:
                score += 2
        scores[category] = score
    if org_type in {"research", "university"}:
        scores["University / Research"] += 12
    return scores


def classify_category(title: str, description: str, org_type: str = "company") -> tuple[str, list[str]]:
    scores = _category_scores(title, description, org_type)
    ordered = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    best = ordered[0][0] if ordered and ordered[0][1] > 0 else "General New Grad"
    secondary = [category for category, score in ordered[1:] if score >= 8][:2]
    return best, secondary


def experience_warning(text: str) -> tuple[int | None, str | None]:
    lowered = text.lower()
    if re.search(r"0\s*[-–to]+\s*2\s+years", lowered):
        return 0, None
    years = [int(x) for x in re.findall(r"(?<![-–\d])(\d+)\+?\s+(?:years|yrs)", lowered)]
    if not years:
        return None, None
    minimum = min(years)
    if minimum >= 5:
        return minimum, f"Posting mentions {minimum}+ years of experience"
    if minimum >= 3:
        return minimum, f"Posting mentions {minimum}+ years of experience"
    return minimum, None


def analyze_job(job: dict[str, Any], profile: dict[str, Any]) -> dict[str, Any]:
    title = clean_text(job.get("title"))
    description = clean_text(job.get("description"), max_chars=12_000)
    company = clean_text(job.get("company"))
    location = clean_text(job.get("location"))
    org_type = clean_text(job.get("org_type") or "company").lower()
    full = f" {title} {company} {description} ".lower()
    title_l = title.lower()

    category, secondary = classify_category(title, description, org_type)
    category_hint = clean_text(job.get("category_hint"))
    if category_hint in CATEGORY_KEYWORDS and _category_scores(title, description, org_type).get(category, 0) < 8:
        category = category_hint
    group = location_group(location)
    target_groups = set(profile.get("targets", {}).get("location_groups", []))

    reasons: list[str] = []
    warnings: list[str] = []
    matched_skills: list[str] = []
    score = 22

    if job.get("curated_new_grad"):
        score += 18
        reasons.append("Listed by a curated new-grad source")

    if group in target_groups:
        score += 14
        reasons.append(f"Target location: {group}")
    elif group == "Other U.S.":
        score += 3
        reasons.append("U.S.-based role outside the priority metros")
    elif group == "Outside U.S.":
        score -= 30
        warnings.append("Location appears to be outside the United States")
    elif group == "Other / verify location":
        score -= 4
        warnings.append("Location needs verification")
    elif group == "Location not listed":
        score -= 5
        warnings.append("Location is not listed")

    category_scores = _category_scores(title, description, org_type)
    category_strength = category_scores.get(category, 0)
    score += min(26, category_strength)
    if category_strength:
        reasons.append(f"Strong {category.lower()} keyword match")

    for skill, aliases in SKILL_ALIASES.items():
        if any(alias in full for alias in aliases):
            matched_skills.append(skill)
    score += min(24, len(matched_skills) * 3)
    if matched_skills:
        reasons.append("Matches " + ", ".join(matched_skills[:5]))

    entry_level = bool(job.get("curated_new_grad")) or any(term in full for term in ENTRY_TERMS)
    if entry_level:
        score += 16
        reasons.append("Entry-level or bachelor's-friendly language")
    if job.get("curated_new_grad"):
        score += 10
        reasons.append("Listed in a dedicated new-grad feed")

    age = days_old(job.get("posted_at"))
    if age is not None:
        if age <= 7:
            score += 10
            reasons.append("Posted within the last week")
        elif age <= 30:
            score += 5
            reasons.append("Posted within the last month")
        elif age > 60:
            score -= 8
            warnings.append("Posting date is older than 60 days; verify it is still active")

    if any(term in title_l for term in EXCLUDE_TITLE_TERMS):
        score -= 55
        warnings.append("Title looks outside the requested new-grad scope")

    senior_hit = any(term in title_l for term in SENIOR_TITLE_TERMS)
    if senior_hit and not any(term in title_l for term in ("associate product manager", "assistant manager")):
        score -= 34
        warnings.append("Title appears senior")

    years, years_warning = experience_warning(full)
    if years_warning:
        warnings.append(years_warning)
        score -= 12 if years and years < 5 else 22

    if re.search(r"\bph\.?d\.?\b", full) and any(
        phrase in full for phrase in ("phd required", "ph.d. required", "requires a phd", "doctoral degree required")
    ):
        score -= 30
        warnings.append("Doctoral degree appears required")
    elif any(phrase in full for phrase in ("master's preferred", "masters preferred", "m.s. preferred", "ms preferred")):
        score -= 5
        warnings.append("Graduate degree is preferred, but not necessarily required")

    if any(phrase in full for phrase in (
        "unable to provide visa sponsorship", "no visa sponsorship", "will not sponsor",
        "not eligible for sponsorship",
    )):
        warnings.append("Employer states that visa sponsorship is unavailable")

    if job.get("research") or org_type in {"research", "university"}:
        score += 8
        reasons.append("Research-oriented organization or role")

    # Keep the score useful as a ranking heuristic rather than a binary verdict.
    score = max(0, min(100, score))
    if score >= 75:
        tier = "Strong"
    elif score >= 55:
        tier = "Good"
    elif score >= 35:
        tier = "Stretch"
    else:
        tier = "Low"

    job.update({
        "category": category,
        "secondary_categories": secondary,
        "location_group": group,
        "entry_level": entry_level,
        "match_score": score,
        "fit_tier": tier,
        "match_reasons": list(dict.fromkeys(reasons))[:5],
        "matched_skills": list(dict.fromkeys(matched_skills))[:8],
        "warnings": list(dict.fromkeys(warnings))[:5],
    })
    return job


def should_include(job: dict[str, Any], *, max_age_days: int, min_score: int) -> bool:
    title = clean_text(job.get("title")).lower()
    description = clean_text(job.get("description")).lower()
    full = f" {title} {description} "

    if any(term in title for term in EXCLUDE_TITLE_TERMS):
        return False
    company = clean_text(job.get("company")).lower()
    if any(term in f" {title} {company} {description} " for term in RESTRICTED_SECTOR_TERMS):
        return False
    if any(term in company for term in RESTRICTED_ORGANIZATIONS):
        return False
    if any(term in title for term in SENIOR_TITLE_TERMS) and not any(
        exception in title for exception in ("associate product manager", "assistant manager")
    ):
        return False
    if job.get("match_score", 0) < min_score:
        return False

    age = days_old(job.get("posted_at"))
    # Unknown dates remain available from live employer feeds; dated jobs are freshness-gated.
    if age is not None and age > max_age_days and job.get("source_type") not in {"seed", "html"}:
        return False

    if job.get("curated_new_grad"):
        # These feeds have already been curated for recent graduates and US roles.
        return bool(job.get("url"))

    relevant_terms = set(term for values in CATEGORY_KEYWORDS.values() for term in values)
    if not any(term in full for term in relevant_terms) and not job.get("entry_level"):
        return False

    group = job.get("location_group")
    if group in {"Other / verify location", "Location not listed"} and not job.get("research"):
        return False
    return True
