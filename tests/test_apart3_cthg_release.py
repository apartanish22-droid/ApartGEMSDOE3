from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

import numpy as np
import rasterio

from gems32 import cthg
from gems32.paths import ROOT

FILENAME = "apartgemsdoe3-h-apart3-2-cthg-dhc-37654-20261028T084500Z-5d4d0085-zeros.tif"
SHA256 = "9d5cab2ed8b393cd509c196961481520772bee5b1791e322e0b15cdbba696112"


def test_cthg_stack_contract_and_lidar_free_columns() -> None:
    assert len(cthg.CTHG_EXTRA_CHANNELS) == 6
    assert len(set(cthg.CTHG_EXTRA_CHANNELS)) == 6
    assert cthg.CTHG_EXTRA_CHANNELS[0] == "cooper_cowan_tilt_phase_wall"
    assert len(cthg.CTHG_MSUB_COL_INDICES) == 87
    assert len(set(cthg.CTHG_MSUB_COL_INDICES)) == 87
    assert min(cthg.CTHG_MSUB_COL_INDICES) >= 0


def test_cthg_builders_and_post_sharpened_emitter_are_bounded() -> None:
    rng = np.random.default_rng(20261028)
    h = w = 56
    foot = np.ones((h, w), dtype=bool)
    vis = np.zeros((h, w), dtype=bool)
    vis[5:8, :] = True
    region = np.zeros_like(foot)
    region[8:-4, :] = True
    p = rng.random((h, w), dtype=np.float32)
    cb = rng.random((h, w), dtype=np.float32)
    pd = rng.random((h, w), dtype=np.float32)
    dots, report = cthg.emit_cthg_post_moat_dhc(
        p, pd, cb, vis, foot, foot,
        np.maximum(2.1, np.ones((h, w), dtype=np.float32) * 7.0),
        budget=24, f_stage1=0.63, min_sep_px=3.24,
    )
    assert dots.shape == foot.shape
    assert int(dots.sum()) == 24
    assert report["budget_total"] == 24
    assert report["min_sep_px"] == 3.24
    assert np.isfinite(dots).all()

    stack = rng.random((h, w, 6), dtype=np.float32)
    cfkc_stack = rng.random((h, w, 8), dtype=np.float32)
    bhgc_stack = rng.random((h, w, 6), dtype=np.float32)
    trhv_stack = rng.random((h, w, 8), dtype=np.float32)
    conduit = cthg.build_cthg_off_catalogue_surface(cfkc_stack, bhgc_stack, stack, trhv_stack, foot)
    assert conduit.shape == foot.shape
    assert np.isfinite(conduit).all()
    assert float(conduit.min()) >= 0.0 and float(conduit.max()) <= 1.0


def test_cthg_candidate_format_and_fail_closed_upload_status() -> None:
    tif = ROOT / "docs" / "downloads" / FILENAME
    assert tif.is_file()
    assert hashlib.sha256(tif.read_bytes()).hexdigest() == SHA256
    zip_path = tif.with_name(tif.name + ".zip")
    assert zip_path.is_file()
    with zipfile.ZipFile(zip_path) as zf:
        members = [n for n in zf.namelist() if n.lower().endswith((".tif", ".tiff"))]
        assert len(members) == 1
        assert zf.testzip() is None
    with rasterio.open(tif) as ds:
        assert ds.count == 1
        assert ds.shape == (3730, 3292)
        assert ds.crs.to_string() == "EPSG:32611"
        assert ds.transform.to_gdal() == (243350.0, 100.0, 0.0, 4508550.0, 0.0, -100.0)
        assert ds.dtypes[0] == "float32"
        assert ds.nodata is None
        a = ds.read(1)
        assert np.isfinite(a).all()
        assert float(a.min()) >= 0.0 and float(a.max()) <= 1.0
        assert int((a > 0.5).sum()) == 37654

    card = json.loads((ROOT / "evidence" / "apart3_cthg_dhc_run_card.json").read_text())
    assert card["raster_sha256"] == SHA256
    assert card["validator"]["finite"] is True
    assert card["validator"]["range_0_1"] is True
    assert card["validator"]["crs_match"] is True
    assert card["validator"]["shape_match"] is True
    assert card["validator"]["transform_match"] is True
    assert card["duplicate_gate_failure"]["final_dots_literal_gate_passed"] is False
    assert card["scientific_integrity_gate"]["passed"] is False
    assert card["scientific_integrity_gate"]["irregularity_id"] == "IR-CTHG-BAND6-TC-02"
    assert card["ok_to_submit"] is False
    assert card["selector_required"] is True
    assert card["protocol_budget_audit"]["compliant"] is False
    assert card["verdict"] == "negative"
