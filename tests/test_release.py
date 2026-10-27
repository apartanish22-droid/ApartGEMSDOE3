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
    assert max(x for x in c['overlap_vs_registry'].values() if x is not None) <= .70
    assert hashlib.sha256(TIF.read_bytes()).hexdigest() == c['raster_sha256']

def test_submission_is_strictly_finite_and_aligned():
    with rasterio.open(TIF) as s, rasterio.open(ROOT/'data/bridge/sample_submission.tif') as t:
        a=s.read(1)
        assert s.count == 1 and s.dtypes == ('float32',)
        assert (s.crs,s.shape,s.transform)==(t.crs,t.shape,t.transform)
        assert np.isfinite(a).all()
        assert a.min() >= 0 and a.max() <= 1
        assert np.count_nonzero(a) == 37654
