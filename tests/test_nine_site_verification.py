"""Regression checks for the 2026-10-30 nine-site verification record.

These tests read only committed evidence files (no restored competition data), so they run in CI.
They guard the claims made in docs/research/nine-site-verification-20261030.md.
"""

from __future__ import annotations

import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "evidence" / "nine_site_verification_20261030.json"
AUDIT = ROOT / "evidence" / "nine_site_best_files_audit.json"
DOC = ROOT / "docs" / "research" / "nine-site-verification-20261030.md"

NAN_SITES = {"GEMSDOE24", "GEMSDOE25", "GEMSDOE27", "GEMSDOE28", "GEMSDOE31"}
FOOTPRINT_OUTSIDE = 7111787


def _load():
    return json.loads(EVIDENCE.read_text())


def test_nine_sites_match_audit_hashes_and_scores():
    ev = _load()
    audit = json.loads(AUDIT.read_text())["sites"]
    by_site = {s["site"]: s for s in ev["sites"]}
    assert len(ev["sites"]) == 9
    for a in audit:
        row = by_site[a["site"]]
        assert row["sha256"] == a["sha256"]
        assert row["owner_reported_score_OWNER_REPORT"] == a["published_score_OWNER_REPORT"]
        assert row["sha256_matches_audit"] is True


def test_strict_validator_pattern_and_nan_counts():
    ev = _load()
    for row in ev["sites"]:
        nan = row["raster"]["nan_count"]
        if row["site"] in NAN_SITES:
            assert nan == FOOTPRINT_OUTSIDE
            assert row["validator_strict_finite_passed"] is False
        else:
            assert nan == 0
            assert row["validator_strict_finite_passed"] is True
        assert row["raster"]["out_of_range_finite_count"] == 0


def test_only_gemsdoe25_and_30_are_exact_duplicates():
    assert _load()["exact_duplicate_positive_masks"] == [["GEMSDOE25", "GEMSDOE30"]]


def test_every_nine_site_pair_fails_the_70_percent_gate():
    ev = _load()
    names = [s["site"] for s in ev["sites"]]
    m = ev["pairwise_3px_overlap_row_within_3px_of_column"]
    for a, b in itertools.combinations(names, 2):
        assert max(m[f"{a}->{b}"], m[f"{b}->{a}"]) > 0.70, (a, b)


def test_holdout_is_hide_and_recover_with_fixed_withheld_count():
    ev = _load()
    for row in ev["sites"]:
        h = row["holdout_dti"]
        assert h["label"] == "HOLDOUT-DTI"
        assert h["evaluator_version"] == "GEMSDOE32-HIDE-RECOVER-v3.0"
        assert h["withheld_positives"] == 22232
        lo, hi = h["ci95_cluster_bootstrap"]
        assert lo <= h["pooled_dti"] <= hi


def test_rank_direction_documented_in_evidence():
    corr = _load()["correlations"]
    assert corr["spearman_owner_vs_holdout_dti"]["rho"] < -0.8
    assert corr["spearman_owner_vs_sgmc_calibrated"]["rho"] > 0.9
    assert corr["spearman_owner_vs_frac_beyond_1km"]["rho"] > 0.9


def test_decision_statement_is_fail_closed():
    text = DOC.read_text()
    assert "no file from this repository is authorized for download or upload." in text.lower()
    assert "not estimable" in text
