import hashlib
import json
from pathlib import Path

import numpy as np
import pytest
from scipy.ndimage import distance_transform_edt
from scipy.stats import spearmanr

from audit_priority import ROOT, binary_rho, git_blob_file, overlap_lower_bound, overlap_with_distance


def test_git_blob_uses_git_header(tmp_path):
    p = tmp_path / "x"
    p.write_bytes(b"abc\x00\xff")
    assert git_blob_file(p) == hashlib.sha1(b"blob 5\0abc\x00\xff", usedforsecurity=False).hexdigest()


def test_binary_tied_ranks_match_scipy_and_constant_is_unknown():
    a = np.array([0, 1, 0, 1, 1, 0, 0, 1])
    b = np.array([1, 1, 0, 1, 0, 0, 0, 1])
    assert binary_rho(int(a.sum()), int(b.sum()), int((a & b).sum()), len(a)) == pytest.approx(spearmanr(a, b).statistic)
    assert binary_rho(0, 1, 0, 8) is None
    with pytest.raises(ValueError):
        binary_rho(1, 1, 2, 8)


def test_exact_inclusive_three_pixel_overlap_and_empty_candidate():
    ref = np.zeros((8, 8), bool)
    ref[3, 3] = True
    candidate = np.zeros_like(ref)
    candidate[3, 6] = True  # distance exactly 3
    candidate[6, 6] = True  # distance sqrt(18), outside 3
    distance = distance_transform_edt(~ref)
    assert overlap_with_distance(candidate, distance) == .5
    assert overlap_with_distance(np.zeros_like(ref), distance) is None
    with pytest.raises(ValueError):
        overlap_with_distance(candidate[:2], distance)


def test_geometric_bound_uses_strict_greater_than_not_greater_equal():
    # Seven of ten must overlap: equality is not a stop under the requested rule.
    equal = overlap_lower_bound(10, 3)
    assert equal["minimum_overlap_fraction"] == .7
    assert equal["necessarily_exceeds_70_percent"] is False
    assert overlap_lower_bound(11, 3)["necessarily_exceeds_70_percent"] is True
    actual = overlap_lower_bound(37654, 6649)
    assert actual["minimum_overlap_dots"] == 31005
    assert actual["minimum_overlap_fraction"] == pytest.approx(0.8234184947150369)
    with pytest.raises(ValueError):
        overlap_lower_bound(0, 3)


def test_frozen_audit_is_consistent_and_never_approves():
    report = json.loads((ROOT / "evidence/historical_audit.json").read_text())
    assert len(report["artifacts"]) == 9
    pairs = report["pairwise_directional_comparisons"]
    assert len(pairs) == 72
    assert all(p["literal_duplicate"] for p in pairs)
    assert not any(a["ok_to_submit"] for a in report["artifacts"].values())
    assert report["submission_authorized"] is False
    assert report["new_rasters_generated"] == 0
    assert report["mirror_sample_label_contamination"]["sample_values_equal_labels_on_footprint"] is True
    assert report["lattice_geometry"]["outside_3px_footprint_pixels"] == 6649
    assert report["lineage"]["h33_equals_d28_after_removing_at_most_2px_from_mirrored_catalogue"]
    assert report["lineage"]["h33_new_dots_vs_d28"] == 0
    assert report["lineage"]["anderson_contains_all_h33_dots"]


def test_manifest_matches_checked_in_audit():
    manifest = json.loads((ROOT / "registry/focus_sites.json").read_text())
    audit = json.loads((ROOT / "evidence/historical_audit.json").read_text())
    assert len({row["site"] for row in manifest["sites"]}) == 9
    for row in manifest["sites"]:
        assert audit["artifacts"][row["site"]]["git_blob"] == row["git_blob"]
        assert audit["artifacts"][row["site"]]["estimated_organizer_score"] is None
        assert "receipt" in row["value_evidence"]
