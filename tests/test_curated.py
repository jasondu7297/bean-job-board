from datetime import date
import unittest

from jobboard.curated import looks_like_us_location, parse_curated_feed, parse_posted_date


class CuratedSourceTests(unittest.TestCase):
    def setUp(self):
        self.source = {
            "name": "Test New-Grad Feed",
            "url": "https://raw.githubusercontent.com/example/jobs/main/README.md",
            "page_url": "https://github.com/example/jobs",
            "category_hint": "Data Analysis / Data Science",
            "scope": "us",
        }

    def test_markdown_table_filters_non_us_and_parses_relative_date(self):
        text = """
| Company | Position | Location | Salary | Posting | Age |
|---|---|---|---|---|---|
| [Meta](https://meta.com) | Data Engineer - University Grad | Bellevue, WA | $186k/yr | [Apply](https://example.com/job) | 2d |
| [Other](https://other.com) | Data Analyst | Toronto, Canada |  | [Apply](https://example.com/ca) | 1d |
"""
        jobs = parse_curated_feed(text, self.source, now=date(2026, 6, 25))
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0]["company"], "Meta")
        self.assertEqual(jobs[0]["posted_at"], "2026-06-23")
        self.assertEqual(jobs[0]["salary"], "$186k/yr")
        self.assertTrue(jobs[0]["curated_new_grad"])

    def test_markdown_continuation_rows_keep_company(self):
        text = """
| Company | Job Title | Location | Work Model | Date Posted |
| ----- | --------- | --------- | ---- | ------- |
| **[Booz Allen](https://boozallen.com)** | **[Data Scientist](https://jobright.ai/jobs/1)** | Fort Meade, MD, US | On Site | Jun 24 |
| ↳ | **[Data Scientist I](https://jobright.ai/jobs/2)** | Atlanta, GA | Hybrid | Jun 24 |
"""
        jobs = parse_curated_feed(text, self.source, now=date(2026, 6, 25))
        self.assertEqual(len(jobs), 2)
        self.assertEqual(jobs[1]["company"], "Booz Allen")
        self.assertEqual(jobs[1]["workplace"], "Hybrid")

    def test_html_table_and_application_url(self):
        text = """
<table>
<tr><th>Company</th><th>Role</th><th>Location</th><th>Application</th><th>Age</th></tr>
<tr><td>Example Bio</td><td>Bioinformatics Analyst I</td><td>Boston, MA</td><td><a href="https://careers.example.org/jobs/123">Apply</a></td><td>today</td></tr>
</table>
"""
        jobs = parse_curated_feed(text, self.source, now=date(2026, 6, 25))
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0]["url"], "https://careers.example.org/jobs/123")
        self.assertEqual(jobs[0]["posted_at"], "2026-06-25")
        self.assertTrue(jobs[0]["research"])

    def test_location_filter(self):
        self.assertTrue(looks_like_us_location("Boston, MA, US"))
        self.assertTrue(looks_like_us_location("Remote, United States"))
        self.assertTrue(looks_like_us_location("Colorado"))
        self.assertTrue(looks_like_us_location("SF"))
        self.assertFalse(looks_like_us_location("Toronto, Ontario, Canada"))

    def test_date_parser(self):
        self.assertEqual(parse_posted_date("3d", now=date(2026, 6, 25)), "2026-06-22")
        self.assertEqual(parse_posted_date("Jun 24", now=date(2026, 6, 25)), "2026-06-24")


if __name__ == "__main__":
    unittest.main()
