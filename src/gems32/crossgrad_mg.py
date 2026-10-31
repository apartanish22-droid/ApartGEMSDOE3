"""H-M1 (2026-10-31): magnetic-gravity co-gradient alignment (rank 2 in docs/research/h-candidates-20261031.md).

Functional form identical to H35-C (``gems32.h35_new.build_h35c``: gradient-magnitude product times
the absolute cosine of gradient-direction alignment), applied to a NEW layer pair:
band 2 ``rtp`` (magnetic) and band 13 ``iso_grav_anom`` (gravity). Only the layer pair differs.
``robust_unit`` is imported from ``gems32.h35_new`` (pure helper, no side effects) to keep the scaling identical.
"""
from __future__ import annotations

import numpy as np
from scipy.ndimage import gaussian_filter

from gems32.h35_new import robust_unit
from gems32.spectral_rolloff import SENTINEL_MIN, detrended_residual

SIGMA_PX = 1.5  # 150 m, same smoothing as H35-C


def _fill_residual(raw: np.ndarray, foot: np.ndarray) -> np.ndarray:
    a = np.array(raw, dtype=np.float64)
    bad = ~np.isfinite(a) | (a <= SENTINEL_MIN)
    a[bad] = np.nan
    a[~foot] = np.nan
    resid, _valid = detrended_residual(a, foot)
    return resid


def build_hm1(rtp_raw: np.ndarray, grav_raw: np.ndarray, foot: np.ndarray) -> np.ndarray:
    """Return the H-M1 score in [0, 1] (footprint only; zero outside)."""
    rtp = _fill_residual(rtp_raw, foot)
    grav = _fill_residual(grav_raw, foot)
    gy_m, gx_m = np.gradient(gaussian_filter(rtp, SIGMA_PX, mode="nearest"))
    gy_g, gx_g = np.gradient(gaussian_filter(grav, SIGMA_PX, mode="nearest"))
    mag_m = np.hypot(gy_m, gx_m)
    mag_g = np.hypot(gy_g, gx_g)
    mag_prod = robust_unit(mag_m * mag_g, foot)
    cos = np.abs(gy_m * gy_g + gx_m * gx_g) / (mag_m * mag_g + 1e-9)
    align = np.clip((cos - 0.5) / 0.5, 0.0, 1.0)
    score = mag_prod * align
    score[~foot] = 0.0
    return robust_unit(score, foot).astype(np.float32)
