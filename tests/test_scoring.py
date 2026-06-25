from __future__ import annotations

import unittest
from pathlib import Path

import yaml

from jobboard.emails import generate_cold_email
from jobboard.scoring import analyze_job, location_group, should_include


ROOT = Path(__file__).resolve().parents[1]
PROFILE = yaml.safe_load((ROOT / "config" / "profile.yml").read_text(encoding="utf-8"))


class ScoringTests(unittest.TestCase):
    def test_bioinformatics_new_grad_is_strong(self) -> None:
        job = {
            "title": "Bioinformatics Engineer",
            "company": "Research Institute",
            "location": "Boston, MA",
            "description": (
                "Entry-level position requiring a bachelor's degree and 0-2 years. "
                "Build Python, R, SQL, Linux, genomic data pipelines and analyze RNA-seq data."
            ),
            "posted_at": "2026-06-24",
            "research": True,
            "org_type": "research",
            "source_type": "seed",
        }
        analyzed = analyze_job(job, PROFILE)
        self.assertEqual(analyzed["location_group"], "Boston / Cambridge")
        self.assertGreaterEqual(analyzed["match_score"], 75)
        self.assertEqual(analyzed["fit_tier"], "Strong")
        self.assertTrue(should_include(analyzed, max_age_days=45, min_score=28))

    def test_senior_role_is_penalized(self) -> None:
        job = {
            "title": "Senior Director of Data Science",
            "company": "Company",
            "location": "New York, NY",
            "description": "Requires 8+ years and a PhD required.",
            "research": False,
            "org_type": "company",
            "source_type": "greenhouse",
        }
        analyzed = analyze_job(job, PROFILE)
        self.assertLess(analyzed["match_score"], 35)
        self.assertFalse(should_include(analyzed, max_age_days=45, min_score=28))

    def test_location_groups(self) -> None:
        self.assertEqual(location_group("South San Francisco, CA"), "San Francisco Bay Area")
        self.assertEqual(location_group("Cambridge, Massachusetts"), "Boston / Cambridge")
        self.assertEqual(location_group("Remote - United States"), "Remote - US")

    def test_research_email_is_personalized(self) -> None:
        job = {
            "title": "Bioinformatics Analyst",
            "company": "University Lab",
            "lab_or_team": "Cancer Genomics Lab",
            "recipient": "Professor Example",
            "description": "Analyze single-cell RNA-seq and spatial transcriptomics in cancer.",
            "research": True,
            "org_type": "university",
        }
        email = generate_cold_email(job, PROFILE)
        self.assertIsNotNone(email)
        assert email is not None
        self.assertIn("Professor Example", email["body"])
        self.assertIn("BRCA1/BRCA2", email["body"])
        self.assertIn("15–20 minute conversation", email["body"])


if __name__ == "__main__":
    unittest.main()
