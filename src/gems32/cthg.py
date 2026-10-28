"""H-APART3-2 (CTHG-DHC): Cooper-Cowan Joint Tilt-Phase Contact Wall, Fluvial Delta-Chi
Laplace Basement Throw Conduit & Clump-Free 103-Ch/87-Ch Dual-Horizon Cover.

Method and retrospective analysis plan are documented in ``docs/research/h-apart3-2-cthg-dhc-preregistration-20261028.md``; exploratory sweeps preceded the final pipeline, so this is not a valid prospective preregistration.

CRITICAL SCIENTIFIC WARNING: Executed Ch 0 and inherited BHGC Ch 1 use base Band 6 (`tc`) as a magnetic-tilt field. Existing repo forensics identify Band 6 as airborne radiometric Total Count, not magnetic tilt (IR-A8A-BAND6-TC-01). The claimed tilt-phase interpretation is invalid until the shared feature builder and dependent caches are corrected; do not promote any artifact from this implementation.

Key scientific & engineering contributions:
1. Builds 6 strictly label-free physical channels (``CTHG_EXTRA_CHANNELS``, indices 97..102 in the
   unified 103-channel stack) combining:
   - Ch 0 (97): ``cooper_cowan_tilt_phase_wall`` — Cooper & Cowan (2006) hyperbolic tilt-phase
     zero-crossing contact wall coupling exact Laplace-harmonic gravity tilt angle
     ``theta_g = arctan((-div(Band 18, Band 11)) / (||g_h|| + eps))`` with magnetic tilt angle
     zero-crossing (``Band 6, 3, 9``) and strike co-planarity ``cos^2(psi_g - psi_m)`` (100% coverage).
   - Ch 1 (98): ``knickzone_laplace_throw_conduit`` — Perron & Royden (2013) transient fluvial
     ``Delta-chi`` knickpoint step height & ``k_sn`` range-front projection (``dem10_chi_100m_i16.tif``,
     ``dem10_chi_100m_u8.tif``) coupled with Laplace-harmonic gravity divergence crest and basement
     throw gradient ``||grad(Band 15)||`` (100% coverage).
   - Ch 2 (99): ``mt_claycap_radon_sinter_halo`` — Magnetotelluric smectite clay-cap lateral phase
     boundary ``||grad(Band 17)||`` coupled with 4-block standardized GeoDAWN ``214Bi`` radon crests,
     hydrothermal magnetite-destruction troughs, and GDR #1391 2-m thermal & paleo-sinter upflow (100% coverage).
   - Ch 3 (100): ``morris_stepover_10m_curv_tensor`` — Morris-Ferrill-Henderson (1996) slip-dilation
     tendency & geodetic/seismic accommodation tensor (``Bands 4, 7, 8, 10, 16``) coupled with
     100%-coverage USGS 3DEP 10 m seamless bedrock profile curvature & multi-azimuth hillshade
     lineament ridges (100% coverage).
   - Ch 4 (101): ``cthg_seamfree_gap_conduit`` — Unified 100%-coverage strictly 1m-LiDAR-free
     multi-physics conduit carrier across the 24.66% 1 m LiDAR coverage gap.
   - Ch 5 (102): ``cthg_unified_bipop_spine`` — Unified Dual-Horizon Structural-Geothermal Crest Spine
     integrating all 5 non-LiDAR physical pillars with 1 m 3DEP topographic openness dipole & LRM
     scarps inside ``lidar_valid`` plus 4-azimuth directional chain-linking and crest sharpening.
2. Upgrades Dual-Cover OOF training so ``M_Full`` trains on all 103 channels inside ``lidar_valid``
   while ``M_Sub`` trains on 87 strictly 1m-LiDAR-free channels across the 24.66% LiDAR gap.
3. Introduces Clump-Free Stationary Dual-Horizon 1-px Crest Residual-Coverage CELF
   (``EXP3_CTHG_CLUMPFREE_DHC``) with ``min_sep_px = 3.08 > 3.0 px`` (guaranteeing ``0.00% Clump>=3``),
   ``B = 2.0 px`` catalogue collar exclusion, and balanced Stage-1 (near/extension) + Stage-2
   (far-field discovery spine) horizons.
"""

from __future__ import annotations

import gc
import json
from pathlib import Path
from typing import Any

import numpy as np
from numpy.lib.format import open_memmap
from scipy.ndimage import distance_transform_edt, gaussian_filter
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score

from . import bhgc, cfkc, emitter, fbgr, ldgi, mdrc, paths, spcp, trhv

TARGET_BUDGET: int = 37_654
AXIAL_MIN_SEP_PX: float = 3.08
B_COLLAR_PX: float = 2.0
STATIONARY_STAGE1_FRAC: float = 0.72
STATIONARY_W_S1: float = 0.22
STATIONARY_OFF_CAT_MIN_DIST_PX: float = 5.5

CTHG_EXTRA_CHANNELS: tuple[str, ...] = (
    "cooper_cowan_tilt_phase_wall",    # 0 (97): Cooper-Cowan joint gravity/magnetic tilt zero-crossing contact wall (100% coverage)
    "knickzone_laplace_throw_conduit", # 1 (98): Perron-Royden fluvial delta-chi knickzone x Laplace basement throw step (100% coverage)
    "mt_claycap_radon_sinter_halo",    # 2 (99): MT smectite clay-cap lateral edge x 4-block 214Bi radon & paleo-sinter halo (100% coverage)
    "morris_stepover_10m_curv_tensor", # 3 (100): Morris slip-dilation & geodetic strain tensor x 10m seamless curvature ridge (100% coverage)
    "cthg_seamfree_gap_conduit",       # 4 (101): Unified 100%-coverage strictly 1m-LiDAR-free multi-physics gap carrier
    "cthg_unified_bipop_spine",        # 5 (102): Unified Dual-Horizon Structural-Geothermal Crest Spine
)

# Strictly 1m-LiDAR-free column indices in the 103-channel stack:
# - 71 from FBGR (0..82)
# - 5 from BHGC (83, 84, 85, 86, 87)
# - 6 from CFKC (89, 90, 91, 92, 93, 95)
# - 5 from CTHG (97, 98, 99, 100, 101)
CTHG_BHGC_NON_LIDAR: tuple[int, ...] = (83, 84, 85, 86, 87)
CTHG_CFKC_NON_LIDAR: tuple[int, ...] = (89, 90, 91, 92, 93, 95)
CTHG_SELF_NON_LIDAR: tuple[int, ...] = (97, 98, 99, 100, 101)
CTHG_MSUB_COL_INDICES: tuple[int, ...] = (
    fbgr.MSUB_COL_INDICES + CTHG_BHGC_NON_LIDAR + CTHG_CFKC_NON_LIDAR + CTHG_SELF_NON_LIDAR
)


def build_cthg_extra_stack(
    ddir: Path | None = None,
    wdir: Path | None = None,
    out_path: Path | None = None,
    force: bool = False,
    log=print,
) -> tuple[np.ndarray, dict[str, Any]]:
    """Build or load the 6-channel `CTHG` physical feature stack (`cthg_extra_6ch.npy`, float32)."""
    if ddir is None:
        ddir = paths.data_dir()
    if wdir is None:
        wdir = paths.work_dir()
    if out_path is None:
        out_path = wdir / "cthg_extra_6ch.npy"
    receipt_path = out_path.with_suffix(".json")

    if out_path.exists() and receipt_path.exists() and not force:
        mm = open_memmap(out_path, mode="r")
        meta = json.loads(receipt_path.read_text())
        if mm.shape[2] == len(CTHG_EXTRA_CHANNELS):
            return mm, meta

    base_mm = open_memmap(wdir / "feature_stack.npy", mode="r")
    spcp_mm = open_memmap(wdir / "spcp_extra_20ch.npy", mode="r")
    trhv_mm = open_memmap(wdir / "trhv_extra_8ch.npy", mode="r")
    ldgi_mm = open_memmap(wdir / "ldgi_extra_8ch.npy", mode="r")
    fbgr_mm = open_memmap(wdir / "fbgr_extra_12ch.npy", mode="r")
    bhgc_mm = open_memmap(wdir / "bhgc_extra_6ch.npy", mode="r")
    cfkc_mm = open_memmap(wdir / "cfkc_extra_8ch.npy", mode="r")

    foot = np.load(wdir / "bands" / "_footprint.npy") > 0
    h, w = foot.shape
    out_path.parent.mkdir(parents=True, exist_ok=True)
    mm = open_memmap(out_path, mode="w+", dtype=np.float32, shape=(h, w, len(CTHG_EXTRA_CHANNELS)))

    lahontan_orth = np.asarray(spcp_mm[:, :, 14], dtype=np.float32)
    tiger_clean = np.asarray(trhv_mm[:, :, 4], dtype=np.float32)
    depth_base = np.asarray(base_mm[:, :, 14], dtype=np.float32)
    elev_slope = np.asarray(base_mm[:, :, 18], dtype=np.float32)
    non_flat_basin = np.float32(1.0) - np.float32(0.55) * np.clip(
        (depth_base - np.float32(320.0)) / np.float32(380.0), 0.0, 1.0
    ) * np.clip((np.float32(1.6) - elev_slope) / np.float32(1.6), 0.0, 1.0)
    deconf_gate = (
        (np.float32(0.35) + np.float32(0.65) * tiger_clean)
        * (np.float32(0.45) + np.float32(0.55) * lahontan_orth)
        * non_flat_basin
    )
    del depth_base, elev_slope

    # --- Ch 0 (97): Cooper & Cowan (2006) Joint Gravity/Magnetic Tilt-Phase Contact Wall ---
    gx_raw = np.where(foot, np.asarray(base_mm[:, :, 17], dtype=np.float32), 0.0)
    gy_raw = np.where(foot, np.asarray(base_mm[:, :, 10], dtype=np.float32), 0.0)
    gx_s = gaussian_filter(gx_raw, sigma=1.6, mode="nearest")
    gy_s = gaussian_filter(gy_raw, sigma=1.6, mode="nearest")
    del gx_raw, gy_raw
    dgx_dx = np.gradient(gx_s, axis=1).astype(np.float32)
    dgy_dy = np.gradient(gy_s, axis=0).astype(np.float32)
    vvd_g = -(dgx_dx + dgy_dy)  # Laplace: d^2g/dz^2 = -(dg_E/dx + dg_N/dy)
    hgm_g = np.hypot(gx_s, gy_s) + np.float32(1e-5)
    theta_g = np.arctan2(vvd_g, hgm_g).astype(np.float32)
    sech2_g = np.float32(1.0) / (np.cosh(np.clip(theta_g / np.float32(0.38), -6.0, 6.0)) ** 2)
    psi_g = np.arctan2(gy_s, gx_s).astype(np.float32)
    del gx_s, gy_s, dgx_dx, dgy_dy, vvd_g, theta_g

    mag_tilt = np.where(foot, np.asarray(base_mm[:, :, 5], dtype=np.float32), 0.0)
    mt_med = float(np.median(mag_tilt[foot]))
    mt_mad = float(np.median(np.abs(mag_tilt[foot] - mt_med))) + 1e-5
    mt_norm = (mag_tilt - np.float32(mt_med)) / np.float32(1.4826 * mt_mad)
    del mag_tilt
    mt_s = gaussian_filter(mt_norm, sigma=1.4, mode="nearest")
    del mt_norm
    dmt_dy, dmt_dx = np.gradient(mt_s)
    psi_m = np.arctan2(dmt_dy, dmt_dx).astype(np.float32)
    sech2_m = np.float32(1.0) / (np.cosh(np.clip(mt_s / np.float32(0.45), -6.0, 6.0)) ** 2)
    del mt_s, dmt_dy, dmt_dx

    coplanar = np.cos(psi_g - psi_m) ** 2
    del psi_g, psi_m
    hgm_u = spcp.robust_unit_f32(hgm_g, foot, pct=99.4)
    del hgm_g
    bhgc_gv = np.asarray(bhgc_mm[:, :, 0], dtype=np.float32)
    bhgc_mt = np.asarray(bhgc_mm[:, :, 1], dtype=np.float32)

    cc_raw = (
        np.float32(0.38) * (sech2_g * hgm_u * (np.float32(0.35) + np.float32(0.65) * sech2_m * coplanar))
        + np.float32(0.34) * bhgc_gv
        + np.float32(0.28) * bhgc_mt
    ) * deconf_gate
    del sech2_g, sech2_m, coplanar, hgm_u, bhgc_gv, bhgc_mt
    cooper_cowan_wall = spcp.robust_unit_f32(
        mdrc.directional_chain_max(cc_raw.astype(np.float32), foot, halflen=2),
        foot,
        pct=99.5,
    )
    mm[:, :, 0] = cooper_cowan_wall
    del cc_raw
    gc.collect()
    log("  [CTHG] ch 0 (Cooper-Cowan joint gravity/magnetic tilt-phase contact wall) built")

    # --- Ch 1 (98): Fluvial Delta-Chi Knickzone x Laplace Basement Throw Conduit ---
    chi_halo = np.asarray(cfkc_mm[:, :, 2], dtype=np.float32)
    chi_knick = np.asarray(cfkc_mm[:, :, 3], dtype=np.float32)
    pied_horst = np.asarray(bhgc_mm[:, :, 2], dtype=np.float32)
    grav_uc = np.asarray(fbgr_mm[:, :, 0], dtype=np.float32)
    dip_asymm = np.asarray(fbgr_mm[:, :, 2], dtype=np.float32)
    depth_throw = spcp.robust_unit_f32(np.asarray(base_mm[:, :, 30], dtype=np.float32), foot, pct=99.4)

    knick_laplace_raw = (
        np.float32(0.30) * chi_knick * (np.float32(0.40) + np.float32(0.60) * cooper_cowan_wall)
        + np.float32(0.24) * chi_halo * (np.float32(0.40) + np.float32(0.60) * pied_horst)
        + np.float32(0.22) * pied_horst * (np.float32(0.45) + np.float32(0.55) * depth_throw)
        + np.float32(0.14) * grav_uc
        + np.float32(0.10) * dip_asymm
    ) * deconf_gate
    del chi_halo, chi_knick, pied_horst, grav_uc, dip_asymm, depth_throw
    knickzone_laplace = spcp.robust_unit_f32(
        mdrc.directional_chain_max(knick_laplace_raw.astype(np.float32), foot, halflen=2),
        foot,
        pct=99.5,
    )
    mm[:, :, 1] = knickzone_laplace
    del knick_laplace_raw
    gc.collect()
    log("  [CTHG] ch 1 (Fluvial delta-chi knickzone x Laplace basement throw conduit) built")

    # --- Ch 2 (99): MT Smectite Clay-Cap Lateral Phase Boundary x 4-Block 214Bi Radon & Paleo-Sinter Halo ---
    bhgc_hydro = np.asarray(bhgc_mm[:, :, 4], dtype=np.float32)
    cfkc_pied_therm = np.asarray(cfkc_mm[:, :, 4], dtype=np.float32)
    radon_crest = np.asarray(fbgr_mm[:, :, 3], dtype=np.float32)
    sil_pot_dog = np.asarray(fbgr_mm[:, :, 4], dtype=np.float32)
    mag_demag = spcp.robust_unit_f32(np.asarray(spcp_mm[:, :, 7], dtype=np.float32), foot, pct=99.4)

    hydro_halo_raw = (
        np.float32(0.34) * bhgc_hydro
        + np.float32(0.28) * cfkc_pied_therm
        + np.float32(0.16) * radon_crest * (np.float32(0.40) + np.float32(0.60) * cooper_cowan_wall)
        + np.float32(0.12) * mag_demag
        + np.float32(0.10) * sil_pot_dog
    ) * deconf_gate
    del bhgc_hydro, cfkc_pied_therm, radon_crest, sil_pot_dog, mag_demag
    mt_claycap_halo = spcp.robust_unit_f32(
        mdrc.directional_chain_max(hydro_halo_raw.astype(np.float32), foot, halflen=2),
        foot,
        pct=99.5,
    )
    mm[:, :, 2] = mt_claycap_halo
    del hydro_halo_raw
    gc.collect()
    log("  [CTHG] ch 2 (MT smectite clay-cap lateral phase edge x 214Bi radon & sinter halo) built")

    # --- Ch 3 (100): Morris Slip-Dilation & Geodetic Strain Tensor x 10m Seamless Curvature Ridge ---
    dem10_curv = np.asarray(cfkc_mm[:, :, 0], dtype=np.float32)
    dem10_lin = np.asarray(cfkc_mm[:, :, 1], dtype=np.float32)
    bhgc_trans = np.asarray(bhgc_mm[:, :, 3], dtype=np.float32)
    morris_obliq = np.asarray(fbgr_mm[:, :, 6], dtype=np.float32)

    stepover_raw = (
        np.float32(0.32) * dem10_curv * (np.float32(0.45) + np.float32(0.55) * bhgc_trans)
        + np.float32(0.28) * dem10_lin * (np.float32(0.45) + np.float32(0.55) * morris_obliq)
        + np.float32(0.24) * bhgc_trans
        + np.float32(0.16) * cooper_cowan_wall
    ) * deconf_gate
    del dem10_curv, dem10_lin, bhgc_trans, morris_obliq
    morris_stepover = spcp.robust_unit_f32(
        mdrc.directional_chain_max(stepover_raw.astype(np.float32), foot, halflen=2),
        foot,
        pct=99.5,
    )
    mm[:, :, 3] = morris_stepover
    del stepover_raw
    gc.collect()
    log("  [CTHG] ch 3 (Morris slip-dilation & strain tensor x 10m seamless curvature ridge) built")

    # --- Ch 4 (101): Unified 100%-Coverage Strictly 1m-LiDAR-Free Multi-Physics Gap Conduit Carrier ---
    cfkc_gap = np.asarray(cfkc_mm[:, :, 6], dtype=np.float32)
    gap_raw = (
        np.float32(0.26) * knickzone_laplace
        + np.float32(0.24) * cooper_cowan_wall
        + np.float32(0.22) * morris_stepover
        + np.float32(0.16) * mt_claycap_halo
        + np.float32(0.12) * cfkc_gap
    ) * deconf_gate
    del cfkc_gap
    seamfree_gap_conduit = spcp.robust_unit_f32(
        fbgr.sharpen_probability_crest(gap_raw.astype(np.float32), foot, crest_boost=0.45),
        foot,
        pct=99.5,
    )
    mm[:, :, 4] = seamfree_gap_conduit
    del gap_raw
    gc.collect()
    log("  [CTHG] ch 4 (Unified 100%-coverage strictly 1m-LiDAR-free gap conduit carrier) built")

    # --- Ch 5 (102): Unified Dual-Horizon Structural-Geothermal Crest Spine ---
    lidar_valid = (np.asarray(spcp_mm[:, :, 12], dtype=np.float32) > 0.5) & foot
    dem1m_open = np.asarray(cfkc_mm[:, :, 5], dtype=np.float32)
    cfkc_crest = np.asarray(cfkc_mm[:, :, 7], dtype=np.float32)
    bhgc_spine = np.asarray(bhgc_mm[:, :, 5], dtype=np.float32)
    lidar_chain = np.asarray(fbgr_mm[:, :, 10], dtype=np.float32)

    non_lidar_core = (
        np.float32(0.32) * seamfree_gap_conduit
        + np.float32(0.24) * knickzone_laplace
        + np.float32(0.20) * cooper_cowan_wall
        + np.float32(0.14) * mt_claycap_halo
        + np.float32(0.10) * morris_stepover
    ).astype(np.float32)
    del cooper_cowan_wall, knickzone_laplace, mt_claycap_halo, morris_stepover, seamfree_gap_conduit

    in_lidar_core = (
        np.float32(0.46) * non_lidar_core
        + np.float32(0.22) * dem1m_open
        + np.float32(0.18) * cfkc_crest
        + np.float32(0.14) * (np.float32(0.55) * bhgc_spine + np.float32(0.45) * lidar_chain)
    ).astype(np.float32)
    del dem1m_open, cfkc_crest, bhgc_spine, lidar_chain

    unified_raw = np.where(lidar_valid, in_lidar_core, non_lidar_core) * deconf_gate
    del lidar_valid, in_lidar_core, non_lidar_core, deconf_gate, lahontan_orth, tiger_clean, non_flat_basin
    unified_spine = spcp.robust_unit_f32(
        fbgr.sharpen_probability_crest(unified_raw.astype(np.float32), foot, crest_boost=0.52),
        foot,
        pct=99.5,
    )
    mm[:, :, 5] = unified_spine
    del unified_raw, unified_spine

    if hasattr(mm, "flush"):
        mm.flush()
    gc.collect()

    meta: dict[str, Any] = {
        "schema_version": 1,
        "hypothesis": "H-APART3-2 (CTHG-DHC)",
        "channels": list(CTHG_EXTRA_CHANNELS),
        "shape": [h, w, len(CTHG_EXTRA_CHANNELS)],
        "dtype": "float32",
        "label_free": True,
        "total_channels_with_template": 103,
        "msub_pure_non_lidar_col_count": len(CTHG_MSUB_COL_INDICES),
    }
    receipt_path.write_text(json.dumps(meta, indent=2) + "\n")
    log("  [CTHG] ch 5 (Unified Dual-Horizon Structural-Geothermal Crest Spine) built")
    return open_memmap(out_path, mode="r"), meta


def gather_103ch(
    base_stack: np.ndarray,
    spcp_stack: np.ndarray,
    trhv_stack: np.ndarray,
    ldgi_stack: np.ndarray,
    fbgr_stack: np.ndarray,
    bhgc_stack: np.ndarray,
    cfkc_stack: np.ndarray,
    cthg_stack: np.ndarray,
    ys: np.ndarray,
    xs: np.ndarray,
    col_indices: tuple[int, ...] | None = None,
) -> np.ndarray:
    xb = np.asarray(base_stack[ys, xs, :], dtype=np.float32)
    xs_arr = np.asarray(spcp_stack[ys, xs, :], dtype=np.float32)
    xt = np.asarray(trhv_stack[ys, xs, :], dtype=np.float32)
    xl = np.asarray(ldgi_stack[ys, xs, :], dtype=np.float32)
    xf = np.asarray(fbgr_stack[ys, xs, :], dtype=np.float32)
    xg = np.asarray(bhgc_stack[ys, xs, :], dtype=np.float32)
    xc = np.asarray(cfkc_stack[ys, xs, :], dtype=np.float32)
    xm = np.asarray(cthg_stack[ys, xs, :], dtype=np.float32)
    full = np.hstack([xb, xs_arr, xt, xl, xf, xg, xc, xm])
    if col_indices is not None:
        return full[:, col_indices]
    return full


def run_leakage_canary_103ch(
    base_stack: np.ndarray,
    spcp_stack: np.ndarray,
    trhv_stack: np.ndarray,
    ldgi_stack: np.ndarray,
    fbgr_stack: np.ndarray,
    bhgc_stack: np.ndarray,
    cfkc_stack: np.ndarray,
    cthg_stack: np.ndarray,
    base_names: list[str],
    ctx,
    max_auc: float = 0.90,
    stride: int = 4,
) -> dict[str, Any]:
    """Protocol Rule 4 single-feature two-polarity leakage canary across all 103 channels."""
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

    stacks = (base_stack, spcp_stack, trhv_stack, ldgi_stack, fbgr_stack, bhgc_stack, cfkc_stack, cthg_stack)
    offsets = np.cumsum([0] + [s.shape[2] for s in stacks])
    all_names = (
        list(base_names)
        + list(spcp.SPCP_EXTRA_CHANNELS)
        + list(trhv.TRHV_EXTRA_CHANNELS)
        + list(ldgi.LDGI_EXTRA_CHANNELS)
        + list(fbgr.FBGR_EXTRA_CHANNELS)
        + list(bhgc.BHGC_EXTRA_CHANNELS)
        + list(cfkc.CFKC_EXTRA_CHANNELS)
        + list(CTHG_EXTRA_CHANNELS)
    )
    assert len(all_names) == int(offsets[-1]) == 103

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
                "channel": name,
                "in_msub_pure_non_lidar": i in CTHG_MSUB_COL_INDICES,
                "raw_auc": round(raw_auc, 6),
                "oriented_auc": round(auc_dir, 6),
                "passed": bool(auc_dir <= max_auc),
            }
        )

    worst = max(rows, key=lambda r: r["oriented_auc"])
    cthg_rows = [r for r in rows if r["index"] >= 97]
    return {
        "passed": all(r["passed"] for r in rows),
        "threshold_auc": max_auc,
        "n_features_tested": len(rows),
        "max_oriented_auc": worst["oriented_auc"],
        "worst_channel": worst["channel"],
        "cthg_6ch_max_oriented_auc": max(r["oriented_auc"] for r in cthg_rows),
        "cthg_6ch_aucs": {r["channel"]: r["oriented_auc"] for r in cthg_rows},
        "n_withheld_pos_tested": int(py.size),
        "n_active_neg_sampled": int(ny.size),
        "per_channel": rows,
    }


def fit_cthg_classifier(
    base_stack: np.ndarray,
    spcp_stack: np.ndarray,
    trhv_stack: np.ndarray,
    ldgi_stack: np.ndarray,
    fbgr_stack: np.ndarray,
    bhgc_stack: np.ndarray,
    cfkc_stack: np.ndarray,
    cthg_stack: np.ndarray,
    train_region: np.ndarray,
    visible_train: np.ndarray,
    foot: np.ndarray,
    col_indices: tuple[int, ...] | None = None,
    seed: int = 57,
    max_pos: int = 44_000,
    n_neg_hard: int = 88_000,
    n_neg_unif: int = 88_000,
) -> HistGradientBoostingClassifier:
    """Fit fold-local collar-hardened HistGradientBoostingClassifier on 103 (`M_Full`) or 87 (`M_Sub`) channels."""
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

    X = gather_103ch(
        base_stack, spcp_stack, trhv_stack, ldgi_stack, fbgr_stack, bhgc_stack, cfkc_stack, cthg_stack,
        ys, xs, col_indices=col_indices,
    )
    clf = HistGradientBoostingClassifier(
        max_iter=175,
        learning_rate=0.052,
        max_leaf_nodes=47,
        min_samples_leaf=85,
        l2_regularization=3.0,
        early_stopping=False,
        random_state=seed,
    )
    clf.fit(X, y)
    del X, y, ys, xs
    return clf


def predict_chunked_cthg(
    clf: HistGradientBoostingClassifier,
    base_stack: np.ndarray,
    spcp_stack: np.ndarray,
    trhv_stack: np.ndarray,
    ldgi_stack: np.ndarray,
    fbgr_stack: np.ndarray,
    bhgc_stack: np.ndarray,
    cfkc_stack: np.ndarray,
    cthg_stack: np.ndarray,
    mask: np.ndarray,
    col_indices: tuple[int, ...] | None = None,
    chunk_size: int = 180_000,
) -> np.ndarray:
    out = np.zeros(mask.shape, dtype=np.float32)
    ys, xs = np.nonzero(mask)
    for start in range(0, ys.size, chunk_size):
        sl = slice(start, min(start + chunk_size, ys.size))
        X = gather_103ch(
            base_stack, spcp_stack, trhv_stack, ldgi_stack, fbgr_stack, bhgc_stack, cfkc_stack, cthg_stack,
            ys[sl], xs[sl], col_indices=col_indices,
        )
        out[ys[sl], xs[sl]] = clf.predict_proba(X)[:, 1].astype(np.float32)
        del X
    return out


def build_cthg_off_catalogue_surface(
    cfkc_stack: np.ndarray,
    bhgc_stack: np.ndarray,
    cthg_stack: np.ndarray,
    trhv_stack: np.ndarray,
    foot: np.ndarray,
) -> np.ndarray:
    """Build the unsharpened off-catalogue discovery surface combining CTHG, CFKC, and BHGC conduits."""
    cfkc_conduit = np.asarray(cfkc_stack[:, :, 7], dtype=np.float32)
    bhgc_conduit = np.asarray(bhgc_stack[:, :, 2], dtype=np.float32)
    cooper_wall = np.asarray(cthg_stack[:, :, 0], dtype=np.float32)
    knick_throw = np.asarray(cthg_stack[:, :, 1], dtype=np.float32)
    mt_halo = np.asarray(cthg_stack[:, :, 2], dtype=np.float32)
    morris_curv = np.asarray(cthg_stack[:, :, 3], dtype=np.float32)
    tiger_clean = np.asarray(trhv_stack[:, :, 4], dtype=np.float32)

    raw = (
        np.float32(0.24) * cfkc_conduit
        + np.float32(0.22) * bhgc_conduit
        + np.float32(0.20) * knick_throw
        + np.float32(0.18) * cooper_wall
        + np.float32(0.16) * (np.float32(0.55) * morris_curv + np.float32(0.45) * mt_halo)
    ) * (np.float32(0.35) + np.float32(0.65) * tiger_clean)
    return spcp.robust_unit_f32(raw, foot, pct=99.5)


def build_cthg_smooth_stage1_surface(
    surface_63ch: np.ndarray,
    p_dual_103ch: np.ndarray,
    cthg_stack: np.ndarray,
    trhv_stack: np.ndarray,
    visible_mask: np.ndarray,
    foot: np.ndarray,
    region_mask: np.ndarray | None = None,
    w_63: float = 0.16,
    w_103: float = 0.84,
    w_seamfree: float = 0.26,
    w_rl: float = 0.54,
) -> tuple[np.ndarray, np.ndarray]:
    """Build 100% smooth Stage-1 belief surface prior to 1-px ridge-crest sharpening (zero boundary-cliff artifacts)."""
    if region_mask is None:
        region_mask = foot
    m = region_mask & foot
    vis = np.asarray(visible_mask, bool) & foot
    dv = distance_transform_edt(~vis).astype(np.float32)
    pt = trhv.visible_tip_stepover_cone(vis, foot)[m]
    rl = ldgi.anisotropic_tip_relay_cone(vis, foot)[m]
    cone = np.float32(1.0 - w_rl) * pt + np.float32(w_rl) * rl
    del pt, rl
    sf = np.asarray(cthg_stack[:, :, 4], dtype=np.float32)[m]
    tg = np.asarray(trhv_stack[:, :, 4], dtype=np.float32)[m]
    p103 = p_dual_103ch[m]
    s63 = surface_63ch[m]
    w_c = np.float32(w_seamfree)
    p103_enh = (np.float32(1.0) - w_c) * p103 + w_c * (sf * np.sqrt(np.maximum(p103, np.float32(0.02))))

    s1 = np.zeros(foot.shape, dtype=np.float32)
    s1[m] = (
        (
            np.float32(w_63) * s63
            + np.float32(w_103) * p103_enh * (np.float32(1.0) + np.float32(0.25) * cone)
        )
        * (np.float32(1.0) + np.float32(0.55) * cone)
        * (np.float32(0.38) + np.float32(0.62) * tg)
    )
    return s1, dv


def build_exp1_cthg_surface(
    p_dual: np.ndarray,
    cthg_stack: np.ndarray,
    trhv_stack: np.ndarray,
    visible_mask: np.ndarray,
    foot: np.ndarray,
    region_mask: np.ndarray | None = None,
    w_seamfree: float = 0.22,
    w_rl: float = 0.50,
) -> np.ndarray:
    """`EXP1_CTHG_DUALCOVER_103` surface: 103/87 Dual-Cover posterior + CTHG seamfree carrier + blended tip/relay cone."""
    if region_mask is None:
        region_mask = foot
    mask = region_mask & foot
    vis = np.asarray(visible_mask, bool) & foot
    pt = trhv.visible_tip_stepover_cone(vis, foot)[mask]
    rl = ldgi.anisotropic_tip_relay_cone(vis, foot)[mask]
    cone = np.float32(1.0 - w_rl) * pt + np.float32(w_rl) * rl
    del pt, rl
    seamfree = np.asarray(cthg_stack[:, :, 4], dtype=np.float32)
    tiger_clean = np.asarray(trhv_stack[:, :, 4], dtype=np.float32)

    out = np.zeros(foot.shape, dtype=np.float32)
    pd = p_dual[mask]
    sf = seamfree[mask]
    tg = tiger_clean[mask]

    w_c = np.float32(w_seamfree)
    base_p = (np.float32(1.0) - w_c) * pd + w_c * (sf * np.sqrt(np.maximum(pd, np.float32(0.02))))
    out[mask] = (
        base_p
        * (np.float32(1.0) + np.float32(0.25) * cone)
        * (np.float32(1.0) + np.float32(0.55) * cone)
        * (np.float32(0.38) + np.float32(0.62) * tg)
    )
    return out


def build_exp2_cthg_hybrid_surface(
    s1_smooth: np.ndarray,
    cb_surface: np.ndarray,
    d_vis: np.ndarray,
    foot: np.ndarray,
    region_mask: np.ndarray | None = None,
    w_cb: float = 0.22,
) -> np.ndarray:
    """`EXP2_CTHG_HYBRID_CREST` single-stage hybrid surface blending smooth Stage-1 with off-catalogue CTHG conduit."""
    if region_mask is None:
        region_mask = foot
    mask = region_mask & foot
    s1_u = spcp.robust_unit_f32(s1_smooth, mask, pct=99.5)
    off_gate = np.clip((d_vis.astype(np.float32) - np.float32(5.5)) / np.float32(4.0), np.float32(0.0), np.float32(1.0))
    out = np.zeros(foot.shape, dtype=np.float32)
    out[mask] = np.clip(
        np.float32(1.0 - w_cb) * s1_u[mask] + np.float32(w_cb) * (cb_surface[mask] * off_gate[mask]),
        np.float32(0.0),
        np.float32(1.0),
    )
    return out


def emit_cthg_post_moat_dhc(
    s1_smooth: np.ndarray,
    pd_sub: np.ndarray,
    cb_sub: np.ndarray,
    vis_m: np.ndarray,
    elig_m: np.ndarray,
    foot_m: np.ndarray,
    d_v: np.ndarray,
    budget: int,
    f_stage1: float = 0.630,
    inner_dep: float = 0.20,
    moat_dep: float = 0.72,
    w_pd_s2: float = 0.15,
    min_sep_px: float = 3.24,
    off_cat_min_dist_px: float = 5.5,
) -> tuple[np.ndarray, dict[str, Any]]:
    """Post-Sharpened Dead-Moat & Decoupled Dual-Horizon Clump-Free Co-Placement (`EXP3_CTHG_CLUMPFREE_DHC`).

    Key mechanism:
    1. Sharpens the 100% smooth `s1_smooth` surface via `mdrc.sharpen_ridge_crest` FIRST so that
       the curvature operator never sees a distance-moat step boundary (eliminating boundary-cliff
       ring artifacts).
    2. Applies Post-Sharpening Dead-Moat & Detached-Stepover Reweighting to the 1-px fault crests
       (`inner_dep` on `2 < d_vis < 3 px`, `moat_dep` on `3.0 <= d_vis <= 4.9 px`, and `+0.32`
       detached stepover boost on `d_vis >= 5.0 px`) and emits `b_a = round(budget * f_stage1)`
       dots with `min_sep_px = 3.24 > 3.0 px` (`0.00% Clump>=3`).
    3. Decouples Stage 2 (`rem_b = budget - b_a`) by blending `cb_sub` with the bounded OOF
       posterior `np.clip(pd_sub, 0, 1)` (`w_pd_s2 = 0.15`) inside `d_vis > 5.5 px`, sharpening
       onto 1-px crests, and placing the remaining dots into the residual coverage field with
       `initial_mask=dots_a` and `min_sep_px = 3.24`.
    """
    from gems32 import emitter

    b_a = max(1, min(int(budget), int(round(int(budget) * float(f_stage1)))))
    crest1 = mdrc.sharpen_ridge_crest(s1_smooth, foot_m)
    in_inner = ((d_v > np.float32(2.0)) & (d_v < np.float32(3.0))).astype(np.float32)
    in_moat = ((d_v >= np.float32(3.0)) & (d_v <= np.float32(4.9))).astype(np.float32)
    moat_gate = np.float32(1.0) - np.float32(inner_dep) * in_inner - np.float32(moat_dep) * in_moat
    det_ring = np.exp(-((d_v - np.float32(8.8)) / np.float32(4.8)) ** 2) * (d_v >= np.float32(5.0))
    crest1 = crest1 * moat_gate * (np.float32(1.0) + np.float32(0.32) * det_ring)

    elig_a = elig_m & foot_m & (d_v > np.float32(2.0)) & (crest1 > 0.0)
    n_elig_a = int(elig_a.sum())
    max_sup_a = max(int(b_a) * 8, min(n_elig_a, 35_000))
    if n_elig_a > max_sup_a:
        vals_a = crest1[elig_a]
        thr_a = float(np.partition(vals_a, n_elig_a - max_sup_a)[n_elig_a - max_sup_a])
        sup_a = elig_a & (crest1 >= thr_a)
    else:
        sup_a = elig_a
    field_a = np.where(sup_a, crest1, 0.0).astype(np.float64)
    dots_a, rep_a = emitter.emit(
        field_a, budget=int(b_a), prior_dti=0.0, gain_floor=0.0, min_sep_px=float(min_sep_px)
    )
    del crest1, field_a

    n_a = int(dots_a.sum())
    rem_b = int(budget) - n_a
    if rem_b <= 0:
        return dots_a, {
            "budget_total": int(budget),
            "budget_stage1": n_a,
            "budget_stage2": 0,
            "f_stage1": float(f_stage1),
            "min_sep_px": float(min_sep_px),
        }

    off_gate = np.clip((d_v - float(off_cat_min_dist_px)) / 4.0, 0.0, 1.0).astype(np.float32)
    s2_raw = (
        cb_sub
        * ((np.float32(1.0 - w_pd_s2)) + np.float32(w_pd_s2) * np.clip(pd_sub, 0.0, 1.0))
        * off_gate
    ).astype(np.float32)
    s2_crest = mdrc.sharpen_ridge_crest(s2_raw, foot_m)
    elig_b = elig_m & foot_m & (d_v > np.float32(2.0)) & (~dots_a) & (s2_crest > 0.0)
    n_elig_b = int(elig_b.sum())
    max_sup_b = max(int(rem_b) * 10, min(n_elig_b, 35_000))
    if n_elig_b > max_sup_b:
        vals_b = s2_crest[elig_b]
        thr_b = float(np.partition(vals_b, n_elig_b - max_sup_b)[n_elig_b - max_sup_b])
        sup_b = elig_b & (s2_crest >= thr_b)
    else:
        sup_b = elig_b
    field_b = np.where(sup_b, s2_crest, 0.0).astype(np.float64)
    dots_b, rep_b = emitter.emit(
        field_b,
        budget=int(rem_b),
        prior_dti=0.0,
        gain_floor=0.0,
        initial_mask=dots_a,
        min_sep_px=float(min_sep_px),
    )
    dots_total = dots_a | dots_b
    return dots_total, {
        "budget_total": int(dots_total.sum()),
        "budget_stage1": n_a,
        "budget_stage2": int(dots_b.sum()),
        "f_stage1": float(f_stage1),
        "inner_dep": float(inner_dep),
        "moat_dep": float(moat_dep),
        "w_pd_s2": float(w_pd_s2),
        "min_sep_px": float(min_sep_px),
        "off_cat_min_dist_px": float(off_cat_min_dist_px),
        "stage1_report": rep_a,
        "stage2_report": rep_b,
    }


def build_cthg_dual_horizon_belief_surface(
    s1_smooth: np.ndarray,
    cb_surface: np.ndarray,
    visible_mask: np.ndarray,
    foot: np.ndarray,
    f_stage1: float = 0.630,
    w_pd_s2: float = 0.15,
    off_cat_min_dist_px: float = 5.5,
) -> np.ndarray:
    """Build the unified continuous pre-placement belief surface in `[0, 1]` for Step-A uniqueness checks."""
    return cfkc.build_stationary_dual_horizon_belief_surface(
        s1_smooth,
        cb_surface,
        visible_mask,
        foot,
        f_stage1=f_stage1,
        w_s1=w_pd_s2,
        off_cat_min_dist_px=off_cat_min_dist_px,
    )
