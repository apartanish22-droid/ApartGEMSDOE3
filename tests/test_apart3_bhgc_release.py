"""Fail-closed checks for current release status; legacy BHGC files are audit artifacts."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_current_run_card_is_negative_and_slot_is_not_authorized() -> None:
    card = json.loads((ROOT / "run_card.json").read_text(encoding="utf-8"))
    assert card["verdict"] == "negative"
    assert card["ok_to_submit"] is False
    assert card["slot_used"] is False
    assert card["correlation_vs_registry"]["status"].startswith("FAIL")
    assert card["correlation_vs_registry"]["candidate_dots_within_3px_fraction"] > 0.70


def test_literal_calibration_lattice_overlap_blocks_candidate() -> None:
    raw = json.loads((ROOT / "evidence/apart3_cfkc_dhc_run_card.json").read_text(encoding="utf-8"))
    scan = raw["correlation_and_overlap_vs_registry"]
    lattice = scan["literal_5px_calibration_lattice_probe"]
    assert lattice["within_3px_fraction"] > 0.70
    assert raw["release_gate_decision"]["selector_required"] is True
    # The historical candidate's promote flag is retained in evidence but superseded.
    assert raw["verdict"] == "promote"
    assert "DO NOT SUBMIT" in json.loads((ROOT / "run_card.json").read_text())["reason"]


def test_research_tif_hash_matches_current_card_metadata() -> None:
    card = json.loads((ROOT / "run_card.json").read_text(encoding="utf-8"))
    artifact = ROOT / "docs/downloads/gemsdoe32-apart3-h-apart3-1-cfkc-dhc-37654-20261027T215000Z-9dedadfc-zeros.tif"
    assert artifact.is_file()
    assert hashlib.sha256(artifact.read_bytes()).hexdigest() == card["raster_sha256"]


def test_legacy_site_builder_refuses_to_restore_stale_promotion_claims() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/build_site.py")],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert "Refusing to regenerate legacy pages" in result.stdout


def test_entry_pages_and_release_status_are_explicitly_fail_closed() -> None:
    for rel in ("README.md", "docs/index.html", "index.html", "docs/executive-summary.html", "docs/release-status.html"):
        text = (ROOT / rel).read_text(encoding="utf-8")
        assert "NOT AUTHORIZED" in text or "not authorized" in text or "NO SUBMISSION IS AUTHORIZED" in text or "DO NOT SUBMIT" in text, rel
    summary = (ROOT / "docs/release-status.html").read_text(encoding="utf-8")
    assert "99.8513%" in summary
    assert "Download research artifact only — NOT FOR SUBMISSION" in summary
