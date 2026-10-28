"""Regression tests for a fail-closed partial release review."""
from pathlib import Path
import importlib.util
import json

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('audit_release', ROOT / 'scripts/audit_release.py')
audit_release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit_release)


def write_raster(path, array, transform=None):
    with rasterio.open(path, 'w', driver='GTiff', width=array.shape[1], height=array.shape[0],
                       count=1, dtype='float32', crs='EPSG:32611',
                       transform=transform or from_origin(0, 1000, 100, 100)) as dst:
        dst.write(array.astype('float32'), 1)


def test_overlap_is_directional_and_never_authorizes(tmp_path):
    template, ref, candidate = (tmp_path / n for n in ('template.tif', 'ref.tif', 'candidate.tif'))
    values = np.zeros((10, 10), dtype='float32')
    write_raster(template, values)
    r = values.copy(); r[4, 4] = 1
    write_raster(ref, r)
    c = values.copy(); c[4, 4] = 1; c[9, 9] = 1
    write_raster(candidate, c)
    report = audit_release.audit(template, ref, candidate)
    assert report['directional_within_3px'] == .5
    assert report['literal_dot_gate_passed'] is True
    assert report['ok_to_submit'] is False
    assert report['format']['passed'] is True
    c[4, 5] = 1
    write_raster(candidate, c)
    assert audit_release.audit(template, ref, candidate)['literal_dot_gate_passed'] is True  # 2/3
    c[5, 4] = 1
    write_raster(candidate, c)
    assert audit_release.audit(template, ref, candidate)['literal_dot_gate_passed'] is False  # 3/4


def test_misaligned_or_invalid_candidate_fails_closed(tmp_path):
    template, ref, candidate = (tmp_path / n for n in ('template.tif', 'ref.tif', 'candidate.tif'))
    a = np.zeros((10, 10), dtype='float32'); a[4, 4] = 1
    write_raster(template, a); write_raster(candidate, a)
    write_raster(ref, a, from_origin(100, 1000, 100, 100))
    with pytest.raises(ValueError, match='grid'):
        audit_release.audit(template, ref, candidate)
    write_raster(ref, a)
    a[0, 0] = np.nan; write_raster(candidate, a)
    with pytest.raises(ValueError, match='nonfinite'):
        audit_release.audit(template, ref, candidate)


def test_site_and_run_card_are_fail_closed():
    card = json.loads((ROOT / 'run_card.json').read_text())
    assert card['verdict'] == 'negative' and card['ok_to_submit'] is False
    for p in ['index.html', 'docs/index.html', 'docs/executive-summary.html', 'docs/submissions.html']:
        page = (ROOT / p).read_text()
        assert 'DO NOT SUBMIT' in page
        assert 'NO FILE AUTHORIZED' in page
        assert 'READY TO DOWNLOAD AND SUBMIT' not in page
