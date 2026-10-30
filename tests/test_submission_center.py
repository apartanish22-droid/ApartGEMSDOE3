"""The Submission Center must stay fail-closed and must read every number from evidence."""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "docs/submit.html"
CARD = ROOT / "evidence/vo-learn-hgb-frac15_run_card.json"
PAIRWISE = ROOT / "evidence/nine_site_pairwise_uniqueness_20261030.json"
SITES = ["GEMSDOE24", "GEMSDOE25", "GEMSDOE27", "GEMSDOE28", "GEMSDOE30",
         "GEMSDOE31", "GEMSDOE32", "GEMSDOE33", "GEMSDOE36"]


def _reject_constant(token: str) -> None:
    raise ValueError(f"non-strict JSON constant: {token}")


def _card() -> dict:
    return json.loads(CARD.read_text(), parse_constant=_reject_constant)


def test_run_card_is_strict_json_and_fail_closed() -> None:
    card = _card()
    assert card["decision"]["status"] == "NOT CLEARED"
    assert card["decision"]["ok_to_submit"] is False
    assert card["decision"]["weekly_slot_used"] is False
    assert card["decision"]["promoted_to_slot"] is False
    assert card["experiments_used"] == 3 and card["experiment_budget"] == 3
    assert card["registry_gate"]["final_literal_rule_passed"] is False
    assert card["registry_gate"]["audit_complete"] is False
    assert card["estimated_leaderboard_score"].startswith("NOT ESTIMABLE")


def test_run_card_ids_exist_in_irregularity_ledger() -> None:
    card = _card()
    ledger = json.loads((ROOT / "registry/irregularities.json").read_text())
    ids = {item["id"] for item in ledger["items"]}
    missing = [i for i in card["irregularities_referenced"] if i not in ids]
    assert not missing, missing


def test_public_artifact_is_byte_identical_to_writer_output() -> None:
    card = _card()
    art = card["final_artifact"]
    path = ROOT / art["public_downloadable_zeros_tif"]
    assert path.is_file()
    assert hashlib.sha256(path.read_bytes()).hexdigest() == art["sha256_zeros_tif"]
    assert art["on_catalogue_positive_pixels"] == 0
    assert art["in_footprint_min"] >= 0.0 and art["in_footprint_max"] <= 1.0


def test_public_artifact_passes_format_check_when_template_is_present() -> None:
    template = ROOT / ".cache/gems_data/sample_submission.tif"
    if not template.exists():
        return  # restored by scripts/restore_data.py; CI restores the core group
    art = _card()["final_artifact"]["public_downloadable_zeros_tif"]
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts/check_submission.py"), "--template", str(template),
         "--strict-finite", str(ROOT / art)],
        capture_output=True, text=True, cwd=ROOT,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_page_is_not_cleared_and_has_no_submit_call_to_action() -> None:
    html = PAGE.read_text()
    assert "NOT CLEARED" in html and "DO NOT SUBMIT" in html
    lowered = html.lower()
    for forbidden in ("submit now", "download and submit", "promote — download", "ok to submit: yes"):
        assert forbidden not in lowered
    # README rule 7: no download call to action for a candidate that has not passed every gate
    assert re.search(r'download="' , html) is None


def test_page_covers_all_nine_sites_and_labels_scores() -> None:
    html = PAGE.read_text()
    rows = re.findall(r"<tr><td><b>(GEMSDOE\d+)</b>", html)
    assert rows == SITES
    assert html.count("OWNER-REPORT") >= 9
    assert "HOLDOUT-DTI" in html
    assert "ORGANIZER-CONFIRMED" in html  # named only as the label that is not yet earned
    pairwise = json.loads(PAIRWISE.read_text())
    assert [r["site"] for r in pairwise["results"]] == SITES


def test_page_flags_leaderboard_conflict_without_resolving_it() -> None:
    html = PAGE.read_text()
    for value in ("0.3195", "0.4413", "0.4544"):
        assert value in html
    assert "not reconciled" in html or "flagged, not resolved" in html.lower()


def test_hypotheses_are_proposals_not_scores() -> None:
    html = PAGE.read_text()
    assert html.count("proposal · not run · no slot") == 4
    assert "Expected gain (unmeasured)" in html


def test_index_links_to_submission_center_and_keeps_fail_closed_text() -> None:
    index = (ROOT / "docs/index.html").read_text()
    assert 'href="submit.html"' in index
    summary = (ROOT / "docs/executive-summary.html").read_text()
    assert "There is no file currently OK to submit" in summary
    gateway = (ROOT / "index.html").read_text()
    assert "docs/submit.html" in gateway
