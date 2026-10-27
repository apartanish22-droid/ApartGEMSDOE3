"""The review must not silently treat missing/stale geometry as a pass."""
import json
from pathlib import Path

from gems.current_review import _recorded_lattice_audit

ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_SHA = 'fb4400e342e8aab8b059e067cfac8b2225b48534e46800d6efe69c2f2d9403d1'


def test_recorded_lattice_witness_is_bound_to_actual_candidate_and_grid():
    witness = _recorded_lattice_audit(ROOT, CANDIDATE_SHA, 37654)
    assert witness['overlapping_dots'] == witness['candidate_dots'] == 37654
    assert witness['overlap_fraction'] == 1.0 and witness['duplicate_by_overlap'] is True
    assert witness['complete_registry_checked'] is False
    assert 'not rerun' in witness['status']


def test_stale_or_missing_lattice_witness_never_becomes_a_pass(tmp_path):
    assert _recorded_lattice_audit(tmp_path, CANDIDATE_SHA, 37654)['duplicate_by_overlap'] is None
    assert _recorded_lattice_audit(ROOT, '0' * 64, 37654)['duplicate_by_overlap'] is None
    assert _recorded_lattice_audit(ROOT, CANDIDATE_SHA, 37653)['duplicate_by_overlap'] is None
