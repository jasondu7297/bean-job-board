from __future__ import annotations

from typing import Any

from .utils import clean_text


def _research_focus(text: str) -> tuple[str, str]:
    lowered = text.lower()
    if any(x in lowered for x in ("genomic rearrangement", "cancer genome", "dna repair")):
        return (
            "how genomic rearrangements and DNA-repair errors reveal cancer vulnerabilities",
            "my BRCA1/BRCA2 population-variant project gave me practical experience building reproducible variant-analysis workflows and thinking carefully about how genomic evidence is interpreted",
        )
    if any(x in lowered for x in ("pediatric brain", "brain tumor", "neuro-oncology")):
        return (
            "using multi-omic data to improve the biological understanding and treatment of pediatric brain tumors",
            "my cancer-genomics project and experience with Python, R, Snakemake, BCFtools, and ANNOVAR would let me contribute quickly to reproducible sequencing analyses",
        )
    if any(x in lowered for x in ("single-cell", "single cell", "spatial transcript")):
        return (
            "the lab's use of single-cell and spatial transcriptomic data to connect molecular mechanisms with therapeutic questions",
            "I have built reproducible genomics workflows and enjoy translating complex biological questions into clear, testable computational analyses",
        )
    if any(x in lowered for x in ("microbiome", "host-microbiome")):
        return (
            "the lab's work on the molecular mechanisms of host–microbiome interactions",
            "my biology training and computational workflow experience would help me bridge experimental context with careful data handling and analysis",
        )
    if any(x in lowered for x in ("neurotechnology", "neuroscience", "brain-wide", "neurobiology")):
        return (
            "the lab's combination of neurotechnology, quantitative biology, and questions about brain-wide computation",
            "my background spans biology, scientific programming, and reproducible data pipelines, and I am eager to apply that mix in a neuroscience setting",
        )
    if any(x in lowered for x in ("multi-omics", "digital twin", "virtual cell", "real-world evidence", "biomarker")):
        return (
            "the group's effort to integrate multi-omic and clinical data with AI for biomarker and therapeutic discovery",
            "my background in bioinformatics, pipeline development, and an LLM-assisted competency-mapping project has made me especially interested in rigorous, interpretable AI for biomedical data",
        )
    if any(x in lowered for x in ("data management", "multi-cloud", "data platform", "database")):
        return (
            "building scalable data systems that let research and clinical teams use biological data reliably",
            "I have built API-driven and Snakemake-based pipelines, automated SQL workflows, and worked across both scientific and software contexts",
        )
    return (
        "the team's use of quantitative and computational methods to answer meaningful biological questions",
        "my background in biology, bioinformatics, Python, R, SQL, Linux, and reproducible workflow development aligns well with that kind of cross-disciplinary work",
    )


def generate_cold_email(job: dict[str, Any], profile: dict[str, Any]) -> dict[str, str] | None:
    if not (job.get("research") or job.get("org_type") in {"research", "university"}):
        return None

    title = clean_text(job.get("title"))
    company = clean_text(job.get("company"))
    team = clean_text(job.get("lab_or_team") or company)
    recipient = clean_text(job.get("recipient") or f"{team} Hiring Team")
    description = clean_text(job.get("description"))
    focus, bridge = _research_focus(f"{title} {team} {description}")
    name = clean_text(profile.get("name") or "Celina Lin")
    degree = clean_text(profile.get("education", {}).get("degree") or "Bachelor of Science in Biology/Bioinformatics")
    school = clean_text(profile.get("education", {}).get("school") or "the University of Waterloo")
    linkedin = clean_text(profile.get("linkedin"))
    ask = clean_text(profile.get("cold_email", {}).get("meeting_ask") or "15–20 minute conversation")
    signoff = clean_text(profile.get("cold_email", {}).get("signoff") or "Best,")

    subject = f"Interest in {title} — biology/bioinformatics graduate"
    school_phrase = school if school.lower().startswith("the ") else f"the {school}"

    body = f"""Dear {recipient},

My name is {name}, and I recently completed my {degree} at {school_phrase}. I am reaching out about the {title} opportunity with {team} at {company}.

I am especially interested in {focus}. In my independent BRCA1/BRCA2 project, I built a reproducible Python and Snakemake workflow using BCFtools and ANNOVAR to analyze population-specific variants and examine discrepancies between clinical labels and observed allele frequencies. I also completed two bioinformatics internships at the Ontario Institute for Cancer Research, where I developed an LLM-assisted competency-mapping pipeline and created research-data-management learning resources. More broadly, {bridge}.

The combination of rigorous biological questions, collaborative research, and hands-on computational work in this role is exactly the environment in which I hope to grow. I would be grateful for a {ask} to learn more about the lab's current priorities and discuss where my background could be useful. I have attached my resume for context.

{signoff}
{name}
{linkedin}"""
    return {"subject": subject, "body": body}
