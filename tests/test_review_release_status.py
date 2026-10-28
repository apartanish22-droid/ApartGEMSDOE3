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
    for page in ['index.html', 'docs/index.html', 'docs/executive-summary.html', 'docs/executive-summary/index.html', 'docs/submissions.html']:
        text = (ROOT / page).read_text()
        assert 'DO NOT SUBMIT' in text
        assert 'PROMOTE — DOWNLOAD' not in text


def test_release_check_rejects_inconsistent_gate(tmp_path, monkeypatch):
    card = json.loads((ROOT / 'run_card.json').read_text())
    card['release_gate_decision']['gates']['final'] = True
    (tmp_path / 'run_card.json').write_text(json.dumps(card))
    monkeypatch.setattr(module, 'ROOT', tmp_path)
    with pytest.raises(SystemExit, match='failed release gates'):
        module.main()
