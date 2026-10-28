"""H49-1-MFFR: Multi-Scale Scarp-Stepover & Cooper Generalized Tilt-Phase Fault-Relay Synthesis.

Pre-registered in `docs/research/h49-mffr-preregistration-20261027.md`:
1. Appends 6 label-free physical channels (`MFFR_EXTRA_CHANNELS`, indices `83..88`, bringing the
   cached stack to `89` channels total):
     - `piedmont_inflection_pf_chord` (Ch 83): Basin-margin piedmont scarp-toe / bedrock-slope
       inflection coupled with gravity/magnetic horizontal-gradient crest concordance.
     - `multiscale_ridge_log_chord` (Ch 84): Multi-scale topographic-geophysical ridge log-chord
       product across `100 m`, `250 m`, and `500 m` filter banks (`H19-5` / `D2.8` scarp-ridge prior).
     - `cooper_theta_phase_contact` (Ch 85): Cooper & Cowan (2006) generalized tilt-phase contact
       sharpness `cos(theta_grav)` + `cos(theta_rtp)` via upward-continuation vertical derivatives.
     - `play_fairway_conduit_corridor` (Ch 86): Heat-flow + magnetotelluric + radon + silica/potassic
       play-fairway conduit corridor concordant with subsurface basement gradient walls.
     - `multimodal_tensor_coherence` (Ch 87): Joint 2x2 structure-tensor strike coherence across
       gravity, RTP magnetic, and de-confounded topographic scarp gradients.
     - `mffr_composite_unsup_carrier` (Ch 88): Label-free physical MFFR ridge-corridor carrier with
       150 m TIGER road damping (`trhv_stack[:, :, 4]`) and playa flat-sink suppression.
2. Fits Dual-Cover 89-ch / 76-ch fold-local `HistGradientBoostingClassifier` models (`M_Full` on
   `lidar_valid`, `M_Sub` on all footprints with fold-local quantile calibration onto `M_Full`).
3. Builds a stationary pre-placement belief surface (`build_stationary_mffr_surface`) combining the
   89-ch Dual-Cover posterior `p_dual` with the physical `MFFR + LDGI` ridge carrier (`carrier`),
   far-basin hallucination damping (`far_gate` at `d_vis > 18 px`), and fold-local anisotropic tip/relay
   continuation (`ldgi.anisotropic_tip_relay_cone`), then thins to 1-px oriented ridge crests via
   `mdrc.sharpen_ridge_crest` and emits `37,654` (`B = 2`) off-catalogue dots with axial spacing
   `min_sep_px = 3.08 px` (`d^2 >= 10`, `0.00%` 2D clumping).
"""

from __future__ import annotations

from dataclasses import asdict
import gc
import json
from pathlib import Path
from typing import Any, Callable

import numpy as np
from numpy.lib.format import open_memmap
from scipy.ndimage import (
    binary_dilation,
    distance_transform_edt,
    gaussian_filter,
    maximum_filter,
    minimum_filter,
)
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score

from gems32 import emitter, fbgr, ldgi, mdrc, spcp, trhv

MFFR_EXTRA_FILENAME = "mffr_extra_6ch.npy"
MFFR_RECEIPT_FILENAME = "mffr_feature_receipt.json"

MFFR_EXTRA_CHANNELS: tuple[str, ...] = (
    "piedmont_inflection_pf_chord",
    "multiscale_ridge_log_chord",
    "cooper_theta_phase_contact",
    "play_fairway_conduit_corridor",
    "multimodal_tensor_coherence",
    "mffr_composite_unsup_carrier",
)

# 89-channel stack layout:
#   0..42  (43 ch): base features_43ch.npy (cols 37..42 are 1m LiDAR)
#  43..62  (20 ch): spcp_extra_20ch.npy    (cols 55..56 are 1m LiDAR)
#  63..70  ( 8 ch): trhv_extra_8ch.npy     (cols 68..69 are 1m LiDAR)
#  71..78  ( 8 ch): ldgi_extra_8ch.npy     (cols 72, 76, 78 use 1m LiDAR)
#  79..82  ( 4 ch): fbgr_extra_12ch.npy    (col 89 uses 1m LiDAR; total 12 ch = 79..90 -> 83 ch before MFFR)
#  83..88  ( 6 ch): mffr_extra_6ch.npy     (strictly 100 m Statewide + GeoDAWN + Potential-Field)
LIDAR_DEPENDENT_COLS_89: tuple[int, ...] = (
    37, 38, 39, 40, 41, 42,
    55, 56,
    68, 69,
    72, 76, 78,
    89,
)

MSUB_COL_INDICES_89: tuple[int, ...] = tuple(
    i for i in range(89) if i not in LIDAR_DEPENDENT_COLS_89
)

TARGET_BUDGET = 37_654
AXIAL_MIN_SEP_PX = 3.08
B_COLLAR_PX = 2.0


def build_mffr_carrier_components(
    spcp_stack: np.ndarray,
    trhv_stack: np.ndarray,
    ldgi_stack: np.ndarray,
    mffr_stack: np.ndarray,
    foot: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Precompute stationary physical `(carrier, mffr_pure, road_w)` float32 arrays on `foot`."""
    ldgi_unsup = ldgi.build_ldgi_crest_unsup_surface(spcp_stack, trhv_stack, ldgi_stack, foot)
    ch0 = np.asarray(mffr_stack[:, :, 0], dtype=np.float32)
    ch1 = np.asarray(mffr_stack[:, :, 1], dtype=np.float32)
    ch2 = np.asarray(mffr_stack[:, :, 2], dtype=np.float32)
    ch3 = np.asarray(mffr_stack[:, :, 3], dtype=np.float32)
    ch4 = np.asarray(mffr_stack[:, :, 4], dtype=np.float32)
    tiger_clean = np.asarray(trhv_stack[:, :, 4], dtype=np.float32)
    road_w = (np.float32(0.35) + np.float32(0.65) * tiger_clean).astype(np.float32)

    mffr_pure = spcp.robust_unit_f32(
        np.float32(0.34) * ch1
        + np.float32(0.22) * ch0
        + np.float32(0.16) * ch2
        + np.float32(0.14) * ch3
        + np.float32(0.14) * ch4,
        foot,
        pct=99.5,
    )
    carrier = (np.float32(0.52) * ldgi_unsup + np.float32(0.48) * mffr_pure).astype(np.float32)
    return carrier, mffr_pure, road_w


def build_mffr_extra_stack(
    base_stack: np.ndarray,
    spcp_stack: np.ndarray,
    trhv_stack: np.ndarray,
    ldgi_stack: np.ndarray,
    fbgr_stack: np.ndarray,
    foot: np.ndarray,
    ddir: Path,
    wdir: Path,
    force: bool = False,
    log: Callable[[str], None] = print,
) -> tuple[np.ndarray, dict[str, Any]]:
    """Build or load cached `(H, W, 6)` float32 `mffr_extra_6ch.npy` stack (`labels.tif` never read)."""
    out_path = wdir / MFFR_EXTRA_FILENAME
    receipt_path = wdir / MFFR_RECEIPT_FILENAME
    if out_path.exists() and receipt_path.exists() and not force:
        arr = open_memmap(out_path, mode="r")
        if arr.shape == (foot.shape[0], foot.shape[1], len(MFFR_EXTRA_CHANNELS)):
            return arr, json.loads(receipt_path.read_text())

    h, w = foot.shape
    mm = open_memmap(
        out_path,
        mode="w+",
        dtype=np.float32,
        shape=(h, w, len(MFFR_EXTRA_CHANNELS)),
    )

    def _clean_base(idx: int) -> np.ndarray:
        a = np.asarray(base_stack[:, :, idx], dtype=np.float32)
        med = float(np.nanmedian(a[foot])) if np.isfinite(a[foot]).any() else 0.0
        return np.where(np.isfinite(a) & foot, a, np.float32(med)).astype(np.float32)

    # --- Ch 0 (83): Basin-Margin Piedmont Scarp-Toe Inflection & Potential-Field Chord ---
    det_elev = _clean_base(11)     # Band 12: detrended_elevation
    depth_base = _clean_base(14)   # Band 15: depth_to_base_surf
    elev_slope = _clean_base(18)   # Band 19: elevation_slope
    tiger_clean = np.asarray(trhv_mm_4 := trhv_stack[:, :, 4], dtype=np.float32)

    slope_s1 = gaussian_filter(elev_slope, sigma=1.2, mode="nearest")
    slope_s4 = gaussian_filter(elev_slope, sigma=4.5, mode="nearest")
    slope_break = np.maximum(slope_s1 - np.float32(0.75) * slope_s4, np.float32(0.0))
    del slope_s1, slope_s4

    piedmont_zone = (
        spcp._sigmoid_f32((elev_slope - np.float32(1.4)) / np.float32(0.8))
        * spcp._sigmoid_f32((np.float32(16.0) - elev_slope) / np.float32(4.0))
        * spcp._sigmoid_f32((depth_base - np.float32(60.0)) / np.float32(120.0))
        * spcp._sigmoid_f32((np.float32(1400.0) - depth_base) / np.float32(450.0))
    ).astype(np.float32)

    grav_p = np.asarray(fbgr_stack[:, :, 0], dtype=np.float32)
    rtp_p = np.asarray(fbgr_stack[:, :, 1], dtype=np.float32)
    dip_asymm = np.asarray(fbgr_stack[:, :, 2], dtype=np.float32)
    pf_chord = np.sqrt(np.maximum(grav_p * rtp_p, np.float32(0.0))) + np.float32(0.45) * np.maximum(grav_p, rtp_p)

    u_sb = spcp.robust_unit_f32(slope_break, foot, pct=99.4)
    del slope_break
    piedmont_pf = spcp.robust_unit_f32(
        (np.float32(0.55) * u_sb + np.float32(0.45) * piedmont_zone)
        * (np.float32(0.35) + np.float32(0.65) * pf_chord + np.float32(0.30) * dip_asymm)
        * (np.float32(0.35) + np.float32(0.65) * tiger_clean),
        foot,
        pct=99.5,
    )
    mm[:, :, 0] = piedmont_pf
    del u_sb, piedmont_zone, pf_chord, dip_asymm

    # --- Ch 1 (84): Multi-Scale Topographic-Geophysical Ridge Log-Chord (100m, 250m, 500m) ---
    k100, str100 = spcp.principal_negative_curvature_and_strike(det_elev, sigma=1.1)
    k250, _ = spcp.principal_negative_curvature_and_strike(det_elev, sigma=2.5)
    k500, _ = spcp.principal_negative_curvature_and_strike(det_elev, sigma=5.0)
    u_k100 = spcp.robust_unit_f32(k100, foot, pct=99.4)
    u_k250 = spcp.robust_unit_f32(k250, foot, pct=99.4)
    u_k500 = spcp.robust_unit_f32(k500, foot, pct=99.4)
    del k100, k250, k500

    lidar_clean = np.asarray(trhv_stack[:, :, 5], dtype=np.float32)
    spcp_unsup = np.asarray(spcp_stack[:, :, 19], dtype=np.float32)
    topo_ms = (
        np.float32(0.40) * np.cbrt(np.maximum(u_k100 * u_k250 * u_k500, np.float32(0.0)))
        + np.float32(0.35) * np.maximum(u_k100, u_k250)
        + np.float32(0.25) * np.maximum(lidar_clean, spcp_unsup)
    )
    del u_k100, u_k250, u_k500, lidar_clean

    ridge_log_chord = spcp.robust_unit_f32(
        topo_ms
        * (np.float32(0.40) + np.float32(0.60) * np.maximum(grav_p, rtp_p))
        * (np.float32(0.35) + np.float32(0.65) * tiger_clean),
        foot,
        pct=99.5,
    )
    mm[:, :, 1] = ridge_log_chord
    del topo_ms
    log("  [MFFR] ch 0..1 (piedmont inflection + multiscale ridge log-chord) built")

    # --- Ch 2 (85): Cooper & Cowan (2006) Generalized Tilt-Phase Contact Sharpness ---
    cba = _clean_base(0)  # Band 01: cba
    rtp = _clean_base(1)  # Band 02: rtp
    g_uc500, g_uc2k = fbgr.harmonic_upward_continue_pair_f32(cba, foot, heights_m=(500.0, 2000.0))
    m_uc500, m_uc2k = fbgr.harmonic_upward_continue_pair_f32(rtp, foot, heights_m=(500.0, 2000.0))
    del cba, rtp

    gh500, gy_g, gx_g = fbgr._hgrad_mag_and_vec(g_uc500, sigma=0.9)
    mh500, gy_m, gx_m = fbgr._hgrad_mag_and_vec(m_uc500, sigma=0.9)
    gz = (g_uc500 - g_uc2k) / np.float32(15.0)
    mz = (m_uc500 - m_uc2k) / np.float32(15.0)
    del g_uc500, g_uc2k, m_uc500, m_uc2k

    as_g = np.hypot(gh500, gz) + np.float32(1e-4)
    as_m = np.hypot(mh500, mz) + np.float32(1e-4)
    cos_theta_g = gh500 / as_g
    cos_theta_m = mh500 / as_m
    del gz, mz, as_g, as_m

    kg_phase, _ = spcp.principal_negative_curvature_and_strike(cos_theta_g, sigma=1.3)
    km_phase, _ = spcp.principal_negative_curvature_and_strike(cos_theta_m, sigma=1.3)
    u_kgp = spcp.robust_unit_f32(kg_phase * spcp.robust_unit_f32(gh500, foot, pct=99.4), foot, pct=99.4)
    u_kmp = spcp.robust_unit_f32(km_phase * spcp.robust_unit_f32(mh500, foot, pct=99.4), foot, pct=99.4)
    del cos_theta_g, cos_theta_m, kg_phase, km_phase, gh500, mh500

    cooper_contact = spcp.robust_unit_f32(
        (np.float32(0.45) * u_kgp + np.float32(0.45) * u_kmp + np.float32(0.10) * np.sqrt(u_kgp * u_kmp))
        * (np.float32(0.40) + np.float32(0.60) * tiger_clean),
        foot,
        pct=99.5,
    )
    mm[:, :, 2] = cooper_contact
    del u_kgp, u_kmp

    # --- Ch 3 (86): Play-Fairway Heat-Flow + MT + Radon + Alteration Conduit Corridor ---
    hf = _clean_base(4)          # Band 05: heat_flow
    mt_surf = _clean_base(16)    # Band 17: log10_cond_surf
    mt_2km = _clean_base(15)     # Band 16: log10_cond_2km
    radon_c = np.asarray(fbgr_stack[:, :, 3], dtype=np.float32)
    dog_alt = np.asarray(fbgr_stack[:, :, 4], dtype=np.float32)
    blm_c = np.asarray(fbgr_stack[:, :, 5], dtype=np.float32)
    svd_wall = np.asarray(ldgi_stack[:, :, 5], dtype=np.float32)

    u_hf = spcp.robust_unit_f32(hf - gaussian_filter(hf, sigma=18.0, mode="nearest"), foot, pct=99.2)
    u_mt = spcp.robust_unit_f32(np.maximum(mt_2km - np.float32(0.65) * mt_surf, np.float32(0.0)), foot, pct=99.2)
    del hf, mt_surf, mt_2km

    pf_corridor = spcp.robust_unit_f32(
        (
            np.float32(0.24) * u_hf
            + np.float32(0.22) * u_mt
            + np.float32(0.20) * radon_c
            + np.float32(0.18) * dog_alt
            + np.float32(0.16) * blm_c
        )
        * (np.float32(0.40) + np.float32(0.60) * np.maximum(svd_wall, np.maximum(grav_p, rtp_p))),
        foot,
        pct=99.5,
    )
    mm[:, :, 3] = pf_corridor
    del u_hf, u_mt, radon_c, dog_alt, blm_c, svd_wall

    # --- Ch 4 (87): Multi-Modal Structure-Tensor Strike Coherence (Gravity + RTP + Scarp) ---
    str_g = (np.arctan2(gy_g, gx_g) + np.float32(0.5 * np.pi)).astype(np.float32)
    str_m = (np.arctan2(gy_m, gx_m) + np.float32(0.5 * np.pi)).astype(np.float32)
    del gy_g, gx_g, gy_m, gx_m

    c2 = (
        np.float32(0.38) * np.cos(np.float32(2.0) * str_g)
        + np.float32(0.32) * np.cos(np.float32(2.0) * str_m)
        + np.float32(0.30) * np.cos(np.float32(2.0) * str100)
    )
    s2 = (
        np.float32(0.38) * np.sin(np.float32(2.0) * str_g)
        + np.float32(0.32) * np.sin(np.float32(2.0) * str_m)
        + np.float32(0.30) * np.sin(np.float32(2.0) * str100)
    )
    del str_g, str_m, str100
    coherence = np.hypot(
        gaussian_filter(c2, sigma=2.0, mode="nearest"),
        gaussian_filter(s2, sigma=2.0, mode="nearest"),
    ).astype(np.float32)
    del c2, s2

    tensor_coh = spcp.robust_unit_f32(
        coherence
        * (np.float32(0.35) + np.float32(0.65) * np.maximum(ridge_log_chord, cooper_contact))
        * (np.float32(0.35) + np.float32(0.65) * tiger_clean),
        foot,
        pct=99.5,
    )
    mm[:, :, 4] = tensor_coh
    del coherence

    # --- Ch 5 (88): Unified Physical MFFR Ridge-Corridor Carrier (`mffr_composite_unsup_carrier`) ---
    local_relief_1km = maximum_filter(det_elev, size=15) - minimum_filter(det_elev, size=15)
    playa_veto = np.clip(
        np.float32(1.0)
        - np.float32(0.85)
        * spcp._sigmoid_f32((np.float32(1.0) - elev_slope) / np.float32(0.35))
        * spcp._sigmoid_f32((np.float32(10.0) - local_relief_1km) / np.float32(3.5)),
        np.float32(0.15),
        np.float32(1.0),
    ).astype(np.float32)
    del det_elev, elev_slope, depth_base, local_relief_1km

    ldgi_corridor = (
        np.float32(0.35) * np.asarray(ldgi_stack[:, :, 0], dtype=np.float32)
        + np.float32(0.35) * np.asarray(ldgi_stack[:, :, 2], dtype=np.float32)
        + np.float32(0.30) * np.asarray(ldgi_stack[:, :, 4], dtype=np.float32)
    )
    mffr_carrier = spcp.robust_unit_f32(
        (
            np.float32(0.28) * ridge_log_chord
            + np.float32(0.22) * piedmont_pf
            + np.float32(0.18) * cooper_contact
            + np.float32(0.16) * tensor_coh
            + np.float32(0.16) * pf_corridor
        )
        * (np.float32(0.45) + np.float32(0.55) * ldgi_corridor)
        * playa_veto
        * (np.float32(0.30) + np.float32(0.70) * tiger_clean),
        foot,
        pct=99.5,
    )
    mm[:, :, 5] = mffr_carrier
    del piedmont_pf, ridge_log_chord, cooper_contact, pf_corridor, tensor_coh, ldgi_corridor, playa_veto, grav_p, rtp_p, spcp_unsup, tiger_clean

    if hasattr(mm, "flush"):
        mm.flush()
    gc.collect()

    meta: dict[str, Any] = {
        "channels": list(MFFR_EXTRA_CHANNELS),
        "shape": [h, w, len(MFFR_EXTRA_CHANNELS)],
        "dtype": "float32",
        "label_free": True,
        "total_stack_channels": 89,
        "msub_pure_non_lidar_col_count": len(MSUB_COL_INDICES_89),
    }
    receipt_path.write_text(json.dumps(meta, indent=2) + "\n")
    log("  [MFFR] ch 2..5 (Cooper tilt-phase contact + play-fairway corridor + tensor coherence + MFFR carrier) built")
    return open_memmap(out_path, mode="r"), meta


def gather_89ch(
    base_stack: np.ndarray,
    spcp_stack: np.ndarray,
    trhv_stack: np.ndarray,
    ldgi_stack: np.ndarray,
    fbgr_stack: np.ndarray,
    mffr_stack: np.ndarray,
    ys: np.ndarray,
    xs: np.ndarray,
    col_indices: tuple[int, ...] | None = None,
) -> np.ndarray:
    xb = np.asarray(base_stack[ys, xs, :], dtype=np.float32)
    xs_arr = np.asarray(spcp_stack[ys, xs, :], dtype=np.float32)
    xt = np.asarray(trhv_stack[ys, xs, :], dtype=np.float32)
    xl = np.asarray(ldgi_stack[ys, xs, :], dtype=np.float32)
    xf = np.asarray(fbgr_stack[ys, xs, :], dtype=np.float32)
    xm = np.asarray(mffr_stack[ys, xs, :], dtype=np.float32)
    full = np.hstack([xb, xs_arr, xt, xl, xf, xm])
    if col_indices is not None:
        return full[:, col_indices]
    return full


def run_leakage_canary_89ch(
    base_stack: np.ndarray,
    spcp_stack: np.ndarray,
    trhv_stack: np.ndarray,
    ldgi_stack: np.ndarray,
    fbgr_stack: np.ndarray,
    mffr_stack: np.ndarray,
    base_names: list[str],
    ctx,
    max_auc: float = 0.90,
    stride: int = 4,
) -> dict[str, Any]:
    """Protocol Rule 4 single-feature two-polarity leakage canary across all 89 channels."""
    pos_mask = np.zeros(ctx.foot.shape, dtype=bool)
    neg_mask = np.zeros(ctx.foot.shape, dtype=bool)
    for cell in ctx.cells:
        if cell.seed != 20:
            continue
        sl = cell.bbox
        sub_t = np.zeros(cell.active_sub.shape, dtype=bool)
        sub_t[cell.truth_coords] = True
        pos_mask[sl] |= sub_t
        neg_mask[sl] |= cell.active_sub & ~sub_t

    py, px = np.nonzero(pos_mask)
    ny, nx = np.nonzero(neg_mask)
    ny, nx = ny[::stride], nx[::stride]
    y_true = np.concatenate([np.ones(py.size, dtype=np.int8), np.zeros(ny.size, dtype=np.int8)])

    stacks = (base_stack, spcp_stack, trhv_stack, ldgi_stack, fbgr_stack, mffr_stack)
    offsets = np.cumsum([0] + [s.shape[2] for s in stacks])
    all_names = (
        list(base_names)
        + list(spcp.SPCP_EXTRA_CHANNELS)
        + list(trhv.TRHV_EXTRA_CHANNELS)
        + list(ldgi.LDGI_EXTRA_CHANNELS)
        + list(fbgr.FBGR_EXTRA_CHANNELS)
        + list(MFFR_EXTRA_CHANNELS)
    )
    assert len(all_names) == int(offsets[-1]) == 89

    rows = []
    for i, name in enumerate(all_names):
        s_idx = int(np.searchsorted(offsets[1:], i, side="right"))
        plane = stacks[s_idx][:, :, i - int(offsets[s_idx])]
        vals = np.concatenate([plane[py, px], plane[ny, nx]]).astype(np.float64)
        vals = np.nan_to_num(vals, nan=0.0, posinf=0.0, neginf=0.0)
        if np.ptp(vals) <= 1e-12:
            raw_auc, auc_dir = 0.5, 0.5
        else:
            raw_auc = float(roc_auc_score(y_true, vals))
            auc_dir = max(raw_auc, 1.0 - raw_auc)
        rows.append(
            {
                "index": i,
                "name": name,
                "group": ("base", "spcp", "trhv", "ldgi", "fbgr", "mffr")[s_idx],
                "in_msub": i in MSUB_COL_INDICES_89,
                "raw_auc": round(raw_auc, 6),
                "oriented_auc": round(auc_dir, 6),
                "flagged": bool(auc_dir > max_auc),
            }
        )

    flagged = [r for r in rows if r["flagged"]]
    top_ch = max(rows, key=lambda r: r["oriented_auc"])
    return {
        "rule": f"single-feature two-polarity holdout ROC AUC <= {max_auc:.2f}",
        "n_channels_tested": len(rows),
        "n_positive_samples": int(py.size),
        "n_negative_samples": int(ny.size),
        "max_oriented_auc": top_ch["oriented_auc"],
        "max_oriented_channel": top_ch["name"],
        "flagged_channels": flagged,
        "passed": len(flagged) == 0,
        "channels": rows,
    }


def fit_mffr_classifier(
    base_stack: np.ndarray,
    spcp_stack: np.ndarray,
    trhv_stack: np.ndarray,
    ldgi_stack: np.ndarray,
    fbgr_stack: np.ndarray,
    mffr_stack: np.ndarray,
    train_region: np.ndarray,
    visible_train: np.ndarray,
    foot: np.ndarray,
    col_indices: tuple[int, ...] | None = None,
    seed: int = 49,
    max_pos: int = 44_000,
    n_neg_hard: int = 88_000,
    n_neg_unif: int = 88_000,
) -> HistGradientBoostingClassifier:
    """Fit a fold-local hard-negative `HistGradientBoostingClassifier` on `train_region`."""
    rng = np.random.default_rng(seed)
    tr_pos = train_region & visible_train
    d_tr = distance_transform_edt(~tr_pos)

    pos_y, pos_x = np.nonzero(tr_pos)
    if pos_y.size > max_pos:
        pp = rng.choice(pos_y.size, size=max_pos, replace=False)
        pos_y, pos_x = pos_y[pp], pos_x[pp]

    hard_y, hard_x = np.nonzero(train_region & (~visible_train) & (d_tr >= 5.0) & (d_tr <= 24.0))
    unif_y, unif_x = np.nonzero(train_region & (~visible_train) & (d_tr > 24.0))
    del d_tr

    nh = min(n_neg_hard, hard_y.size)
    nu = min(n_neg_unif, unif_y.size)
    ph = rng.choice(hard_y.size, size=nh, replace=False)
    pu = rng.choice(unif_y.size, size=nu, replace=False)

    ys = np.concatenate([pos_y, hard_y[ph], unif_y[pu]])
    xs = np.concatenate([pos_x, hard_x[ph], unif_x[pu]])
    y = np.concatenate([np.ones(pos_y.size, dtype=np.int8), np.zeros(nh + nu, dtype=np.int8)])
    del pos_y, pos_x, hard_y, hard_x, unif_y, unif_x

    order = np.argsort(ys * foot.shape[1] + xs)
    ys, xs, y = ys[order], xs[order], y[order]

    X = gather_89ch(
        base_stack, spcp_stack, trhv_stack, ldgi_stack, fbgr_stack, mffr_stack,
        ys, xs, col_indices=col_indices,
    )
    clf = HistGradientBoostingClassifier(
        max_iter=175,
        learning_rate=0.055,
        max_leaf_nodes=47,
        min_samples_leaf=80,
        l2_regularization=2.5,
        early_stopping=False,
        random_state=seed,
    )
    clf.fit(X, y)
    del X, y, ys, xs
    return clf


def predict_chunked_mffr(
    clf: HistGradientBoostingClassifier,
    base_stack: np.ndarray,
    spcp_stack: np.ndarray,
    trhv_stack: np.ndarray,
    ldgi_stack: np.ndarray,
    fbgr_stack: np.ndarray,
    mffr_stack: np.ndarray,
    mask: np.ndarray,
    col_indices: tuple[int, ...] | None = None,
    chunk_size: int = 200_000,
) -> np.ndarray:
    out = np.zeros(mask.shape, dtype=np.float32)
    ys, xs = np.nonzero(mask)
    for start in range(0, ys.size, chunk_size):
        sl = slice(start, min(start + chunk_size, ys.size))
        X = gather_89ch(
            base_stack, spcp_stack, trhv_stack, ldgi_stack, fbgr_stack, mffr_stack,
            ys[sl], xs[sl], col_indices=col_indices,
        )
        out[ys[sl], xs[sl]] = clf.predict_proba(X)[:, 1].astype(np.float32)
        del X
    return out


def build_stationary_mffr_surface(
    p_dual: np.ndarray,
    carrier: np.ndarray,
    road_w: np.ndarray,
    visible_mask: np.ndarray,
    foot: np.ndarray,
    w_p: float = 0.41,
    w_c: float = 0.53,
    w_far: float = 0.11,
    alpha: float = 0.46,
    far_start_px: float = 18.0,
    far_span_px: float = 14.0,
    far_damp: float = 0.38,
    w_tip_relay: float = 0.52,
) -> np.ndarray:
    """Stationary pre-placement MFFR belief surface (identical formula on OOF folds and full map).

    Uses ZERO holdout-vs-live censorship switch (`eta`):
      - Combines `p_dual` (`89-ch / 76-ch` Dual-Cover posterior) with the physical `MFFR + LDGI`
        ridge carrier (`carrier * max(p_dual, 0.008)^alpha`),
      - Damps uncalibrated far-basin `p_dual` hallucinations at `d_vis > far_start_px` while
        anchoring far-basin predictions on the physical `MFFR + LDGI` ridge carrier (`w_far`),
      - Modulates by the fold-local anisotropic tip/relay continuation cone (`ldgi.anisotropic_tip_relay_cone`)
        and the 150 m TIGER road prism damping (`road_w`).
    """
    vis = np.asarray(visible_mask, bool) & foot
    d_vis = distance_transform_edt(~vis).astype(np.float32)
    far_gate = np.clip((d_vis - np.float32(far_start_px)) / np.float32(far_span_px), np.float32(0.0), np.float32(1.0))
    del d_vis

    relay = ldgi.anisotropic_tip_relay_cone(vis, foot)
    p_pow = np.power(np.maximum(p_dual, np.float32(0.008)), np.float32(alpha))

    near_term = (np.float32(w_p) * p_dual + np.float32(w_c) * carrier * p_pow) * (
        np.float32(1.0) - np.float32(far_damp) * far_gate
    )
    far_term = np.float32(w_far) * far_gate * carrier * (np.float32(0.42) + np.float32(0.58) * p_pow)
    surf = (near_term + far_term) * (np.float32(1.0) + np.float32(w_tip_relay) * relay) * road_w
    del far_gate, relay, p_pow, near_term, far_term
    return np.where(foot, np.clip(surf, 0.0, 1.0), 0.0).astype(np.float32)


def emit_mffr_submodular(
    surface: np.ndarray,
    visible_mask: np.ndarray,
    eligible_mask: np.ndarray,
    foot: np.ndarray,
    budget: int = TARGET_BUDGET,
    min_sep_px: float = AXIAL_MIN_SEP_PX,
    b_collar_px: float = B_COLLAR_PX,
    support_mult: int = 9,
    gamma: float = 1.35,
) -> tuple[np.ndarray, dict[str, Any]]:
    """Thin `surface` to 1-px oriented ridge crests (`mdrc.sharpen_ridge_crest`) and emit `budget` dots.

    1-px crest thinning reduces candidate neighbor density inside `2R = 6 px` from ~60 to ~6,
    allowing exact lazy-greedy submodular emission (`emitter.emit`) to complete in ~11s on the full
    `(3730, 3292)` grid with `0.00%` 2D clumping (`>= 3` neighbors within `3 px`).
    """
    if budget <= 0 or not (eligible_mask & foot).any():
        return np.zeros(surface.shape, dtype=bool), {"n_emitted": 0, "stopped_by": "zero_budget"}

    vis = np.asarray(visible_mask, bool) & foot
    if b_collar_px == 2.0:
        elig_base = eligible_mask & foot & ~binary_dilation(vis, structure=spcp._disk_mask(2.0))
    else:
        d_vis = distance_transform_edt(~vis).astype(np.float32)
        elig_base = eligible_mask & foot & (d_vis > float(b_collar_px))
        del d_vis

    crest = mdrc.sharpen_ridge_crest(surface, foot)
    elig = elig_base & (crest > 0.0)
    n_elig = int(elig.sum())
    if n_elig == 0:
        return np.zeros(surface.shape, dtype=bool), {"n_emitted": 0, "stopped_by": "empty_eligible"}

    max_sup = min(n_elig, max(int(budget) * int(support_mult), 45_000))
    if n_elig > max_sup:
        vals = crest[elig]
        thr = float(np.partition(vals, n_elig - max_sup)[n_elig - max_sup])
        sup = elig & (crest >= thr)
        del vals
    else:
        thr = float(crest[elig].min())
        sup = elig

    field = np.where(sup, np.power(np.clip(crest, 0.0, 1.0), float(gamma)), 0.0).astype(np.float64)
    del crest, elig, sup
    dots, elog = emitter.emit(
        field,
        budget=int(budget),
        prior_dti=0.0,
        gain_floor=0.0,
        min_sep_px=float(min_sep_px),
    )
    info = asdict(elog)
    info["candidate_pool_size"] = int(n_elig)
    info["support_size"] = int(max_sup)
    info["support_threshold"] = float(thr)
    info["min_sep_px"] = float(min_sep_px)
    return dots, info
