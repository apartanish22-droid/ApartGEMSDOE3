from __future__ import annotations

import hashlib
import json
import zipfile

import numpy as np
import pytest

from gems57 import grid, submission_writer


@pytest.fixture
def tiny_writer(tiny_grid, monkeypatch):
    f = tiny_grid
    monkeypatch.setattr(grid, "SHAPE", f["shape"])
    monkeypatch.setattr(grid, "HEIGHT", f["shape"][0])
    monkeypatch.setattr(grid, "WIDTH", f["shape"][1])
    monkeypatch.setattr(grid, "TRANSFORM", f["transform"])
    return f


def test_writer_roundtrip_is_local_validation_not_slot_selection(tiny_writer, tmp_path):
    f = tiny_writer
    output = tmp_path / "synthetic-test.tif"
    receipt = submission_writer.write_submission(output, f["prediction"], f["cache"] / "sample.tif",
        f["footprint"], catalogue=f["catalogue"] > 0, name="SYNTHETIC-TEST", note="Synthetic fixture only")
    assert output.exists() and receipt["validator"]["all_checks_passed"]
    assert receipt["sha256"] == hashlib.sha256(output.read_bytes()).hexdigest()
    assert receipt["approved_for_weekly_slot"] is False and receipt["promoted"] is False
    with zipfile.ZipFile(output.with_suffix(".zip")) as archive:
        assert archive.namelist() == [output.name] and archive.read(output.name) == output.read_bytes()
    assert json.loads(output.with_suffix(".json").read_text())["sha256"] == receipt["sha256"]
    with pytest.raises(FileExistsError):
        submission_writer.write_submission(output, f["prediction"], f["cache"] / "sample.tif",
            f["footprint"], name="SYNTHETIC-TEST", note="Synthetic fixture only")


@pytest.mark.parametrize("variant", ["nan", "out_of_range", "outside", "catalogue", "long_note"])
def test_writer_rejects_instead_of_repairing_and_creates_no_files(tiny_writer, tmp_path, variant):
    f = tiny_writer
    prediction = f["prediction"].copy(); note = "Synthetic fixture"
    if variant == "nan": prediction[3, 4] = np.nan
    if variant == "out_of_range": prediction[3, 4] = 1.001
    if variant == "outside": prediction[0, 0] = 1
    if variant == "catalogue": prediction[2, 2] = 1
    if variant == "long_note": note = "x" * 141
    path = tmp_path / "should-not-exist.tif"
    with pytest.raises(ValueError):
        submission_writer.write_submission(path, prediction, f["cache"] / "sample.tif", f["footprint"],
            catalogue=f["catalogue"] > 0, name="SYNTHETIC", note=note)
    assert not path.exists() and not path.with_suffix(".zip").exists() and not path.with_suffix(".json").exists()
