"""Unit and artifact-verification tests for H49-1-MFFR (Multi-Scale Scarp-Stepover, Cooper Tilt-Phase & Dual-89ch Axial d=3.08 CELF)."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import rasterio

from gems32 import mffr

ROOT = Path(__file__).resolve().parents[1]


def test_mffr_channel_list_and_carrier_components_synthetic() -> None:
    assert len(mffr.MFFR_EXTRA_CHANNELS) == 6
    assert list(mffr.MFFR_EXTRA_CHANNELS) == [
        "piedmont_inflection_pf_chord",
        "multiscale_ridge_log_chord",
        "cooper_theta_phase_contact",
        "play_fairway_conduit_corridor",
        "multimodal_tensor_coherence",
        "mffr_composite_unsup_carrier",
    ]
    rng = np.random.default_rng(49)
    H, W = 64, 64
    foot = np.ones((H, W), dtype=bool)
    foot[:4, :] = False
    spcp_stack = rng.uniform(0.0, 1.0, size=(H, W, 20)).astype(np.float32)
    trhv_stack = rng.uniform(0.0, 1.0, size=(H, W, 8)).astype(np.float32)
    ldgi_stack = rng.uniform(0.0, 1.0, size=(H, W, 8)).astype(np.float32)
    mffr_stack = rng.uniform(0.0, 1.0, size=(H, W, 6)).astype(np.float32)

    carrier, mffr_pure, road_w = mffr.build_mffr_carrier_components(
        spcp_stack, trhv_stack, ldgi_stack, mffr_stack, foot
    )
    for arr in (carrier, mffr_pure, road_w):
        assert arr.shape == (H, W)
        assert arr.dtype == np.float32
        assert np.all(np.isfinite(arr))
        assert float(arr.min()) >= 0.0
        assert float(arr.max()) <= 1.0 + 1e-6


def test_stationary_mffr_surface_and_axial308_emission_synthetic() -> None:
    H, W = 72, 72
    foot = np.ones((H, W), dtype=bool)
    foot[:5, :] = False
    visible = np.zeros((H, W), dtype=bool)
    visible[36, 15:55] = True

    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    ridge = np.exp(-0.5 * ((yy - 24.0) / 1.5) ** 2) + np.exp(-0.5 * ((xx - 48.0) / 1.5) ** 2)
    ridge = np.clip(ridge, 0.0, 1.0).astype(np.float32)

    p_dual = (0.75 * ridge + 0.05).astype(np.float32)
    road_w = np.ones((H, W), dtype=np.float32)

    surf = mffr.build_stationary_mffr_surface(
        p_dual=p_dual,
        carrier=ridge,
        road_w=road_w,
        visible_mask=visible,
        foot=foot,
    )
    assert surf.shape == (H, W)
    assert surf.dtype == np.float32
    assert np.all(np.isfinite(surf))
    assert float(surf[~foot].max()) == 0.0

    dots, info = mffr.emit_mffr_submodular(
        surface=surf,
        visible_mask=visible,
        eligible_mask=foot,
        foot=foot,
        budget=20,
        b_collar_px=2.0,
        min_sep_px=3.08,
    )
    assert dots.shape == (H, W)
    assert dots.dtype == bool
    assert int(dots.sum()) == 20
    assert int((dots & visible).sum()) == 0
    assert int((dots & ~foot).sum()) == 0
    assert info["min_sep_px"] == 3.08

    # Verify pairwise Euclidean distance >= 3.08 px (hence 0 neighbors within 3.0 px)
    pts = np.argwhere(dots).astype(np.float64)
    diff = pts[:, None, :] - pts[None, :, :]
    dist = np.sqrt((diff ** 2).sum(axis=-1))
    np.fill_diagonal(dist, np.inf)
    assert float(dist.min()) >= 3.08 - 1e-5


def test_h49_run_card_and_shipped_artifacts_verified() -> None:
    card_path = ROOT / "evidence" / "h49_mffr_run_card.json"
    exp_path = ROOT / "evidence" / "h49_mffr_experiments.json"
    receipt_path = ROOT / "registry" / "mffr_feature_receipt.json"
    assert card_path.is_file()
    assert exp_path.is_file()
    assert receipt_path.is_file()

    card = json.loads(card_path.read_text())
    assert card["candidate_id"] == "H49-1-MFFR"
    assert card["verdict"] == "negative"
    assert card["ok_to_submit"] is False
    assert card["download_for_research_ok"] is True
    assert card["weekly_slots_used"] == 0
    assert card["experiments_used"] == 3
    assert card["experiments_budget_cap"] == 3
    assert len(card["submission_note"]) <= 140

    # Leakage canary pass across all 89 channels
    canary = card["leakage_canary"]
    assert canary["passed"] is True
    assert canary["n_features_tested"] == 89
    assert float(canary["max_oriented_auc"]) <= 0.90

    # Beats 0.2778 Champion across ALL FOUR holdout benchmarks simultaneously
    hd = card["holdout_dti"]
    assert hd["primary_hide_and_recover"]["pooled_dti"] > hd["incumbent_02778_same_evaluator"]["pooled_dti"]
    assert hd["paired_delta_vs_02778_champion"]["ci95"][0] > 0.0
    assert hd["paired_delta_vs_02778_champion"]["prob_positive"] >= 0.99
    assert hd["censorship_matched_d2"]["pooled_dti"] > 0.004780
    assert hd["detached_600m_segments"]["pooled_dti"] > hd["incumbent_detached_600m"]["pooled_dti"]
    assert (
        hd["off_catalogue_sgmc"]["prevalence_calibrated_dti"]
        > hd["incumbent_02778_sgmc"]["prevalence_calibrated_dti"]
    )
    assert (
        hd["off_catalogue_sgmc"]["prevalence_calibrated_dti"]
        > hd["historical_comparators_same_evaluator"]["H48_1_sgmc_calibrated_dti"]
    )
    assert (
        hd["off_catalogue_sgmc"]["prevalence_calibrated_dti"]
        > hd["historical_comparators_same_evaluator"]["H47_1_sgmc_calibrated_dti"]
    )

    # Genuine uniqueness pass
    uq = card["correlation_and_overlap_vs_registry"]
    assert uq["genuine_pre_placement_surface_passed"] is True
    assert uq["genuine_final_dots_passed"] is True
    assert uq["focus_site_genuine_final_passed"] is True
    assert float(uq["max_abs_surface_spearman"]) <= 0.90
    assert float(uq["max_genuine_3px_dot_overlap"]) <= 0.70
    assert float(uq["max_focus_site_3px_dot_overlap"]) <= 0.70

    # Zero 3-px clumping and stationary allocation
    alloc = card["artifacts"]["spatial_allocation"]
    assert alloc["stationary_formula_no_eta_switch"] is True
    assert float(alloc["clump_ge3_nbr3_frac"]) == 0.0
    assert 0.20 <= float(alloc["lidar_gap_dot_frac"]) <= 0.30

    # Saved GeoTIFF byte & format audit
    tif_path = ROOT / card["artifacts"]["primary_zeros_tif"]
    assert tif_path.is_file()
    sha = hashlib.sha256(tif_path.read_bytes()).hexdigest()
    assert sha == card["raster_sha256"]
    with rasterio.open(tif_path) as ds:
        assert ds.count == 1
        assert (ds.height, ds.width) == (3730, 3292)
        assert str(ds.crs) == "EPSG:32611"
        assert ds.nodata is None
        arr = ds.read(1)
    assert arr.dtype == np.float32
    assert int(np.isnan(arr).sum()) == 0
    assert float(arr.min()) == 0.0
    assert float(arr.max()) == 1.0
    assert int((arr > 0.5).sum()) == 37654
