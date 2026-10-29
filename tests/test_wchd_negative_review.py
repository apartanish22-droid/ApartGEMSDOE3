"""An exploratory format-valid raster is not an authorized submission."""
import hashlib
import json
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]


def test_wchd_literal_failure_and_saved_bytes():
    card = json.loads((ROOT / 'evidence/wchd_run_card.json').read_text())
    recheck = json.loads((ROOT / 'evidence/wchd_literal_recheck.json').read_text())['results'][0]
    path = ROOT / card['artifact']
    assert hashlib.sha256(path.read_bytes()).hexdigest() == card['raster_sha256'] == recheck['candidate_sha256']
    assert card['verdict'] == 'negative' and card['ok_to_submit'] is False
    assert card['selector_required'] is True and card['slot_used'] is False
    assert card['correlation_vs_registry']['literal_all_rasters_final_passed'] is False
    assert recheck['literal_dot_gate_passed'] is False and recheck['directional_within_3px'] > .70
    assert recheck['format']['passed'] is True
    with rasterio.open(path) as ds:
        assert ds.count == 1
        values = ds.read(1)
        assert np.isfinite(values).all()
        assert values.min() >= 0 and values.max() <= 1


def test_public_pages_keep_wchd_research_only():
    for page in ('docs/index.html', 'docs/executive-summary.html', 'docs/release-status.html'):
        text = (ROOT / page).read_text()
        assert 'WCHD research artifact — DO NOT SUBMIT' in text
        assert 'Download GeoTIFF for research only' in text
        assert '99.56%' in text
