"""Preserve the parallel artifact and assert the current fail-closed decision."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import rasterio

ROOT = Path(__file__).parents[1]
ORIGINAL = ROOT / 'evidence/run_card.json'
CURRENT = ROOT / 'evidence/mrcj_current_run_card.json'
TIF = ROOT / 'docs/downloads/apartgems3-mrcj-curvature-junction-37654-20261027-zeros.tif'


def test_original_run_card_and_bytes_are_preserved():
    c = json.loads(ORIGINAL.read_text())
    assert c['experiments_run'] <= c['budget_limit'] == 3
    assert c['feature_leakage_canary']['passed']
    assert c['feature_leakage_canary']['worst_pooled_auc'] <= .90
    assert max(abs(x) for x in c['correlation_vs_registry'].values() if x is not None) <= .90
    assert len(c['overlap_vs_registry']) == 9 and max(c['overlap_vs_registry'].values()) <= .70
    assert c['verdict'] == 'promote' and c['ok_to_submit'] is True  # superseded historical claim
    assert hashlib.sha256(TIF.read_bytes()).hexdigest() == c['raster_sha256']


def test_submission_is_strictly_finite_and_aligned():
    with rasterio.open(TIF) as s, rasterio.open(ROOT / 'data/bridge/sample_submission.tif') as t:
        a = s.read(1)
        assert s.count == 1 and s.dtypes == ('float32',)
        assert (s.crs, s.shape, s.transform) == (t.crs, t.shape, t.transform)
        assert np.isfinite(a).all() and a.min() >= 0 and a.max() <= 1
        assert np.count_nonzero(a) == 37654


def test_current_decision_rejects_historical_promotion():
    audit = json.loads((ROOT / 'evidence/mrcj_audit.json').read_text())
    old = json.loads(ORIGINAL.read_text())
    current = json.loads(CURRENT.read_text())
    assert current['verdict'] == 'negative' and current['ok_to_submit'] is False
    assert current['approved_for_weekly_slot'] is False
    assert audit['candidate_sha256'] == current['raster_sha256'] == old['raster_sha256']
    assert audit['three_pixel_overlap_count'] == audit['candidate_in_footprint_dots'] == 37654
    assert audit['three_pixel_overlap_fraction'] == 1.0 and audit['duplicate_by_overlap']
    assert len(audit['historical_comparisons']) == 9
    assert max(r['candidate_dot_overlap_within_3px'] for r in audit['historical_comparisons']) < .70
    assert audit['complete_registry_checked'] is False
    assert 'DO NOT SUBMIT' in current['submission_note'] and len(current['submission_note']) <= 140


def test_archived_experiment_runner_stops_before_overwriting():
    before = hashlib.sha256(TIF.read_bytes()).hexdigest()
    card_before = hashlib.sha256(ORIGINAL.read_bytes()).hexdigest()
    p = subprocess.run([sys.executable, str(ROOT / 'scripts/run_experiments.py')],
                       capture_output=True, text=True, timeout=20)
    assert p.returncode != 0 and 'STOP: archived MRCJ runner' in p.stderr
    assert hashlib.sha256(TIF.read_bytes()).hexdigest() == before
    assert hashlib.sha256(ORIGINAL.read_bytes()).hexdigest() == card_before


def test_current_review_rechecks_focus_registry_and_stays_negative():
    from gems.current_review import review_current_best
    report = review_current_best(ROOT)
    assert report['verdict'] == 'negative' and report['ok_to_submit'] is False
    assert report['ok_to_download_for_research'] is True
    assert report['novel_vs_each_focus_raster_under_thresholds'] is True
    assert report['focus_registry_count'] == 9
    assert report['external_registry_hazard']['conditional_minimum_candidate_overlap'] > .70
    assert report['independent_lattice_audit']['overlap_fraction'] == 1.0
    assert report['independent_lattice_audit']['duplicate_by_overlap'] is True
    assert 'DO NOT SUBMIT' in report['submission_note']
    assert report['validator_output']['format_valid'] is True
    assert report['validator_output']['official_format_compliant'] is False
    assert report['holdout_dti']['label'] == 'HOLDOUT-DTI'
    assert report['selector']['decision'] == 'DO_NOT_SUBMIT'
    from gems.executive_decisions import build_decisions
    packet = build_decisions(ROOT, report)
    assert len(packet['rows']) == 9
    assert all(row['ok_to_submit'] is False for row in packet['rows'])
    assert all(row['organizer_confirmed_score'] is None and row['leaderboard_estimate'] is None for row in packet['rows'])
    assert all(row['uniqueness'].startswith('PASS vs tracked raster only') for row in packet['rows'])
    assert packet['global_novelty'].startswith('FAIL vs pinned lattice')
    assert all(row['global_novelty'] == packet['global_novelty'] for row in packet['rows'])
