"""End-to-end automated release & protocol tests for ApartGEMSDOE3 H-APART3-3 (WCHD)."""
from __future__ import annotations

import hashlib
import inspect
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import rasterio

from gems32 import bhgc, wchd

ROOT = Path(__file__).resolve().parents[1]
PRIMARY_FILENAME = "apartgemsdoe3-h3-wchd-dual104-axial388-37654-20261028T224500Z-b3dbc603-zeros.tif"
PRIMARY_TIF = ROOT / "docs" / "downloads" / PRIMARY_FILENAME
MIRROR_TIF = ROOT / "submission" / PRIMARY_FILENAME
CANONICAL_ZEROS = ROOT / "docs" / "downloads" / "gemsdoe32-apart3-wchd-dual104-axial388-37654-20261028T224500Z-b3dbc603-zeros.tif"
CANONICAL_ZIP = ROOT / "docs" / "downloads" / "gemsdoe32-apart3-wchd-dual104-axial388-37654-20261028T224500Z-b3dbc603-zeros.zip"
EXPECTED_SHA256 = "11f698c3c3f342029a1aa44d805d49b366a6a7724c178025d09790b47152a9dc"


def _strict_json_load(path: Path) -> dict:
    def _forbid_nan(val: str) -> None:
        raise ValueError(f"Non-RFC8259 constant {val!r} in {path}")

    return json.loads(path.read_text(encoding="utf-8"), parse_constant=_forbid_nan)


def test_bhgc_v2_band6_tc_bugfix_and_wchd_module_constants() -> None:
    """Verify IR-BHGC-BAND6-01 & IR-WCHD-BAND6-DROP-01 are permanently resolved."""
    bhgc_src = inspect.getsource(bhgc.build_bhgc_extra_stack)
    assert "_clean_base(5)" not in bhgc_src, "0-based col 5 (Band 6 radiometric TC) must not be read as magnetic tilt in bhgc.py"
    assert "_clean_base(1)" in bhgc_src and "_clean_base(2)" in bhgc_src and "_clean_base(8)" in bhgc_src
    bhgc_rec = _strict_json_load(ROOT / "registry" / "bhgc_feature_receipt.json")
    assert bhgc_rec.get("schema_version") == 2
    assert bhgc_rec.get("band6_tc_bug_fixed") is True

    assert len(wchd.WCHD_EXTRA_CHANNELS) == 8
    assert wchd.DEFAULT_AXIAL_SEP_PX == 3.88
    assert len(wchd.CLEAN_104_RAW_COLS) == 104
    assert 84 not in wchd.CLEAN_104_RAW_COLS
    assert len(wchd.MGAP_91_RAW_COLS) == 91
    assert len(wchd.MSUBSPACE_34_RAW_COLS) == 34

    rng = np.random.default_rng(7)
    foot = np.ones((24, 24), dtype=bool)
    vis = np.zeros((24, 24), dtype=bool)
    vis[10, 4:10] = True
    ps = rng.uniform(0.0, 1.0, size=(24, 24)).astype(np.float32)
    pd = rng.uniform(0.0, 1.0, size=(24, 24)).astype(np.float32)
    psub = rng.uniform(0.0, 1.0, size=(24, 24)).astype(np.float32)
    base = np.zeros((24, 24, 35), dtype=np.float32)
    base[:, :, 11] = 10.0
    base[:, :, 14] = 210.0
    base[:, :, 18] = 8.0
    trhv = rng.uniform(0.0, 1.0, size=(24, 24, 8)).astype(np.float32)
    ws = rng.uniform(0.0, 1.0, size=(24, 24, 8)).astype(np.float32)

    surf = wchd.build_bipopulation_wchd_surface(ps, pd, psub, base, trhv, ws, vis, foot)
    assert surf.shape == (24, 24)
    assert surf.dtype == np.float32
    assert np.isfinite(surf).all()
    assert float(surf.min()) >= 0.0 and float(surf.max()) <= 1.0
    assert np.all(surf[vis] == 0.0)


def test_promoted_wchd_geotiff_binary_portal_safety() -> None:
    """Verify [0, 1] finite safety, EPSG:32611, 3730x3292, exact geotransform, and SHA-256."""
    for p in (PRIMARY_TIF, MIRROR_TIF, CANONICAL_ZEROS):
        assert p.exists(), f"Missing promoted GeoTIFF {p}"
        digest = hashlib.sha256(p.read_bytes()).hexdigest()
        assert digest == EXPECTED_SHA256
    assert CANONICAL_ZIP.exists()

    with rasterio.open(PRIMARY_TIF) as ds:
        assert ds.count == 1
        assert ds.dtypes == ("float32",)
        assert (ds.height, ds.width) == (3730, 3292)
        assert ds.crs.to_epsg() == 32611
        assert ds.nodata is None
        with rasterio.open(ROOT / ".cache" / "gems_data" / "sample_submission.tif") as tmpl:
            assert ds.transform == tmpl.transform
            assert ds.crs == tmpl.crs
            assert (ds.height, ds.width) == (tmpl.height, tmpl.width)
        assert ds.transform.to_gdal() == (243350.0, 100.0, 0.0, 4508550.0, 0.0, -100.0)
        arr = ds.read(1)

    assert arr.size == 12_279_160
    assert np.isfinite(arr).all(), "Predicted values must have zero NaNs/Infs across entire 3730x3292 grid"
    assert float(arr.min()) == 0.0 and float(arr.max()) == 1.0
    uniq = set(np.unique(arr).tolist())
    assert uniq == {0.0, 1.0}
    assert int((arr > 0.5).sum()) == 37_654

    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check_submission.py"), "--strict-finite", str(PRIMARY_TIF)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr


def test_wchd_release_gates_and_ablation_ledger() -> None:
    """Verify H-APART3-3 WCHD passes all 7 release_gate checks and logs full experiment ledger."""
    card = _strict_json_load(ROOT / "run_card.json")
    wcard = _strict_json_load(ROOT / "evidence" / "wchd_run_card.json")
    exp = _strict_json_load(ROOT / "evidence" / "wchd_experiments.json")
    ledger = _strict_json_load(ROOT / "evidence" / "wchd_experiment_ledger.json")

    assert card == wcard
    assert card["candidate_id"] == "H-APART3-3-WCHD"
    assert card["experiments_used"] == 3
    assert card["verdict"] == "promote"
    assert card["selector_required"] is True
    assert card["slot_used"] is False
    assert card["release_gate_decision"]["verdict"] == "promote"
    assert all(card["release_gate_decision"]["gates"].values())

    hr = card["holdout_dti"]["primary_hide_and_recover"]
    det = card["holdout_dti"]["detached_600m_blind_segments"]
    sgmc = card["holdout_dti"]["off_catalogue_sgmc"]

    assert hr["score_label"] == "HOLDOUT-DTI"
    assert det["score_label"] == "HOLDOUT-DTI"
    assert sgmc["score_label"] == "HOLDOUT-DTI"

    assert hr["dti"] > hr["incumbent_02778_champion_dti"]
    assert hr["paired_bootstrap_vs_02778_champion"]["ci95"][0] > 0.0
    assert sgmc["prevalence_calibrated_dti"] > sgmc["incumbent_02778_champion_calibrated_dti"]

    exp2 = card["holdout_dti"]["ablation_summary"]["EXP2_WCHD_SINGLE104_OOF"]
    assert exp2["hide_recover_dti"] > 0.120
    assert exp2["detached_600m_dti"] > 0.103

    assert card["leakage_canary"]["passed"] is True
    assert card["leakage_canary"]["n_features_tested"] == 104
    assert card["leakage_canary"]["max_oriented_auc"] <= 0.90

    assert set(exp["experiments"].keys()) == {
        "EXP1_WCHD_UNSUP_UPDIP",
        "EXP2_WCHD_SINGLE104_OOF",
        "EXP3_WCHD_DUAL104_UPDIP",
    }
    assert len(ledger["canonical_three_experiment_ladder"]) == 3
    assert len(ledger["shared_bugfixes_before_final_ladder"]) >= 3


def test_wchd_942_raster_uniqueness_and_site_hygiene() -> None:
    """Verify Step A (<=0.90) & Step B (<=0.70) across 942 unique rasters, including CSHD 37b32d5b."""
    scan = _strict_json_load(ROOT / "registry" / "registry_uniqueness_scan_20261028.json")
    nine = _strict_json_load(ROOT / "evidence" / "nine_site_refreshed_audit_20261028.json")
    card = _strict_json_load(ROOT / "run_card.json")
    _strict_json_load(ROOT / "docs" / "assets" / "site-data.json")
    _strict_json_load(ROOT / "registry" / "irregularities.json")

    assert scan["n_unique_rasters_checked"] >= 940
    assert scan["n_genuine_rasters_checked"] >= 910
    assert scan["genuine_surface_passed"] is True
    assert scan["genuine_final_dots_passed"] is True
    assert scan["focus_site_genuine_final_passed"] is True
    assert card["correlation_vs_registry"]["max_abs_spearman_surface"] <= 0.90
    assert float(scan["worst_genuine_overlap"]["within_3px_fraction"]) <= 0.70
    assert float(card["correlation_vs_registry"]["within_3px_vs_cshd_37b32d5b"]) <= 0.70
    assert float(card["correlation_vs_registry"]["within_3px_vs_bhgc3_ab6646b7"]) <= 0.70
    assert float(card["correlation_vs_registry"]["within_3px_vs_cfkc_9dedadfc"]) <= 0.70
    assert float(card["correlation_vs_registry"]["within_3px_vs_cthg_5d4d0085"]) <= 0.70
    assert len(nine["sites"]) == 9

    assert len(card["submission_note"]) <= 140
    assert card["raster_sha256"] == EXPECTED_SHA256

    deliverables = [
        ROOT / "README.md",
        ROOT / "index.html",
        ROOT / "docs" / "index.html",
        ROOT / "docs" / "executive-summary.html",
        ROOT / "docs" / "executive-summary" / "index.html",
        ROOT / "docs" / "submissions.html",
        ROOT / "docs" / "release-status.html",
        ROOT / "docs" / "research.html",
        ROOT / "docs" / "hypotheses.html",
        ROOT / "docs" / "leaderboard.html",
        ROOT / "docs" / "sources.html",
        ROOT / "docs" / "assets" / "fig_wchd_apart3.png",
        ROOT / "docs" / "research" / "h-apart3-3-wchd-preregistration-20261028.md",
    ]
    for p in deliverables:
        assert p.exists(), f"Missing deliverable {p}"
        if p.suffix in {".md", ".html", ".json"}:
            txt = p.read_text(encoding="utf-8")
            assert "/home/user/" not in txt, f"Leaked sandbox path in {p}"
            if p.name in {"index.html", "executive-summary.html", "README.md"}:
                assert PRIMARY_FILENAME in txt
                assert EXPECTED_SHA256 in txt
                assert card["submission_name"] in txt
