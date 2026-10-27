from __future__ import annotations

import hashlib
import json

import numpy as np
import pytest

import audit_candidate
from conftest import write_tif


@pytest.mark.parametrize("lattice_xy,duplicate", [((3, 4), True), ((6, 7), False)])
def test_one_witness_audit_is_always_fail_closed(tiny_grid, monkeypatch, lattice_xy, duplicate):
    f = tiny_grid
    manifest_path = f["root"] / "registry/input_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    lattice = np.zeros(f["shape"], np.float32); lattice[lattice_xy] = 1
    lattice_path = write_tif(f["cache"] / "lattice.tif", lattice, transform=f["transform"])
    manifest["files"].append({"id": "lattice", "destination": "lattice.tif",
        "repo": "owner/repo", "ref": "a" * 40, "path": "lattice.tif",
        "sha256": hashlib.sha256(lattice_path.read_bytes()).hexdigest()})
    manifest_path.write_text(json.dumps(manifest))
    write_tif(f["path"], f["prediction"], transform=f["transform"])
    monkeypatch.setattr(audit_candidate, "ROOT", f["root"])
    report = audit_candidate.run(f["path"], f["cache"], "synthetic fixture")
    assert report["candidate_in_footprint_dots"] == 1
    assert report["duplicate_by_overlap"] is duplicate
    assert report["three_pixel_overlap_fraction"] == float(duplicate)
    assert report["format"]["local_format_passed"] is True
    assert report["complete_registry_checked"] is False
    assert report["surface_rank_correlation"] is None
    assert report["approved_for_weekly_slot"] is False and report["verdict"] == "negative"
    json.dumps(report, allow_nan=False)
