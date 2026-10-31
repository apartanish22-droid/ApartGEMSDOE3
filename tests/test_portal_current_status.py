"""Regression checks that the published portal/feed cannot present a withdrawn card as current."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_latest_feed_is_current_unique_hypothesis_and_negative() -> None:
    source = json.loads((ROOT / "evidence/H1-LIDAR-SCARP-DEM-CHI_run_card.json").read_text())
    historical = json.loads((ROOT / "evidence/apart3_cthg_dhc_run_card.json").read_text())
    feed = json.loads((ROOT / "docs/data/latest-run-card.json").read_text())
    assert source["candidate_id"] == "H1-LIDAR-SCARP-DEM-CHI"
    assert source["verdict"] == "negative"
    assert source["ok_to_submit"] is False
    assert historical["candidate_id"] == "H-APART3-2-CTHG-DHC"
    assert historical["verdict"] == "negative"
    assert feed["candidate_id"] == source["candidate_id"]
    assert feed["raster_sha256"] == source["raster_sha256"]
    assert feed["release_status"] == "negative"
    assert feed["ok_to_download_as_submission"] is False
    assert feed["ok_to_submit"] is False
    assert feed["verdict"] == "negative"


def test_executive_summary_labels_scores_and_all_nine_duplicates() -> None:
    page = (ROOT / "docs/executive-summary.html").read_text()
    assert "DO NOT SUBMIT" in page
    assert "NOT YET OK TO SUBMIT" in page
    assert "OWNER-REPORT" in page
    assert "Not estimable" in page
    assert "NOT UNIQUE" in page
    for site in ("GEMSDOE24", "GEMSDOE25", "GEMSDOE27", "GEMSDOE28", "GEMSDOE30", "GEMSDOE31", "GEMSDOE32", "GEMSDOE33", "GEMSDOE36"):
        assert site in page
    assert "H1-LIDAR-SCARP-DEM-CHI" in page
    assert "gemsdoe32-h1-lidar-scarp-dem-chi" in page
    assert "PROMOTE — DOWNLOAD" not in page


def test_portal_builder_fails_closed_and_is_reproducible() -> None:
    import importlib.util

    spec = importlib.util.spec_from_file_location("build_review_site", ROOT / "scripts/build_review_site.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    source = json.loads((ROOT / "evidence/H1-LIDAR-SCARP-DEM-CHI_run_card.json").read_text())
    audit = json.loads((ROOT / "evidence/nine_site_best_files_audit.json").read_text())
    status = json.loads((ROOT / "registry/current_status.json").read_text())
    regenerated = module.build_page(source, audit, status)
    assert regenerated == (ROOT / "docs/executive-summary.html").read_text()
