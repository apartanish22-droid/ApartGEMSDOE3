from __future__ import annotations

import csv
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit

import pytest

import build_site
from conftest import ROOT


class LinkCollector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.ids = []
    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if values.get("id"):
            self.ids.append(values["id"])
        for attr in ("href", "src"):
            if values.get(attr):
                self.links.append(values[attr])


def html_pages():
    return [ROOT / "index.html", *sorted((ROOT / "docs").rglob("*.html"))]


def test_generated_site_matches_audit_and_templates():
    generated = build_site.outputs()
    assert len(generated) == 11  # nine briefs, index, CSV
    for path, content in generated.items():
        assert path.read_text() == content, f"generated artifact drift: {path}"
        assert "{{" not in content and "}}" not in content


def test_local_links_and_anchors_resolve_without_network():
    parser_by_path = {}
    for path in html_pages():
        parser = LinkCollector(); parser.feed(path.read_text())
        assert len(parser.ids) == len(set(parser.ids)), f"duplicate id in {path}"
        parser_by_path[path.resolve()] = parser
    failures = []
    for path, parser in parser_by_path.items():
        for link in parser.links:
            url = urlsplit(link)
            if url.scheme or url.netloc:
                continue
            target = (path.parent / unquote(url.path)).resolve() if url.path else path
            if not target.is_relative_to(ROOT.resolve()) or not target.is_file():
                failures.append(f"{path.relative_to(ROOT)}: {link} missing")
            elif url.fragment and target in parser_by_path and unquote(url.fragment) not in parser_by_path[target].ids:
                failures.append(f"{path.relative_to(ROOT)}: {link} missing anchor")
    assert not failures, "\n".join(failures)


def test_evidence_and_csv_cannot_indicate_historical_files_are_approved():
    audit = json.loads((ROOT / "evidence/prior_audit.json").read_text())
    assert len(audit["historic"]) == 9 and len(audit["pairwise"]) == 72
    assert all(row["duplicate"] and row["overlap_within_3px"] > .70 for row in audit["pairwise"])
    assert audit["lattice"]["bound_at_37654_distinct_dots"] > .70
    with (ROOT / "docs/data/site_scorecard.csv").open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 9
    for row in rows:
        assert row["submit"] == row["unique_vs_named_sites"] == "NO"
        assert not row["estimated_organizer_score"]
        assert row["historical_user_report_unverified"]
        assert row["sha256"] == audit["historic"][row["site"]]["sha256"]
    run = json.loads((ROOT / "docs/data/run_card.json").read_text())
    assert run["verdict"] == "negative" and run["approved_for_weekly_slot"] is False
    parallel = json.loads((ROOT / "evidence/mrcj_audit.json").read_text())
    assert run["raster_sha256"] == parallel["candidate_sha256"] and run["submission_name"] is None
    assert run["registry"]["final_dot_overlap_vs_lattice"] == 1.0
    assert run["experiments_run_in_this_review"] == run["submission_slots_used_in_this_review"] == 0
    assert len(run["submission_note"]) <= 140 and "DO NOT SUBMIT" in run["submission_note"]


def test_vendor_files_match_immutable_blob_provenance():
    provenance = json.loads((ROOT / "vendor/template-provenance.json").read_text())
    assert re.fullmatch(r"[0-9a-f]{40}", provenance["commit"])
    paths = {item["local"] for item in provenance["files"]}
    assert paths == {str(p.relative_to(ROOT)) for p in (ROOT / "vendor/gems57").glob("*.py")}
    for item in provenance["files"]:
        blob = (ROOT / item["local"]).read_bytes()
        assert hashlib.sha256(blob).hexdigest() == item["sha256"]
        framed = f"blob {len(blob)}\0".encode() + blob
        assert hashlib.sha1(framed).hexdigest() == item["git_blob"]


def test_manifest_has_immutable_pins_and_safe_unique_destinations():
    manifest = json.loads((ROOT / "registry/input_manifest.json").read_text())
    records = manifest["files"]
    assert len({r["id"] for r in records}) == len(records)
    assert len({r["destination"] for r in records}) == len(records)
    for item in records:
        assert re.fullmatch(r"[0-9a-f]{40}", item["ref"])
        assert re.fullmatch(r"[0-9a-f]{64}", item["sha256"])
        path = Path(item["destination"])
        assert not path.is_absolute() and ".." not in path.parts
