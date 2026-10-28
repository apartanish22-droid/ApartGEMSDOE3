"""H-APART3-2 (CSHD): Crustal Seismogenic-Hydrothermal-Piedmont Dual-Cover
Conduit Detection & Collar-Balanced Axial CELF Packing.

Implements the pre-registered `docs/research/h-apart3-2-cshd-preregistration-20261028.md`
8-channel label-free, 1 m LiDAR-free geological feature stack (`CSHD_EXTRA_CHANNELS`,
global indices 89..96 on top of the 89-channel template + SPCP + TRHV + LDGI + FBGR + BHGC
stack = 97 channels total):

  0 (89) `comcat_brittle_hypocenter_density`:
         Official USGS ANSS ComCat 1900-2026 earthquake hypocenters (`usgs_comcat_geodawn.csv`,
         Public Domain 17 U.S.C. 105, 2,040 in-footprint events) weighted by magnitude energy
         and the 2-12 km Great Basin brittle geothermal circulation depth window, fused with
         official seismicity edges (`Bands 10, 16`).
  1 (90) `comcat_post2021_lineament_bridge`:
         Modern post-2021 earthquakes (`year >= 2021`, 541 events recorded AFTER the 2021
         GDR #1391 fault compilation cutoff) + brittle-crust epicenters bridged along strike
         via an 8-azimuth directional fault-chord filter (`sigma_par=8.5 px, sigma_perp=1.6 px`).
  2 (91) `gdr_blind_geotherm_disequilibrium`:
         Fournier (1977) / Fournier-Truesdell (1973) chemical geothermometer thermal
         disequilibrium `max(T_quartz, T_chalc, T_NaKCa) - T_discharge` from official DOE
         GDR #1391 (`gdr_wellspring_in_footprint.csv`, `dist_known_fault_px` strictly dropped),
         isolating 653 blind cold/tepid-discharge (<45 C) high-geothermometer (>85 C) wells
         and springs, fused with GDR #1391 2-m probe conductive anomalies and sinter vents.
  3 (92) `cond_radon_upflow_gradient`:
         Hydrothermal smectite clay-cap boundary gradient & negative-Laplacian ridge on
         `Band 17` (`cond_surf`) coupled with 4-block contractor-normalized 214Bi/232Th
         fault-gas excess and blind chemical geothermometer disequilibrium, damped on flat
         closed-basin salt playas (`depth > 350 m & slope < 1.8 deg`).
  4 (93) `seamless_10m_piedmont_apron_scarp`:
         100%-coverage USGS 3DEP 10 m seamless DEM scarp sharpness (`topo_10m_derived_100m_u8.tif`:
         `curv_prof_absmax`, `aspect_coherence`, `hs_lineament`, `slope_std`) weighted by the
         INGENIOUS range-front piedmont apron envelope (`1.65 deg <= slope <= 13.5 deg`),
         resolving degraded alluvial-fan scarps across 100% of the 24.63% 1 m LiDAR gap while
         suppressing Lake Lahontan (~1,332 m) shorelines and TIGER road prisms.
  5 (94) `piedmont_chi_gravity_concordance`:
         USGS 3DEP 10 m Perron-Royden (2013) fluvial chi-step & normalized channel steepness
         (`dem10_chi_100m_i16.tif`, `dem10_chi_100m_u8.tif`) gated strictly to piedmont
         range-front valley exits (suppressing >14.5 deg mountain-divide chi mimics) and
         concordant with Laplace-harmonic / Fourier upward-continued basement gravity gradients.
  6 (95) `strain_kinematic_reactivation_index`:
         Geodetic strain-rate tensor kinematic partitioning (`Bands 04, 07, 08`: transtensional
         dilation-to-shear regime angle `arctan2(dilatation, shear)` + spatial strain-locking
         gradient) coupled with seamless 10 m scarp & potential-field strike selectivity.
  7 (96) `cshd_piedmont_geothermal_conduit_crest`:
         Unified 100% label-free, 100% 1 m LiDAR-free seismogenic-hydrothermal-piedmont
         structural crest spine thinned via 4-azimuth directional crest sharpening, flat-playa
         vetoed, BLM mining-scar damped, and TIGER road-damped.

Zero catalogue labels (`labels.tif` / `existing_faults.tif`) are ever read during feature
construction. Fold-visible catalogue geometry (`cell.visible_full` on OOF folds; `labels` on
final emission) enters exclusively in `build_stationary_cshd_surface` and strict `B = 2 px`
post-collar emission via `gems32.emitter.emit`.
"""
from __future__ import annotations

import gc
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import rasterio
from numpy.lib.format import open_memmap
from scipy.ndimage import (
    distance_transform_edt,
    gaussian_filter,
    gaussian_filter1d,
    rotate,
    sobel,
)
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score

from gems32 import bhgc, emitter, fbgr, ldgi, paths, spcp, trhv

TARGET_BUDGET: int = 37_654
B_COLLAR_PX: float = 2.0
DEFAULT_AXIAL_SEP_PX: float = 3.62

CSHD_EXTRA_CHANNELS: tuple[str, ...] = (
    "comcat_brittle_hypocenter_density",      # 0 (global 89)
    "comcat_post2021_lineament_bridge",       # 1 (global 90)
    "gdr_blind_geotherm_disequilibrium",      # 2 (global 91)
    "cond_radon_upflow_gradient",             # 3 (global 92)
    "seamless_10m_piedmont_apron_scarp",      # 4 (global 93)
    "piedmont_chi_gravity_concordance",       # 5 (global 94)
    "strain_kinematic_reactivation_index",    # 6 (global 95)
    "cshd_piedmont_geothermal_conduit_crest", # 7 (global 96)
)

# All 8 CSHD channels (89..96) are 100% 1 m LiDAR-free, giving M_Gap 76 + 8 = 84 pure channels.
LIDAR_DEPENDENT_97_COLS: frozenset[int] = bhgc.LIDAR_DEPENDENT_89_COLS
MSUB_97_COL_INDICES: tuple[int, ...] = tuple(
    i for i in range(89 + len(CSHD_EXTRA_CHANNELS)) if i not in LIDAR_DEPENDENT_97_COLS
)
assert len(MSUB_97_COL_INDICES) == 84, f"Expected 84 pure non-LiDAR columns, got {len(MSUB_97_COL_INDICES)}"


def _grad_mag_f32(a: np.ndarray, sigma: float = 1.0) -> np.ndarray:
    s = gaussian_filter(a.astype(np.float32, copy=False), sigma, mode="nearest") if sigma > 0 else a.astype(np.float32, copy=False)
    gy = sobel(s, axis=0).astype(np.float32) * np.float32(0.125)
    gx = sobel(s, axis=1).astype(np.float32) * np.float32(0.125)
    return np.hypot(gx, gy).astype(np.float32)


def _oriented_chord_kernels(
    n_angles: int = 8,
    sigma_par: float = 8.5,
    sigma_perp_narrow: float = 1.6,
    sigma_perp_wide: float = 4.8,
) -> list[np.ndarray]:
    """Build zero-DC-clutter anisotropic fault-strike chord kernels across `n_angles` azimuths."""
    half = int(np.ceil(2.6 * sigma_par))
    yy, xx = np.mgrid[-half : half + 1, -half : half + 1].astype(np.float32)
    kernels: list[np.ndarray] = []
    for k in range(n_angles):
        theta = float(k) * np.pi / float(n_angles)
        c, sn = np.float32(np.cos(theta)), np.float32(np.sin(theta))
        u_par = xx * c + yy * sn
        u_perp = -xx * sn + yy * c
        along = np.exp(-0.5 * (u_par / np.float32(sigma_par)) ** 2)
        narrow = np.exp(-0.5 * (u_perp / np.float32(sigma_perp_narrow)) ** 2) / np.float32(sigma_perp_narrow)
        wide = np.exp(-0.5 * (u_perp / np.float32(sigma_perp_wide)) ** 2) / np.float32(sigma_perp_wide)
        kern = along * (narrow - np.float32(0.55) * wide)
        pos_sum = float(np.maximum(kern, 0.0).sum())
        if pos_sum > 0:
            kern = (kern / np.float32(pos_sum)).astype(np.float32)
        kernels.append(kern)
    return kernels


def _directional_seismic_lineament(src: np.ndarray, sigma_par: float = 8.5) -> np.ndarray:
    """Fast FFT convolution over 8 fault-strike azimuths returning maximum positive chord response."""
    from scipy.signal import fftconvolve

    best = np.zeros(src.shape, dtype=np.float32)
    s_f32 = src.astype(np.float32, copy=False)
    for kern in _oriented_chord_kernels(n_angles=8, sigma_par=sigma_par):
        resp = fftconvolve(s_f32, kern, mode="same").astype(np.float32)
        np.maximum(best, resp, out=best)
        del resp
    return best


def _build_comcat_channels(
    ddir: Path,
    base_mm: np.ndarray,
    foot: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    """Build ch 0 (`comcat_brittle_hypocenter_density`) & ch 1 (`comcat_post2021_lineament_bridge`)."""
    csv_path = ddir / "external" / "usgs_comcat_geodawn.csv"
    df = pd.read_csv(csv_path)
    assert "dist_known_fault_px" not in df.columns, "Forbidden fault-distance column in ComCat CSV!"

    h, w = foot.shape
    rows = pd.to_numeric(df["row_100m"], errors="coerce").fillna(-1).to_numpy(dtype=np.int32)
    cols = pd.to_numeric(df["col_100m"], errors="coerce").fillna(-1).to_numpy(dtype=np.int32)
    years = pd.to_numeric(df["year"], errors="coerce").fillna(1980).to_numpy(dtype=np.int32)
    mags = pd.to_numeric(df["magnitude"], errors="coerce").fillna(2.5).to_numpy(dtype=np.float32)
    depths = pd.to_numeric(df["depth_km"], errors="coerce").fillna(7.0).to_numpy(dtype=np.float32)

    in_box = (rows >= 0) & (rows < h) & (cols >= 0) & (cols < w)
    rows_v, cols_v = rows[in_box], cols[in_box]
    in_fp = foot[rows_v, cols_v]

    w_mag = np.float32(1.0) + np.float32(0.55) * np.clip(mags[in_box] - np.float32(2.0), np.float32(0.0), np.float32(4.5))
    w_depth = np.exp(-((np.clip(depths[in_box], 0.0, 35.0) - np.float32(6.5)) / np.float32(5.5)) ** 2).astype(np.float32)
    w_brittle = (w_mag * (np.float32(0.35) + np.float32(0.65) * w_depth)).astype(np.float32)

    grid_all = np.zeros((h, w), dtype=np.float32)
    np.add.at(grid_all, (rows_v, cols_v), w_brittle)

    post2021_mask = years[in_box] >= 2021
    grid_post21 = np.zeros((h, w), dtype=np.float32)
    np.add.at(grid_post21, (rows_v[post2021_mask], cols_v[post2021_mask]), w_brittle[post2021_mask])

    dens_multi = (
        np.float32(0.48) * gaussian_filter(grid_all, sigma=4.0, mode="nearest")
        + np.float32(0.34) * gaussian_filter(grid_all, sigma=11.0, mode="nearest")
        + np.float32(0.18) * gaussian_filter(grid_all, sigma=24.0, mode="nearest")
    )
    # Fuse with log-compressed official seismicity edge sharpness (Bands 10, 16 -> indices 9, 15)
    b10 = np.log1p(np.maximum(np.asarray(base_mm[:, :, 9], dtype=np.float32), np.float32(0.0)))
    b16 = np.log1p(np.maximum(np.asarray(base_mm[:, :, 15], dtype=np.float32), np.float32(0.0)))
    seis_edge = spcp.robust_unit_f32(_grad_mag_f32(b10, sigma=1.8) + np.float32(0.7) * _grad_mag_f32(b16, sigma=1.8), foot, pct=99.4)
    del b10, b16

    ch0 = spcp.robust_unit_f32(
        np.float32(0.74) * spcp.robust_unit_f32(dens_multi, foot, pct=99.3) + np.float32(0.26) * seis_edge,
        foot,
        pct=99.5,
    )
    del dens_multi, seis_edge

    # Directional fault-strike chord bridge emphasizing post-2021 uncatalogued swarms
    src_bridge = grid_all + np.float32(1.85) * grid_post21
    chord_resp = _directional_seismic_lineament(src_bridge, sigma_par=8.5)
    post21_halo = gaussian_filter(grid_post21, sigma=5.5, mode="nearest")
    del grid_all, grid_post21, src_bridge

    ch1 = spcp.robust_unit_f32(
        np.float32(0.68) * spcp.robust_unit_f32(chord_resp, foot, pct=99.4)
        + np.float32(0.32) * spcp.robust_unit_f32(post21_halo, foot, pct=99.3),
        foot,
        pct=99.5,
    )
    del chord_resp, post21_halo

    stats = {
        "comcat_in_bbox_events": int(in_box.sum()),
        "comcat_in_footprint_events": int(in_fp.sum()),
        "comcat_post2021_in_bbox_events": int(post2021_mask.sum()),
        "comcat_post2021_in_footprint_events": int((post2021_mask & in_fp).sum()),
    }
    return ch0, ch1, stats


def _build_blind_geotherm_and_claycap(
    ddir: Path,
    base_mm: np.ndarray,
    trhv_mm: np.ndarray,
    fbgr_mm: np.ndarray,
    foot: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    """Build ch 2 (`gdr_blind_geotherm_disequilibrium`) & ch 3 (`cond_radon_upflow_gradient`)."""
    ws_path = ddir / "external" / "gdr_wellspring_in_footprint.csv"
    ws = pd.read_csv(ws_path)
    if "dist_known_fault_px" in ws.columns:
        ws = ws.drop(columns=["dist_known_fault_px"])
    assert "dist_known_fault_px" not in ws.columns

    h, w = foot.shape
    rows = np.clip(pd.to_numeric(ws["row"], errors="coerce").fillna(0).to_numpy(dtype=np.int32), 0, h - 1)
    cols = np.clip(pd.to_numeric(ws["col"], errors="coerce").fillna(0).to_numpy(dtype=np.int32), 0, w - 1)
    t_surf = pd.to_numeric(ws["temp_c"], errors="coerce").fillna(14.0).to_numpy(dtype=np.float32)

    g_arrays = [
        pd.to_numeric(ws[c], errors="coerce").fillna(-999.0).to_numpy(dtype=np.float32)
        for c in ("geothermquartz_c", "geothermchalc_c", "geothermcat_c")
        if c in ws.columns
    ]
    t_geo = np.maximum.reduce(g_arrays)
    has_geo = t_geo > np.float32(0.0)
    diseq = np.where(has_geo, np.maximum(t_geo - np.maximum(t_surf, np.float32(12.0)), np.float32(0.0)), np.float32(0.0))

    blind_cold = has_geo & (t_surf < np.float32(45.0)) & (t_geo > np.float32(85.0)) & (diseq > np.float32(50.0))
    # Normalized disequilibrium strength with 1.45x boost on blind cold-discharge plumes
    diseq_strength = np.clip((diseq - np.float32(25.0)) / np.float32(110.0), np.float32(0.0), np.float32(2.5))
    diseq_strength = np.where(blind_cold, diseq_strength * np.float32(1.45), diseq_strength).astype(np.float32)

    src_diseq = np.zeros((h, w), dtype=np.float32)
    pos_idx = diseq_strength > np.float32(0.0)
    np.maximum.at(src_diseq, (rows[pos_idx], cols[pos_idx]), diseq_strength[pos_idx])

    halo_diseq = (
        np.float32(0.58) * gaussian_filter(src_diseq, sigma=3.5, mode="nearest")
        + np.float32(0.42) * gaussian_filter(src_diseq, sigma=10.5, mode="nearest")
    )
    del src_diseq

    probe_2m = np.asarray(trhv_mm[:, :, 0], dtype=np.float32)
    probe_grad = np.asarray(trhv_mm[:, :, 1], dtype=np.float32)
    paleo_sinter = np.asarray(trhv_mm[:, :, 2], dtype=np.float32)

    ch2 = spcp.robust_unit_f32(
        np.float32(0.52) * spcp.robust_unit_f32(halo_diseq, foot, pct=99.2)
        + np.float32(0.22) * probe_2m
        + np.float32(0.14) * probe_grad
        + np.float32(0.12) * paleo_sinter,
        foot,
        pct=99.4,
    )
    del halo_diseq, probe_2m, probe_grad, paleo_sinter

    # Band 17 (`cond_surf`, index 16) clay-cap edge + negative Laplacian ridge + 214Bi radon (`fbgr` ch 3)
    cond = np.asarray(base_mm[:, :, 16], dtype=np.float32)
    depth = np.asarray(base_mm[:, :, 14], dtype=np.float32)
    slope = np.asarray(base_mm[:, :, 18], dtype=np.float32)
    cond_edge = spcp.robust_unit_f32(_grad_mag_f32(cond, sigma=1.6), foot, pct=99.4)
    cond_ridge = spcp.robust_unit_f32(
        np.maximum(
            -(
                gaussian_filter(cond, 2.2, order=(2, 0), mode="nearest")
                + gaussian_filter(cond, 2.2, order=(0, 2), mode="nearest")
            ),
            np.float32(0.0),
        ),
        foot,
        pct=99.4,
    )
    del cond
    bi214_radon = np.asarray(fbgr_mm[:, :, 3], dtype=np.float32)

    # Suppress conductive closed-basin evaporite salt pans (depth > 350 m & slope < 1.8 deg)
    playa_damp = np.float32(1.0) - np.float32(0.80) * (
        (np.float32(1.0) / (np.float32(1.0) + np.exp(np.clip(-(depth - np.float32(350.0)) / np.float32(75.0), -30.0, 30.0))))
        * (np.float32(1.0) / (np.float32(1.0) + np.exp(np.clip((slope - np.float32(1.8)) / np.float32(0.35), -30.0, 30.0))))
    )
    del depth, slope

    ch3 = spcp.robust_unit_f32(
        playa_damp
        * (
            np.float32(0.36) * cond_edge
            + np.float32(0.24) * cond_ridge
            + np.float32(0.22) * bi214_radon
            + np.float32(0.18) * ch2
        ),
        foot,
        pct=99.5,
    )
    del cond_edge, cond_ridge, bi214_radon, playa_damp

    stats = {
        "gdr_wellspring_rows": int(len(ws)),
        "gdr_blind_cold_high_geotherm_count": int(blind_cold.sum()),
        "gdr_blind_median_diseq_c": round(float(np.median(diseq[blind_cold])), 2) if blind_cold.any() else 0.0,
    }
    return ch2, ch3, stats


def _build_piedmont_10m_and_chi_channels(
    ddir: Path,
    base_mm: np.ndarray,
    trhv_mm: np.ndarray,
    fbgr_mm: np.ndarray,
    bhgc_mm: np.ndarray,
    foot: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    """Build ch 4 (`seamless_10m_piedmont_apron_scarp`) & ch 5 (`piedmont_chi_gravity_concordance`)."""
    topo10_path = ddir / "external" / "topo_10m_derived_100m_u8.tif"
    chi_i16_path = ddir / "external" / "dem10_chi_100m_i16.tif"
    chi_u8_path = ddir / "external" / "dem10_chi_100m_u8.tif"

    with rasterio.open(topo10_path) as ds:
        # 1: slope_p90, 4: slope_std, 6: curv_prof_absmax, 7: aspect_coherence, 8: hs_lineament
        slope_p90 = ds.read(1).astype(np.float32) * np.float32(1.0 / 255.0)
        slope_std = ds.read(4).astype(np.float32) * np.float32(1.0 / 255.0)
        curv_prof = ds.read(6).astype(np.float32) * np.float32(1.0 / 255.0)
        aspect_coh = ds.read(7).astype(np.float32) * np.float32(1.0 / 255.0)
        hs_lin = ds.read(8).astype(np.float32) * np.float32(1.0 / 255.0)

    det_elev = np.asarray(base_mm[:, :, 11], dtype=np.float32)
    depth = np.asarray(base_mm[:, :, 14], dtype=np.float32)
    slope_deg = np.asarray(base_mm[:, :, 18], dtype=np.float32)
    tiger_clean = np.asarray(trhv_mm[:, :, 4], dtype=np.float32)
    lahontan_veto = np.asarray(trhv_mm[:, :, 5], dtype=np.float32)

    # Empirical INGENIOUS Quaternary fault piedmont-apron envelope (labels.tif median slope=5.55 deg vs SGMC 13.37 deg)
    above_playa = np.float32(1.0) / (np.float32(1.0) + np.exp(np.clip(-(slope_deg - np.float32(1.65)) / np.float32(0.65), -30.0, 30.0)))
    below_crest = np.exp(-np.minimum(((np.maximum(slope_deg - np.float32(13.5), np.float32(0.0))) ** 2) / np.float32(72.0), np.float32(30.0)))
    below_high_core = np.exp(-np.minimum(((np.maximum(det_elev - np.float32(185.0), np.float32(0.0))) ** 2) / np.float32(260.0**2), np.float32(30.0)))
    piedmont_env = (above_playa * below_crest * (np.float32(0.30) + np.float32(0.70) * below_high_core)).astype(np.float32)
    del above_playa, below_crest, below_high_core, det_elev

    scarp10_raw = (
        (np.float32(0.38) * curv_prof + np.float32(0.26) * hs_lin + np.float32(0.20) * slope_std + np.float32(0.16) * slope_p90)
        * (np.float32(0.35) + np.float32(0.65) * aspect_coh)
        * piedmont_env
        * (np.float32(0.45) + np.float32(0.55) * lahontan_veto)
        * (np.float32(0.40) + np.float32(0.60) * tiger_clean)
    )
    del slope_p90, slope_std, curv_prof, aspect_coh, hs_lin, lahontan_veto, tiger_clean
    ch4 = spcp.robust_unit_f32(scarp10_raw, foot, pct=99.5)
    del scarp10_raw

    with rasterio.open(chi_i16_path) as ds:
        # 1: step_max_x1000, 3: ksn_max_m0.9
        chi_step = np.maximum(ds.read(1).astype(np.float32), np.float32(0.0)) * np.float32(0.001)
        ksn_max = np.maximum(ds.read(3).astype(np.float32), np.float32(0.0))
    with rasterio.open(chi_u8_path) as ds:
        # 2: knick_n, 3: raised_n
        knick_n = ds.read(2).astype(np.float32)
        raised_n = ds.read(3).astype(np.float32)

    chi_norm = (
        np.float32(0.42) * spcp.robust_unit_f32(np.log1p(chi_step), foot, pct=99.3)
        + np.float32(0.28) * spcp.robust_unit_f32(np.log1p(ksn_max), foot, pct=99.3)
        + np.float32(0.18) * spcp.robust_unit_f32(gaussian_filter(knick_n, sigma=1.4, mode="nearest"), foot, pct=99.3)
        + np.float32(0.12) * spcp.robust_unit_f32(gaussian_filter(raised_n, sigma=1.8, mode="nearest"), foot, pct=99.3)
    )
    del chi_step, ksn_max, knick_n, raised_n

    # Gate fluvial chi to piedmont valley-exit / basin-margin transitions and couple with basement gravity
    basin_margin_gate = piedmont_env * (
        np.float32(0.25) + np.float32(0.75) / (np.float32(1.0) + np.exp(np.clip(-(depth - np.float32(35.0)) / np.float32(25.0), -30.0, 30.0)))
    )
    del piedmont_env, depth, slope_deg

    grav_div = np.asarray(bhgc_mm[:, :, 0], dtype=np.float32)
    grav_fft = np.asarray(fbgr_mm[:, :, 0], dtype=np.float32)
    grav_wall = np.float32(0.58) * grav_div + np.float32(0.42) * grav_fft
    del grav_div, grav_fft

    ch5 = spcp.robust_unit_f32(
        basin_margin_gate * chi_norm * (np.float32(0.38) + np.float32(0.62) * np.sqrt(np.maximum(grav_wall, np.float32(0.01)))),
        foot,
        pct=99.5,
    )
    del basin_margin_gate, chi_norm, grav_wall

    stats = {
        "seamless_10m_valid_in_footprint_fraction": round(float((ch4[foot] >= 0.0).mean()), 6),
        "piedmont_chi_p95_in_footprint": round(float(np.percentile(ch5[foot][::8], 95.0)), 5),
    }
    return ch4, ch5, stats


def _build_strain_and_crest_channels(
    base_mm: np.ndarray,
    trhv_mm: np.ndarray,
    fbgr_mm: np.ndarray,
    bhgc_mm: np.ndarray,
    ch0_seis: np.ndarray,
    ch1_post21: np.ndarray,
    ch2_diseq: np.ndarray,
    ch3_clay: np.ndarray,
    ch4_scarp10: np.ndarray,
    ch5_chigrav: np.ndarray,
    foot: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Build ch 6 (`strain_kinematic_reactivation_index`) & ch 7 (`cshd_piedmont_geothermal_conduit_crest`)."""
    # Bands 4, 7, 8 -> indices 3 (`geod_2ndinv`), 6 (`geod_shearrate`), 7 (`geod_dilaterate`)
    inv2 = np.maximum(np.asarray(base_mm[:, :, 3], dtype=np.float32), np.float32(0.0))
    shear = np.maximum(np.asarray(base_mm[:, :, 6], dtype=np.float32), np.float32(0.0))
    dilat = np.asarray(base_mm[:, :, 7], dtype=np.float32)

    # Kinematic transtensional dilation-to-shear regime index in [0, 1] + locking-transition gradient
    psi_ext = (np.arctan2(dilat, shear + np.float32(0.5)) + np.float32(0.5 * np.pi)) / np.float32(np.pi)
    strain_mag = spcp.robust_unit_f32(np.sqrt(shear * shear + np.maximum(dilat, np.float32(0.0)) ** 2 + np.float32(0.25) * inv2), foot, pct=99.2)
    strain_lock_grad = spcp.robust_unit_f32(_grad_mag_f32(shear, sigma=2.5) + _grad_mag_f32(dilat, sigma=2.5), foot, pct=99.2)
    del inv2, shear, dilat

    morris_obliq = np.asarray(fbgr_mm[:, :, 6], dtype=np.float32)
    ch6 = spcp.robust_unit_f32(
        (np.float32(0.46) * strain_mag * (np.float32(0.40) + np.float32(0.60) * psi_ext) + np.float32(0.28) * strain_lock_grad + np.float32(0.26) * morris_obliq)
        * (np.float32(0.32) + np.float32(0.68) * np.maximum(ch4_scarp10, np.asarray(bhgc_mm[:, :, 0], dtype=np.float32))),
        foot,
        pct=99.5,
    )
    del psi_ext, strain_mag, strain_lock_grad, morris_obliq

    # Unified 100% 1 m LiDAR-free physical CSHD crest spine
    grav_div = np.asarray(bhgc_mm[:, :, 0], dtype=np.float32)
    mag_tilt = np.asarray(bhgc_mm[:, :, 1], dtype=np.float32)
    pied_horst = np.asarray(bhgc_mm[:, :, 2], dtype=np.float32)
    blm_clean = np.asarray(fbgr_mm[:, :, 10], dtype=np.float32)
    tiger_clean = np.asarray(trhv_mm[:, :, 4], dtype=np.float32)
    depth = np.asarray(base_mm[:, :, 14], dtype=np.float32)
    slope = np.asarray(base_mm[:, :, 18], dtype=np.float32)

    flat_playa_veto = np.float32(1.0) - np.float32(0.88) * (
        (np.float32(1.0) / (np.float32(1.0) + np.exp(np.clip(-(depth - np.float32(300.0)) / np.float32(55.0), -30.0, 30.0))))
        * (np.float32(1.0) / (np.float32(1.0) + np.exp(np.clip((slope - np.float32(2.0)) / np.float32(0.32), -30.0, 30.0))))
    )
    del depth, slope

    raw_spine = (
        np.float32(0.23) * ch4_scarp10
        + np.float32(0.17) * ch5_chigrav
        + np.float32(0.14) * grav_div
        + np.float32(0.11) * pied_horst
        + np.float32(0.10) * ch1_post21
        + np.float32(0.08) * ch0_seis
        + np.float32(0.07) * ch6
        + np.float32(0.05) * (np.float32(0.55) * ch2_diseq + np.float32(0.45) * ch3_clay)
        + np.float32(0.05) * mag_tilt
    )
    del grav_div, mag_tilt, pied_horst

    gated_spine = (
        raw_spine
        * flat_playa_veto
        * (np.float32(0.45) + np.float32(0.55) * tiger_clean)
        * (np.float32(0.65) + np.float32(0.35) * np.clip(blm_clean, 0.0, 1.0))
    ).astype(np.float32)
    del raw_spine, flat_playa_veto, tiger_clean, blm_clean

    sharpened = fbgr.sharpen_probability_crest(gated_spine, foot, crest_boost=0.52)
    del gated_spine
    ch7 = spcp.robust_unit_f32(sharpened, foot, pct=99.6)
    del sharpened
    return ch6, ch7


def build_cshd_extra_stack(
    ddir: Path | None = None,
    base_stack_path: Path | None = None,
    spcp_path: Path | None = None,
    trhv_path: Path | None = None,
    ldgi_path: Path | None = None,
    fbgr_path: Path | None = None,
    bhgc_path: Path | None = None,
    out_path: Path | None = None,
    force: bool = False,
    log=print,
) -> tuple[np.ndarray, dict[str, Any]]:
    """Build or open the 8-channel strictly label-free, 1 m LiDAR-free `CSHD` memmap stack."""
    ddir = ddir or paths.data_dir()
    wdir = paths.work_dir()
    wdir.mkdir(parents=True, exist_ok=True)

    base_stack_path = base_stack_path or (wdir / "feature_stack.npy")
    spcp_path = spcp_path or (wdir / "spcp_extra_20ch.npy")
    trhv_path = trhv_path or (wdir / "trhv_extra_8ch.npy")
    ldgi_path = ldgi_path or (wdir / "ldgi_extra_8ch.npy")
    fbgr_path = fbgr_path or (wdir / "fbgr_extra_12ch.npy")
    bhgc_path = bhgc_path or (wdir / "bhgc_extra_6ch.npy")
    out_path = out_path or (wdir / "cshd_extra_8ch.npy")
    receipt_path = out_path.with_suffix(".json")

    # Ensure prerequisite cached stacks exist
    if not spcp_path.exists():
        spcp.build_spcp_extra_stack(ddir, base_stack_path, out_path=spcp_path, log=log)
        gc.collect()
    if not trhv_path.exists():
        trhv.build_trhv_extra_stack(ddir, base_stack_path, spcp_path, out_path=trhv_path)
        gc.collect()
    if not ldgi_path.exists():
        ldgi.build_ldgi_extra_stack(out_path=ldgi_path)
        gc.collect()
    if not fbgr_path.exists():
        fbgr.build_fbgr_extra_stack(
            ddir=ddir, base_stack_path=base_stack_path, spcp_path=spcp_path,
            trhv_path=trhv_path, ldgi_path=ldgi_path, out_path=fbgr_path, log=log,
        )
        gc.collect()
    if not bhgc_path.exists():
        bhgc.build_bhgc_extra_stack(
            ddir=ddir, base_stack_path=base_stack_path, spcp_path=spcp_path,
            trhv_path=trhv_path, ldgi_path=ldgi_path, fbgr_path=fbgr_path,
            out_path=bhgc_path, log=log,
        )
        gc.collect()

    if out_path.exists() and receipt_path.exists() and not force:
        mm = open_memmap(out_path, mode="r")
        if mm.shape[2] == len(CSHD_EXTRA_CHANNELS):
            return mm, json.loads(receipt_path.read_text())

    with rasterio.open(ddir / "sample_submission.tif") as src:
        sample = src.read(1)
        foot = np.isfinite(sample)
        h, w = sample.shape
    del sample

    base_mm = open_memmap(base_stack_path, mode="r")
    trhv_mm = open_memmap(trhv_path, mode="r")
    fbgr_mm = open_memmap(fbgr_path, mode="r")
    bhgc_mm = open_memmap(bhgc_path, mode="r")

    out_mm = open_memmap(out_path, mode="w+", dtype=np.float32, shape=(h, w, len(CSHD_EXTRA_CHANNELS)))

    ch0, ch1, seis_stats = _build_comcat_channels(ddir, base_mm, foot)
    out_mm[:, :, 0] = ch0
    out_mm[:, :, 1] = ch1
    out_mm.flush()
    log(f"  [CSHD] ch 0..1 (USGS ComCat hypocenters + {seis_stats['comcat_post2021_in_footprint_events']} post-2021 lineaments) built")

    ch2, ch3, chem_stats = _build_blind_geotherm_and_claycap(ddir, base_mm, trhv_mm, fbgr_mm, foot)
    out_mm[:, :, 2] = ch2
    out_mm[:, :, 3] = ch3
    out_mm.flush()
    log(f"  [CSHD] ch 2..3 (GDR #1391 {chem_stats['gdr_blind_cold_high_geotherm_count']} blind cold-well diseq + clay-cap/radon) built")

    ch4, ch5, pied_stats = _build_piedmont_10m_and_chi_channels(ddir, base_mm, trhv_mm, fbgr_mm, bhgc_mm, foot)
    out_mm[:, :, 4] = ch4
    out_mm[:, :, 5] = ch5
    out_mm.flush()
    log("  [CSHD] ch 4..5 (Seamless 10m 3DEP piedmont scarp + valley-exit fluvial chi x harmonic gravity) built")

    ch6, ch7 = _build_strain_and_crest_channels(
        base_mm, trhv_mm, fbgr_mm, bhgc_mm, ch0, ch1, ch2, ch3, ch4, ch5, foot
    )
    out_mm[:, :, 6] = ch6
    out_mm[:, :, 7] = ch7
    out_mm.flush()
    del ch0, ch1, ch2, ch3, ch4, ch5, ch6, ch7
    gc.collect()
    log("  [CSHD] ch 6..7 (Geodetic strain kinematic reactivation + unified CSHD conduit crest) built")

    meta = {
        "schema_version": 1,
        "module": "gems32.cshd",
        "hypothesis": "H-APART3-2 (CSHD)",
        "channels": list(CSHD_EXTRA_CHANNELS),
        "n_channels": len(CSHD_EXTRA_CHANNELS),
        "total_unified_channels": 89 + len(CSHD_EXTRA_CHANNELS),
        "msub_pure_non_lidar_col_count": len(MSUB_97_COL_INDICES),
        "all_cshd_channels_lidar1m_free": True,
        "zero_catalogue_label_inputs": True,
        **seis_stats,
        **chem_stats,
        **pied_stats,
    }
    receipt_path.write_text(json.dumps(meta, indent=2) + "\n")
    return open_memmap(out_path, mode="r"), meta


def gather_97ch(
    stacks: tuple[np.ndarray, ...],
    ys: np.ndarray,
    xs: np.ndarray,
    col_indices: tuple[int, ...] | None = None,
) -> np.ndarray:
    """Memory-lean row gather directly into a single pre-allocated `float32` matrix."""
    n_rows = int(ys.size)
    if col_indices is None:
        total_cols = sum(int(s.shape[2]) for s in stacks)
        out = np.empty((n_rows, total_cols), dtype=np.float32)
        c0 = 0
        for s in stacks:
            w_s = int(s.shape[2])
            out[:, c0 : c0 + w_s] = s[ys, xs, :]
            c0 += w_s
        return out

    col_set = set(col_indices)
    out = np.empty((n_rows, len(col_indices)), dtype=np.float32)
    global_c0 = 0
    write_pos = 0
    for s in stacks:
        w_s = int(s.shape[2])
        local_keep = [j for j in range(w_s) if (global_c0 + j) in col_set]
        if local_keep:
            block = np.asarray(s[ys, xs, :], dtype=np.float32)
            out[:, write_pos : write_pos + len(local_keep)] = block[:, local_keep]
            write_pos += len(local_keep)
            del block
        global_c0 += w_s
    return out


def run_leakage_canary_97ch(
    stacks: tuple[np.ndarray, ...],
    base_names: list[str],
    ctx,
    max_auc: float = 0.90,
    stride: int = 4,
) -> dict[str, Any]:
    """Protocol Rule 4 single-feature two-polarity leakage canary across all 97 channels."""
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

    offsets = np.cumsum([0] + [int(s.shape[2]) for s in stacks])
    all_names = (
        list(base_names)
        + list(spcp.SPCP_EXTRA_CHANNELS)
        + list(trhv.TRHV_EXTRA_CHANNELS)
        + list(ldgi.LDGI_EXTRA_CHANNELS)
        + list(fbgr.FBGR_EXTRA_CHANNELS)
        + list(bhgc.BHGC_EXTRA_CHANNELS)
        + list(CSHD_EXTRA_CHANNELS)
    )
    assert len(all_names) == int(offsets[-1]) == 97

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
                "in_msub_pure_non_lidar": i in MSUB_97_COL_INDICES,
                "raw_auc": round(raw_auc, 6),
                "oriented_auc": round(auc_dir, 6),
                "passed": bool(auc_dir <= max_auc),
            }
        )

    worst = max(rows, key=lambda r: r["oriented_auc"])
    cshd_rows = [r for r in rows if r["index"] >= 89]
    return {
        "passed": all(r["passed"] for r in rows),
        "threshold_auc": max_auc,
        "n_features_tested": len(rows),
        "max_oriented_auc": worst["oriented_auc"],
        "worst_channel": worst["channel"],
        "cshd_8ch_max_oriented_auc": max(r["oriented_auc"] for r in cshd_rows),
        "cshd_8ch_aucs": {r["channel"]: r["oriented_auc"] for r in cshd_rows},
        "n_withheld_pos_tested": int(py.size),
        "n_active_neg_sampled": int(ny.size),
        "per_channel": rows,
    }


def fit_cshd_ensemble(
    stacks: tuple[np.ndarray, ...],
    train_region: np.ndarray,
    visible_train: np.ndarray,
    foot: np.ndarray,
    col_indices: tuple[int, ...] | None = None,
    seed: int = 52,
    max_pos: int = 44_000,
    n_neg_hard: int = 86_000,
    n_neg_unif: int = 86_000,
) -> tuple[HistGradientBoostingClassifier, HistGradientBoostingClassifier]:
    """Fit a complementary 2-learner HGB ensemble (structural-interaction + regularized generalizer)."""
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

    def _fit_one(local_seed: int, max_leaves: int, min_leaf: int, l2_reg: float, lr: float, n_iter: int) -> HistGradientBoostingClassifier:
        r_loc = np.random.default_rng(local_seed)
        nh = min(n_neg_hard, hard_y.size)
        nu = min(n_neg_unif, unif_y.size)
        ph = r_loc.choice(hard_y.size, size=nh, replace=False)
        pu = r_loc.choice(unif_y.size, size=nu, replace=False)

        ys = np.concatenate([pos_y, hard_y[ph], unif_y[pu]])
        xs = np.concatenate([pos_x, hard_x[ph], unif_x[pu]])
        y = np.concatenate([np.ones(pos_y.size, dtype=np.int8), np.zeros(nh + nu, dtype=np.int8)])
        order = np.argsort(ys * foot.shape[1] + xs)
        ys, xs, y = ys[order], xs[order], y[order]

        X = gather_97ch(stacks, ys, xs, col_indices=col_indices)
        clf = HistGradientBoostingClassifier(
            max_iter=n_iter,
            learning_rate=lr,
            max_leaf_nodes=max_leaves,
            min_samples_leaf=min_leaf,
            l2_regularization=l2_reg,
            early_stopping=False,
            random_state=local_seed,
        )
        clf.fit(X, y)
        del X, y, ys, xs
        return clf

    clf_struct = _fit_one(seed, max_leaves=51, min_leaf=80, l2_reg=3.0, lr=0.050, n_iter=180)
    clf_reg = _fit_one(seed + 1000, max_leaves=29, min_leaf=145, l2_reg=8.0, lr=0.046, n_iter=185)
    del pos_y, pos_x, hard_y, hard_x, unif_y, unif_x
    gc.collect()
    return clf_struct, clf_reg


def predict_chunked_cshd(
    ensemble: tuple[HistGradientBoostingClassifier, HistGradientBoostingClassifier],
    stacks: tuple[np.ndarray, ...],
    mask: np.ndarray,
    col_indices: tuple[int, ...] | None = None,
    chunk_size: int = 160_000,
) -> np.ndarray:
    """Predict blended probability (`0.58 * clf_struct + 0.42 * clf_reg`) in low-RAM chunks."""
    clf_a, clf_b = ensemble
    out = np.zeros(mask.shape, dtype=np.float32)
    ys, xs = np.nonzero(mask)
    for start in range(0, ys.size, chunk_size):
        sl = slice(start, min(start + chunk_size, ys.size))
        X = gather_97ch(stacks, ys[sl], xs[sl], col_indices=col_indices)
        pa = clf_a.predict_proba(X)[:, 1].astype(np.float32)
        pb = clf_b.predict_proba(X)[:, 1].astype(np.float32)
        out[ys[sl], xs[sl]] = np.float32(0.58) * pa + np.float32(0.42) * pb
        del X, pa, pb
    return out


def _quantile_match_gap_to_lidar(
    p_gap_vals: np.ndarray,
    ref_sub: np.ndarray,
    tgt_full: np.ndarray,
    n_knots: int = 1001,
) -> np.ndarray:
    """Monotone rank-preserving quantile map aligning `M_Gap` onto `M_Full`'s distribution."""
    if p_gap_vals.size == 0 or ref_sub.size < 100 or tgt_full.size < 100:
        return p_gap_vals.astype(np.float32)
    qs = np.linspace(0.0, 100.0, n_knots, dtype=np.float64)
    src_q = np.percentile(ref_sub[::4], qs)
    dst_q = np.percentile(tgt_full[::4], qs)
    src_u, u_idx = np.unique(src_q, return_index=True)
    dst_u = np.maximum.accumulate(dst_q[u_idx])
    return np.interp(p_gap_vals, src_u, dst_u).astype(np.float32)


def train_dual_cover_cshd_oof(
    stacks: tuple[np.ndarray, ...],
    ctx,
    lidar_valid: np.ndarray,
    seed: int = 52,
    log=print,
) -> dict[str, Any]:
    """Train 4-quadrant 1.5 km-collared OOF & full-map single-cover (`97ch`) + Dual-Cover (`97ch/84ch`)."""
    foot = ctx.foot
    labels = ctx.labels
    q_masks = fbgr.build_quadrant_masks(foot)

    p_single_oof = np.zeros(foot.shape, dtype=np.float32)
    p_dual_oof = np.zeros(foot.shape, dtype=np.float32)
    fold_stats: dict[str, Any] = {}

    for qi, qname in enumerate(("NW", "NE", "SW", "SE")):
        q_val = q_masks[qname]
        train_region = fbgr.collared_train_region(q_val, foot, collar_px=15)
        # Fold-visible catalogue labels strictly inside collared training quadrants
        vis_train = labels & train_region

        # 1. M_Full (97 channels): evaluated across entire q_val for EXP-2 (SingleCover) and on lidar_valid for EXP-3 (DualCover)
        ens_full = fit_cshd_ensemble(
            stacks=stacks,
            train_region=train_region & lidar_valid,
            visible_train=vis_train,
            foot=foot,
            col_indices=None,
            seed=seed + 10 * qi,
        )
        # Also fit a single-cover 97-ch learner on all train_region for EXP-2 clean ablation
        ens_single = fit_cshd_ensemble(
            stacks=stacks,
            train_region=train_region,
            visible_train=vis_train,
            foot=foot,
            col_indices=None,
            seed=seed + 10 * qi + 3,
        )
        p_single_q = predict_chunked_cshd(ens_single, stacks, q_val, col_indices=None)
        p_single_oof[q_val] = p_single_q
        del ens_single, p_single_q
        gc.collect()

        # 2. M_Gap (84 strictly 1 m LiDAR-free channels): trained across ALL train_region
        ens_gap = fit_cshd_ensemble(
            stacks=stacks,
            train_region=train_region,
            visible_train=vis_train,
            foot=foot,
            col_indices=MSUB_97_COL_INDICES,
            seed=seed + 10 * qi + 6,
        )

        val_li = q_val & lidar_valid
        val_gap = q_val & (~lidar_valid)
        p_li = predict_chunked_cshd(ens_full, stacks, val_li, col_indices=None)
        p_dual_oof[val_li] = p_li

        # Quantile-calibrate M_Gap to M_Full using collared training LiDAR-valid pixels
        cal_mask = train_region & lidar_valid
        ref_full = predict_chunked_cshd(ens_full, stacks, cal_mask, col_indices=None)
        ref_gap = predict_chunked_cshd(ens_gap, stacks, cal_mask, col_indices=MSUB_97_COL_INDICES)
        raw_gap_val = predict_chunked_cshd(ens_gap, stacks, val_gap, col_indices=MSUB_97_COL_INDICES)
        p_dual_oof[val_gap] = _quantile_match_gap_to_lidar(
            raw_gap_val[val_gap], ref_gap[cal_mask], ref_full[cal_mask]
        )

        fold_stats[qname] = {
            "val_px": int(q_val.sum()),
            "val_lidar_px": int(val_li.sum()),
            "val_gap_px": int(val_gap.sum()),
            "mean_p_lidar": round(float(p_dual_oof[val_li].mean()), 5),
            "mean_p_gap_cal": round(float(p_dual_oof[val_gap].mean()), 5),
            "mean_p_single_gap": round(float(p_single_oof[val_gap].mean()), 5),
        }
        log(f"  [CSHD OOF] {qname}: mean_li={fold_stats[qname]['mean_p_lidar']:.4f}, mean_gap_cal={fold_stats[qname]['mean_p_gap_cal']:.4f} (single_gap={fold_stats[qname]['mean_p_single_gap']:.4f})")
        del ens_full, ens_gap, p_li, ref_full, ref_gap, raw_gap_val
        gc.collect()

    # Full-footprint production models for EXP-2 (single-cover) and EXP-3 (Dual-Cover)
    log("  [CSHD Full] Fitting full-map 97ch M_Full, 84ch M_Gap, and 97ch SingleCover ensembles...")
    ens_single_all = fit_cshd_ensemble(stacks, foot, labels, foot, col_indices=None, seed=seed + 200)
    p_single_full = predict_chunked_cshd(ens_single_all, stacks, foot, col_indices=None)
    del ens_single_all
    gc.collect()

    ens_full_all = fit_cshd_ensemble(stacks, foot & lidar_valid, labels, foot, col_indices=None, seed=seed + 300)
    ens_gap_all = fit_cshd_ensemble(stacks, foot, labels, foot, col_indices=MSUB_97_COL_INDICES, seed=seed + 400)

    p_dual_full = np.zeros(foot.shape, dtype=np.float32)
    foot_li = foot & lidar_valid
    foot_gap = foot & (~lidar_valid)
    p_full_li = predict_chunked_cshd(ens_full_all, stacks, foot_li, col_indices=None)
    p_dual_full[foot_li] = p_full_li

    ref_gap_all = predict_chunked_cshd(ens_gap_all, stacks, foot_li, col_indices=MSUB_97_COL_INDICES)
    raw_gap_all = predict_chunked_cshd(ens_gap_all, stacks, foot_gap, col_indices=MSUB_97_COL_INDICES)
    p_dual_full[foot_gap] = _quantile_match_gap_to_lidar(
        raw_gap_all[foot_gap], ref_gap_all[foot_li], p_full_li[foot_li]
    )
    del ens_full_all, ens_gap_all, p_full_li, ref_gap_all, raw_gap_all
    gc.collect()

    return {
        "p_single_oof": p_single_oof,
        "p_single_full": p_single_full,
        "p_dual_oof": p_dual_oof,
        "p_dual_full": p_dual_full,
        "fold_stats": fold_stats,
    }


def build_stationary_cshd_surface(
    p_dual: np.ndarray,
    base_stack: np.ndarray,
    trhv_stack: np.ndarray,
    bhgc_stack: np.ndarray,
    cshd_stack: np.ndarray,
    visible_mask: np.ndarray,
    foot: np.ndarray,
    region_mask: np.ndarray | None = None,
    w_carrier_blend: float = 0.34,
    w_tip_relay: float = 0.36,
    w_mid_conduit: float = 0.44,
    w_far_conduit: float = 0.56,
    d0_far_px: float = 15.0,
    collar_depletion_strength: float = 0.08,
    sharpen_crest: bool = True,
    crest_boost: float = 0.52,
) -> np.ndarray:
    """Posterior-Gated Piedmont-Conduit & Collar-Balanced Belief Surface.

    Identical stationary formula across every OOF holdout cell (`visible_mask = cell.visible_full`)
    and on full-map emission (`visible_mask = labels`). Uses pure CSHD channels (`ch 0..7`:
    USGS ComCat hypocenters/post-2021 lineaments, GDR #1391 blind chemical geothermometer
    disequilibrium, seamless 10 m 3DEP piedmont scarp & valley-exit fluvial chi, and geodetic
    strain kinematic reactivation) with a Michaelis-Menten posterior gate `p / (p + 0.022)` in
    the far field (`d_vis > d0_far_px`) so barren zero-probability playas stay at zero (`flat < 0.7%`)
    while PU-diluted unmapped piedmont/graben conduits are cleanly recovered.
    """
    if region_mask is None:
        region_mask = foot
    mask = region_mask & foot
    vis = np.asarray(visible_mask, dtype=bool) & foot
    d_vis = distance_transform_edt(~vis).astype(np.float32)
    relay = ldgi.anisotropic_tip_relay_cone(vis, foot)

    c_seis = np.asarray(cshd_stack[:, :, 0], dtype=np.float32)
    c_post21 = np.asarray(cshd_stack[:, :, 1], dtype=np.float32)
    c_diseq = np.asarray(cshd_stack[:, :, 2], dtype=np.float32)
    c_clay = np.asarray(cshd_stack[:, :, 3], dtype=np.float32)
    c_scarp10 = np.asarray(cshd_stack[:, :, 4], dtype=np.float32)
    c_chigrav = np.asarray(cshd_stack[:, :, 5], dtype=np.float32)
    c_strain = np.asarray(cshd_stack[:, :, 6], dtype=np.float32)
    c_crest = np.asarray(cshd_stack[:, :, 7], dtype=np.float32)
    tg = np.asarray(trhv_stack[:, :, 4], dtype=np.float32)
    depth = np.asarray(base_stack[:, :, 14], dtype=np.float32)
    slope = np.asarray(base_stack[:, :, 18], dtype=np.float32)

    # Pure CSHD carrier (orthogonal to BHGC-3's bhgc_stack spine)
    cshd_carrier = spcp.robust_unit_f32(
        np.float32(0.30) * c_crest
        + np.float32(0.24) * c_scarp10
        + np.float32(0.18) * c_chigrav
        + np.float32(0.11) * c_post21
        + np.float32(0.07) * c_seis
        + np.float32(0.05) * c_strain
        + np.float32(0.05) * (np.float32(0.60) * c_diseq + np.float32(0.40) * c_clay),
        foot,
        pct=99.6,
    )
    del c_seis, c_post21, c_diseq, c_clay, c_scarp10, c_chigrav, c_strain, c_crest

    flat_playa_gate = np.float32(1.0) - np.float32(0.92) * (
        (np.float32(1.0) / (np.float32(1.0) + np.exp(np.clip(-(depth - np.float32(300.0)) / np.float32(55.0), -30.0, 30.0))))
        * (np.float32(1.0) / (np.float32(1.0) + np.exp(np.clip((slope - np.float32(2.0)) / np.float32(0.30), -30.0, 30.0))))
    )
    del depth, slope

    surf = np.zeros(foot.shape, dtype=np.float32)
    pd_m = np.clip(p_dual[mask], np.float32(0.0), np.float32(1.0))
    cc_m = cshd_carrier[mask]
    rl_m = np.clip(relay[mask], np.float32(0.0), np.float32(1.0))
    dv_m = d_vis[mask]
    fp_m = flat_playa_gate[mask]
    tg_m = tg[mask]
    del cshd_carrier, relay, d_vis, flat_playa_gate, tg

    collar_mod = np.float32(1.0) - np.float32(collar_depletion_strength) * np.exp(
        -np.maximum(dv_m - np.float32(2.0), np.float32(0.0)) / np.float32(1.2)
    ) * (np.float32(1.0) - np.float32(0.92) * rl_m)

    mid_win = np.exp(-((dv_m - np.float32(11.5)) / np.float32(7.5)) ** 2) * (dv_m > np.float32(4.5))
    gamma_far = np.float32(1.0) - np.exp(
        -((np.maximum(dv_m - np.float32(d0_far_px), np.float32(0.0))) / np.float32(5.8)) ** 2
    )

    w_cb = np.float32(w_carrier_blend)
    near_mid_term = (
        ((np.float32(1.0) - w_cb) * pd_m + w_cb * (pd_m ** np.float32(0.62)) * (np.float32(0.25) + np.float32(0.75) * cc_m))
        * (np.float32(1.0) + np.float32(w_tip_relay) * rl_m)
        * collar_mod
        * (np.float32(1.0) + np.float32(w_mid_conduit) * mid_win * cc_m)
        * (np.float32(1.0) - np.float32(0.38) * gamma_far * (np.float32(1.0) - cc_m))
    )

    # Michaelis-Menten posterior-gated CSHD far-field discovery term (0 when pd_m == 0; recovers PU-diluted conduits)
    mm_gate = pd_m / (pd_m + np.float32(0.020))
    far_discover_term = (
        np.float32(w_far_conduit)
        * gamma_far
        * mm_gate
        * (cc_m ** np.float32(1.18))
    )

    surf[mask] = (np.float32(0.74) * near_mid_term + far_discover_term) * fp_m * (np.float32(0.38) + np.float32(0.62) * tg_m)
    del pd_m, cc_m, rl_m, dv_m, fp_m, tg_m, collar_mod, mid_win, gamma_far, near_mid_term, mm_gate, far_discover_term

    if sharpen_crest:
        surf = fbgr.sharpen_probability_crest(surf, mask, crest_boost=crest_boost)
    return np.clip(surf, 0.0, 1.0).astype(np.float32)


def build_bipopulation_cshd_surface(
    p_single: np.ndarray,
    p_dual: np.ndarray,
    base_stack: np.ndarray,
    trhv_stack: np.ndarray,
    bhgc_stack: np.ndarray,
    cshd_stack: np.ndarray,
    visible_mask: np.ndarray,
    foot: np.ndarray,
    region_mask: np.ndarray | None = None,
    beta_blind: float = 0.834,
    w_subsurface_blind: float = 0.485,
    w_subsurface_cont: float = 0.25,
    collar_depletion_strength: float = 0.45,
    w_mid_conduit_cont: float = 0.14,
    rank_gamma: float = 6.0,
) -> np.ndarray:
    """Stationary Two-Population Bayesian Envelope Surface for `H-APART3-2 (CSHD)`.

    Applies the exact same stationary formula across all 8 collared OOF holdout cells
    (`visible_mask = cell.visible_full`, `region_mask = pred_reg`) and full-footprint emission
    (`visible_mask = labels`, `region_mask = foot`):
      1. `sub_crest`: Subsurface hydro-seismo-chi physical crest combining GDR #1391 blind
         cold-spring chemical geothermometer disequilibrium (`ch2`), valley-exit fluvial chi x
         harmonic basement gravity (`ch5`), MT clay-cap + 214Bi radon upflow (`ch3`), and USGS
         ComCat post-2021 lineaments & brittle hypocenters (`ch1`, `ch0`), gated against flat
         desert playas (`depth > 300 m, slope < 2.0 deg`) and anthropogenic corridors.
      2. `P_cont`: 97-ch CSHD continuation/step-over crest (`0.90 * p_single + 0.10 * p_dual`)
         with anisotropic tip-relay cones, mid-field (`>= 600 m`) conduit bridging, non-relay
         flank moderation, and subsurface hydro-seismic coupling.
      3. `P_blind`: Michaelis-Menten dual-cover OOF posterior gate (`p_dual / (p_dual + 0.015)`)
         coupled with `(1 - w_subsurface_blind) * s_unsup + w_subsurface_blind * sub_crest`.
      4. Clean two-population envelope `max(R(P_cont)^gamma, beta_blind * R(P_blind)^gamma)` in
         `[0, 1]` with zero cross-term dilution of continuation crests.
    """
    m = foot if region_mask is None else (foot & region_mask)
    depth_all = np.asarray(base_stack[:, :, 14], dtype=np.float32)
    slope_all = np.asarray(base_stack[:, :, 18], dtype=np.float32)
    playa_gate = np.float32(1.0) - np.float32(0.92) * (
        (np.float32(1.0) / (np.float32(1.0) + np.exp(np.clip(-(depth_all - np.float32(300.0)) / np.float32(55.0), -30.0, 30.0))))
        * (np.float32(1.0) / (np.float32(1.0) + np.exp(np.clip((slope_all - np.float32(2.0)) / np.float32(0.30), -30.0, 30.0))))
    )
    del depth_all, slope_all
    tg_all = np.asarray(trhv_stack[:, :, 4], dtype=np.float32)

    sub_raw = spcp.robust_unit_f32(
        (
            np.float32(0.28) * np.asarray(cshd_stack[:, :, 2], dtype=np.float32)
            + np.float32(0.24) * np.asarray(cshd_stack[:, :, 5], dtype=np.float32)
            + np.float32(0.18) * np.asarray(cshd_stack[:, :, 3], dtype=np.float32)
            + np.float32(0.16) * np.asarray(cshd_stack[:, :, 1], dtype=np.float32)
            + np.float32(0.14) * np.asarray(cshd_stack[:, :, 0], dtype=np.float32)
        )
        * playa_gate
        * (np.float32(0.42) + np.float32(0.58) * tg_all),
        foot,
        pct=99.6,
    )
    del playa_gate, tg_all
    sub_crest = fbgr.sharpen_probability_crest(sub_raw, foot, crest_boost=0.55)
    del sub_raw

    p_cont = build_stationary_cshd_surface(
        np.float32(0.90) * p_single + np.float32(0.10) * p_dual,
        base_stack,
        trhv_stack,
        bhgc_stack,
        cshd_stack,
        visible_mask,
        foot,
        region_mask=region_mask,
        w_carrier_blend=0.10,
        w_tip_relay=0.38,
        w_mid_conduit=w_mid_conduit_cont,
        w_far_conduit=0.0,
        d0_far_px=16.5,
        collar_depletion_strength=collar_depletion_strength,
        sharpen_crest=True,
    )
    pc_vals = p_cont[m] * (
        np.float32(1.0 - w_subsurface_cont) + np.float32(w_subsurface_cont) * sub_crest[m]
    )
    del p_cont

    p_unsup = np.asarray(cshd_stack[:, :, 7], dtype=np.float32)
    s_unsup = build_stationary_cshd_surface(
        p_unsup,
        base_stack,
        trhv_stack,
        bhgc_stack,
        cshd_stack,
        visible_mask,
        foot,
        region_mask=region_mask,
        w_carrier_blend=0.60,
        w_tip_relay=0.0,
        w_mid_conduit=0.25,
        w_far_conduit=0.65,
        d0_far_px=13.5,
        collar_depletion_strength=0.30,
        sharpen_crest=True,
    )
    del p_unsup

    pd_m = np.clip(p_dual[m], np.float32(0.0), np.float32(1.0))
    mm_gate = pd_m / (pd_m + np.float32(0.015))
    blind_mix = (
        np.float32(1.0 - w_subsurface_blind) * np.clip(s_unsup[m], np.float32(0.0), np.float32(1.0))
        + np.float32(w_subsurface_blind) * sub_crest[m]
    )
    prod = (mm_gate ** np.float32(0.32)) * (blind_mix ** np.float32(0.88))
    del pd_m, mm_gate, s_unsup, sub_crest, blind_mix

    n_m = max(int(prod.size), 1)
    o_b = np.argsort(prod, kind="mergesort")
    rk_b = np.empty(prod.size, dtype=np.float32)
    rk_b[o_b] = (np.arange(prod.size, dtype=np.float32) + np.float32(0.5)) / np.float32(n_m)
    del prod, o_b

    o_c = np.argsort(pc_vals, kind="mergesort")
    rk_c = np.empty(pc_vals.size, dtype=np.float32)
    rk_c[o_c] = (np.arange(pc_vals.size, dtype=np.float32) + np.float32(0.5)) / np.float32(n_m)
    del pc_vals, o_c

    out = np.zeros(foot.shape, dtype=np.float32)
    out[m] = np.maximum(
        np.power(rk_c, np.float32(rank_gamma)),
        np.float32(beta_blind) * np.power(rk_b, np.float32(rank_gamma)),
    )
    vis = np.asarray(visible_mask, dtype=bool) & foot
    out[vis] = np.float32(0.0)
    return np.clip(out, 0.0, 1.0).astype(np.float32)


def emit_cshd_dots(
    surface: np.ndarray,
    visible_mask: np.ndarray,
    foot: np.ndarray,
    region_mask: np.ndarray | None = None,
    budget: int = TARGET_BUDGET,
    b_collar_px: float = B_COLLAR_PX,
    min_sep_px: float = DEFAULT_AXIAL_SEP_PX,
    top_support_mult: float = 4.6,
) -> tuple[np.ndarray, dict[str, Any]]:
    """Emit discrete `{0, 1}` dots strictly outside `d_vis <= b_collar_px` via `gems32.emitter.emit`."""
    if region_mask is None:
        region_mask = foot
    vis = np.asarray(visible_mask, dtype=bool) & foot
    d_vis = distance_transform_edt(~vis)
    eligible = region_mask & foot & (d_vis > float(b_collar_px)) & (surface > 0.0)
    del d_vis

    n_elig = int(eligible.sum())
    if n_elig == 0 or budget <= 0:
        return np.zeros(foot.shape, dtype=bool), {"n_emitted": 0, "n_eligible": n_elig}

    # Confine CELF heap to top `budget * top_support_mult` support pixels for fast exact packing
    max_sup = min(n_elig, max(int(round(budget * top_support_mult)), budget + 2000))
    vals = surface[eligible]
    if n_elig > max_sup:
        thresh = float(np.partition(vals, n_elig - max_sup)[n_elig - max_sup])
        sup_mask = eligible & (surface >= thresh)
    else:
        sup_mask = eligible
    del vals, eligible

    field = np.where(sup_mask, surface, np.float32(0.0))
    del sup_mask
    emitted_f32, log_obj = emitter.emit(
        field,
        budget=int(budget),
        prior_dti=0.0,
        min_sep_px=float(min_sep_px),
    )
    dots = (emitted_f32 > 0.5) & foot
    return dots, log_obj.as_dict()
