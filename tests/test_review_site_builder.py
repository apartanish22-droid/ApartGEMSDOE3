"""The public review pages must remain distinct and fail closed."""
from __future__ import annotations

import importlib.util
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("review_site", ROOT / "scripts/build_review_site.py")
review_site = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(review_site)


def test_builder_creates_distinct_pages_with_clear_submission_status():
    pages = review_site.build_pages(ROOT)
    assert len(pages) == 10
    assert len(set(pages.values())) == len(pages)
    expected = {
        "index.html": "Decision at a glance",
        "executive-summary.html": "Nine-site comparison",
        "release-status.html": "Current release gates",
        "submissions.html": "Submission checklist",
        "research.html": "Research status",
        "hypotheses.html": "Unrun candidates",
        "leaderboard.html": "Scope and evidence classes",
        "review.html": "Current review",
        "sources.html": "Official review pointers",
    }
    for filename, marker in expected.items():
        content = pages[filename]
        assert marker in content
        assert "DO NOT SUBMIT" in content
        assert 'aria-label="Main navigation"' in content
    assert "OWNER-REPORT 0.2778" in pages["executive-summary.html"]
    assert "Not estimable" in pages["executive-summary.html"]
    assert "Not estimable" in pages["leaderboard.html"]
    assert "xiaofanhu 0.4544" in pages["leaderboard.html"]
    assert "not a score for any GEMSDOE file" in pages["leaderboard.html"]
    assert pages["executive-summary.html"].count("NOT UNIQUE vs supplied nine") == 9
    assert "paired comparison with the local mask" in pages["executive-summary.html"]
    assert "GEMSDOE32-HIDE-RECOVER-v3.0, 22,232 withheld positives" in pages["executive-summary.html"]
    assert "DO NOT SUBMIT" in pages["executive-summary/index.html"]
    assert 'href="downloads/' not in pages["executive-summary.html"]
    assert 'href="../downloads/' not in pages["executive-summary/index.html"]
    assert 'href="https://github.com/apartanish22-droid/ApartGEMSDOE3/blob/main/knowledge/' in pages[
        "executive-summary/index.html"
    ]
    assert "PROMOTE — DOWNLOAD" not in "".join(pages.values())
    page_html = "".join(pages.values())
    assert "Download GeoTIFF for research only" not in page_html
    raster_download_link = re.search(
        r'href="[^"]+\.(?:tif|tiff|zip)(?:\?[^"]*)?"',
        page_html,
        re.IGNORECASE,
    )
    assert raster_download_link is None
    assert "repo-review-current-session-2026-10-30.md" in pages["review.html"]
    assert "companion nine-site and source review" in pages["review.html"]
    assert "109 passed, 2 skipped, 0 failed" in pages["review.html"]
    assert "101 passed, 2 skipped" not in pages["review.html"]


def test_status_and_public_feed_point_to_current_negative_candidate_card():
    import json

    review_site.sync_status_artifacts(ROOT)
    status = json.loads((ROOT / "registry/current_status.json").read_text())
    feed = json.loads((ROOT / "docs/data/feed.json").read_text())
    latest = json.loads((ROOT / "docs/data/latest-run-card.json").read_text())
    site_data = json.loads((ROOT / "docs/assets/site-data.json").read_text())
    review_path = ROOT / status["current_review"]
    candidate_card_path = ROOT / status["current_run_card"]
    review_card = json.loads(review_path.read_text())
    assert review_path.is_file() and candidate_card_path.is_file()
    assert status["any_file_ok_to_submit"] is False
    assert status["current_review"] == "evidence/session_review_20261030.json"
    assert review_card["holdout_dti"] is None
    assert feed["current_review"]["review_card"] == status["current_review"]
    assert feed["current_review"]["review_report"] == review_card["review_report"]
    assert feed["generated_utc"] == status["updated_utc"]
    assert status["feed_scope_note"] in feed["feed_scope_note"]
    latest_board = review_site.latest_verified_leaderboard(ROOT)
    assert feed["leaderboard"] == latest_board["rows"]
    assert feed["leaderboard_observed_utc"] == latest_board["observed_utc"]
    assert feed["leaderboard_verified"] is True
    history_records = [
        json.loads(line)
        for line in (ROOT / "registry/leaderboard_history.jsonl").read_text().splitlines()
        if line.strip()
    ]
    snapshot_dates = {
        record["observed_utc"][:10]
        for record in history_records
        if record.get("verified") is True
    }
    assert feed["leaderboard_snapshots"] == len(snapshot_dates)
    assert "not a score for any gemsdoe file" in feed["leaderboard_note"].lower()
    assert status["leaderboard_top"]["score"] == latest_board["rows"][0]["score"]
    assert latest["candidate_id"] == status["current_candidate"]["candidate_id"]
    assert latest["candidate_id"] == "H-APART3-UNIQUE-OFFCATALOGUE-GEOPHYS"
    assert len(latest["submission_note"]) <= 140
    assert feed["current_candidate"]["run_card"] == status["current_run_card"]
    assert feed["current_candidate"]["verdict"] == "negative"
    assert feed["current_candidate"]["ok_to_submit"] is False
    assert feed["submission"]["ok_to_submit"] is False
    assert latest["verdict"] == "negative" and latest["ok_to_submit"] is False
    assert latest["session_branch"]
    assert site_data["run_card"]["ok_to_submit"] is False
    assert site_data["run_card"]["candidate_id"] == status["current_candidate"]["candidate_id"]


def test_builder_does_not_use_markdown_links_and_keeps_internal_links_valid():
    pages = review_site.build_pages(ROOT)
    assert "[DOE GEMS competition](" not in pages["submissions.html"]
    assert 'href="https://www.drivendata.org/competitions/306/competition-doe-gems/"' in pages[
        "executive-summary.html"
    ]
    assert 'href="https://www.drivendata.org/competitions/306/competition-doe-gems/data/"' in pages[
        "submissions.html"
    ]
    for relative, content in pages.items():
        base = (ROOT / "docs" / relative).parent
        for target in re.findall(r'(?:href|src)="([^"#?]+)"', content):
            if target.startswith(("http://", "https://", "mailto:", "javascript:")):
                continue
            assert (base / target).resolve().exists(), f"Broken link in {relative}: {target}"
