"""End-to-end automated release & protocol tests for ApartGEMSDOE3 H-APART3-2 (CSHD)."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import rasterio

from gems32 import cshd

ROOT = Path(__file__).resolve().parents[1]
PRIMARY_FILENAME = "apartgemsdoe3-h2-cshd-dual97-axial362-37654-20261028T063000Z-37b32d5b-zeros.tif"
PRIMARY_TIF = ROOT / "docs" / "downloads" / PRIMARY_FILENAME
MIRROR_TIF = ROOT / "submission" / PRIMARY_FILENAME
CANONICAL_ZEROS = ROOT / "docs" / "downloads" / "gemsdoe32-apart3-cshd-dual97-axial362-37654-20261028T063000Z-37b32d5b-zeros.tif"
EXPECTED_SHA256 = "65f2ac84ff2c762495107487769a49e90919c5c6bf4a7948ca77e4a6971e5b38"


def _strict_json_load(path: Path) -> dict:
    def _forbid_nan(val: str) -> None:
        raise ValueError(f"Non-RFC8259 constant {val!r} in {path}")

    return json.loads(path.read_text(encoding="utf-8"), parse_constant=_forbid_nan)


def test_cshd_module_constants_and_envelope_stationarity() -> None:
    assert len(cshd.CSHD_EXTRA_CHANNELS) == 8
    assert cshd.DEFAULT_AXIAL_SEP_PX == 3.62
    rng = np.random.default_rng(42)
    foot = np.ones((24, 24), dtype=bool)
    vis = np.zeros((24, 24), dtype=bool)
    vis[12, 5:10] = True
    ps = rng.uniform(0.0, 1.0, size=(24, 24)).astype(np.float32)
    pd = rng.uniform(0.0, 1.0, size=(24, 24)).astype(np.float32)
    base = np.zeros((24, 24, 35), dtype=np.float32)
    base[:, :, 11] = 10.0
    base[:, :, 14] = 220.0
    base[:, :, 18] = 8.5
    trhv = rng.uniform(0.0, 1.0, size=(24, 24, 8)).astype(np.float32)
    bhgc = rng.uniform(0.0, 1.0, size=(24, 24, 6)).astype(np.float32)
    cs = rng.uniform(0.0, 1.0, size=(24, 24, 8)).astype(np.float32)

    surf = cshd.build_bipopulation_cshd_surface(ps, pd, base, trhv, bhgc, cs, vis, foot)
    assert surf.shape == (24, 24)
    assert surf.dtype == np.float32
    assert np.isfinite(surf).all()
    assert float(surf.min()) >= 0.0 and float(surf.max()) <= 1.0
    assert np.all(surf[vis] == 0.0)


def test_promoted_cshd_geotiff_binary_portal_safety() -> None:
    """Verify [0, 1] finite safety, EPSG:32611, 3730x3292, exact geotransform, and SHA-256."""
    for p in (PRIMARY_TIF, MIRROR_TIF, CANONICAL_ZEROS):
        assert p.exists(), f"Missing promoted GeoTIFF {p}"
        digest = hashlib.sha256(p.read_bytes()).hexdigest()
        assert digest == EXPECTED_SHA256

    with rasterio.open(PRIMARY_TIF) as ds:
        assert ds.count == 1
        assert ds.dtypes == ("float32",)
        assert (ds.height, ds.width) == (3730, 3292)
        assert ds.crs.to_epsg() == 32611
        assert ds.nodata is None
        # GDAL geotransform verified directly against sample_submission.tif
        with rasterio.open(ROOT / ".cache" / "gems_data" / "sample_submission.tif") as tmpl:
            assert ds.transform == tmpl.transform
            assert ds.crs == tmpl.crs
            assert (ds.height, ds.width) == (tmpl.height, tmpl.width)
        assert ds.transform.to_gdal() == (243350.0, 100.0, 0.0, 4508550.0, 0.0, -100.0)
        arr = ds.read(1)

    assert arr.size == 12_279_160
    assert np.isfinite(arr).all(), "Predicted values must have zero NaNs/Infs across entire 3730x3292 grid"
    assert float(arr.min()) >= 0.0 and float(arr.max()) <= 1.0
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


def test_cshd_pareto_dominance_and_paired_cis_positive() -> None:
    """Verify archived H-APART3-2 CSHD card beats 0.2778 Champion on HR, Detached>=600m, and SGMC."""
    card = _strict_json_load(ROOT / "evidence" / "cshd_run_card.json")
    exp = _strict_json_load(ROOT / "evidence" / "cshd_experiments.json")

    assert card["candidate_id"] == "H-APART3-2-CSHD"
    assert card["experiments_used"] <= 3
    assert card["verdict"] == "promote"
    assert card["release_gate_decision"]["verdict"] == "promote"
    assert all(card["release_gate_decision"]["gates"].values())

    hr = card["holdout_dti"]["primary_hide_and_recover"]
    det = card["holdout_dti"]["detached_600m_blind_segments"]
    sgmc = card["holdout_dti"]["off_catalogue_sgmc"]

    assert hr["score_label"] == "HOLDOUT-DTI"
    assert det["score_label"] == "HOLDOUT-DTI"
    assert sgmc["score_label"] == "HOLDOUT-DTI"

    assert hr["dti"] > hr["incumbent_02778_champion_dti"]
    assert det["dti"] > det["incumbent_02778_champion_dti"]
    assert sgmc["prevalence_calibrated_dti"] > sgmc["incumbent_02778_champion_calibrated_dti"]

    # Both primary paired bootstrap 95% CIs strictly positive
    assert hr["paired_bootstrap_vs_02778_champion"]["ci95"][0] > 0.0
    assert sgmc["paired_bootstrap_vs_02778_champion"]["ci95"][0] > 0.0

    # Leakage canary across all 97 channels
    assert card["leakage_canary"]["passed"] is True
    assert card["leakage_canary"]["n_features_tested"] == 97
    assert card["leakage_canary"]["max_oriented_auc"] <= 0.90

    # Controlled 3-experiment ablation ladder present
    assert set(exp["experiments"].keys()) == {
        "EXP1_CSHD_UNSUP_CREST",
        "EXP2_CSHD_SINGLE97_OOF",
        "EXP3_CSHD_DUAL97_FULL",
    }


def test_cshd_784_raster_uniqueness_and_rfc8259_json_hygiene() -> None:
    """Verify Step A (<=0.90) & Step B (<=0.70) across 784 unique rasters and strict JSON/path hygiene."""
    scan = _strict_json_load(ROOT / "registry" / "registry_uniqueness_scan_20261028.json")
    nine = _strict_json_load(ROOT / "evidence" / "nine_site_refreshed_audit_20261028.json")
    card = _strict_json_load(ROOT / "evidence" / "cshd_run_card.json")
    _strict_json_load(ROOT / "docs" / "assets" / "site-data.json")
    _strict_json_load(ROOT / "registry" / "irregularities.json")

    assert scan["n_unique_rasters_checked"] >= 780
    assert scan["n_genuine_rasters_checked"] >= 750
    assert scan["genuine_surface_passed"] is True
    assert scan["genuine_final_dots_passed"] is True
    assert scan["focus_site_genuine_final_passed"] is True
    assert card["correlation_vs_registry"]["max_abs_spearman_surface"] <= 0.90
    assert float(scan["worst_genuine_overlap"]["within_3px_fraction"]) <= 0.70
    assert float(scan["worst_focus_site_overlap"]["within_3px_fraction"]) <= 0.70
    assert len(nine["sites"]) == 9

    assert len(card["submission_note"]) <= 140
    assert card["raster_sha256"] == EXPECTED_SHA256

    deliverables = [
        ROOT / "README.md",
        ROOT / "index.html",
        ROOT / "docs" / "index.html",
        ROOT / "docs" / "executive-summary.html",
        ROOT / "docs" / "executive-summary" / "index.html",
        ROOT / "docs" / "research.html",
        ROOT / "docs" / "hypotheses.html",
        ROOT / "docs" / "leaderboard.html",
        ROOT / "docs" / "sources.html",
        ROOT / "docs" / "assets" / "fig_cshd_apart3.png",
        ROOT / "docs" / "research" / "h-apart3-2-cshd-preregistration-20261028.md",
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
