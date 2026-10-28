"""End-to-end release & protocol verification suite for ApartGEMSDOE3 (H-APART-1 BHGC-3)."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import rasterio

from gems32 import bhgc, submission
from gems32.paths import ROOT, data_dir, downloads_dir, evidence_dir, work_dir


EXPECTED_SHA256 = "ba092640a4f776e3a22c8af1a5fe503487d4fa3f2277020a6e8268fd08e0797a"
PRIMARY_FILENAME = "apartgemsdoe3-h1-bhgc3-bipop-axial32-37654-20261027T214500Z-ab6646b7-zeros.tif"


def test_bhgc_module_constants_and_lidar_free_subset() -> None:
    """Verify the 89-channel BHGC feature list and 76-channel LiDAR-free M_Sub indices."""
    assert len(bhgc.BHGC_EXTRA_CHANNELS) == 6
    assert len(bhgc.MSUB_89_COL_INDICES) == 76
    # Verify none of the 13 1m LiDAR channels appear in MSUB_89_COL_INDICES
    lidar_cols = set(bhgc.LIDAR_DEPENDENT_89_COLS)
    assert len(lidar_cols) == 13
    assert lidar_cols.isdisjoint(set(bhgc.MSUB_89_COL_INDICES))


def test_leakage_canary_89ch_passed() -> None:
    """Protocol Rule 4: Every feature tested alone on holdout must have oriented AUC <= 0.90."""
    exp_data = json.loads((evidence_dir() / "bhgc_experiments.json").read_text(encoding="utf-8"))
    canary = exp_data["leakage_canary_89ch"]
    assert canary["passed"] is True
    assert canary["n_features_tested"] == 89
    assert canary["threshold_auc"] == 0.90
    assert canary["max_oriented_auc"] <= 0.90
    for ch_name in bhgc.BHGC_EXTRA_CHANNELS:
        assert ch_name in canary["bhgc_6ch_aucs"]
        val = canary["bhgc_6ch_aucs"][ch_name]
        auc = float(val["oriented_auc"]) if isinstance(val, dict) else float(val)
        assert 0.50 <= auc <= 0.90


def test_primary_geotiff_automated_validation() -> None:
    """Verify primary GeoTIFF strictly in [0, 1], 0 NaN, 0 Inf, EPSG:32611, 3730x3292, 37654 dots."""
    ddir = data_dir()
    tif_path = downloads_dir() / PRIMARY_FILENAME
    mirror_path = ROOT / "submission" / PRIMARY_FILENAME
    assert tif_path.exists(), f"Missing {tif_path}"
    assert mirror_path.exists(), f"Missing {mirror_path}"

    sha_dl = hashlib.sha256(tif_path.read_bytes()).hexdigest()
    sha_sub = hashlib.sha256(mirror_path.read_bytes()).hexdigest()
    assert sha_dl == EXPECTED_SHA256
    assert sha_sub == EXPECTED_SHA256

    with rasterio.open(ddir / "sample_submission.tif") as ref_ds:
        ref_arr = ref_ds.read(1)
        foot = np.isfinite(ref_arr)
        ref_crs = ref_ds.crs
        ref_transform = ref_ds.transform
        ref_shape = ref_ds.shape

    with rasterio.open(ddir / "labels.tif") as lab_ds:
        labels = np.isfinite(lab_ds.read(1)) & (lab_ds.read(1) > 0) & foot

    with rasterio.open(tif_path) as ds:
        assert ds.count == 1
        assert ds.shape == (3730, 3292)
        assert ds.shape == ref_shape
        assert ds.crs == ref_crs
        assert str(ds.crs) == "EPSG:32611"
        assert ds.transform == ref_transform
        assert ds.dtypes[0] == "float32"
        assert ds.nodata is None
        arr = ds.read(1)

    # Whole-array finite & [0, 1] check (fixes DrivenData "Predicted values must be in range [0, 1]" error)
    assert np.isfinite(arr).all(), "GeoTIFF contains NaN or Inf"
    assert float(arr.min()) == 0.0
    assert float(arr.max()) == 1.0
    assert float(arr[~foot].max()) == 0.0
    assert int((arr[foot] > 0.5).sum()) == 37654
    assert int((arr[labels] > 0.0).sum()) == 0

    audit_13 = submission.audit_geotiff(
        tif_path, foot, labels, mode="zeros", template_tif=ddir / "sample_submission.tif"
    )
    assert all(audit_13["checks"].values()), f"Failed checks: {audit_13['checks']}"


def test_pareto_dominance_and_three_experiment_budget() -> None:
    """Verify EXP-3 beats 0.2778 Champion on Hide-and-Recover, Detached >=600m, AND Off-Catalogue SGMC."""
    exp_data = json.loads((evidence_dir() / "bhgc_experiments.json").read_text(encoding="utf-8"))
    assert exp_data["budget_experiments_used"] == 3
    assert exp_data["budget_max_experiments"] == 3
    assert set(exp_data["experiments"].keys()) == {
        "EXP1_BHGC_UNSUP_SPINE",
        "EXP2_BHGC_OOF_NEAR",
        "EXP3_BHGC_BIPOP_FULL",
    }

    champ = exp_data["baselines"]["incumbent_02778_champion"]
    exp3 = exp_data["experiments"]["EXP3_BHGC_BIPOP_FULL"]

    assert exp3["hide_and_recover_v3"]["pooled_dti"] > champ["hide_and_recover_v3"]["pooled_dti"]
    assert exp3["detached_600m_segments"]["pooled_dti"] > champ["detached_600m_segments"]["pooled_dti"]
    assert (
        exp3["sgmc_off_catalogue_v3"]["prevalence_calibrated_dti"]
        > champ["sgmc_off_catalogue_v3"]["prevalence_calibrated_dti"]
    )


def test_registry_uniqueness_gates_passed() -> None:
    """Protocol Rule 1: Pre-placement |Spearman| <= 0.90 and final dots genuine 3-px overlap <= 0.70."""
    scan = json.loads((ROOT / "registry" / "registry_uniqueness_scan_20261027.json").read_text(encoding="utf-8"))
    assert scan["n_unique_rasters_checked"] >= 500
    assert scan["n_genuine_rasters_checked"] >= 480
    assert scan["genuine_surface_passed"] is True
    assert scan["genuine_final_dots_passed"] is True
    assert scan["focus_site_genuine_final_passed"] is True
    assert abs(float(scan["worst_genuine_surface"]["surface_spearman"])) <= 0.90
    assert float(scan["worst_genuine_overlap"]["within_3px_fraction"]) <= 0.70


def test_run_card_and_site_hygiene() -> None:
    """Protocol Rule 5: Verify archived bhgc_run_card.json schema, note length <=140, and zero leaked local paths."""
    card = json.loads((ROOT / "evidence" / "bhgc_run_card.json").read_text(encoding="utf-8"))
    required_keys = {
        "hypothesis",
        "mechanism",
        "named_non_fault_mimic_process",
        "holdout_dti",
        "leakage_canary",
        "correlation_vs_registry",
        "raster_sha256",
        "validator",
        "submission_name",
        "submission_note",
        "verdict",
    }
    assert required_keys.issubset(set(card.keys()))
    assert card["raster_sha256"] == EXPECTED_SHA256
    assert len(card["submission_note"]) <= 140
    assert all(card["validator"].values())
    assert card["verdict"] in {"promote", "negative"}

    # Verify all HTML pages and README exist and have zero leaked /home/user paths
    pages = [
        ROOT / "README.md",
        ROOT / "index.html",
        ROOT / "docs" / "index.html",
        ROOT / "docs" / "executive-summary.html",
        ROOT / "docs" / "executive-summary" / "index.html",
        ROOT / "docs" / "research.html",
        ROOT / "docs" / "hypotheses.html",
        ROOT / "docs" / "leaderboard.html",
        ROOT / "docs" / "sources.html",
        ROOT / "docs" / "assets" / "fig_bhgc_apart3.png",
    ]
    for p in pages:
        assert p.exists(), f"Missing deliverable {p}"
        if p.suffix in {".md", ".html", ".json"}:
            txt = p.read_text(encoding="utf-8")
            assert "/home/user/" not in txt, f"Leaked absolute path in {p}"
            if p.name in {"index.html", "executive-summary.html", "README.md"}:
                assert "DO NOT SUBMIT" in txt
