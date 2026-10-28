import copy
import importlib.util
import json
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('status_check',ROOT/'scripts/check_release_status.py')
status=importlib.util.module_from_spec(spec);spec.loader.exec_module(status)

def test_legacy_promotion_cannot_exempt_dense_registry():
    card=json.loads((ROOT/'run_card.json').read_text())
    status.check(card)
    forged=copy.deepcopy(card)
    forged['verdict']='promote'
    forged['release_gate_decision']['verdict']='promote'
    forged['release_gate_decision']['gates']['final']=True
    with pytest.raises(ValueError,match='literal'):
        status.check(forged)

def test_rechecked_bytes_are_bound_to_current_card():
    card=json.loads((ROOT/'run_card.json').read_text())
    review=json.loads((ROOT/'evidence/session_literal_review_20261028.json').read_text())['results'][0]
    assert review['candidate_sha256']==card['raster_sha256']
    assert review['directional_within_3px']>.70
    assert review['literal_dot_gate_passed'] is False
    assert review['format']['passed'] is True
