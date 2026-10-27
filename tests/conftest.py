"""Small local fixtures; the test suite never downloads or submits a TIFF."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "vendor"))
from template_utils import verify_template  # noqa: E402
verify_template()


def write_tif(path, array, *, transform, crs="EPSG:32611", nodata=None, count=1):
    array = np.asarray(array)
    with rasterio.open(path, "w", driver="GTiff", height=array.shape[0],
                       width=array.shape[1], count=count, dtype=array.dtype,
                       crs=crs, transform=transform, nodata=nodata) as dst:
        for i in range(1, count + 1):
            dst.write(array, i)
    return path


@pytest.fixture
def tiny_grid(tmp_path, monkeypatch):
    import validate_submission as checker
    from gems57 import validate

    root = tmp_path / "project"
    cache = tmp_path / "inputs"
    (root / "registry").mkdir(parents=True)
    cache.mkdir()
    shape = (8, 9)
    transform = from_origin(243350, 4508550, 100, 100)
    footprint = np.zeros(shape, bool)
    footprint[1:7, 1:8] = True
    sample = np.where(footprint, 0, np.nan).astype(np.float32)
    catalogue = np.zeros(shape, np.float32)
    catalogue[2, 2] = 1
    write_tif(cache / "sample.tif", sample, transform=transform, nodata=np.nan)
    write_tif(cache / "labels.tif", catalogue, transform=transform)
    records = []
    for ident in ("sample", "labels"):
        filename = f"{ident}.tif"
        digest = hashlib.sha256((cache / filename).read_bytes()).hexdigest()
        records.append({"id": ident, "destination": filename, "sha256": digest})
    (root / "registry/input_manifest.json").write_text(json.dumps({"files": records}))
    monkeypatch.setattr(checker, "ROOT", root)
    monkeypatch.setattr(validate, "HEIGHT", shape[0])
    monkeypatch.setattr(validate, "WIDTH", shape[1])
    monkeypatch.setattr(validate, "TRANSFORM", transform)
    result = np.zeros(shape, np.float32)
    result[3, 3] = .8
    return {"root": root, "cache": cache, "shape": shape, "transform": transform,
            "footprint": footprint, "catalogue": catalogue, "prediction": result,
            "path": tmp_path / "prediction.tif"}
