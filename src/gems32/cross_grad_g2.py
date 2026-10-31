"""G2 · Gravity-magnetic gradient coupling (pre-registered in knowledge/10 §5, row G2).

Layers: band 13 ``iso_grav_anom`` (isostatic gravity anomaly) and band 14 ``tmi`` (total magnetic
intensity). Both gradient fields are computed by FFT (gems32.euler_n1.derivatives), normalised by
their own footprint 95th percentile so that neither field dominates.

Joint structure measure (Gallardo & Meju 2003 cross-gradient idea, used as a coupling score):
    sin_theta = |g x m| / (|g| |m|)          (0 = gradients parallel/antiparallel, 1 = orthogonal)
    co        = min(|g|_norm, |m|_norm)      (both fields must have a gradient at the same place)
    S         = co * (1 - sin_theta)         (high where both gradients are strong AND aligned)

NOTE (flagged for review): the pre-registration table describes the signal as "high gradient magnitude
where the two fields' gradients are collinear". That matches S above; the cross-product magnitude
|g x m| itself is zero for collinear gradients and is therefore not used as the score.
"""
from __future__ import annotations

import numpy as np
from scipy.ndimage import gaussian_filter

from gems32.euler_n1 import derivatives

EPS = 1e-12


def _grad(field: np.ndarray, foot: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    gx, gy, _ = derivatives(field)
    return gx, gy


def coupling_surface(grav: np.ndarray, mag: np.ndarray, foot: np.ndarray, sigma_px: float = 2.0) -> np.ndarray:
    """Return float64 coupling density, 0 outside footprint. ``grav``/``mag`` are nodata-free."""
    gx, gy = _grad(grav, foot)
    mx, my = _grad(mag, foot)
    gn = np.hypot(gx, gy)
    mn = np.hypot(mx, my)
    gn = gn / max(np.percentile(gn[foot], 95), EPS)
    mn = mn / max(np.percentile(mn[foot], 95), EPS)
    cross = np.abs(gx * my - gy * mx)
    denom = np.hypot(gx, gy) * np.hypot(mx, my) + EPS
    sin_t = np.clip(cross / denom, 0.0, 1.0)
    co = np.minimum(gn, mn)
    s = co * (1.0 - sin_t)
    s = np.where(foot, s, 0.0)
    s = gaussian_filter(s, sigma=sigma_px, mode="constant")
    s[~foot] = 0.0
    return s
