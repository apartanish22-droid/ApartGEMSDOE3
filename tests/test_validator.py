from __future__ import annotations

import hashlib
import json

import numpy as np
import pytest
from rasterio.transform import Affine

import validate_submission as checker
from conftest import write_tif


def test_valid_file_only_passes_local_format_gate(tiny_grid):
    f = tiny_grid
    write_tif(f["path"], f["prediction"], transform=f["transform"])
    report = checker.check(f["path"], f["cache"])
    assert report["format_passed"] is True
    assert report["sha256"] == hashlib.sha256(f["path"].read_bytes()).hexdigest()
    assert report["local"]["checks"]["in_footprint_all_finite"]
    assert report["local"]["checks"]["in_footprint_range_0_1"]
    assert report["template"]["crs"] == "EPSG:32611"
    assert report["approved_for_weekly_slot"] is False
    assert report["verdict"] == "negative"
    assert not report["uniqueness_checked"] and not report["holdout_checked"]
    json.dumps(report, allow_nan=False)


def test_nan_nodata_is_a_structured_failure_not_a_json_crash(tiny_grid, tmp_path, capsys):
    f = tiny_grid
    write_tif(f["path"], f["prediction"], transform=f["transform"], nodata=float("nan"))
    out = tmp_path / "receipt.json"
    assert checker.main([str(f["path"]), "--cache", str(f["cache"]), "--out", str(out)]) == 1
    report = json.loads(out.read_text(), parse_constant=lambda value: pytest.fail(f"invalid JSON: {value}"))
    assert report["format_passed"] is False
    assert report["local"]["meta"]["nodata"] == "NaN"
    assert "nodata tag" in " ".join(report["template"]["problems"])
    assert report["approved_for_weekly_slot"] is False
    assert capsys.readouterr().out


def test_nonfinite_diagnostics_are_not_silently_lost():
    result = checker.json_safe({"x": [np.float32(np.nan), np.float64(np.inf), -np.inf]})
    assert result == {"x": ["NaN", "Infinity", "-Infinity"]}
    assert json.loads(json.dumps(result, allow_nan=False)) == result


@pytest.mark.parametrize("variant", ["nan_inside", "positive_infinity", "above_one", "sentinel", "outside", "catalogue", "wrong_crs", "wrong_transform", "two_bands", "float64"])
def test_invalid_saved_bytes_fail_closed(tiny_grid, variant):
    f = tiny_grid
    data = f["prediction"].copy()
    opts = {"transform": f["transform"]}
    if variant == "nan_inside":
        data[3, 4] = np.nan
    elif variant == "positive_infinity":
        data[3, 4] = np.inf
    elif variant == "above_one":
        data[3, 4] = 1.001
    elif variant == "sentinel":
        data[3, 4] = -9999
    elif variant == "outside":
        data[0, 0] = 1
    elif variant == "catalogue":
        data[2, 2] = 1
    elif variant == "wrong_crs":
        opts["crs"] = "EPSG:32612"
    elif variant == "wrong_transform":
        opts["transform"] = f["transform"] * Affine.translation(1, 0)
    elif variant == "two_bands":
        opts["count"] = 2
    elif variant == "float64":
        data = data.astype(np.float64)
    write_tif(f["path"], data, **opts)
    report = checker.check(f["path"], f["cache"])
    assert report["format_passed"] is False
    assert report["approved_for_weekly_slot"] is False
    json.dumps(report, allow_nan=False)


def test_references_are_verified_before_validation(tiny_grid):
    f = tiny_grid
    write_tif(f["path"], f["prediction"], transform=f["transform"])
    (f["cache"] / "sample.tif").write_bytes(b"tampered")
    with pytest.raises(ValueError, match="hash-mismatched sample"):
        checker.check(f["path"], f["cache"])


def test_missing_tiff_fails_without_a_pass_receipt(tiny_grid, tmp_path, capsys):
    out = tmp_path / "not-written.json"
    assert checker.main([str(tiny_grid["path"]), "--cache", str(tiny_grid["cache"]), "--out", str(out)]) == 1
    assert not out.exists()
    assert "FORMAT CHECK FAILED" in capsys.readouterr().err
