import hashlib, json
from pathlib import Path
import numpy as np
import rasterio

ROOT=Path(__file__).parents[1]
CARD=ROOT/'evidence/run_card.json'
TIF=ROOT/'docs/downloads/apartgems3-mrcj-curvature-junction-37654-20261027-zeros.tif'

def test_run_card_and_bytes_agree():
    c=json.loads(CARD.read_text())
    assert c['experiments_run'] <= c['budget_limit'] == 3
    assert c['feature_leakage_canary']['passed']
    assert c['feature_leakage_canary']['worst_pooled_auc'] <= .90
    assert max(abs(x) for x in c['correlation_vs_registry'].values() if x is not None) <= .90
    # The old comparison against the nine sites was incomplete: the separate
    # lattice witness is decisive and must override the historical promotion.
    nine = {k: v for k, v in c['overlap_vs_registry'].items() if k.startswith('GEMSDOE')}
    assert len(nine) == 9 and max(nine.values()) <= .70
    assert c['overlap_vs_registry']['registered_calibration_lattice'] == 1.0
    assert c['verdict'] == 'negative' and c['ok_to_submit'] is False
    assert c['approved_for_weekly_slot'] is False
    assert hashlib.sha256(TIF.read_bytes()).hexdigest() == c['raster_sha256']

def test_submission_is_strictly_finite_and_aligned():
    with rasterio.open(TIF) as s, rasterio.open(ROOT/'data/bridge/sample_submission.tif') as t:
        a=s.read(1)
        assert s.count == 1 and s.dtypes == ('float32',)
        assert (s.crs,s.shape,s.transform)==(t.crs,t.shape,t.transform)
        assert np.isfinite(a).all()
        assert a.min() >= 0 and a.max() <= 1
        assert np.count_nonzero(a) == 37654


def test_current_decision_rejects_historical_promotion_and_preserves_receipt():
    audit = json.loads((ROOT / 'evidence/mrcj_audit.json').read_text())
    old = json.loads((ROOT / 'evidence/mrcj_original_run_card.json').read_text())
    current = json.loads(CARD.read_text())
    assert old['verdict'] == 'promote' and old['ok_to_submit'] is True  # archived source claim
    assert current['verdict'] == 'negative' and current['ok_to_submit'] is False
    assert audit['candidate_sha256'] == current['raster_sha256'] == old['raster_sha256']
    assert audit['three_pixel_overlap_count'] == audit['candidate_in_footprint_dots'] == 37654
    assert audit['three_pixel_overlap_fraction'] == 1.0 and audit['duplicate_by_overlap']
    assert len(audit['historical_comparisons']) == 9
    assert max(r['candidate_dot_overlap_within_3px'] for r in audit['historical_comparisons']) < .70
    assert audit['complete_registry_checked'] is False
    assert 'DO NOT SUBMIT' in current['submission_note'] and len(current['submission_note']) <= 140


def test_archived_experiment_runner_stops_before_overwriting():
    import subprocess, sys
    before = hashlib.sha256(TIF.read_bytes()).hexdigest()
    card_before = hashlib.sha256(CARD.read_bytes()).hexdigest()
    p = subprocess.run([sys.executable, str(ROOT/'scripts/run_experiments.py')],
                       capture_output=True, text=True, timeout=20)
    assert p.returncode != 0 and 'STOP: archived MRCJ runner' in p.stderr
    assert hashlib.sha256(TIF.read_bytes()).hexdigest() == before
    assert hashlib.sha256(CARD.read_bytes()).hexdigest() == card_before
