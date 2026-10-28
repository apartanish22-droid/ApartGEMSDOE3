from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
import pytest
import rasterio

from gems32 import fbgr, ldgi, mdrc, spcp, trhv
from gems32.cfkc import (
    CFKC_EXTRA_CHANNELS,
    CFKC_MSUB_EXTRA_INDICES,
    build_exp1_dualcover_surface,
    build_exp2_hybrid_surface,
    build_stationary_dual_horizon_belief_surface,
    emit_stationary_dual_horizon_cfkc,
)

ROOT = Path(__file__).resolve().parents[1]


def test_cfkc_channel_names_and_synthetic_placement() -> None:
    assert len(CFKC_EXTRA_CHANNELS) == 8
    assert CFKC_EXTRA_CHANNELS[-1] == "cfkc_hybrid_crustal_crest"
    assert len(CFKC_MSUB_EXTRA_INDICES) == 6

    rng = np.random.default_rng(42)
    h, w = 64, 64
    foot = np.ones((h, w), dtype=bool)
    visible_mask = np.zeros((h, w), dtype=bool)
    visible_mask[:3, :] = True
    surface_63 = rng.uniform(0.0, 1.0, size=(h, w)).astype(np.float32)
    p_dual_91 = rng.uniform(0.0, 1.0, size=(h, w)).astype(np.float32)
    cfkc_stack = rng.uniform(0.0, 1.0, size=(h, w, 8)).astype(np.float32)
    trhv_stack = rng.uniform(0.0, 1.0, size=(h, w, 8)).astype(np.float32)

    s1 = build_exp1_dualcover_surface(
        p_dual=p_dual_91,
        cfkc_stack=cfkc_stack,
        trhv_stack=trhv_stack,
        visible_mask=visible_mask,
        foot=foot,
    )
    assert s1.shape == (h, w)
    assert np.isfinite(s1).all()

    surf = build_exp2_hybrid_surface(
        surface_63ch=surface_63,
        p_dual_91ch=p_dual_91,
        cfkc_stack=cfkc_stack,
        visible_mask=visible_mask,
        foot=foot,
    )
    assert surf.shape == (h, w)
    assert np.isfinite(surf).all()

    belief = build_stationary_dual_horizon_belief_surface(
        surface_stage1=surf,
        crest_b=cfkc_stack[:, :, 7],
        visible_mask=visible_mask,
        mask=foot,
    )
    assert belief.shape == (h, w)
    assert np.isfinite(belief).all()

    dots, log = emit_stationary_dual_horizon_cfkc(
        surface_stage1=surf,
        crest_b=cfkc_stack[:, :, 7],
        visible_mask=visible_mask,
        eligible_mask=foot,
        foot=foot,
        budget=40,
        min_sep_px=2.8,
        b_collar_px=2.0,
    )
    assert dots.shape == (h, w)
    assert int(dots.sum()) == 40
    assert log["total_dots"] == 40
    assert int(dots[:5, :].sum()) == 0


def test_supporting_physical_modules_spcp_trhv_ldgi_fbgr_mdrc() -> None:
    assert len(spcp.SPCP_EXTRA_CHANNELS) == 20
    assert len(set(spcp.SPCP_EXTRA_CHANNELS)) == 20
    assert len(trhv.TRHV_EXTRA_CHANNELS) == 8
    assert len(ldgi.LDGI_EXTRA_CHANNELS) == 8
    assert len(fbgr.FBGR_EXTRA_CHANNELS) == 12

    rng = np.random.default_rng(7)
    field = rng.normal(size=(48, 48)).astype(np.float32)
    foot = np.ones((48, 48), dtype=bool)
    u1, u2 = fbgr.harmonic_upward_continue_pair_f32(field, foot, heights_m=(500.0, 2000.0), pad_px=8)
    assert u1.shape == field.shape and u2.shape == field.shape
    assert np.isfinite(u1).all() and np.isfinite(u2).all()

    crest = mdrc.sharpen_ridge_crest(np.abs(field), foot)
    assert crest.shape == field.shape
    assert np.isfinite(crest).all()


def test_cfkc_geotiff_is_research_artifact_not_authorized_submission() -> None:
    tif_main = ROOT / "docs/downloads/apartgemsdoe3-h-apart3-1-cfkc-dhc-37654-20261027T215000Z-9dedadfc-zeros.tif"
    tif_canon = ROOT / "docs/downloads/gemsdoe32-apart3-h-apart3-1-cfkc-dhc-37654-20261027T215000Z-9dedadfc-zeros.tif"
    zip_main = ROOT / "docs/downloads/apartgemsdoe3-h-apart3-1-cfkc-dhc-37654-20261027T215000Z-9dedadfc-zeros.zip"
    assert tif_main.exists()
    assert tif_canon.exists()
    assert zip_main.exists()
    assert tif_main.read_bytes() == tif_canon.read_bytes()

    with rasterio.open(tif_main) as src:
        assert str(src.crs) == "EPSG:32611"
        assert (src.height, src.width) == (3730, 3292)
        assert src.count == 1
        assert str(src.dtypes[0]) == "float32"
        assert src.nodata is None
        arr = src.read(1)
        assert int(np.isnan(arr).sum()) == 0
        assert int(np.isinf(arr).sum()) == 0
        assert float(arr.min()) >= 0.0
        assert float(arr.max()) <= 1.0
        assert int((arr > 0.5).sum()) == 37654


def test_run_card_and_html_links_integrity() -> None:
    rc_path = ROOT / "evidence/apart3_cfkc_dhc_run_card.json"
    docs_rc_path = ROOT / "docs/data/latest-run-card.json"
    assert rc_path.exists()
    assert docs_rc_path.exists()
    rc = json.loads(rc_path.read_text())

    assert rc["verdict"] == "promote"  # historical experiment result; not current release authorization
    assert rc["ok_to_submit"] is True  # legacy field, superseded by the literal all-registry gate
    current = json.loads((ROOT / "run_card.json").read_text())
    assert current["verdict"] == "negative"
    assert current["ok_to_submit"] is False
    assert current["correlation_vs_registry"]["candidate_dots_within_3px_fraction"] == pytest.approx(0.998513)
    assert current["correlation_vs_registry"]["candidate_dots_within_3px_fraction"] > 0.70
    assert current["slot_used"] is False
    vo = rc["validator_output"]
    assert vo["validated_without_human_intervention"] is True
    assert vo["audit_geotiff_13_checks_passed"] is True
    assert vo["nan_inside_footprint"] == 0
    assert vo["nan_anywhere_in_raster"] == 0
    assert vo["values_in_0_1"] is True
    assert vo["required_validator_flags"]["crs_match"] is True
    assert vo["required_validator_flags"]["shape_match"] is True
    assert vo["required_validator_flags"]["transform_match"] is True
    assert rc["leakage_canary"]["passed"] is True
    assert rc["leakage_canary"]["max_oriented_auc"] < 0.90
    reg = rc["correlation_and_overlap_vs_registry"]
    assert reg["genuine_pre_placement_surface_passed"] is True
    assert reg["genuine_final_dots_passed"] is True
    assert reg["focus_site_genuine_final_passed"] is True
    assert reg["max_abs_surface_spearman"] < 0.90
    assert reg["max_genuine_3px_dot_overlap"] < 0.70
    assert reg["max_focus_site_3px_dot_overlap"] < 0.70
    assert len(rc["submission_note"]) <= 140

    for html_rel, base_dir in [
        ("docs/index.html", ROOT / "docs"),
        ("docs/executive-summary.html", ROOT / "docs"),
        ("docs/submissions.html", ROOT / "docs"),
        ("index.html", ROOT),
    ]:
        html_file = ROOT / html_rel
        assert html_file.exists(), f"Missing {html_rel}"
        text = html_file.read_text()
        for m in re.finditer(r'(?:href|src)="([^"#?]+)"', text):
            target = m.group(1)
            if target.startswith(("http://", "https://", "mailto:", "javascript:")):
                continue
            resolved = (base_dir / target).resolve()
            assert resolved.exists(), f"Broken link in {html_rel}: {target} -> {resolved}"
