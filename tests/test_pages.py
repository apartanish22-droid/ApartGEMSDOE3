import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
PAGES = (
    ROOT / "index.html",
    ROOT / "docs" / "index.html",
    ROOT / "docs" / "executive-summary.html",
    ROOT / "docs" / "hypotheses.html",
    ROOT / "docs" / "submission-guide.html",
)
SITES = (
    "GEMSDOE24", "GEMSDOE25", "GEMSDOE27", "GEMSDOE28", "GEMSDOE30",
    "GEMSDOE31", "GEMSDOE32", "GEMSDOE33", "GEMSDOE36",
)


class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        for key in ("href", "src"):
            if attributes.get(key):
                self.links.append((tag, key, attributes[key]))


class StaticPageTests(unittest.TestCase):
    def test_local_page_links_resolve(self):
        for page in PAGES:
            parser = LinkParser()
            parser.feed(page.read_text(encoding="utf-8"))
            for _tag, _key, value in parser.links:
                if value.startswith(("https://", "http://", "mailto:", "data:")):
                    continue
                parsed = urlsplit(value)
                if not parsed.path:
                    continue
                with self.subTest(page=str(page.relative_to(ROOT)), href=value):
                    target = (page.parent / parsed.path).resolve()
                    self.assertTrue(target.is_relative_to(ROOT.resolve()), "local link escaped repository")
                    self.assertTrue(target.exists(), f"broken local link: {value}")

    def test_pages_deployed_from_docs_have_local_stylesheets(self):
        for page in PAGES[1:]:
            parser = LinkParser()
            parser.feed(page.read_text(encoding="utf-8"))
            stylesheets = [value for _tag, key, value in parser.links if key == "href" and value.endswith(".css")]
            with self.subTest(page=str(page.relative_to(ROOT))):
                self.assertTrue(stylesheets)
                for stylesheet in stylesheets:
                    self.assertTrue((page.parent / stylesheet).is_file(), stylesheet)

    def test_current_executive_summary_is_fail_closed_and_covers_all_sites(self):
        html = (ROOT / "docs" / "index.html").read_text(encoding="utf-8")
        self.assertIn("DO NOT SUBMIT", html)
        self.assertIn("Research download: available", html)
        self.assertIn("official-format compliance fails", html)
        self.assertIn("user-supplied owner reports, not organizer receipts", html.lower())
        self.assertIn("not an organizer score", html.lower())
        detailed = (ROOT / "docs" / "executive-summary.html").read_text(encoding="utf-8")
        self.assertIn("h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros", detailed)
        for site in SITES:
            with self.subTest(site=site):
                self.assertIn(site, html)
        self.assertEqual(html.count("<tr>"), 10)  # header plus nine pre-rendered site rows
        self.assertIn('href="hypotheses.html"', html)
        self.assertIn('href="submission-guide.html"', html)


if __name__ == "__main__":
    unittest.main()
