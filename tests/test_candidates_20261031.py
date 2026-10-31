"""Fail-closed regressions for the 2026-10-31 H-S1 and H-M1 candidates.

These tests check the saved artifacts only. They do not re-run the registry scan.
"""
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SUMMARY = ROOT / "evidence/candidates_20261031_summary.json"


def _load(name, rel):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def summary():
    if not SUMMARY.is_file():
        pytest.skip("gate summary not generated; run scripts/summarize_candidates_20261031.py")
    return json.loads(SUMMARY.read_text())


def test_nothing_is_cleared(summary):
    assert summary["any_file_ok_to_submit"] is False
    assert len(summary["candidates"]) == 3
    for c in summary["candidates"]:
        assert c["ok_to_submit"] is False
        assert c["verdict"] == "negative", c["candidate_id"]
        assert c["live_score_estimate"].startswith("NOT ESTIMABLE")
        assert c["gates"]["G7_method_lane_assigned"]["passed"] is False
        assert c["gates"]["G8_selector_authorization_weekly_slot"]["passed"] is False
        assert c["gates"]["G2_single_feature_leakage_canary_max_auc_le_0.90"]["passed"] in (True, False)


def test_artifact_hashes_and_note_length(summary):
    for c in summary["candidates"]:
        path = ROOT / c["file"]
        assert path.is_file(), c["file"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == c["sha256"]
        assert c["note_chars"] <= 140
        assert c["submission_name"] and c["submission_name"] != "not recorded"


def test_candidate_files_pass_strict_format(summary):
    sys.path.insert(0, str(ROOT / "src"))
    from gemsdoe32.submission import validate_submission_geotiff as validate
    template = ROOT / ".cache/gems_data/sample_submission.tif"
    if not template.is_file():
        pytest.skip("template not restored")
    for c in summary["candidates"]:
        rep = validate(ROOT / c["file"], template, strict_whole_array_finite=True).to_dict()
        assert rep["passed"] is True, (c["file"], rep)


def test_note_dot_count_gate_is_recorded_not_hidden(summary):
    """The submission notes were written from the target dot count, not the raster count.

    The gate must report the mismatch as a failure until the note is regenerated.
    """
    for c in summary["candidates"]:
        g = c["gates"]["G9_submission_note_states_actual_dot_count"]
        assert g["note_says"] != g["raster_dots"] or g["passed"] is True
        if g["note_says"] != g["raster_dots"]:
            assert g["passed"] is False


def test_pages_show_block_and_no_download_authorization(summary):
    for rel in ["docs/executive-summary.html", "docs/executive-summary/index.html", "docs/index.html"]:
        text = (ROOT / rel).read_text()
        assert "DO NOT SUBMIT any file" in text, rel
        assert "Not estimable" in text or "NOT ESTIMABLE" in text or "not estimable" in text, rel
        for c in summary["candidates"]:
            assert c["sha256"] in text, (rel, c["candidate_id"])


def test_readme_links_session_brief_and_decision():
    readme = (ROOT / "README.md").read_text()
    assert "docs/session-prompts/2026-10-31-requirements.md" in readme
    assert "Decision (2026-10-31)" in readme
    assert (ROOT / "docs/session-prompts/2026-10-31-requirements.md").is_file()


@pytest.mark.parametrize("scan", [
    "evidence/H-S1-SPECTRAL-ROLLOFF_registry_scan.json",
    "evidence/H-M1-CROSSGRAD-MG_registry_scan.json",
    "evidence/H1-LIDAR-SCARP-DEM-CHI_registry_scan_20261031.json",
])
def test_scan_gate_matches_stage_records(scan):
    """Regression for IR-20261031-15: the gate must read the surface stage's 'passed' flag."""
    d = json.loads((ROOT / scan).read_text())
    gate = d["gate"]
    assert gate["final_dots_literal_passed"] == bool(d["final_dots"]["literal_rule_passed"])
    if "surface" in d:
        assert gate["surface_literal_passed"] == bool(d["surface"]["passed"])
        assert gate["all_literal_checks_passed"] is (gate["surface_literal_passed"] and gate["final_dots_literal_passed"])
    else:
        assert "surface_literal_passed" not in gate  # no surface was supplied; the surface stage was not run
        assert gate["all_literal_checks_passed"] is gate["final_dots_literal_passed"]
    assert gate["all_literal_checks_passed"] is False
