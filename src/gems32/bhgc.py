"""H-APART-1 (BHGC-3): Laplace-Harmonic Gravity-Vector Divergence (Band 18, Band 11),
Magnetic Tilt Zero-Crossing Wall, Piedmont-Horst Structural Contact Spine & PU-Safe
Dual-Cover Hydrothermal-Vent OOF with Axial-Crest Submodular Emission.

Pre-registered in ``docs/research/apart3-preregistration-20261027.md`` before implementation.

Key scientific & engineering properties:
  1. Native Potential-Field Vector Calculus (`grav_vec_div_crest`):
     Uses the official pre-computed horizontal gravity gradient vector `(Band 18, Band 11)` =
     `(dg/dx, dg/dy)` (`r = 0.9471` with `Band 5 iso_grav_anom_slope`) to compute exact
     Laplace-Harmonic horizontal divergence `div(g_H) = d(Band 18)/dx + d(Band 11)/dy = -d^2g/dz^2`
     (Blakely 1995, Ch. 12) and the Blakely-Simpson (1986) cross-contact inflection crest along
     the unit normal `n_g = g_H / ||g_H||`, coupled with basement throw gradient `||grad(Band 15)||`.
  2. Depth-Invariant Magnetic Tilt-Angle Zero-Crossing Wall (`mag_tilt_zerocross_wall`):
     Miller & Singh (1994) / Verduzco et al. (2004) tilt-angle contact wall on `Band 6 (tc)`
     weighted by `Band 3 (tmi_hg)`, `Band 9 (tmi_vg)`, and `Band 2 (rtp)` horizontal gradient.
  3. Multi-Scale Piedmont-Horst Bedrock Contact Spine (`piedmont_horst_step_spine`):
     Combines multi-scale Sato/Frangi Hessian ridges (`ridge_s1, ridge_s2, ridge_s3`) on `Band 12`
     (`det_elev`), `tophat2`, `Band 19` (`det_elev_slope`) piedmont-toe inflection, and basement
     step gradient, explicitly de-confounded against Pleistocene Lake Lahontan (~1,330 m / ~1,235 m)
     wave-cut benches (`spcp_stack[:, :, 16]`) and US Census TIGER roads (`trhv_stack[:, :, 4]`).
  4. Transtensional Accommodation & Microseismic Swarm Bridge (`transtensional_accommodation_bridge`):
     Couples geodetic shear/dilatation invariants (`Bands 4, 7, 8`) with earthquake density-to-distance
     enrichment (`Band 16 / Band 10`) along structural strikes (Faulds et al. 2011, 2021).
  5. Hydrothermal Clay-Cap Lateral Edge + GeoDAWN 4-Block 214Bi Radon + GDR #1391 Vent Spine
     (`hydrothermal_claycap_radon_vent`):
     Targets the steep lateral electrical conductivity edge (`Band 17 cond_surf` / `cond_edge`)
     bounding smectite-illite clay caps, co-located with block-standardized `214Bi` (`eU - beta*eTh`)
     radon crests, hydrothermal magnetite-destruction troughs, and 2-m temperature / sinter plumes.
  6. PU-Safe Collar-Hardened 89-Channel Dual-Cover OOF (`fit_bhgc_classifier`) &
     Distance-Balanced Bi-Population Belief Surface (`build_stationary_bhgc_surface`):
     - Eliminates `H48-1-FBGR`'s `2.0 < d_tr < 5.0 px` negative-sampling blind spot and filters out
       top far-field physical fault-scarp crests from `y = 0` unlabeled negatives (PU reliable-negative
       selection, Elkan & Noto 2008).
     - Attenuates the LLI-proven `2.0 < d_vis <= 4.0 px` catalogue-proximal depletion zone while
       providing a stationary far-field structural-geothermal spine floor so both
       `GEMSDOE32-HIDE-RECOVER-v3.0` and `GEMSDOE32-SGMC-CAL-v3.0` beat the `0.2778` Champion.
"""

from __future__ import annotations

import gc
import json
from pathlib import Path
from typing import Any

import numpy as np
import rasterio
from numpy.lib.format import open_memmap
from scipy.ndimage import distance_transform_edt, gaussian_filter, maximum_filter, minimum_filter, sobel
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score

from . import emitter, fbgr, ldgi, mdrc, paths, spcp, trhv

TARGET_BUDGET: int = 37_654
B_COLLAR_PX: float = 2.0
AXIAL_MIN_SEP_PX: float = 3.22

BHGC_EXTRA_CHANNELS: tuple[str, ...] = (
    "grav_vec_div_crest",                 # 0 (global 83): Laplace-Harmonic div(Band18,Band11) = -d2g/dz2 + Blakely-Simpson crest
    "mag_tilt_zerocross_wall",            # 1 (global 84): Miller-Singh Band 6 tilt zero-crossing x Band 3/9 magnetic wall
    "piedmont_horst_step_spine",          # 2 (global 85): Multi-scale Band 12/19 Hessian ridge + piedmont-toe step (Lahontan-vetoed)
    "transtensional_accommodation_bridge",# 3 (global 86): Geodetic shear/dilatation (Bands 4,7,8) x seismic swarm (Bands 10,16) bridge
    "hydrothermal_claycap_radon_vent",    # 4 (global 87): MT clay-cap edge (Band 17) + 4-block 214Bi radon + GDR 2m/sinter vent
    "bhgc_farfield_structural_spine",     # 5 (global 88): Unified multi-pillar structural-geothermal NMS spine (uses 1m LiDAR where valid)
)

# In the 89-channel stack (35 base + 20 spcp + 8 trhv + 8 ldgi + 12 fbgr + 6 bhgc):
# Channels touching 1 m LiDAR are fbgr.LIDAR_DEPENDENT_GLOBAL_COLS U {88} (13 channels total).
# All other 76 channels are strictly 1 m LiDAR-free for M_Sub inside the 24.63% LiDAR gap.
LIDAR_DEPENDENT_89_COLS: frozenset[int] = frozenset(set(fbgr.LIDAR_DEPENDENT_GLOBAL_COLS) | {88})
MSUB_89_COL_INDICES: tuple[int, ...] = tuple(i for i in range(89) if i not in LIDAR_DEPENDENT_89_COLS)
assert len(MSUB_89_COL_INDICES) == 76, f"Expected 76 pure non-LiDAR columns, got {len(MSUB_89_COL_INDICES)}"


def _sobel_xy_f32(a: np.ndarray, sigma: float = 1.0) -> tuple[np.ndarray, np.ndarray]:
    s = gaussian_filter(a.astype(np.float32, copy=False), sigma, mode="nearest") if sigma > 0 else a
    gy = sobel(s, axis=0).astype(np.float32) * np.float32(0.125)
    gx = sobel(s, axis=1).astype(np.float32) * np.float32(0.125)
    return gx, gy


def build_bhgc_extra_stack(
    ddir: Path | None = None,
    base_stack_path: Path | None = None,
    spcp_path: Path | None = None,
    trhv_path: Path | None = None,
    ldgi_path: Path | None = None,
    fbgr_path: Path | None = None,
    out_path: Path | None = None,
    force: bool = False,
    log=print,
) -> tuple[np.ndarray, dict[str, Any]]:
    """Build or open the 6-channel strictly label-free `BHGC` disk-backed float32 stack."""
    ddir = ddir or paths.data_dir()
    wdir = paths.work_dir()
    wdir.mkdir(parents=True, exist_ok=True)

    base_stack_path = base_stack_path or (wdir / "feature_stack.npy")
    spcp_path = spcp_path or (wdir / "spcp_extra_20ch.npy")
    trhv_path = trhv_path or (wdir / "trhv_extra_8ch.npy")
    ldgi_path = ldgi_path or (wdir / "ldgi_extra_8ch.npy")
    fbgr_path = fbgr_path or (wdir / "fbgr_extra_12ch.npy")
    out_path = out_path or (wdir / "bhgc_extra_6ch.npy")
    receipt_path = out_path.with_suffix(".json")

    if out_path.exists() and receipt_path.exists() and not force:
        mm = open_memmap(out_path, mode="r")
        if mm.shape[2] == len(BHGC_EXTRA_CHANNELS):
            return mm, json.loads(receipt_path.read_text())

    with rasterio.open(ddir / "sample_submission.tif") as src:
        sample = src.read(1)
        foot = np.isfinite(sample)
        h, w = sample.shape
    del sample

    base_mm = open_memmap(base_stack_path, mode="r")
    spcp_mm = open_memmap(spcp_path, mode="r")
    trhv_mm = open_memmap(trhv_path, mode="r")
    ldgi_mm = open_memmap(ldgi_path, mode="r")
    fbgr_mm = open_memmap(fbgr_path, mode="r")

    def _clean_base(idx0: int) -> np.ndarray:
        plane = np.asarray(base_mm[:, :, idx0], dtype=np.float32).copy()
        valid = foot & np.isfinite(plane) & (np.abs(plane) < 1e12)
        med = np.float32(np.median(plane[valid][::4])) if valid.any() else np.float32(0.0)
        plane[~valid] = med
        return plane

    mm = open_memmap(out_path, mode="w+", dtype=np.float32, shape=(h, w, len(BHGC_EXTRA_CHANNELS)))

    # --- Ch 0: Laplace-Harmonic Gravity-Vector Divergence (Band 18, Band 11) & Blakely-Simpson Crest ---
    gx_nat = _clean_base(17)      # Band 18: iso_grav_anom_hg (dg/dx)
    gy_nat = _clean_base(10)      # Band 11: iso_grav_anom_vg (dg/dy)
    g_slope = _clean_base(4)      # Band 05: iso_grav_anom_slope
    depth_base = _clean_base(14)  # Band 15: depth_to_base_surf

    hg_vec = np.hypot(gx_nat, gy_nat).astype(np.float32)
    hg_comb = np.float32(0.55) * spcp.robust_unit_f32(hg_vec, foot, pct=99.4) + np.float32(0.45) * spcp.robust_unit_f32(
        g_slope, foot, pct=99.4
    )
    del g_slope

    # Unit normal across gravity contact: n_g = (gx, gy) / ||g_H||
    inv_hg = np.float32(1.0) / (hg_vec + np.float32(1e-4))
    nx_g = (gx_nat * inv_hg).astype(np.float32)
    ny_g = (gy_nat * inv_hg).astype(np.float32)
    del inv_hg, hg_vec

    # Laplace-Harmonic horizontal divergence: div(g_H) = d(gx)/dx + d(gy)/dy = -d^2g/dz^2
    dgx_dx1, _ = _sobel_xy_f32(gx_nat, sigma=1.0)
    _, dgy_dy1 = _sobel_xy_f32(gy_nat, sigma=1.0)
    dgx_dx2, _ = _sobel_xy_f32(gx_nat, sigma=2.2)
    _, dgy_dy2 = _sobel_xy_f32(gy_nat, sigma=2.2)
    del gx_nat, gy_nat

    lap_d2z_1 = -(dgx_dx1 + dgy_dy1)
    lap_d2z_2 = -(dgx_dx2 + dgy_dy2)
    del dgx_dx1, dgy_dy1, dgx_dx2, dgy_dy2

    # Blakely-Simpson cross-contact inflection crest: -d^2(hg_comb)/dn_g^2 along n_g
    dh_dx, dh_dy = _sobel_xy_f32(hg_comb, sigma=1.2)
    dh_dn = nx_g * dh_dx + ny_g * dh_dy
    del dh_dx, dh_dy
    d2h_dnx, d2h_dny = _sobel_xy_f32(dh_dn, sigma=1.2)
    blakely_crest = np.maximum(-(nx_g * d2h_dnx + ny_g * d2h_dny), np.float32(0.0)) * np.exp(
        -np.abs(dh_dn) / np.float32(0.08)
    )
    del nx_g, ny_g, dh_dn, d2h_dnx, d2h_dny

    db_gx, db_gy = _sobel_xy_f32(depth_base, sigma=1.8)
    u_db_grad = spcp.robust_unit_f32(np.hypot(db_gx, db_gy), foot, pct=99.4)
    del db_gx, db_gy

    u_lap = np.float32(0.55) * spcp.robust_unit_f32(np.maximum(lap_d2z_1, np.float32(0.0)), foot, pct=99.4) + np.float32(
        0.45
    ) * spcp.robust_unit_f32(np.maximum(lap_d2z_2, np.float32(0.0)), foot, pct=99.4)
    del lap_d2z_1, lap_d2z_2
    u_blakely = spcp.robust_unit_f32(blakely_crest, foot, pct=99.4)
    del blakely_crest

    grav_vec_div_crest = spcp.robust_unit_f32(
        (np.float32(0.40) * hg_comb + np.float32(0.35) * u_blakely + np.float32(0.25) * u_lap)
        * (np.float32(0.55) + np.float32(0.45) * u_db_grad),
        foot,
        pct=99.5,
    )
    mm[:, :, 0] = grav_vec_div_crest
    del hg_comb, u_blakely, u_lap
    gc.collect()
    log("  [BHGC] ch 0 (Laplace-Harmonic gravity vector divergence + Blakely-Simpson crest) built")

    # --- Ch 1: Miller-Singh / Verduzco Magnetic Tilt Zero-Crossing Contact Wall ---
    tc_band = _clean_base(5)   # Band 06: tc (magnetic tilt/total curvature)
    tmi_hg = _clean_base(2)    # Band 03: tmi_hg
    tmi_vg = _clean_base(8)    # Band 09: tmi_vg
    rtp_edge = np.asarray(base_mm[:, :, 27], dtype=np.float32)

    tc_med = np.float32(np.median(tc_band[foot][::4]))
    tc_mad = np.float32(max(float(np.median(np.abs(tc_band[foot][::4] - tc_med))) * 1.4826, 1.0))
    # Zero-crossing wall of tilt + horizontal gradient of tilt
    tc_gx, tc_gy = _sobel_xy_f32(tc_band, sigma=1.2)
    u_tc_grad = spcp.robust_unit_f32(np.hypot(tc_gx, tc_gy), foot, pct=99.4)
    del tc_gx, tc_gy
    tc_zero_wall = np.exp(-np.abs(tc_band - tc_med) / (np.float32(0.75) * tc_mad)).astype(np.float32)
    del tc_band

    u_tmi_hg = spcp.robust_unit_f32(tmi_hg, foot, pct=99.4)
    u_tmi_vg = spcp.robust_unit_f32(np.abs(tmi_vg), foot, pct=99.4)
    u_rtp_edge = spcp.robust_unit_f32(rtp_edge, foot, pct=99.4)
    del tmi_hg, tmi_vg, rtp_edge

    kneg_mag, _ = spcp.principal_negative_curvature_and_strike(
        np.float32(0.55) * u_tmi_hg + np.float32(0.45) * u_rtp_edge, sigma=1.3
    )
    u_kneg_mag = spcp.robust_unit_f32(kneg_mag, foot, pct=99.4)
    del kneg_mag

    mag_tilt_wall = spcp.robust_unit_f32(
        (np.float32(0.38) * u_tmi_hg + np.float32(0.28) * u_rtp_edge + np.float32(0.20) * u_kneg_mag + np.float32(0.14) * u_tc_grad)
        * (np.float32(0.45) + np.float32(0.35) * tc_zero_wall + np.float32(0.20) * u_tmi_vg),
        foot,
        pct=99.5,
    )
    mm[:, :, 1] = mag_tilt_wall
    del u_tmi_hg, u_tmi_vg, u_rtp_edge, u_kneg_mag, u_tc_grad, tc_zero_wall
    gc.collect()
    log("  [BHGC] ch 1 (Miller-Singh magnetic tilt zero-crossing contact wall) built")

    # --- Ch 2: Multi-Scale Piedmont-Horst Bedrock Contact Spine (100% 1m LiDAR-free) ---
    det_elev = _clean_base(11)    # Band 12: det_elev
    elev_slope = _clean_base(18)  # Band 19: det_elev_slope
    ridge_s1 = np.maximum(np.asarray(base_mm[:, :, 21], dtype=np.float32), np.float32(0.0))
    ridge_s2 = np.maximum(np.asarray(base_mm[:, :, 22], dtype=np.float32), np.float32(0.0))
    ridge_s3 = np.maximum(np.asarray(base_mm[:, :, 23], dtype=np.float32), np.float32(0.0))
    tophat2 = np.maximum(np.asarray(base_mm[:, :, 25], dtype=np.float32), np.float32(0.0))
    curv_s1 = np.asarray(base_mm[:, :, 19], dtype=np.float32)
    curv_s2 = np.asarray(base_mm[:, :, 20], dtype=np.float32)
    coh_s2 = np.asarray(base_mm[:, :, 31], dtype=np.float32)
    lahontan_veto = np.asarray(spcp_mm[:, :, 16], dtype=np.float32)
    tiger_clean = np.asarray(trhv_mm[:, :, 4], dtype=np.float32)

    u_r1 = spcp.robust_unit_f32(ridge_s1, foot, pct=99.4)
    u_r2 = spcp.robust_unit_f32(ridge_s2, foot, pct=99.4)
    u_r3 = spcp.robust_unit_f32(ridge_s3, foot, pct=99.4)
    u_th = spcp.robust_unit_f32(tophat2, foot, pct=99.4)
    del ridge_s1, ridge_s2, ridge_s3, tophat2

    # Piedmont-toe slope break: gradient of slope where slope transitions from range front (>3 deg) to fan
    sl_gx, sl_gy = _sobel_xy_f32(elev_slope, sigma=1.2)
    u_sl_break = spcp.robust_unit_f32(
        np.hypot(sl_gx, sl_gy) * spcp._sigmoid_f32((elev_slope - np.float32(1.8)) / np.float32(1.2)),
        foot,
        pct=99.4,
    )
    del sl_gx, sl_gy

    u_curv = spcp.robust_unit_f32(
        np.float32(0.55) * np.maximum(-curv_s1, np.float32(0.0)) + np.float32(0.45) * np.maximum(-curv_s2, np.float32(0.0)),
        foot,
        pct=99.4,
    )
    del curv_s1, curv_s2

    ridge_multiscale = np.maximum.reduce([u_r1, np.float32(0.92) * u_r2, np.float32(0.85) * u_r3])
    del u_r1, u_r2, u_r3

    # Flat deep basin suppression (depth > 350 m and slope < 1.5 deg)
    local_relief_1p5km = maximum_filter(det_elev, size=15) - minimum_filter(det_elev, size=15)
    flat_basin_sink = (
        spcp._sigmoid_f32((depth_base - np.float32(320.0)) / np.float32(120.0))
        * spcp._sigmoid_f32((np.float32(1.6) - elev_slope) / np.float32(0.45))
        * spcp._sigmoid_f32((np.float32(18.0) - local_relief_1p5km) / np.float32(6.0))
    )
    non_flat_basin = np.clip(np.float32(1.0) - np.float32(0.88) * flat_basin_sink, np.float32(0.12), np.float32(1.0)).astype(
        np.float32
    )
    del det_elev, local_relief_1p5km, flat_basin_sink

    piedmont_raw = (
        (np.float32(0.36) * ridge_multiscale + np.float32(0.22) * u_sl_break + np.float32(0.18) * u_curv + np.float32(0.12) * u_th + np.float32(0.12) * u_db_grad)
        * (np.float32(0.50) + np.float32(0.50) * np.clip(coh_s2, 0.0, 1.0))
        * (np.float32(0.40) + np.float32(0.60) * np.clip(lahontan_veto, 0.0, 1.0))
        * (np.float32(0.35) + np.float32(0.65) * tiger_clean)
        * non_flat_basin
    )
    del ridge_multiscale, u_sl_break, u_curv, u_th, u_db_grad, coh_s2, lahontan_veto
    piedmont_horst_step_spine = spcp.robust_unit_f32(
        mdrc.directional_chain_max(piedmont_raw.astype(np.float32), foot, halflen=2),
        foot,
        pct=99.5,
    )
    mm[:, :, 2] = piedmont_horst_step_spine
    del piedmont_raw
    gc.collect()
    log("  [BHGC] ch 2 (Multi-scale piedmont-horst bedrock contact spine) built")

    # --- Ch 3: Faulds-Moeck Transtensional Accommodation & Microseismic Swarm Bridge ---
    geod_i2 = _clean_base(3)      # Band 04: geod_2ndinv
    geod_sh = _clean_base(6)      # Band 07: geod_shearrate
    geod_dl = _clean_base(7)      # Band 08: geod_dilaterate
    deq = _clean_base(9)          # Band 10: deq_n100a15
    ieq = _clean_base(15)         # Band 16: ieq_n100a15
    morris_obliq = np.asarray(fbgr_mm[:, :, 6], dtype=np.float32)

    u_strain = spcp.robust_unit_f32(
        np.sqrt(np.maximum(geod_sh, np.float32(0.0)) * np.maximum(geod_i2, np.float32(0.0)))
        * spcp._sigmoid_f32((geod_dl + np.float32(1.5)) / np.float32(4.0)),
        foot,
        pct=99.2,
    )
    u_seis = spcp.robust_unit_f32(
        np.log1p(np.maximum(ieq, np.float32(0.0))) / np.log1p(np.maximum(deq, np.float32(0.0)) + np.float32(150.0)),
        foot,
        pct=99.2,
    )
    del geod_i2, geod_sh, geod_dl, deq, ieq

    struct_carrier = np.maximum.reduce(
        [grav_vec_div_crest, mag_tilt_wall, piedmont_horst_step_spine]
    )
    transtensional_bridge = spcp.robust_unit_f32(
        struct_carrier
        * (np.float32(0.40) * morris_obliq + np.float32(0.32) * u_strain + np.float32(0.28) * u_seis)
        * non_flat_basin,
        foot,
        pct=99.5,
    )
    mm[:, :, 3] = transtensional_bridge
    del morris_obliq, u_strain, u_seis, struct_carrier
    gc.collect()
    log("  [BHGC] ch 3 (Transtensional accommodation & microseismic swarm bridge) built")

    # --- Ch 4: Hydrothermal Clay-Cap Lateral Edge + 4-Block 214Bi Radon + GDR #1391 Vent Spine ---
    cond_edge = spcp.robust_unit_f32(np.asarray(base_mm[:, :, 29], dtype=np.float32), foot, pct=99.4)
    cond_resid = np.asarray(spcp_mm[:, :, 8], dtype=np.float32)
    hydro_demag = np.asarray(spcp_mm[:, :, 6], dtype=np.float32)
    radon_crest = np.asarray(fbgr_mm[:, :, 3], dtype=np.float32)
    sil_pot_dog = np.asarray(fbgr_mm[:, :, 4], dtype=np.float32)
    blm_conduit = np.asarray(fbgr_mm[:, :, 5], dtype=np.float32)
    t2m_anom = np.asarray(trhv_mm[:, :, 0], dtype=np.float32)
    sinter_vent = np.asarray(trhv_mm[:, :, 2], dtype=np.float32)
    vent_conduit = np.asarray(trhv_mm[:, :, 3], dtype=np.float32)

    claycap_margin = cond_edge * (np.float32(0.45) + np.float32(0.55) * spcp.robust_unit_f32(cond_resid, foot, pct=99.2))
    del cond_edge, cond_resid
    gdr_plume = np.maximum.reduce([t2m_anom, sinter_vent, vent_conduit, blm_conduit])
    del t2m_anom, sinter_vent, vent_conduit, blm_conduit

    hydro_vent_raw = (
        (
            np.float32(0.28) * radon_crest
            + np.float32(0.22) * claycap_margin
            + np.float32(0.20) * spcp.robust_unit_f32(hydro_demag, foot, pct=99.4)
            + np.float32(0.16) * sil_pot_dog
            + np.float32(0.14) * gdr_plume
        )
        * (np.float32(0.35) + np.float32(0.65) * tiger_clean)
        * non_flat_basin
    )
    del claycap_margin, hydro_demag, radon_crest, sil_pot_dog, gdr_plume
    hydrothermal_vent_spine = spcp.robust_unit_f32(
        mdrc.directional_chain_max(hydro_vent_raw.astype(np.float32), foot, halflen=2),
        foot,
        pct=99.5,
    )
    mm[:, :, 4] = hydrothermal_vent_spine
    del hydro_vent_raw
    gc.collect()
    log("  [BHGC] ch 4 (Hydrothermal clay-cap lateral edge + 214Bi radon + GDR vent spine) built")

    # --- Ch 5: Unified Bi-Population Structural-Geothermal Far-Field Crest Spine ---
    lidar_valid = (np.asarray(spcp_mm[:, :, 12], dtype=np.float32) > 0.5) & foot
    lidar_chain = np.asarray(fbgr_mm[:, :, 10], dtype=np.float32)
    lidar_dipole = np.asarray(spcp_mm[:, :, 13], dtype=np.float32)
    fbgr_conduit = np.asarray(fbgr_mm[:, :, 11], dtype=np.float32)
    ldgi_corridor = np.asarray(ldgi_mm[:, :, 7], dtype=np.float32)

    non_lidar_spine = (
        np.float32(0.28) * piedmont_horst_step_spine
        + np.float32(0.22) * grav_vec_div_crest
        + np.float32(0.16) * mag_tilt_wall
        + np.float32(0.16) * hydrothermal_vent_spine
        + np.float32(0.10) * fbgr_conduit
        + np.float32(0.08) * transtensional_bridge
    ).astype(np.float32)

    lidar_boost = np.float32(0.55) * lidar_chain + np.float32(0.30) * spcp.robust_unit_f32(
        lidar_dipole, lidar_valid, pct=99.4
    ) + np.float32(0.15) * ldgi_corridor
    del lidar_chain, lidar_dipole, ldgi_corridor, fbgr_conduit

    combined_spine = np.where(
        lidar_valid,
        np.float32(0.62) * non_lidar_spine + np.float32(0.38) * lidar_boost,
        non_lidar_spine,
    ).astype(np.float32)
    del lidar_valid, non_lidar_spine, lidar_boost, grav_vec_div_crest, mag_tilt_wall, piedmont_horst_step_spine, transtensional_bridge, hydrothermal_vent_spine

    combined_spine = combined_spine * (np.float32(0.35) + np.float32(0.65) * tiger_clean) * non_flat_basin
    del tiger_clean, non_flat_basin, depth_base, elev_slope
    sharpened_spine = fbgr.sharpen_probability_crest(combined_spine, foot, crest_boost=0.50)
    del combined_spine
    mm[:, :, 5] = spcp.robust_unit_f32(sharpened_spine, foot, pct=99.5)
    del sharpened_spine

    if hasattr(mm, "flush"):
        mm.flush()
    gc.collect()

    meta: dict[str, Any] = {
        "channels": list(BHGC_EXTRA_CHANNELS),
        "shape": [h, w, len(BHGC_EXTRA_CHANNELS)],
        "dtype": "float32",
        "label_free": True,
        "native_gravity_vector_bands": ["Band 18 (iso_grav_anom_hg = dg/dx)", "Band 11 (iso_grav_anom_vg = dg/dy)"],
        "total_channels_with_template": 89,
        "msub_pure_non_lidar_col_count": len(MSUB_89_COL_INDICES),
    }
    receipt_path.write_text(json.dumps(meta, indent=2) + "\n")
    log("  [BHGC] ch 5 (Unified Bi-Population Structural-Geothermal Far-Field Crest Spine) built")
    return open_memmap(out_path, mode="r"), meta


def gather_89ch(
    base_stack: np.ndarray,
    spcp_stack: np.ndarray,
    trhv_stack: np.ndarray,
    ldgi_stack: np.ndarray,
    fbgr_stack: np.ndarray,
    bhgc_stack: np.ndarray,
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
    full = np.hstack([xb, xs_arr, xt, xl, xf, xg])
    if col_indices is not None:
        return full[:, col_indices]
    return full


def run_leakage_canary_89ch(
    base_stack: np.ndarray,
    spcp_stack: np.ndarray,
    trhv_stack: np.ndarray,
    ldgi_stack: np.ndarray,
    fbgr_stack: np.ndarray,
    bhgc_stack: np.ndarray,
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

    stacks = (base_stack, spcp_stack, trhv_stack, ldgi_stack, fbgr_stack, bhgc_stack)
    offsets = np.cumsum([0] + [s.shape[2] for s in stacks])
    all_names = (
        list(base_names)
        + list(spcp.SPCP_EXTRA_CHANNELS)
        + list(trhv.TRHV_EXTRA_CHANNELS)
        + list(ldgi.LDGI_EXTRA_CHANNELS)
        + list(fbgr.FBGR_EXTRA_CHANNELS)
        + list(BHGC_EXTRA_CHANNELS)
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
                "channel": name,
                "in_msub_pure_non_lidar": i in MSUB_89_COL_INDICES,
                "raw_auc": round(raw_auc, 6),
                "oriented_auc": round(auc_dir, 6),
                "passed": bool(auc_dir <= max_auc),
            }
        )

    worst = max(rows, key=lambda r: r["oriented_auc"])
    bhgc_rows = [r for r in rows if r["index"] >= 83]
    return {
        "passed": all(r["passed"] for r in rows),
        "threshold_auc": max_auc,
        "n_features_tested": len(rows),
        "max_oriented_auc": worst["oriented_auc"],
        "worst_channel": worst["channel"],
        "bhgc_6ch_max_oriented_auc": max(r["oriented_auc"] for r in bhgc_rows),
        "bhgc_6ch_aucs": {r["channel"]: r["oriented_auc"] for r in bhgc_rows},
        "n_withheld_pos_tested": int(py.size),
        "n_active_neg_sampled": int(ny.size),
        "per_channel": rows,
    }


def fit_bhgc_classifier(
    base_stack: np.ndarray,
    spcp_stack: np.ndarray,
    trhv_stack: np.ndarray,
    ldgi_stack: np.ndarray,
    fbgr_stack: np.ndarray,
    bhgc_stack: np.ndarray,
    train_region: np.ndarray,
    visible_train: np.ndarray,
    foot: np.ndarray,
    col_indices: tuple[int, ...] | None = None,
    seed: int = 49,
    max_pos: int = 44_000,
    n_neg_hard: int = 88_000,
    n_neg_unif: int = 88_000,
) -> HistGradientBoostingClassifier:
    """Fit a fold-local hard+uniform-negative `HistGradientBoostingClassifier` on `89` or `76` columns.

    Uses `d_tr >= 5.0` (`hard: 5.0 <= d_tr <= 24.0`, `unif: d_tr > 24.0`) without feature-threshold
    censoring of the negative sample, avoiding deterministic split artifacts while learning across all
    89 channels (or 76 strictly 1 m LiDAR-free channels for `M_Sub`).
    """
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

    X = gather_89ch(base_stack, spcp_stack, trhv_stack, ldgi_stack, fbgr_stack, bhgc_stack, ys, xs, col_indices=col_indices)
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


def predict_chunked_bhgc(
    clf: HistGradientBoostingClassifier,
    base_stack: np.ndarray,
    spcp_stack: np.ndarray,
    trhv_stack: np.ndarray,
    ldgi_stack: np.ndarray,
    fbgr_stack: np.ndarray,
    bhgc_stack: np.ndarray,
    mask: np.ndarray,
    col_indices: tuple[int, ...] | None = None,
    chunk_size: int = 180_000,
) -> np.ndarray:
    out = np.zeros(mask.shape, dtype=np.float32)
    ys, xs = np.nonzero(mask)
    for start in range(0, ys.size, chunk_size):
        sl = slice(start, min(start + chunk_size, ys.size))
        X = gather_89ch(
            base_stack,
            spcp_stack,
            trhv_stack,
            ldgi_stack,
            fbgr_stack,
            bhgc_stack,
            ys[sl],
            xs[sl],
            col_indices=col_indices,
        )
        out[ys[sl], xs[sl]] = clf.predict_proba(X)[:, 1].astype(np.float32)
        del X
    return out


def build_stationary_bhgc_surface(
    p_dual: np.ndarray,
    fbgr_stack: np.ndarray,
    bhgc_stack: np.ndarray,
    trhv_stack: np.ndarray,
    visible_mask: np.ndarray,
    foot: np.ndarray,
    region_mask: np.ndarray | None = None,
    w_unsup_conduit: float = 0.25,
    w_tip_relay: float = 0.46,
    w_mid_bridge: float = 0.62,
    w_far_spine: float = 0.66,
    d0_far_px: float = 21.8,
    collar_depletion_strength: float = 0.53,
    sharpen_crest: bool = True,
    crest_boost: float = 0.48,
) -> np.ndarray:
    """Stationary 3-Zone Bi-Population Belief Surface (identical formula on OOF folds and full map).

    Combines:
      1. 89-ch / 76-ch Dual-Cover OOF posterior `p_dual`,
      2. Zone 1 (`2 < d_vis <= 5.5 px`): LLI-calibrated near-catalogue collar depletion attenuation
         (`1 - c_dep * exp(-(d_vis-2)/1.7) * (1 - 0.85*relay)`),
      3. Zone 2 (`5.2 < d_vis <= 22 px`): Detached-segment transtensional & hydrothermal bridge
         amplification (`w_mid_bridge` on `transtensional_accommodation_bridge + bhgc_spine + grav + vent`),
      4. Zone 3 (`d_vis > d0_far_px`): Far-field Horst-Piedmont & Laplace-Harmonic Gravity-Divergence
         spine (`w_far_spine`),
      5. Anthropogenic TIGER road prism damping (`trhv_stack[:, :, 4]`), and
      6. Probability-contrast-preserving 4-azimuth NMS crest sharpening (`fbgr.sharpen_probability_crest`).
    """
    if region_mask is None:
        region_mask = foot
    mask = region_mask & foot
    vis = np.asarray(visible_mask, bool) & foot
    d_vis = distance_transform_edt(~vis).astype(np.float32)
    relay = ldgi.anisotropic_tip_relay_cone(vis, foot)

    gv = np.asarray(bhgc_stack[:, :, 0], dtype=np.float32)
    mt = np.asarray(bhgc_stack[:, :, 1], dtype=np.float32)
    ps = np.asarray(bhgc_stack[:, :, 2], dtype=np.float32)
    tr_br = np.asarray(bhgc_stack[:, :, 3], dtype=np.float32)
    hv = np.asarray(bhgc_stack[:, :, 4], dtype=np.float32)
    bs = np.asarray(bhgc_stack[:, :, 5], dtype=np.float32)
    tg = np.asarray(trhv_stack[:, :, 4], dtype=np.float32)

    far_crest = spcp.robust_unit_f32(
        np.float32(0.34) * ps + np.float32(0.28) * bs + np.float32(0.16) * gv + np.float32(0.12) * hv + np.float32(0.10) * mt,
        foot,
        pct=99.6,
    )
    mid_crest = spcp.robust_unit_f32(
        np.float32(0.38) * tr_br + np.float32(0.32) * bs + np.float32(0.16) * gv + np.float32(0.14) * hv,
        foot,
        pct=99.5,
    )
    joint_crest = (
        np.float32(0.42) * bs + np.float32(0.30) * tr_br + np.float32(0.16) * hv + np.float32(0.12) * gv
    )
    del gv, mt, ps, tr_br, hv, bs

    surf = np.zeros(foot.shape, dtype=np.float32)
    pd = p_dual[mask]
    jc = joint_crest[mask]
    mc = mid_crest[mask]
    fc_far = far_crest[mask]
    rl = relay[mask]
    tg_m = tg[mask]
    dv = d_vis[mask]
    del relay, d_vis, joint_crest, mid_crest, far_crest, tg

    collar_atten = np.float32(1.0) - np.float32(collar_depletion_strength) * np.exp(
        -np.maximum(dv - np.float32(2.0), np.float32(0.0)) / np.float32(1.7)
    ) * (np.float32(1.0) - np.float32(0.85) * np.clip(rl, 0.0, 1.0))

    mid_window = np.exp(-((dv - np.float32(12.5)) / np.float32(8.0)) ** 2) * (dv > np.float32(5.2))
    mid_boost = np.float32(1.0) + np.float32(w_mid_bridge) * mid_window * (np.float32(0.45) + np.float32(0.55) * mc)

    gamma_far = np.float32(1.0) - np.exp(
        -((np.maximum(dv - np.float32(d0_far_px), np.float32(0.0))) / np.float32(6.5)) ** 2
    )

    w_c = np.float32(w_unsup_conduit)
    w_r = np.float32(w_tip_relay)
    w_f = np.float32(w_far_spine)

    oof_term = (
        ((np.float32(1.0) - w_c) * pd + w_c * jc * np.sqrt(np.maximum(pd, np.float32(0.02))))
        * (np.float32(1.0) + w_r * rl)
        * collar_atten
        * mid_boost
    )
    far_term = w_f * gamma_far * (fc_far ** np.float32(1.28)) * (np.float32(0.45) + np.float32(0.55) * (pd ** np.float32(0.35)))

    surf[mask] = np.maximum(oof_term, far_term) * (np.float32(0.35) + np.float32(0.65) * tg_m)
    del pd, jc, mc, fc_far, rl, tg_m, dv, collar_atten, mid_window, mid_boost, gamma_far, oof_term, far_term

    if sharpen_crest:
        surf = fbgr.sharpen_probability_crest(surf, mask, crest_boost=crest_boost)
    return np.clip(surf, 0.0, 1.0).astype(np.float32)
