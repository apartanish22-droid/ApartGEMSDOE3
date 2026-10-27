import json
import os
import sys

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

import inspect_submission
from audit_priority import ROOT
from inspect_submission import inspect, validate_output_path


def shared_root():
    manifest = json.loads((ROOT / "registry/shared_template.json").read_text())
    root = ROOT / ".cache/shared_template" / manifest["ref"]
    if not root.exists():
        pytest.skip("Shared template cache absent")
    return root


def write_tif(path, values, nodata=None, mask=None):
    with rasterio.Env(GDAL_TIFF_INTERNAL_MASK=True):
        with rasterio.open(path, "w", driver="GTiff", height=values.shape[0], width=values.shape[1], count=1,
                           dtype="float32", crs="EPSG:32611", transform=from_origin(0, 600, 100, 100), nodata=nodata) as ds:
            ds.write(values.astype("float32"), 1)
            if mask is not None:
                ds.write_mask(mask.astype("uint8") * 255)


def test_nan_and_zero_exterior_have_distinct_diagnostics(tmp_path):
    root = shared_root()
    fp = np.zeros((6, 6), bool)
    fp[1:5, 1:5] = True
    template = np.where(fp, 0, np.nan).astype("float32")
    candidate = np.where(fp, .4, np.nan).astype("float32")
    tp, cp = tmp_path / "template.tif", tmp_path / "candidate.tif"
    write_tif(tp, template, nodata=np.nan)
    write_tif(cp, candidate, nodata=np.nan)
    r = inspect(cp, tp, root)
    assert r["diagnostics"]["inside_all_finite_and_in_0_1"]
    assert r["diagnostics"]["outside_null_or_nan_relative_to_template"]
    assert not r["diagnostics"]["strict_raw_full_array_finite_0_1_diagnostic"]
    # Synthetic grid is intentionally not the shared pinned organizer-like grid.
    assert r["passes_local_textual_checks"] is False
    assert r["ok_to_submit"] is False
    write_tif(cp, np.where(fp, .4, 0))
    r = inspect(cp, tp, root)
    assert r["diagnostics"]["strict_raw_full_array_finite_0_1_diagnostic"]
    assert not r["diagnostics"]["outside_null_or_nan_relative_to_template"]
    assert r["ok_to_submit"] is False


def test_valid_raw_values_and_internal_null_mask_are_separate(tmp_path):
    root = shared_root()
    fp = np.zeros((6, 6), bool)
    fp[1:5, 1:5] = True
    tp, cp = tmp_path / "template.tif", tmp_path / "masked.tif"
    write_tif(tp, np.where(fp, 0, np.nan), nodata=np.nan)
    write_tif(cp, np.where(fp, .5, 0), mask=fp)
    r = inspect(cp, tp, root)
    assert r["diagnostics"]["strict_raw_full_array_finite_0_1_diagnostic"]
    assert r["diagnostics"]["outside_null_or_nan_relative_to_template"]
    assert r["diagnostics"]["inside_no_masked_pixels"]
    assert r["ok_to_submit"] is False  # no science or selector
    mask = fp.copy()
    mask[2, 2] = False
    write_tif(cp, np.where(fp, .5, 0), mask=mask)
    r = inspect(cp, tp, root)
    assert not r["diagnostics"]["inside_no_masked_pixels"]


def test_finite_but_masked_template_exterior_is_not_treated_as_footprint(tmp_path):
    root = shared_root()
    fp = np.zeros((6, 6), bool)
    fp[1:5, 1:5] = True
    tp, cp = tmp_path / "template.tif", tmp_path / "candidate.tif"
    write_tif(tp, np.zeros((6, 6)), mask=fp)
    write_tif(cp, np.where(fp, .5, 0))  # zeros outside are not marked null
    r = inspect(cp, tp, root)
    assert r["diagnostics"]["inside_all_finite_and_in_0_1"]
    assert not r["diagnostics"]["outside_null_or_nan_relative_to_template"]
    assert not r["passes_local_textual_checks"]
    assert not r["ok_to_submit"]


def test_invalid_interior_is_never_sanitized(tmp_path):
    root = shared_root()
    fp = np.zeros((6, 6), bool)
    fp[1:5, 1:5] = True
    tp, cp = tmp_path / "template.tif", tmp_path / "bad.tif"
    write_tif(tp, np.where(fp, 0, np.nan), nodata=np.nan)
    for bad in (1.1, -0.1, np.nan, np.inf):
        arr = np.where(fp, .5, np.nan).astype("float32")
        arr[2, 2] = bad
        write_tif(cp, arr, nodata=np.nan)
        r = inspect(cp, tp, root)
        assert not r["diagnostics"]["inside_all_finite_and_in_0_1"]
        assert not r["ok_to_submit"]


def test_changing_file_during_inspection_is_an_error(tmp_path, monkeypatch):
    root = shared_root()
    tp, cp = tmp_path / "template.tif", tmp_path / "candidate.tif"
    write_tif(tp, np.ones((6, 6)))
    write_tif(cp, np.zeros((6, 6)))
    changing = iter(["candidate-before", "template-before", "candidate-after"])
    monkeypatch.setattr(inspect_submission, "sha256_file", lambda _: next(changing))
    with pytest.raises(ValueError, match="changed during inspection"):
        inspect(cp, tp, root)


def test_report_never_overwrites_input_or_hardlink(tmp_path):
    candidate = tmp_path / "candidate.json"
    candidate.write_text("unchanged")
    with pytest.raises(ValueError):
        validate_output_path(candidate, (candidate,))
    alias = tmp_path / "alias.json"
    os.link(candidate, alias)
    with pytest.raises(ValueError):
        validate_output_path(alias, (candidate,))
    with pytest.raises(ValueError):
        validate_output_path(tmp_path / "report.tif", (candidate,))
    validate_output_path(tmp_path / "report.json", (candidate,))
    assert candidate.read_text() == "unchanged"
