import hashlib, json
from pathlib import Path
import numpy as np
import rasterio

ROOT=Path(__file__).parents[1]
CARD=ROOT/'evidence/run_card.json'
ARCHIVE=ROOT/'evidence/parallel_mrcj_original.json'
TIF=ROOT/'docs/downloads/apartgems3-mrcj-curvature-junction-37654-20261027-zeros.tif'

def test_run_card_and_bytes_agree():
    current=json.loads(CARD.read_text())
    historical=json.loads(ARCHIVE.read_text())
    assert historical['experiments_run'] <= historical['budget_limit'] == 3
    assert historical['feature_leakage_canary']['passed']
    assert historical['feature_leakage_canary']['worst_pooled_auc'] <= .90
    assert max(abs(x) for x in historical['correlation_vs_registry'].values() if x is not None) <= .90
    assert max(x for x in historical['overlap_vs_registry'].values() if x is not None) <= .70
    # Those nine-only results do not waive the independent lattice failure.
    assert current['verdict'] == 'negative' and current['ok_to_submit'] is False
    assert current['correlation_overlap_vs_registry']['final_dots_lattice_overlap'] == 1.0
    assert hashlib.sha256(TIF.read_bytes()).hexdigest() == current['raster_sha256'] == historical['raster_sha256']

def test_submission_is_strictly_finite_and_aligned():
    with rasterio.open(TIF) as s, rasterio.open(ROOT/'data/bridge/sample_submission.tif') as t:
        a=s.read(1)
        assert s.count == 1 and s.dtypes == ('float32',)
        assert (s.crs,s.shape,s.transform)==(t.crs,t.shape,t.transform)
        assert np.isfinite(a).all()
        assert a.min() >= 0 and a.max() <= 1
        assert np.count_nonzero(a) == 37654

def test_current_review_rechecks_focus_registry_and_stays_negative():
    from gems.current_review import review_current_best

    report = review_current_best(ROOT)
    assert report['verdict'] == 'negative'
    assert report['ok_to_submit'] is False
    assert report['ok_to_download_for_research'] is True
    assert report['novel_vs_each_focus_raster_under_thresholds'] is True
    assert report['focus_registry_count'] == 9
    assert report['external_registry_hazard']['conditional_minimum_candidate_overlap'] > 0.70
    assert report['external_registry_hazard']['measured_candidate_overlap'] == 1.0
    assert report['validator_output']['format_valid'] is True
    assert report['validator_output']['official_format_compliant'] is False
    assert report['holdout_dti']['label'] == 'HOLDOUT-DTI'
    assert report['selector']['decision'] == 'DO_NOT_SUBMIT'

    from gems.executive_decisions import build_decisions
    packet = build_decisions(ROOT, report)
    assert len(packet['rows']) == 9
    assert all(row['ok_to_submit'] is False for row in packet['rows'])
    assert all(row['organizer_confirmed_score'] is None for row in packet['rows'])
    assert all(row['leaderboard_estimate'] is None for row in packet['rows'])
    assert all(row['uniqueness'].startswith('PASS vs tracked raster only') for row in packet['rows'])
