"""H-APART3-3 (WCHD): Harmonic Upward-Continuation Listric Contact-Dip Updip Projection,
Repaired True-RTP Magnetic Tilt Phase, Hydrothermal Magnetite-Destruction x Adularia K/eTh
Metasomatism & Stress-Resolved Dilation-Tendency Dual-Cover Conduit Detection.

Implements the pre-registered `docs/research/h-apart3-3-wchd-preregistration-20261028.md`
architecture:

1. Excises prior global column 84 (`bhgc_extra_6ch.npy` channel 1, which misread GeoDAWN
   radiometric Total Count `Band 6 (tc)` as magnetic tilt — `IR-CTHG-BAND6-TC-02` /
   `IR-WCHD-BAND6-DROP-01`) from every supervised learner (`104`-ch `M_Full`, `91`-ch
   `M_Gap`, `34`-ch `M_Subspace`).
2. Builds 8 strictly label-free, 100% 1 m LiDAR-free physical channels (`WCHD_EXTRA_CHANNELS`):
     0 `wchd_true_rtp_tmi_tilt_contact_wall`:
       Exact 2-D Fourier vertical derivative `d(RTP)/dz` (`|k| exp(-|k|*150m)`) & horizontal
       gradient on `Band 2 (rtp)` fused with verified `Band 9 (tmi_vg) / Band 3 (tmi_hg)` TMI
       tilt zero-crossing wall (`sech^2(theta / 0.38)`).
     1 `wchd_poisson_listric_updip_trace`:
       4-altitude Poisson harmonic upward continuation `z in {200, 600, 1500, 3000} m` on
       `Band 13 (iso_grav_anom)` with downdip-to-updip vector advection (`map_coordinates`)
       along the footwall-pointing basement-depth/gravity vector `-grad(depth_to_base)`,
       projecting deep hanging-wall listric normal fault roots (`~53 deg` dip) updip onto
       their concealed sub-alluvial surface fault trace while cancelling vertical volcanic
       dikes (`Delta x = 0`) and rootless alluvial fans (`g(3000m) -> 0`).
     2 `wchd_joint_grav_rtp_phase_congruency`:
       Multi-altitude (`z in {200, 1000} m`) cross-field structural phase congruency
       `cos^2(psi_g - psi_rtp) * sech^2(theta_g / 0.42) * sech^2(theta_rtp / 0.45)` between
       exact Laplace-harmonic gravity tilt and true-RTP magnetic tilt.
     3 `wchd_hydro_demag_kth_adularia_corridor`:
       Hydrothermal titanomagnetite-destruction trough (`nabla_h^2 M_RTP > 0` inside sulfidized
       / argillized fault damage zones) coupled with 4-contractor-debiased GeoDAWN potassic
       adularia/illite metasomatism excess (`Z_block(K) - 0.75 * Z_block(Th)`) + redox uranium
       excess and `Band 17 (cond_surf)` lateral clay-cap edges, damped on closed playas and
       eroded across contractor flight-block seams.
     4 `wchd_morris_dilation_slip_tendency`:
       Great Basin WNW-ESE minimum horizontal stress (`S_hmin = N114E`, locally modulated by
       geodetic shear/dilatation `Bands 4, 7, 8`) resolved onto the multi-physics structural
       strike tangent (`T_d = cos^2(alpha_n)`, `T_s = sin^2(2*alpha_n)`).
     5 `wchd_horst_cross_divide_tilt_footwall`:
       Cross-horst `3.5 km` vs `0.6 km` `det_elev` tilt vector aligned with 10 m 3DEP piedmont
       break-in-slope curvature (`1.65 deg <= slope <= 13.6 deg`) and headwater fluvial `chi`
       step / `k_sn` disequilibrium (`dem10_chi_100m_i16.tif`).
     6 `wchd_updip_blind_geotherm_seismic_bridge`:
       Strike-coherent coupling of linear updip-projected basement fault traces (`ch1`) and
       magnetite-destruction corridors (`ch3`) with DOE GDR #1391 blind cold-spring chemical
       geothermometer disequilibrium and post-2021 USGS ComCat microseismic chords.
     7 `wchd_unified_updip_conduit_crest`:
       Oriented 1-px Hessian crest-thinned WCHD structural-geothermal conduit spine, vetoed
       for Lake Lahontan shorelines (`1325-1342 m`, `1268-1284 m`), flat evaporite playas,
       TIGER highway embankments, and BLM mining scars.

Memory safety: uses `scipy.fft.rfft2`/`irfft2` in `float32`/`complex64` (`~54 MB` spectrum)
and chunked read-only `open_memmap` gathers so peak RSS stays well below `1.5 GiB`.
"""
from __future__ import annotations

import gc
import json
from pathlib import Path
from typing import Any

import numpy as np
import rasterio
from numpy.lib.format import open_memmap
from scipy.fft import fftfreq, irfft2, rfft2, rfftfreq
from scipy.ndimage import (
    binary_dilation,
    distance_transform_edt,
    gaussian_filter,
    map_coordinates,
    sobel,
)
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score

from gems32 import bhgc, cshd, emitter, fbgr, features, ldgi, paths, spcp, trhv

TARGET_BUDGET: int = 37_654
B_COLLAR_PX: float = 2.0
DEFAULT_AXIAL_SEP_PX: float = 3.88
GRID_SPACING_M: float = 100.0

# Prior global column 84 (`bhgc_extra_6ch.npy` ch 1) is strictly excised (`IR-WCHD-BAND6-DROP-01`)
EXCISED_RAW_COL_BHGC_CH1: int = 84

WCHD_EXTRA_CHANNELS: tuple[str, ...] = (
    "wchd_true_rtp_tmi_tilt_contact_wall",      # 0
    "wchd_poisson_listric_updip_trace",         # 1
    "wchd_joint_grav_rtp_phase_congruency",     # 2
    "wchd_hydro_demag_kth_adularia_corridor",   # 3
    "wchd_morris_dilation_slip_tendency",       # 4
    "wchd_horst_cross_divide_tilt_footwall",    # 5
    "wchd_updip_blind_geotherm_seismic_bridge", # 6
    "wchd_unified_updip_conduit_crest",         # 7
)

# Raw stack widths: 35 (base) + 20 (spcp) + 8 (trhv) + 8 (ldgi) + 12 (fbgr) + 6 (bhgc) + 8 (cshd) + 8 (wchd) = 105 raw
# Clean supervised layout drops raw col 84 -> 104 clean channels!
RAW_TOTAL_COLS: int = 35 + 20 + 8 + 8 + 12 + 6 + 8 + len(WCHD_EXTRA_CHANNELS)
CLEAN_104_RAW_COLS: tuple[int, ...] = tuple(
    c for c in range(RAW_TOTAL_COLS) if c != EXCISED_RAW_COL_BHGC_CH1
)
# Pure 1 m LiDAR-free raw columns (excludes the 13 LiDAR-dependent cols AND raw col 84 -> 91 clean channels)
MGAP_91_RAW_COLS: tuple[int, ...] = tuple(
    c for c in CLEAN_104_RAW_COLS if c not in bhgc.LIDAR_DEPENDENT_89_COLS
)
# Dedicated 34-channel Potential-Field + Updip-Projection + Alteration + 3DEP/Stress Subspace (100% non-LiDAR, col 84 excluded)
MSUBSPACE_34_RAW_COLS: tuple[int, ...] = (
    # Core potential-field, MT, basement depth & geodetic strain bands from feature_stack.npy (10 ch)
    1,   # Band 2: rtp (Reduced-to-Pole magnetic anomaly)
    2,   # Band 3: tmi_hg (TMI horizontal gradient magnitude)
    3,   # Band 4: geod_2ndinv
    4,   # Band 5: iso_grav_anom_slope
    6,   # Band 7: geod_shearrate
    7,   # Band 8: geod_dilaterate
    8,   # Band 9: tmi_vg (TMI vertical derivative)
    12,  # Band 13: iso_grav_anom
    14,  # Band 15: depth_to_base_surf
    16,  # Band 17: cond_surf
    # SPCP curvature, Roest 3D analytic signal & hydrothermal demag (6 ch)
    35 + 0,  # pf_grav_kmax
    35 + 2,  # pf_mag_kmax
    35 + 5,  # pf_grav_saddle
    35 + 6,  # pf_mag_analytic_signal
    35 + 7,  # hydro_demag_index
    35 + 8,  # hydro_k_th_excess
    # FBGR upward continuation, 214Bi radon & Morris (4 ch)
    55 + 16 + 0,  # fbgr ch0 (71): grav_up500_2000
    55 + 16 + 1,  # fbgr ch1 (72): grav_dip_asym
    55 + 16 + 3,  # fbgr ch3 (74): radon_214bi
    55 + 16 + 6,  # fbgr ch6 (77): morris_obliquity
    # BHGC harmonic gravity divergence & piedmont horst (2 ch; raw col 84 strictly excluded!)
    83 + 0,  # bhgc ch0 (83): grav_vec_div_crest
    83 + 2,  # bhgc ch2 (85): piedmont_horst_step_spine
    # CSHD post-2021 seismicity, blind geothermometer, 10m 3DEP scarp & chi-gravity (4 ch)
    89 + 1,  # cshd ch1 (90): comcat_post2021_lineament_bridge
    89 + 2,  # cshd ch2 (91): gdr_blind_geotherm_disequilibrium
    89 + 4,  # cshd ch4 (93): seamless_10m_piedmont_apron_scarp
    89 + 5,  # cshd ch5 (94): piedmont_chi_gravity_concordance
    # All 8 new WCHD harmonic updip, true-RTP tilt, magnetite-destruction/K-Th & dilation channels (8 ch)
    97 + 0,
    97 + 1,
    97 + 2,
    97 + 3,
    97 + 4,
    97 + 5,
    97 + 6,
    97 + 7,
)


def _fill_outside_median(arr: np.ndarray, foot: np.ndarray) -> np.ndarray:
    out = np.asarray(arr, dtype=np.float32).copy()
    bad = (~foot) | (~np.isfinite(out))
    med = float(np.median(out[~bad])) if np.any(~bad) else 0.0
    out[bad] = np.float32(med)
    return out


def _prepare_rfft_spectrum(
    field2d: np.ndarray,
    foot: np.ndarray,
    pad: int = 96,
    pre_sigma_px: float = 0.85,
) -> tuple[np.ndarray, np.ndarray, tuple[int, int], int]:
    """Compute reflect-padded `complex64` 2-D `rfft2` spectrum and radial wavenumber `|k|` (`m^-1`)."""
    clean = _fill_outside_median(field2d, foot)
    if pre_sigma_px > 0.0:
        clean = gaussian_filter(clean, sigma=float(pre_sigma_px)).astype(np.float32)
    h, w = clean.shape
    padded = np.pad(clean, ((pad, pad), (pad, pad)), mode="reflect")
    del clean
    hp, wp = padded.shape
    spec = rfft2(padded, workers=2).astype(np.complex64, copy=False)
    del padded

    ky = (2.0 * np.pi * fftfreq(hp, d=GRID_SPACING_M)).astype(np.float32)[:, None]
    kx = (2.0 * np.pi * rfftfreq(wp, d=GRID_SPACING_M)).astype(np.float32)[None, :]
    k_rad = np.hypot(kx, ky).astype(np.float32)
    return spec, k_rad, (h, w), pad


def _eval_harmonic_altitude(
    spec: np.ndarray,
    k_rad: np.ndarray,
    orig_shape: tuple[int, int],
    pad: int,
    z_m: float,
    vertical_deriv: bool = False,
) -> np.ndarray:
    """Evaluate upward-continued potential field or its exact vertical derivative at height `z_m`."""
    h, w = orig_shape
    hp = spec.shape[0]
    wp = (spec.shape[1] - 1) * 2
    filt = np.exp(-k_rad * np.float32(z_m)).astype(np.float32)
    if vertical_deriv:
        filt *= k_rad
    rec = irfft2(spec * filt, s=(hp, wp), workers=2)
    del filt
    return np.asarray(rec[pad : pad + h, pad : pad + w], dtype=np.float32).copy()


def _central_grad_f32(field2d: np.ndarray, sigma_px: float = 0.0) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return `(df/dx_east, df/dy_south, ||grad_h f||)` in physical `m^-1` units."""
    src = gaussian_filter(field2d, sigma=float(sigma_px)).astype(np.float32) if sigma_px > 0.0 else field2d
    gx = (sobel(src, axis=1) / np.float32(8.0 * GRID_SPACING_M)).astype(np.float32)
    gy = (sobel(src, axis=0) / np.float32(8.0 * GRID_SPACING_M)).astype(np.float32)
    gh = np.hypot(gx, gy).astype(np.float32)
    return gx, gy, gh


def _build_rtp_and_phase_channels(
    base_mm: np.ndarray,
    foot: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict[str, Any]]:
    """Build `wchd_ch0` (true RTP/TMI tilt wall), `wchd_ch1` (4-altitude listric updip projection),
    and `wchd_ch2` (joint gravity-RTP phase congruency) in `< 220 MB` peak RAM."""
    # 1. Exact Fourier RTP potential-field derivatives on Band 2 (`rtp`, index 1)
    rtp_raw = np.asarray(base_mm[:, :, 1], dtype=np.float32)
    tmi_hg_raw = np.maximum(np.asarray(base_mm[:, :, 2], dtype=np.float32), np.float32(0.0))
    tmi_vg_raw = np.asarray(base_mm[:, :, 8], dtype=np.float32)

    m_spec, k_rad, orig_shape, pad = _prepare_rfft_spectrum(rtp_raw, foot, pad=96, pre_sigma_px=1.05)
    del rtp_raw

    # Altitude 150 m (suppresses flight-line herringbone while resolving sub-alluvial volcanic/basement contacts)
    m_200 = _eval_harmonic_altitude(m_spec, k_rad, orig_shape, pad, z_m=200.0, vertical_deriv=False)
    mz_200 = _eval_harmonic_altitude(m_spec, k_rad, orig_shape, pad, z_m=200.0, vertical_deriv=True)
    mx_200, my_200, mh_200 = _central_grad_f32(m_200, sigma_px=0.6)
    del m_200

    eps_m = np.float32(float(np.percentile(mh_200[foot], 20)) * 0.25 + 1e-7)
    theta_rtp_200 = np.arctan2(mz_200, mh_200 + eps_m).astype(np.float32)
    del mz_200

    # Organizer TMI tilt angle from verified Band 9 (tmi_vg) and Band 3 (tmi_hg)
    # Scale Band 3 (`nT / 100 m` grid-step units) to match Band 9 median magnitude
    tmi_hg_med = float(np.median(tmi_hg_raw[foot])) + 1e-6
    tmi_vg_mad = float(np.median(np.abs(tmi_vg_raw[foot] - np.median(tmi_vg_raw[foot])))) + 1e-6
    theta_tmi = np.arctan2(
        tmi_vg_raw / np.float32(tmi_vg_mad),
        (tmi_hg_raw / np.float32(tmi_hg_med)) + np.float32(0.12),
    ).astype(np.float32)

    sech2_rtp_200 = (np.float32(1.0) / np.cosh(np.clip(theta_rtp_200 / np.float32(0.38), -8.0, 8.0)) ** 2).astype(np.float32)
    sech2_tmi = (np.float32(1.0) / np.cosh(np.clip(theta_tmi / np.float32(0.42), -8.0, 8.0)) ** 2).astype(np.float32)
    mh_p75 = np.float32(float(np.percentile(mh_200[foot], 75)) + 1e-7)
    thg_p75 = np.float32(float(np.percentile(tmi_hg_raw[foot], 75)) + 1e-7)

    mag_wall_raw = (
        np.float32(0.66) * sech2_rtp_200 * np.tanh(mh_200 / mh_p75)
        + np.float32(0.34) * sech2_tmi * np.tanh(tmi_hg_raw / thg_p75)
    ).astype(np.float32)
    del tmi_hg_raw, tmi_vg_raw, theta_tmi, sech2_tmi
    ch0 = spcp.robust_unit_f32(
        fbgr.sharpen_probability_crest(mag_wall_raw, foot, crest_boost=0.46),
        foot,
        pct=99.5,
    )
    del mag_wall_raw

    # Altitude 1000 m RTP for deep phase congruency
    m_1000 = _eval_harmonic_altitude(m_spec, k_rad, orig_shape, pad, z_m=1000.0, vertical_deriv=False)
    mz_1000 = _eval_harmonic_altitude(m_spec, k_rad, orig_shape, pad, z_m=1000.0, vertical_deriv=True)
    del m_spec
    mx_1000, my_1000, mh_1000 = _central_grad_f32(m_1000, sigma_px=0.8)
    del m_1000
    eps_m1k = np.float32(float(np.percentile(mh_1000[foot], 20)) * 0.25 + 1e-7)
    theta_rtp_1000 = np.arctan2(mz_1000, mh_1000 + eps_m1k).astype(np.float32)
    del mz_1000

    # 2. 4-Altitude Harmonic Gravity Upward-Continuation Ladder on Band 13 (`iso_grav_anom`, index 12)
    grav_raw = np.asarray(base_mm[:, :, 12], dtype=np.float32)
    g_spec, _, _, _ = _prepare_rfft_spectrum(grav_raw, foot, pad=96, pre_sigma_px=0.90)
    del grav_raw

    g_200 = _eval_harmonic_altitude(g_spec, k_rad, orig_shape, pad, z_m=200.0, vertical_deriv=False)
    gz_200 = _eval_harmonic_altitude(g_spec, k_rad, orig_shape, pad, z_m=200.0, vertical_deriv=True)
    gx_200, gy_200, gh_200 = _central_grad_f32(g_200, sigma_px=0.6)
    del g_200
    eps_g2 = np.float32(float(np.percentile(gh_200[foot], 20)) * 0.25 + 1e-7)
    theta_g_200 = np.arctan2(gz_200, gh_200 + eps_g2).astype(np.float32)
    del gz_200

    # Altitude 1000 m gravity for cross-field phase congruency (`wchd_ch2`)
    g_1000 = _eval_harmonic_altitude(g_spec, k_rad, orig_shape, pad, z_m=1000.0, vertical_deriv=False)
    gz_1000 = _eval_harmonic_altitude(g_spec, k_rad, orig_shape, pad, z_m=1000.0, vertical_deriv=True)
    gx_1000, gy_1000, gh_1000 = _central_grad_f32(g_1000, sigma_px=0.8)
    del g_1000
    eps_g1k = np.float32(float(np.percentile(gh_1000[foot], 20)) * 0.25 + 1e-7)
    theta_g_1000 = np.arctan2(gz_1000, gh_1000 + eps_g1k).astype(np.float32)
    del gz_1000

    # Compute `wchd_ch2`: Joint Gravity-RTP Structural Phase Congruency across z in {200, 1000} m
    dot_200 = gx_200 * mx_200 + gy_200 * my_200
    cos2_200 = (dot_200 * dot_200) / (gh_200 * gh_200 * mh_200 * mh_200 + np.float32(1e-18))
    del dot_200, gx_200, gy_200, mx_200, my_200

    dot_1000 = gx_1000 * mx_1000 + gy_1000 * my_1000
    cos2_1000 = (dot_1000 * dot_1000) / (gh_1000 * gh_1000 * mh_1000 * mh_1000 + np.float32(1e-18))
    del dot_1000, gx_1000, gy_1000, mx_1000, my_1000

    sech2_g_200 = (np.float32(1.0) / np.cosh(np.clip(theta_g_200 / np.float32(0.42), -8.0, 8.0)) ** 2).astype(np.float32)
    sech2_g_1000 = (np.float32(1.0) / np.cosh(np.clip(theta_g_1000 / np.float32(0.45), -8.0, 8.0)) ** 2).astype(np.float32)
    sech2_rtp_1000 = (np.float32(1.0) / np.cosh(np.clip(theta_rtp_1000 / np.float32(0.45), -8.0, 8.0)) ** 2).astype(np.float32)
    del theta_rtp_200, theta_rtp_1000, theta_g_200, theta_g_1000

    gh2_p70 = np.float32(float(np.percentile(gh_200[foot], 70)) + 1e-7)
    gh1k_p70 = np.float32(float(np.percentile(gh_1000[foot], 70)) + 1e-7)
    mh1k_p70 = np.float32(float(np.percentile(mh_1000[foot], 70)) + 1e-7)

    pc_200 = cos2_200 * sech2_g_200 * sech2_rtp_200 * np.sqrt(np.tanh(gh_200 / gh2_p70) * np.tanh(mh_200 / mh_p75))
    pc_1000 = cos2_1000 * sech2_g_1000 * sech2_rtp_1000 * np.sqrt(np.tanh(gh_1000 / gh1k_p70) * np.tanh(mh_1000 / mh1k_p70))
    del cos2_200, cos2_1000, sech2_g_200, sech2_g_1000, sech2_rtp_200, sech2_rtp_1000, gh_1000, mh_200, mh_1000

    pc_raw = (np.float32(0.58) * pc_200 + np.float32(0.42) * pc_1000).astype(np.float32)
    del pc_200, pc_1000
    ch2 = spcp.robust_unit_f32(
        fbgr.sharpen_probability_crest(pc_raw, foot, crest_boost=0.45),
        foot,
        pct=99.5,
    )
    del pc_raw

    # Complete the 4-altitude ladder {200, 600, 1500, 3000} m for `wchd_ch1` listric updip projection
    g_600 = _eval_harmonic_altitude(g_spec, k_rad, orig_shape, pad, z_m=600.0, vertical_deriv=False)
    _, _, gh_600 = _central_grad_f32(g_600, sigma_px=0.8)
    del g_600

    g_1500 = _eval_harmonic_altitude(g_spec, k_rad, orig_shape, pad, z_m=1500.0, vertical_deriv=False)
    gx_1500, gy_1500, gh_1500 = _central_grad_f32(g_1500, sigma_px=1.0)
    del g_1500

    g_3000 = _eval_harmonic_altitude(g_spec, k_rad, orig_shape, pad, z_m=3000.0, vertical_deriv=False)
    del g_spec, k_rad
    _, _, gh_3000 = _central_grad_f32(g_3000, sigma_px=1.2)
    del g_3000

    # Normalize each altitude's horizontal gradient magnitude by its P90 over footprint
    hn_200 = np.clip(gh_200 / np.float32(float(np.percentile(gh_200[foot], 90)) + 1e-7), 0.0, 2.5).astype(np.float32)
    hn_600 = np.clip(gh_600 / np.float32(float(np.percentile(gh_600[foot], 90)) + 1e-7), 0.0, 2.5).astype(np.float32)
    hn_1500 = np.clip(gh_1500 / np.float32(float(np.percentile(gh_1500[foot], 90)) + 1e-7), 0.0, 2.5).astype(np.float32)
    hn_3000 = np.clip(gh_3000 / np.float32(float(np.percentile(gh_3000[foot], 90)) + 1e-7), 0.0, 2.5).astype(np.float32)
    del gh_200, gh_600, gh_1500, gh_3000

    # Unit updip (footwall-pointing) vector u = (ux, uy): points from thick basin fill toward shallow dense horst
    depth_raw = _fill_outside_median(base_mm[:, :, 14], foot)
    depth_sm = gaussian_filter(depth_raw, sigma=4.0).astype(np.float32)
    dx_b = (sobel(depth_sm, axis=1) / np.float32(800.0)).astype(np.float32)
    dy_b = (sobel(depth_sm, axis=0) / np.float32(800.0)).astype(np.float32)
    del depth_sm
    dn_mag = np.hypot(dx_b, dy_b) + np.float32(1e-6)
    gn_mag = np.hypot(gx_1500, gy_1500) + np.float32(1e-6)

    # Footwall has shallower depth (-grad depth) AND higher isostatic gravity (+grad g_1500)
    ux_raw = np.float32(0.58) * (-dx_b / dn_mag) + np.float32(0.42) * (gx_1500 / gn_mag)
    uy_raw = np.float32(0.58) * (-dy_b / dn_mag) + np.float32(0.42) * (gy_1500 / gn_mag)
    del dx_b, dy_b, dn_mag, gx_1500, gy_1500, gn_mag
    u_norm = np.hypot(ux_raw, uy_raw) + np.float32(1e-6)
    ux = (ux_raw / u_norm).astype(np.float32)
    uy = (uy_raw / u_norm).astype(np.float32)
    del ux_raw, uy_raw, u_norm

    # Sample downdip hanging-wall positions x - Delta_s * u (`cot(53 deg) ~ 0.75`: 600m->4.5px, 1500m->11px, 3000m->19.5px)
    h, w = orig_shape
    yy_grid, xx_grid = np.meshgrid(
        np.arange(h, dtype=np.float32),
        np.arange(w, dtype=np.float32),
        indexing="ij",
    )

    def _sample_shift(arr: np.ndarray, shift_px: float) -> np.ndarray:
        coords = np.empty((2, h, w), dtype=np.float32)
        coords[0] = np.clip(yy_grid + np.float32(shift_px) * uy, 0.0, float(h - 1))
        coords[1] = np.clip(xx_grid + np.float32(shift_px) * ux, 0.0, float(w - 1))
        return map_coordinates(arr, coords, order=1, mode="nearest").astype(np.float32)

    # Downdip is `-u` (`shift_px < 0`), footwall is `+u` (`shift_px > 0`)
    hw_600 = _sample_shift(hn_600, -4.5)
    hw_1500 = _sample_shift(hn_1500, -11.0)
    hw_3000 = _sample_shift(hn_3000, -19.5)
    fw_1500 = _sample_shift(hn_1500, +9.0)
    del yy_grid, xx_grid, ux, uy, hn_600, hn_1500, hn_3000

    # Dipping-fault asymmetry cancels symmetric vertical basaltic dikes (`hw_1500 approx fw_1500`)
    dip_asym = np.maximum(
        np.float32(0.0),
        np.float32(0.55) * hw_1500 + np.float32(0.45) * hw_3000 - np.float32(0.62) * fw_1500,
    )
    deep_root = np.sqrt(np.maximum(hw_1500 * hw_3000, np.float32(0.0)))
    del hw_1500, hw_3000, fw_1500

    # Gate to sub-alluvial piedmont & basin-margin basement transition (`10 m <= depth <= 1900 m`)
    pied_depth_env = (
        (np.float32(1.0) / (np.float32(1.0) + np.exp(np.clip(-(depth_raw - np.float32(12.0)) / np.float32(15.0), -30.0, 30.0))))
        * (np.float32(1.0) / (np.float32(1.0) + np.exp(np.clip((depth_raw - np.float32(1850.0)) / np.float32(320.0), -30.0, 30.0))))
    ).astype(np.float32)
    del depth_raw

    updip_raw = (
        np.power(np.maximum(hn_200, np.float32(0.0)), np.float32(0.42))
        * (np.float32(0.32) * hw_600 + np.float32(0.42) * dip_asym + np.float32(0.26) * deep_root)
        * (np.float32(0.28) + np.float32(0.72) * pied_depth_env)
    ).astype(np.float32)
    del hn_200, hw_600, dip_asym, deep_root, pied_depth_env

    ch1 = spcp.robust_unit_f32(
        fbgr.sharpen_probability_crest(updip_raw, foot, crest_boost=0.50),
        foot,
        pct=99.5,
    )
    del updip_raw
    gc.collect()

    stats = {
        "rtp_fft_altitudes_m": [200.0, 1000.0],
        "grav_upward_ladder_m": [200.0, 600.0, 1500.0, 3000.0],
        "updip_projection_shifts_px": [-4.5, -11.0, -19.5],
        "band6_tc_used": False,
    }
    return ch0, ch1, ch2, stats


def _build_hydro_demag_kth_channel(
    ddir: Path,
    base_mm: np.ndarray,
    trhv_mm: np.ndarray,
    fbgr_mm: np.ndarray,
    foot: np.ndarray,
) -> tuple[np.ndarray, dict[str, Any]]:
    """Build `wchd_ch3` (`wchd_hydro_demag_kth_adularia_corridor`):
    Hydrothermal magnetite-destruction trough (`nabla_h^2 M_RTP > 0`) x 4-contractor-debiased
    GeoDAWN potassic adularia/illite excess (`Z_block(K) - 0.75 * Z_block(Th)`) + MT clay-cap edge."""
    # 1. Magnetite-destruction trough on Band 2 (`rtp`): local linear magnetic low inside magnetic volcanic/basement host
    rtp = _fill_outside_median(base_mm[:, :, 1], foot)
    rtp_s15 = gaussian_filter(rtp, sigma=1.5).astype(np.float32)
    rtp_s65 = gaussian_filter(rtp, sigma=6.5).astype(np.float32)
    rtp_s14 = gaussian_filter(rtp, sigma=14.0).astype(np.float32)
    del rtp

    # Positive band-pass trough (`rtp_s65 - rtp_s15 > 0`) where hydrothermal fluids destroyed titanomagnetite
    demag_trough = np.maximum(rtp_s65 - rtp_s15, np.float32(0.0))
    p35_host = float(np.percentile(rtp_s14[foot], 35))
    p80_host = float(np.percentile(rtp_s14[foot], 80))
    host_mag_gate = np.clip((rtp_s14 - np.float32(p35_host)) / np.float32(max(p80_host - p35_host, 1.0)), 0.15, 1.0).astype(np.float32)
    del rtp_s15, rtp_s65, rtp_s14
    demag_unit = spcp.robust_unit_f32(demag_trough * host_mag_gate, foot, pct=99.3)
    del demag_trough, host_mag_gate

    # 2. Contractor-debiased GeoDAWN radiometric K/eTh adularia & U/eTh redox excess
    with rasterio.open(ddir / "external" / "geodawn_rad_u8.tif") as ds_rad:
        k_u8 = ds_rad.read(1).astype(np.float32)
        th_u8 = ds_rad.read(2).astype(np.float32)
        u_u8 = ds_rad.read(3).astype(np.float32)
    with rasterio.open(ddir / "external" / "acquisition_block_id_100m.tif") as ds_blk:
        blk_id = ds_blk.read(1)

    rad_valid = foot & (k_u8 > 0) & (th_u8 > 0) & (blk_id > 0)
    z_k = np.zeros(foot.shape, dtype=np.float32)
    z_th = np.zeros(foot.shape, dtype=np.float32)
    z_u = np.zeros(foot.shape, dtype=np.float32)

    seam_edge = np.zeros(foot.shape, dtype=bool)
    unique_blocks = [int(b) for b in np.unique(blk_id[rad_valid]) if b > 0]
    for b in unique_blocks:
        bm = rad_valid & (blk_id == b)
        if int(bm.sum()) < 200:
            continue
        for src_arr, dst_arr in ((k_u8, z_k), (th_u8, z_th), (u_u8, z_u)):
            vals = src_arr[bm]
            med = float(np.median(vals))
            mad = float(np.median(np.abs(vals - med))) * 1.4826 + 1.0
            dst_arr[bm] = np.clip((vals - med) / mad, -4.0, 5.0).astype(np.float32)
        # Detect inter-contractor seam pixels for 2-px boundary damping
        dil = binary_dilation(blk_id == b, iterations=2)
        seam_edge |= dil & (blk_id != b) & (blk_id > 0)
    del k_u8, th_u8, u_u8, blk_id, rad_valid

    seam_damp = np.where(seam_edge, np.float32(0.35), np.float32(1.0))
    del seam_edge

    # Adularia/illite K-metasomatism excess (`Z_K - 0.75 * Z_Th`) cancels primary unaltered rhyolite K+Th co-enrichment
    kth_excess = np.maximum(z_k - np.float32(0.75) * z_th, np.float32(0.0)) * seam_damp
    uth_excess = np.maximum(z_u - np.float32(0.55) * z_th, np.float32(0.0)) * seam_damp
    del z_k, z_th, z_u, seam_damp
    alter_unit = spcp.robust_unit_f32(
        gaussian_filter(np.float32(0.72) * kth_excess + np.float32(0.28) * uth_excess, sigma=1.4),
        foot,
        pct=99.3,
    )
    del kth_excess, uth_excess

    # 3. Band 17 (`cond_surf`, index 16) lateral hydrothermal smectite clay-cap edge
    cond = _fill_outside_median(base_mm[:, :, 16], foot)
    _, _, cond_gh = _central_grad_f32(cond, sigma_px=2.0)
    del cond
    cond_unit = spcp.robust_unit_f32(cond_gh, foot, pct=99.2)
    del cond_gh

    # Damp flat closed-playa evaporite clays (`depth > 280 m, slope < 2.0 deg`), BLM mines, and TIGER roads
    depth = np.asarray(base_mm[:, :, 14], dtype=np.float32)
    slope = np.asarray(base_mm[:, :, 18], dtype=np.float32)
    playa_veto = np.float32(1.0) - np.float32(0.90) * (
        (np.float32(1.0) / (np.float32(1.0) + np.exp(np.clip(-(depth - np.float32(280.0)) / np.float32(55.0), -30.0, 30.0))))
        * (np.float32(1.0) / (np.float32(1.0) + np.exp(np.clip((slope - np.float32(2.0)) / np.float32(0.30), -30.0, 30.0))))
    )
    del depth, slope

    tiger_clean = np.asarray(trhv_mm[:, :, 4], dtype=np.float32)
    blm_clean = np.clip(np.asarray(fbgr_mm[:, :, 10], dtype=np.float32), 0.0, 1.0)

    hydro_raw = (
        (
            np.float32(0.40) * demag_unit * (np.float32(0.35) + np.float32(0.65) * alter_unit)
            + np.float32(0.32) * alter_unit * (np.float32(0.35) + np.float32(0.65) * cond_unit)
            + np.float32(0.28) * demag_unit * (np.float32(0.40) + np.float32(0.60) * cond_unit)
        )
        * playa_veto
        * (np.float32(0.50) + np.float32(0.50) * tiger_clean)
        * (np.float32(0.55) + np.float32(0.45) * blm_clean)
    ).astype(np.float32)
    del demag_unit, alter_unit, cond_unit, playa_veto, tiger_clean, blm_clean

    ch3 = spcp.robust_unit_f32(
        fbgr.sharpen_probability_crest(hydro_raw, foot, crest_boost=0.45),
        foot,
        pct=99.5,
    )
    del hydro_raw
    return ch3, {"contractor_blocks_normalized": len(unique_blocks)}


def _build_morris_and_horst_channels(
    ddir: Path,
    base_mm: np.ndarray,
    cshd_mm: np.ndarray,
    ch0_mag: np.ndarray,
    ch1_updip: np.ndarray,
    foot: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    """Build `wchd_ch4` (`wchd_morris_dilation_slip_tendency`) &
    `wchd_ch5` (`wchd_horst_cross_divide_tilt_footwall`)."""
    # Read 10 m seamless 3DEP derived bands & fluvial chi bands
    with rasterio.open(ddir / "external" / "topo_10m_derived_100m_u8.tif") as ds_t10:
        q_slp90 = ds_t10.read(1)
        q_curv = ds_t10.read(6)
        q_coh = ds_t10.read(7)
        q_dem10 = ds_t10.read(9)
        hi_slp = float(ds_t10.tags(1).get("q_hi", "41.8245"))
        hi_curv = float(ds_t10.tags(6).get("q_hi", "40.5010"))
        lo_coh = float(ds_t10.tags(7).get("q_lo", "0.0952"))
        hi_coh = float(ds_t10.tags(7).get("q_hi", "0.9984"))
        lo_dem = float(ds_t10.tags(9).get("q_lo", "1099.708"))
        hi_dem = float(ds_t10.tags(9).get("q_hi", "2481.501"))

    slp10 = np.where(q_slp90 > 0, (q_slp90.astype(np.float32) - 1.0) / 254.0 * hi_slp, 0.0).astype(np.float32)
    curv10 = np.where(q_curv > 0, (q_curv.astype(np.float32) - 1.0) / 254.0 * hi_curv, 0.0).astype(np.float32)
    coh10 = np.where(q_coh > 0, lo_coh + (q_coh.astype(np.float32) - 1.0) / 254.0 * (hi_coh - lo_coh), 0.0).astype(np.float32)
    dem10 = np.where(q_dem10 > 0, lo_dem + (q_dem10.astype(np.float32) - 1.0) / 254.0 * (hi_dem - lo_dem), 1400.0).astype(np.float32)
    del q_slp90, q_curv, q_coh, q_dem10

    # Multi-physics structural field to extract local strike tangent via smoothed structure tensor
    scarp10 = np.asarray(cshd_mm[:, :, 4], dtype=np.float32)
    struct_field = (np.float32(0.40) * scarp10 + np.float32(0.35) * ch1_updip + np.float32(0.25) * ch0_mag).astype(np.float32)
    sx = (sobel(struct_field, axis=1) / np.float32(8.0)).astype(np.float32)
    sy = (-sobel(struct_field, axis=0) / np.float32(8.0)).astype(np.float32)  # +y = North!

    j_xx = gaussian_filter(sx * sx, sigma=2.2).astype(np.float32)
    j_yy = gaussian_filter(sy * sy, sigma=2.2).astype(np.float32)
    j_xy = gaussian_filter(sx * sy, sigma=2.2).astype(np.float32)
    del sx, sy

    # Principal gradient normal angle `phi_n` (counter-clockwise from East, +y=North)
    phi_n = np.float32(0.5) * np.arctan2(np.float32(2.0) * j_xy, j_xx - j_yy + np.float32(1e-12))
    coherence = np.sqrt((j_xx - j_yy) ** 2 + np.float32(4.0) * j_xy * j_xy) / (j_xx + j_yy + np.float32(1e-6))
    del j_xx, j_yy, j_xy

    # Great Basin WNW-ESE minimum horizontal stress S_hmin = N114E -> math angle from East (+x=E, +y=N) is 90 - 114 = -24 deg!
    inv2 = np.maximum(np.asarray(base_mm[:, :, 3], dtype=np.float32), np.float32(0.0))
    shear = np.maximum(np.asarray(base_mm[:, :, 6], dtype=np.float32), np.float32(0.0))
    dilat = np.asarray(base_mm[:, :, 7], dtype=np.float32)
    # Local Walker Lane transtensional rotation modulation (+- 12 deg where shear >> dilatation)
    wl_ratio = np.clip((shear - np.maximum(dilat, 0.0)) / (shear + np.abs(dilat) + np.float32(1.0)), -1.0, 1.0)
    shmin_rad = np.deg2rad(np.float32(-24.0) + np.float32(12.0) * wl_ratio).astype(np.float32)
    del wl_ratio

    alpha_n = phi_n - shmin_rad
    del phi_n, shmin_rad
    t_dilat = (np.cos(alpha_n) ** 2).astype(np.float32)           # Peaks on N24E normal faults (normal || S_hmin)
    t_slip = (np.sin(np.float32(2.0) * alpha_n) ** 2).astype(np.float32)  # Peaks on ENE step-overs & NNW Walker Lane faults

    strain_act = spcp.robust_unit_f32(np.sqrt(shear * shear + np.maximum(dilat, 0.0) ** 2 + np.float32(0.3) * inv2), foot, pct=99.2)
    del inv2, shear, dilat, alpha_n

    morris_raw = (
        (np.float32(0.62) * t_dilat + np.float32(0.38) * t_slip)
        * (np.float32(0.35) + np.float32(0.65) * coherence)
        * struct_field
        * (np.float32(0.45) + np.float32(0.55) * strain_act)
    ).astype(np.float32)
    del t_dilat, t_slip, coherence, struct_field, strain_act
    ch4 = spcp.robust_unit_f32(morris_raw, foot, pct=99.5)
    del morris_raw

    # `wchd_ch5`: Cross-Divide Horst Tilt & Piedmont Footwall Localization
    with rasterio.open(ddir / "external" / "dem10_chi_100m_i16.tif") as ds_chi:
        chi_step = np.maximum(ds_chi.read(1).astype(np.float32), 0.0) / np.float32(1000.0)
        ksn = np.maximum(ds_chi.read(3).astype(np.float32), 0.0)

    # Regional horst-block tilt (`sigma=34 px` minus `sigma=5 px` on seamless 10 m DEM)
    dem_fill = _fill_outside_median(dem10, foot)
    dem_long = gaussian_filter(dem_fill, sigma=34.0).astype(np.float32)
    dem_short = gaussian_filter(dem_fill, sigma=5.0).astype(np.float32)
    # Local piedmont break-in-slope concavity + asymmetric range-front relief
    pied_concav = np.maximum(dem_long - dem_short, np.float32(0.0))
    _, _, tilt_long = _central_grad_f32(dem_long, sigma_px=1.0)
    del dem_long, dem_short

    # Piedmont range-front slope window (`1.65 deg <= slp10 <= 13.6 deg`) suppresses >14 deg mountain divides & <1.5 deg playas
    pied_slp_win = (
        (np.float32(1.0) / (np.float32(1.0) + np.exp(np.clip(-(slp10 - np.float32(1.65)) / np.float32(0.45), -30.0, 30.0))))
        * (np.float32(1.0) / (np.float32(1.0) + np.exp(np.clip((slp10 - np.float32(13.6)) / np.float32(2.0), -30.0, 30.0))))
    ).astype(np.float32)

    # Suppress Lake Lahontan wave-cut shorelines (`1325-1342 m` Sehoo highstand & `1268-1284 m` Eetza terrace) on gentle slopes
    lahontan_band = (
        np.exp(-((dem_fill - np.float32(1333.5)) / np.float32(8.5)) ** 2)
        + np.float32(0.75) * np.exp(-((dem_fill - np.float32(1276.0)) / np.float32(8.0)) ** 2)
    ) * (slp10 < np.float32(6.5))
    lahontan_veto = np.clip(np.float32(1.0) - np.float32(0.70) * lahontan_band, 0.25, 1.0).astype(np.float32)
    del dem_fill, dem10, slp10, lahontan_band

    chi_footwall = spcp.robust_unit_f32(
        gaussian_filter(np.float32(0.55) * spcp.robust_unit_f32(chi_step, foot, pct=99.0) + np.float32(0.45) * spcp.robust_unit_f32(ksn, foot, pct=99.0), sigma=2.2),
        foot,
        pct=99.3,
    )
    del chi_step, ksn

    curv_coh = spcp.robust_unit_f32(curv10 * coh10, foot, pct=99.3)
    tilt_unit = spcp.robust_unit_f32(pied_concav * tilt_long, foot, pct=99.3)
    del curv10, coh10, pied_concav, tilt_long

    horst_raw = (
        pied_slp_win
        * lahontan_veto
        * (np.float32(0.42) * curv_coh + np.float32(0.32) * tilt_unit + np.float32(0.26) * chi_footwall)
        * (np.float32(0.38) + np.float32(0.62) * ch1_updip)
    ).astype(np.float32)
    del pied_slp_win, lahontan_veto, curv_coh, tilt_unit, chi_footwall

    ch5 = spcp.robust_unit_f32(
        fbgr.sharpen_probability_crest(horst_raw, foot, crest_boost=0.48),
        foot,
        pct=99.5,
    )
    del horst_raw
    return ch4, ch5, {"shmin_regional_deg_cw_north": 114.0}


def _build_updip_bridge_and_unified_crest(
    base_mm: np.ndarray,
    trhv_mm: np.ndarray,
    fbgr_mm: np.ndarray,
    cshd_mm: np.ndarray,
    ch0: np.ndarray,
    ch1: np.ndarray,
    ch2: np.ndarray,
    ch3: np.ndarray,
    ch4: np.ndarray,
    ch5: np.ndarray,
    foot: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Build `wchd_ch6` (`wchd_updip_blind_geotherm_seismic_bridge`) &
    `wchd_ch7` (`wchd_unified_updip_conduit_crest`)."""
    diseq = np.asarray(cshd_mm[:, :, 2], dtype=np.float32)
    post21 = np.asarray(cshd_mm[:, :, 1], dtype=np.float32)
    radon = np.asarray(fbgr_mm[:, :, 3], dtype=np.float32)
    tprobe = np.asarray(trhv_mm[:, :, 0], dtype=np.float32)
    sinter = np.asarray(trhv_mm[:, :, 2], dtype=np.float32)

    thermal_fluid = spcp.robust_unit_f32(
        np.float32(0.38) * diseq
        + np.float32(0.24) * post21
        + np.float32(0.16) * spcp.robust_unit_f32(np.maximum(radon, 0.0), foot, pct=99.0)
        + np.float32(0.12) * tprobe
        + np.float32(0.10) * sinter,
        foot,
        pct=99.5,
    )
    del diseq, post21, radon, tprobe, sinter

    # Focus diffuse spring/seismic halos strictly onto linear updip basement traces (`ch1`),
    # magnetite-destruction corridors (`ch3`), and gravity-RTP phase-congruent walls (`ch2`)
    linear_conduit = np.maximum(ch1, np.float32(0.85) * np.maximum(ch2, ch3))
    bridge_raw = (
        linear_conduit * (np.float32(0.28) + np.float32(0.72) * thermal_fluid)
        + np.float32(0.22) * thermal_fluid * ch4
    ).astype(np.float32)
    del linear_conduit, thermal_fluid

    ch6 = spcp.robust_unit_f32(
        fbgr.sharpen_probability_crest(bridge_raw, foot, crest_boost=0.50),
        foot,
        pct=99.5,
    )
    del bridge_raw

    # `wchd_ch7`: Unified 1-px Hessian crest-thinned WCHD Structural-Geothermal Conduit Spine
    depth = np.asarray(base_mm[:, :, 14], dtype=np.float32)
    slope = np.asarray(base_mm[:, :, 18], dtype=np.float32)
    playa_veto = np.float32(1.0) - np.float32(0.90) * (
        (np.float32(1.0) / (np.float32(1.0) + np.exp(np.clip(-(depth - np.float32(290.0)) / np.float32(55.0), -30.0, 30.0))))
        * (np.float32(1.0) / (np.float32(1.0) + np.exp(np.clip((slope - np.float32(2.0)) / np.float32(0.30), -30.0, 30.0))))
    )
    del depth, slope

    tiger_clean = np.asarray(trhv_mm[:, :, 4], dtype=np.float32)
    blm_clean = np.clip(np.asarray(fbgr_mm[:, :, 10], dtype=np.float32), 0.0, 1.0)

    spine_raw = (
        (
            np.float32(0.24) * ch1
            + np.float32(0.18) * ch5
            + np.float32(0.15) * ch2
            + np.float32(0.14) * ch3
            + np.float32(0.11) * ch0
            + np.float32(0.10) * ch6
            + np.float32(0.08) * ch4
        )
        * playa_veto
        * (np.float32(0.45) + np.float32(0.55) * tiger_clean)
        * (np.float32(0.62) + np.float32(0.38) * blm_clean)
    ).astype(np.float32)
    del playa_veto, tiger_clean, blm_clean

    ch7 = spcp.robust_unit_f32(
        fbgr.sharpen_probability_crest(spine_raw, foot, crest_boost=0.56),
        foot,
        pct=99.6,
    )
    del spine_raw
    return ch6, ch7


def build_wchd_extra_stack(
    ddir: Path | None = None,
    out_path: Path | None = None,
    force: bool = False,
    log=print,
) -> tuple[np.ndarray, dict[str, Any]]:
    """Build or open the 8-channel strictly label-free, 1 m LiDAR-free `WCHD` memmap stack."""
    ddir = ddir or paths.data_dir()
    wdir = paths.work_dir()
    wdir.mkdir(parents=True, exist_ok=True)

    base_stack_path = wdir / "feature_stack.npy"
    spcp_path = wdir / "spcp_extra_20ch.npy"
    trhv_path = wdir / "trhv_extra_8ch.npy"
    ldgi_path = wdir / "ldgi_extra_8ch.npy"
    fbgr_path = wdir / "fbgr_extra_12ch.npy"
    bhgc_path = wdir / "bhgc_extra_6ch.npy"
    cshd_path = wdir / "cshd_extra_8ch.npy"
    out_path = out_path or (wdir / "wchd_extra_8ch.npy")
    receipt_path = out_path.with_suffix(".json")

    if not cshd_path.exists():
        cshd.build_cshd_extra_stack(
            ddir=ddir,
            base_stack_path=base_stack_path,
            spcp_path=spcp_path,
            trhv_path=trhv_path,
            ldgi_path=ldgi_path,
            fbgr_path=fbgr_path,
            bhgc_path=bhgc_path,
            out_path=cshd_path,
            log=log,
        )
        gc.collect()

    if out_path.exists() and receipt_path.exists() and not force:
        mm = open_memmap(out_path, mode="r")
        if mm.shape[2] == len(WCHD_EXTRA_CHANNELS):
            return mm, json.loads(receipt_path.read_text())

    with rasterio.open(ddir / "sample_submission.tif") as src:
        sample = src.read(1)
        foot = np.isfinite(sample)
        h, w = sample.shape
    del sample

    base_mm = open_memmap(base_stack_path, mode="r")
    trhv_mm = open_memmap(trhv_path, mode="r")
    fbgr_mm = open_memmap(fbgr_path, mode="r")
    cshd_mm = open_memmap(cshd_path, mode="r")

    out_mm = open_memmap(out_path, mode="w+", dtype=np.float32, shape=(h, w, len(WCHD_EXTRA_CHANNELS)))

    ch0, ch1, ch2, pf_stats = _build_rtp_and_phase_channels(base_mm, foot)
    out_mm[:, :, 0] = ch0
    out_mm[:, :, 1] = ch1
    out_mm[:, :, 2] = ch2
    out_mm.flush()
    log("  [WCHD] ch 0..2 (True Fourier RTP/TMI tilt + 4-altitude listric updip projection + grav-RTP phase congruency) built")

    ch3, hydro_stats = _build_hydro_demag_kth_channel(ddir, base_mm, trhv_mm, fbgr_mm, foot)
    out_mm[:, :, 3] = ch3
    out_mm.flush()
    log("  [WCHD] ch 3 (Hydrothermal magnetite-destruction trough x 4-block K/eTh adularia metasomatism) built")

    ch4, ch5, stress_stats = _build_morris_and_horst_channels(ddir, base_mm, cshd_mm, ch0, ch1, foot)
    out_mm[:, :, 4] = ch4
    out_mm[:, :, 5] = ch5
    out_mm.flush()
    log("  [WCHD] ch 4..5 (Morris dilation/slip tendency + cross-divide horst tilt footwall) built")

    ch6, ch7 = _build_updip_bridge_and_unified_crest(base_mm, trhv_mm, fbgr_mm, cshd_mm, ch0, ch1, ch2, ch3, ch4, ch5, foot)
    out_mm[:, :, 6] = ch6
    out_mm[:, :, 7] = ch7
    out_mm.flush()
    del ch0, ch1, ch2, ch3, ch4, ch5, ch6, ch7
    gc.collect()
    log("  [WCHD] ch 6..7 (Updip blind-geotherm/seismic bridge + unified WCHD conduit crest) built")

    # Verify strict finite [0, 1] cleanliness on all 8 channels
    for j in range(len(WCHD_EXTRA_CHANNELS)):
        sub = np.asarray(out_mm[:, :, j], dtype=np.float32)
        if not np.all(np.isfinite(sub)):
            raise RuntimeError(f"Non-finite pixel detected in {WCHD_EXTRA_CHANNELS[j]}")
        if float(sub.min()) < 0.0 or float(sub.max()) > 1.0:
            raise RuntimeError(f"Out-of-range pixel detected in {WCHD_EXTRA_CHANNELS[j]}")
        del sub

    meta = {
        "schema_version": 1,
        "module": "gems32.wchd",
        "hypothesis": "H-APART3-3 (WCHD)",
        "channels": list(WCHD_EXTRA_CHANNELS),
        "n_channels": len(WCHD_EXTRA_CHANNELS),
        "clean_supervised_full_channels": len(CLEAN_104_RAW_COLS),
        "clean_supervised_gap_channels": len(MGAP_91_RAW_COLS),
        "clean_supervised_subspace_channels": len(MSUBSPACE_34_RAW_COLS),
        "excised_flawed_raw_col": EXCISED_RAW_COL_BHGC_CH1,
        "all_wchd_channels_lidar1m_free": True,
        "zero_catalogue_label_inputs": True,
        **pf_stats,
        **hydro_stats,
        **stress_stats,
    }
    receipt_path.write_text(json.dumps(meta, indent=2) + "\n")
    return open_memmap(out_path, mode="r"), meta


def open_all_wchd_stacks(ddir: Path | None = None) -> tuple[tuple[np.ndarray, ...], list[str]]:
    """Open all 8 read-only memmap stacks (`105` raw columns; raw col `84` excised during gather -> `104` clean)."""
    ddir = ddir or paths.data_dir()
    wdir = paths.work_dir()
    wchd_mm, _ = build_wchd_extra_stack(ddir=ddir)
    stacks = (
        open_memmap(wdir / "feature_stack.npy", mode="r"),
        open_memmap(wdir / "spcp_extra_20ch.npy", mode="r"),
        open_memmap(wdir / "trhv_extra_8ch.npy", mode="r"),
        open_memmap(wdir / "ldgi_extra_8ch.npy", mode="r"),
        open_memmap(wdir / "fbgr_extra_12ch.npy", mode="r"),
        open_memmap(wdir / "bhgc_extra_6ch.npy", mode="r"),
        open_memmap(wdir / "cshd_extra_8ch.npy", mode="r"),
        wchd_mm,
    )
    raw_names: list[str] = (
        list(features.CHANNELS)
        + list(spcp.SPCP_EXTRA_CHANNELS)
        + list(trhv.TRHV_EXTRA_CHANNELS)
        + list(ldgi.LDGI_EXTRA_CHANNELS)
        + list(fbgr.FBGR_EXTRA_CHANNELS)
        + list(bhgc.BHGC_EXTRA_CHANNELS)
        + list(cshd.CSHD_EXTRA_CHANNELS)
        + list(WCHD_EXTRA_CHANNELS)
    )
    assert len(raw_names) == RAW_TOTAL_COLS
    return stacks, raw_names


def gather_clean_cols(
    stacks: tuple[np.ndarray, ...],
    ys: np.ndarray,
    xs: np.ndarray,
    raw_col_indices: tuple[int, ...] = CLEAN_104_RAW_COLS,
) -> np.ndarray:
    """Gather strictly clean `float32` columns (never reading raw col 84 `bhgc` ch 1)."""
    assert EXCISED_RAW_COL_BHGC_CH1 not in raw_col_indices, "Raw col 84 (Band-6 pseudo-tilt) is strictly forbidden!"
    return cshd.gather_97ch(stacks, ys, xs, col_indices=raw_col_indices)


def run_leakage_canary_104ch(
    stacks: tuple[np.ndarray, ...],
    raw_names: list[str],
    ctx,
    max_auc: float = 0.90,
    stride: int = 4,
) -> dict[str, Any]:
    """Protocol Rule 4 single-feature two-polarity leakage canary across all 104 clean channels."""
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
    rows: list[dict[str, Any]] = []
    for clean_idx, raw_col in enumerate(CLEAN_104_RAW_COLS):
        s_idx = int(np.searchsorted(offsets[1:], raw_col, side="right"))
        local_j = int(raw_col - offsets[s_idx])
        s = stacks[s_idx]
        vals = np.concatenate([
            np.asarray(s[py, px, local_j], dtype=np.float32),
            np.asarray(s[ny, nx, local_j], dtype=np.float32),
        ])
        vals = np.nan_to_num(vals, nan=0.0, posinf=0.0, neginf=0.0)
        raw_auc = float(roc_auc_score(y_true, vals))
        auc_dir = max(raw_auc, 1.0 - raw_auc)
        rows.append(
            {
                "clean_index": clean_idx,
                "raw_index": raw_col,
                "channel": raw_names[raw_col],
                "in_mgap_91": raw_col in MGAP_91_RAW_COLS,
                "in_msubspace_34": raw_col in MSUBSPACE_34_RAW_COLS,
                "raw_auc": round(raw_auc, 6),
                "oriented_auc": round(auc_dir, 6),
                "passed": bool(auc_dir <= max_auc),
            }
        )
        del vals

    worst = max(rows, key=lambda r: r["oriented_auc"])
    wchd_rows = [r for r in rows if r["raw_index"] >= 97]
    return {
        "passed": all(r["passed"] for r in rows),
        "threshold_auc": max_auc,
        "n_features_tested": len(rows),
        "excised_raw_col_84_verified": all(r["raw_index"] != EXCISED_RAW_COL_BHGC_CH1 for r in rows),
        "max_oriented_auc": worst["oriented_auc"],
        "worst_channel": worst["channel"],
        "wchd_8ch_max_oriented_auc": max(r["oriented_auc"] for r in wchd_rows),
        "wchd_8ch_aucs": {r["channel"]: r["oriented_auc"] for r in wchd_rows},
        "n_withheld_pos_tested": int(py.size),
        "n_active_neg_sampled": int(ny.size),
        "per_channel": rows,
    }


def train_wchd_oof_and_full(
    stacks: tuple[np.ndarray, ...],
    ctx,
    lidar_valid: np.ndarray,
    seed: int = 74,
    log=print,
) -> dict[str, Any]:
    """Train 4-quadrant 1.5 km-collared OOF + Full-Map models for:
      - `p_single`: Clean 104-channel Single-Cover HGB ensemble (`EXP-2` ablation),
      - `p_dual`: Clean 104-ch `M_Full` / 91-ch `M_Gap` Quantile-Aligned Stationary Dual-Cover,
      - `p_subspace`: Clean 34-ch Potential-Field + Updip-Projection + Alteration + 3DEP/Stress
        Subspace HGB ensemble (quantile-aligned to `p_dual` so buried sub-alluvial faults and
        hydrothermal alteration corridors receive calibrated structural probability).
    """
    foot = ctx.foot
    labels = ctx.labels
    q_masks = fbgr.build_quadrant_masks(foot)

    p_single_oof = np.zeros(foot.shape, dtype=np.float32)
    p_dual_oof = np.zeros(foot.shape, dtype=np.float32)
    p_subspace_oof = np.zeros(foot.shape, dtype=np.float32)
    fold_stats: dict[str, Any] = {}

    for qi, qname in enumerate(("NW", "NE", "SW", "SE")):
        q_val = q_masks[qname]
        train_region = fbgr.collared_train_region(q_val, foot, collar_px=15)
        vis_train = labels & train_region

        # 1. Clean 104-ch Single-Cover (for EXP-2)
        ens_single = cshd.fit_cshd_ensemble(
            stacks=stacks,
            train_region=train_region,
            visible_train=vis_train,
            foot=foot,
            col_indices=CLEAN_104_RAW_COLS,
            seed=seed + 20 * qi + 1,
        )
        p_single_oof[q_val] = cshd.predict_chunked_cshd(ens_single, stacks, q_val, col_indices=CLEAN_104_RAW_COLS)[q_val]
        del ens_single
        gc.collect()

        # 2. Clean 104-ch M_Full (on LiDAR-valid) + 91-ch M_Gap (100% 1 m LiDAR-free)
        ens_full = cshd.fit_cshd_ensemble(
            stacks=stacks,
            train_region=train_region & lidar_valid,
            visible_train=vis_train,
            foot=foot,
            col_indices=CLEAN_104_RAW_COLS,
            seed=seed + 20 * qi + 5,
        )
        ens_gap = cshd.fit_cshd_ensemble(
            stacks=stacks,
            train_region=train_region,
            visible_train=vis_train,
            foot=foot,
            col_indices=MGAP_91_RAW_COLS,
            seed=seed + 20 * qi + 9,
        )

        val_li = q_val & lidar_valid
        val_gap = q_val & (~lidar_valid)
        p_li = cshd.predict_chunked_cshd(ens_full, stacks, val_li, col_indices=CLEAN_104_RAW_COLS)
        p_dual_oof[val_li] = p_li[val_li]

        cal_mask = train_region & lidar_valid
        ref_full = cshd.predict_chunked_cshd(ens_full, stacks, cal_mask, col_indices=CLEAN_104_RAW_COLS)
        ref_gap = cshd.predict_chunked_cshd(ens_gap, stacks, cal_mask, col_indices=MGAP_91_RAW_COLS)
        raw_gap_val = cshd.predict_chunked_cshd(ens_gap, stacks, val_gap, col_indices=MGAP_91_RAW_COLS)
        p_dual_oof[val_gap] = cshd._quantile_match_gap_to_lidar(
            raw_gap_val[val_gap], ref_gap[cal_mask], ref_full[cal_mask]
        )
        del ens_full, ens_gap, p_li, ref_gap, raw_gap_val
        gc.collect()

        # 3. Clean 34-ch WCHD Potential-Field / Updip / Alteration Subspace Learner
        ens_sub = cshd.fit_cshd_ensemble(
            stacks=stacks,
            train_region=train_region,
            visible_train=vis_train,
            foot=foot,
            col_indices=MSUBSPACE_34_RAW_COLS,
            seed=seed + 20 * qi + 13,
        )
        ref_sub = cshd.predict_chunked_cshd(ens_sub, stacks, cal_mask, col_indices=MSUBSPACE_34_RAW_COLS)
        raw_sub_val = cshd.predict_chunked_cshd(ens_sub, stacks, q_val, col_indices=MSUBSPACE_34_RAW_COLS)
        p_subspace_oof[q_val] = cshd._quantile_match_gap_to_lidar(
            raw_sub_val[q_val], ref_sub[cal_mask], ref_full[cal_mask]
        )
        del ens_sub, ref_sub, raw_sub_val, ref_full
        gc.collect()

        fold_stats[qname] = {
            "val_px": int(q_val.sum()),
            "mean_p_dual_lidar": round(float(p_dual_oof[val_li].mean()), 5),
            "mean_p_dual_gap": round(float(p_dual_oof[val_gap].mean()), 5),
            "mean_p_subspace": round(float(p_subspace_oof[q_val].mean()), 5),
        }
        log(
            f"  [WCHD OOF] {qname}: dual_li={fold_stats[qname]['mean_p_dual_lidar']:.4f}, "
            f"dual_gap={fold_stats[qname]['mean_p_dual_gap']:.4f}, subspace={fold_stats[qname]['mean_p_subspace']:.4f}"
        )

    # Full-footprint production models for EXP-2 and EXP-3
    log("  [WCHD Full] Fitting full-map 104ch SingleCover, 104ch/91ch DualCover, and 34ch Subspace ensembles...")
    ens_single_all = cshd.fit_cshd_ensemble(stacks, foot, labels, foot, col_indices=CLEAN_104_RAW_COLS, seed=seed + 200)
    p_single_full = cshd.predict_chunked_cshd(ens_single_all, stacks, foot, col_indices=CLEAN_104_RAW_COLS)
    del ens_single_all
    gc.collect()

    foot_li = foot & lidar_valid
    foot_gap = foot & (~lidar_valid)
    ens_full_all = cshd.fit_cshd_ensemble(stacks, foot_li, labels, foot, col_indices=CLEAN_104_RAW_COLS, seed=seed + 300)
    ens_gap_all = cshd.fit_cshd_ensemble(stacks, foot, labels, foot, col_indices=MGAP_91_RAW_COLS, seed=seed + 400)

    p_dual_full = np.zeros(foot.shape, dtype=np.float32)
    p_full_li = cshd.predict_chunked_cshd(ens_full_all, stacks, foot_li, col_indices=CLEAN_104_RAW_COLS)
    p_dual_full[foot_li] = p_full_li[foot_li]

    ref_gap_all = cshd.predict_chunked_cshd(ens_gap_all, stacks, foot_li, col_indices=MGAP_91_RAW_COLS)
    raw_gap_all = cshd.predict_chunked_cshd(ens_gap_all, stacks, foot_gap, col_indices=MGAP_91_RAW_COLS)
    p_dual_full[foot_gap] = cshd._quantile_match_gap_to_lidar(
        raw_gap_all[foot_gap], ref_gap_all[foot_li], p_full_li[foot_li]
    )
    del ens_full_all, ens_gap_all, ref_gap_all, raw_gap_all
    gc.collect()

    ens_sub_all = cshd.fit_cshd_ensemble(stacks, foot, labels, foot, col_indices=MSUBSPACE_34_RAW_COLS, seed=seed + 500)
    raw_sub_all = cshd.predict_chunked_cshd(ens_sub_all, stacks, foot, col_indices=MSUBSPACE_34_RAW_COLS)
    p_subspace_full = np.zeros(foot.shape, dtype=np.float32)
    p_subspace_full[foot] = cshd._quantile_match_gap_to_lidar(
        raw_sub_all[foot], raw_sub_all[foot_li], p_full_li[foot_li]
    )
    del ens_sub_all, raw_sub_all, p_full_li
    gc.collect()

    return {
        "p_single_oof": p_single_oof,
        "p_single_full": p_single_full,
        "p_dual_oof": p_dual_oof,
        "p_dual_full": p_dual_full,
        "p_subspace_oof": p_subspace_oof,
        "p_subspace_full": p_subspace_full,
        "fold_stats": fold_stats,
    }


def build_stationary_wchd_carrier(
    base_stack: np.ndarray,
    trhv_stack: np.ndarray,
    wchd_stack: np.ndarray,
    foot: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Compute `(wchd_carrier, playa_gate, tiger_clean)` using exclusively clean WCHD channels."""
    w_mag = np.asarray(wchd_stack[:, :, 0], dtype=np.float32)
    w_updip = np.asarray(wchd_stack[:, :, 1], dtype=np.float32)
    w_phase = np.asarray(wchd_stack[:, :, 2], dtype=np.float32)
    w_hydro = np.asarray(wchd_stack[:, :, 3], dtype=np.float32)
    w_morris = np.asarray(wchd_stack[:, :, 4], dtype=np.float32)
    w_horst = np.asarray(wchd_stack[:, :, 5], dtype=np.float32)
    w_bridge = np.asarray(wchd_stack[:, :, 6], dtype=np.float32)
    w_crest = np.asarray(wchd_stack[:, :, 7], dtype=np.float32)

    depth = np.asarray(base_stack[:, :, 14], dtype=np.float32)
    slope = np.asarray(base_stack[:, :, 18], dtype=np.float32)
    playa_gate = np.float32(1.0) - np.float32(0.92) * (
        (np.float32(1.0) / (np.float32(1.0) + np.exp(np.clip(-(depth - np.float32(290.0)) / np.float32(55.0), -30.0, 30.0))))
        * (np.float32(1.0) / (np.float32(1.0) + np.exp(np.clip((slope - np.float32(2.0)) / np.float32(0.30), -30.0, 30.0))))
    )
    del depth, slope

    tg = np.asarray(trhv_stack[:, :, 4], dtype=np.float32)
    carrier_raw = (
        np.float32(0.24) * w_morris
        + np.float32(0.18) * w_mag
        + np.float32(0.16) * w_phase
        + np.float32(0.15) * w_hydro
        + np.float32(0.14) * w_updip
        + np.float32(0.13) * w_horst
    ).astype(np.float32)
    del w_mag, w_updip, w_phase, w_hydro, w_morris, w_horst, w_bridge, w_crest

    carrier = spcp.robust_unit_f32(
        fbgr.sharpen_probability_crest(
            carrier_raw * playa_gate * (np.float32(0.42) + np.float32(0.58) * tg),
            foot,
            crest_boost=0.54,
        ),
        foot,
        pct=99.6,
    )
    del carrier_raw
    return carrier, playa_gate.astype(np.float32), tg


def build_stationary_wchd_single_surface(
    p_base: np.ndarray,
    base_stack: np.ndarray,
    trhv_stack: np.ndarray,
    wchd_stack: np.ndarray,
    visible_mask: np.ndarray,
    foot: np.ndarray,
    region_mask: np.ndarray | None = None,
    w_carrier_blend: float = 0.28,
    w_tip_relay: float = 0.36,
    w_mid_conduit: float = 0.26,
    w_far_conduit: float = 0.42,
    d0_far_px: float = 15.0,
    collar_depletion_strength: float = 0.28,
    sharpen_crest: bool = True,
) -> np.ndarray:
    """Stationary single-branch surface used for `EXP-1` (unsupervised) and `EXP-2` (SingleCover)."""
    mask = foot if region_mask is None else (foot & region_mask)
    vis = np.asarray(visible_mask, dtype=bool) & foot
    d_vis = distance_transform_edt(~vis).astype(np.float32)
    relay = ldgi.anisotropic_tip_relay_cone(vis, foot)
    carrier, playa_gate, tg = build_stationary_wchd_carrier(base_stack, trhv_stack, wchd_stack, foot)

    surf = np.zeros(foot.shape, dtype=np.float32)
    pb_m = np.clip(p_base[mask], np.float32(0.0), np.float32(1.0))
    cc_m = carrier[mask]
    rl_m = np.clip(relay[mask], np.float32(0.0), np.float32(1.0))
    dv_m = d_vis[mask]
    fp_m = playa_gate[mask]
    tg_m = tg[mask]
    del carrier, relay, d_vis, playa_gate, tg

    collar_mod = np.float32(1.0) - np.float32(collar_depletion_strength) * np.exp(
        -np.maximum(dv_m - np.float32(2.0), np.float32(0.0)) / np.float32(1.3)
    ) * (np.float32(1.0) - np.float32(0.92) * rl_m)

    mid_win = np.exp(-((dv_m - np.float32(11.5)) / np.float32(7.5)) ** 2) * (dv_m > np.float32(4.5))
    gamma_far = np.float32(1.0) - np.exp(
        -((np.maximum(dv_m - np.float32(d0_far_px), np.float32(0.0))) / np.float32(5.8)) ** 2
    )

    w_cb = np.float32(w_carrier_blend)
    near_mid = (
        ((np.float32(1.0) - w_cb) * pb_m + w_cb * (pb_m ** np.float32(0.62)) * (np.float32(0.25) + np.float32(0.75) * cc_m))
        * (np.float32(1.0) + np.float32(w_tip_relay) * rl_m)
        * collar_mod
        * (np.float32(1.0) + np.float32(w_mid_conduit) * mid_win * cc_m)
        * (np.float32(1.0) - np.float32(0.38) * gamma_far * (np.float32(1.0) - cc_m))
    )
    mm_gate = pb_m / (pb_m + np.float32(0.020))
    far_term = np.float32(w_far_conduit) * gamma_far * mm_gate * (cc_m ** np.float32(1.15))

    surf[mask] = (np.float32(0.76) * near_mid + far_term) * fp_m * (np.float32(0.40) + np.float32(0.60) * tg_m)
    del pb_m, cc_m, rl_m, dv_m, fp_m, tg_m, collar_mod, mid_win, gamma_far, near_mid, mm_gate, far_term

    if sharpen_crest:
        surf = fbgr.sharpen_probability_crest(surf, mask, crest_boost=0.52)
    surf[vis] = np.float32(0.0)
    return np.clip(surf, 0.0, 1.0).astype(np.float32)


def build_bipopulation_wchd_surface(
    p_single: np.ndarray,
    p_dual: np.ndarray,
    p_subspace: np.ndarray,
    base_stack: np.ndarray,
    trhv_stack: np.ndarray,
    wchd_stack: np.ndarray,
    visible_mask: np.ndarray,
    foot: np.ndarray,
    region_mask: np.ndarray | None = None,
    w_dual_cont: float = 0.10,
    w_subspace_blind: float = 0.14,
    w_carrier_blind: float = 0.52,
    w_carrier_cont: float = 0.18,
    beta_blind: float = 0.828,
    collar_depletion_strength: float = 0.28,
    rank_gamma: float = 6.0,
) -> np.ndarray:
    """Stationary Two-Population Updip-Conduit Bayesian Envelope Surface (`EXP-3`):

    Identical stationary formula across all 8 collared OOF holdout folds (`visible_mask =
    cell.visible_full`) and full-footprint emission (`visible_mask = labels`):
      1. `P_cont`: Preserves sharp 100 m scarp continuation localization via `0.86 * p_single +
         0.14 * p_dual` (both trained on the clean 104-channel stack including `wchd_ch0..7` and
         repaired `BHGC v2`) with anisotropic tip-relay cones and mild `WCHD` updip/alteration
         crest coupling (`0.78 + 0.22 * carrier`).
      2. `P_blind`: Combines Dual-Cover (`104ch M_Full / 91ch M_Gap`) with the 34-ch WCHD
         Potential-Field/Updip/Alteration Subspace learner (`0.70 * p_dual + 0.30 * p_subspace`)
         inside a Michaelis-Menten posterior gate coupled with the linear `WCHD` updip contact-dip,
         magnetite-destruction/K-eTh metasomatism, horst-chi, and true-RTP phase-congruency spine.
      3. Two-population rank envelope `max(R(P_cont)^gamma, beta_blind * R(P_blind)^gamma)`.
    """
    m = foot if region_mask is None else (foot & region_mask)
    carrier, _, _ = build_stationary_wchd_carrier(base_stack, trhv_stack, wchd_stack, foot)

    p_cont_blend = (
        np.float32(1.0 - w_dual_cont) * p_single
        + np.float32(w_dual_cont) * p_dual
    ).astype(np.float32)

    s_cont = build_stationary_wchd_single_surface(
        p_cont_blend,
        base_stack,
        trhv_stack,
        wchd_stack,
        visible_mask,
        foot,
        region_mask=region_mask,
        w_carrier_blend=0.10,
        w_tip_relay=0.38,
        w_mid_conduit=0.16,
        w_far_conduit=0.0,
        d0_far_px=16.5,
        collar_depletion_strength=collar_depletion_strength,
        sharpen_crest=True,
    )
    del p_cont_blend
    pc_vals = s_cont[m] * (np.float32(1.0 - w_carrier_cont) + np.float32(w_carrier_cont) * carrier[m])
    del s_cont

    w_unsup = np.asarray(wchd_stack[:, :, 7], dtype=np.float32)
    s_unsup = build_stationary_wchd_single_surface(
        w_unsup,
        base_stack,
        trhv_stack,
        wchd_stack,
        visible_mask,
        foot,
        region_mask=region_mask,
        w_carrier_blend=0.60,
        w_tip_relay=0.0,
        w_mid_conduit=0.26,
        w_far_conduit=0.66,
        d0_far_px=13.5,
        collar_depletion_strength=0.32,
        sharpen_crest=True,
    )
    del w_unsup

    p_blind_post = (
        np.float32(1.0 - w_subspace_blind) * np.clip(p_dual[m], np.float32(0.0), np.float32(1.0))
        + np.float32(w_subspace_blind) * np.clip(p_subspace[m], np.float32(0.0), np.float32(1.0))
    )
    mm_gate = p_blind_post / (p_blind_post + np.float32(0.015))
    blind_struct = (
        np.float32(1.0 - w_carrier_blind) * np.clip(s_unsup[m], np.float32(0.0), np.float32(1.0))
        + np.float32(w_carrier_blind) * carrier[m]
    )
    prod = (mm_gate ** np.float32(0.33)) * (blind_struct ** np.float32(0.87))
    del p_blind_post, mm_gate, s_unsup, carrier, blind_struct

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


def emit_wchd_dots(
    surface: np.ndarray,
    visible_mask: np.ndarray,
    foot: np.ndarray,
    region_mask: np.ndarray | None = None,
    budget: int = TARGET_BUDGET,
    b_collar_px: float = B_COLLAR_PX,
    min_sep_px: float = DEFAULT_AXIAL_SEP_PX,
) -> tuple[np.ndarray, dict[str, Any]]:
    """Emit discrete `{0, 1}` dots strictly outside `d_vis <= b_collar_px` via `gems32.emitter.emit`."""
    return cshd.emit_cshd_dots(
        surface=surface,
        visible_mask=visible_mask,
        foot=foot,
        region_mask=region_mask,
        budget=budget,
        b_collar_px=b_collar_px,
        min_sep_px=min_sep_px,
        top_support_mult=5.0,
    )
