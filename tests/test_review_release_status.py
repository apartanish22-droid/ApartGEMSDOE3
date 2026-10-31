"""Safety regressions: don't re-promote historical duplicate rasters."""
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('review_status', ROOT / 'scripts/check_release_status.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_current_card_and_portal_fail_closed():
    assert module.main() is None
    card = json.loads((ROOT / 'run_card.json').read_text())
    assert card['verdict'] == 'negative'
    assert card['correlation_vs_registry']['literal_all_rasters_final_passed'] is False
    assert card['release_gate_decision']['gates']['final'] is False
    status = json.loads((ROOT / 'registry/current_status.json').read_text())
    current = status['current_candidate']
    for page in ['index.html', 'docs/index.html', 'docs/executive-summary.html', 'docs/executive-summary/index.html', 'docs/submissions.html']:
        text = (ROOT / page).read_text()
        assert 'DO NOT SUBMIT' in text
        assert 'PROMOTE — DOWNLOAD' not in text
        assert current['candidate_id'] in text
        assert current['sha256'] in text
    summary = (ROOT / 'docs/executive-summary.html').read_text()
    assert 'H1-LIDAR-SCARP-DEM-CHI' in summary
    assert 'gemsdoe32-h1-lidar-scarp-dem-chi-20261031T044640Z-6660ab7a-zeros.tif' in summary
    assert '0.0062' in summary
    assert 'HOLDOUT-DTI' in summary
    assert 'Historical CSHD:' not in summary
    latest = json.loads((ROOT / 'docs/data/latest-run-card.json').read_text())
    assert latest['candidate_id'] == current['candidate_id']
    site_data = json.loads((ROOT / 'docs/assets/site-data.json').read_text())
    assert site_data['run_card']['candidate_id'] == current['candidate_id']
    feed = json.loads((ROOT / 'docs/data/feed.json').read_text())
    assert feed['current_candidate']['run_card'] == 'evidence/H1-LIDAR-SCARP-DEM-CHI_run_card.json'


def test_release_check_rejects_inconsistent_gate(tmp_path, monkeypatch):
    card = json.loads((ROOT / 'run_card.json').read_text())
    card['release_gate_decision']['gates']['final'] = True
    (tmp_path / 'run_card.json').write_text(json.dumps(card))
    monkeypatch.setattr(module, 'ROOT', tmp_path)
    with pytest.raises(SystemExit, match='final-dot uniqueness failure'):
        module.main()
