import json
import re
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
PAGES = (ROOT / "index.html", ROOT / "docs" / "submission-guide.html", ROOT / "docs" / "hypotheses.html")


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

    def test_executive_summary_has_clear_fail_closed_state(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn("NOT READY · DO NOT SUBMIT", html)
        self.assertIn("No new candidate GeoTIFF exists", html)
        self.assertIn("OWNER-REPORTED", html)
        self.assertIn("no download", html.lower())
        self.assertEqual(html.count("<tr>"), 10)  # header plus nine pre-rendered site rows
        record = json.loads((ROOT / "docs/data/focus-sites.json").read_text(encoding="utf-8"))
        for site in record["sites"]:
            with self.subTest(site=site["site"]):
                self.assertIn(site["site"], html)
                self.assertIn(site["file"], html)
                self.assertIn(site["method_tag"], html)
                self.assertIn(f"{site['reported_score']:.4f}", html)

    def test_javascript_uses_local_audit_records(self):
        script = (ROOT / "assets" / "site.js").read_text(encoding="utf-8")
        self.assertIn('fetch(jsonUrl("focus-sites.json")', script)
        self.assertIn('fetch(jsonUrl("leaderboard.json")', script)
        self.assertIn("textContent", script)
        self.assertNotRegex(script, re.compile(r"innerHTML\s*="))


if __name__ == "__main__":
    unittest.main()
