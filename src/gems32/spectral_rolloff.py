"""H-S1 (2026-10-31): oriented line-integral of local magnetic spectral roll-off.

Pre-registered in ``docs/research/h-candidates-20261031.md`` (rank 1). Layers: band 2 ``rtp`` only.
Band 13 ``iso_grav_anom`` is NOT used by this method.

Signal chain (every step is label-free: no catalogue or fault layer enters the surface):

1. Sentinel-aware read of ``rtp``; remove a 5 km regional trend by normalised convolution
   inside the footprint; fill the footprint residual with 0 for windowed FFTs.
2. For every 32x32-px (3.2 km) window on a 4-px grid, take the Hann-windowed 2-D power
   spectrum, average it over integer radial wavenumber bins, and fit a log-log slope beta over
   k in [2, 14] cycles/window (wavelengths about 230 m to 1.6 km). Windows with under 90 %
   footprint coverage are NaN. Flatter spectra (higher -beta) mean more high-wavenumber power.
3. Flatness A = -beta. Subtract a 4 km normalised-convolution regional mean of A and z-score
   the local residual inside the footprint.
4. Oriented line integral: for 8 orientations over [0, 180) deg, average the z-field along a
   21-px (2.1 km) line; S = max over orientations. The max keeps only linear responses.
5. Dots: ``emission.dot_thin_matched`` at a fixed target count, footprint-only.

The writer (``scripts/submission_writer.py``) and the shared evaluator are used unchanged.
"""
from __future__ import annotations

import numpy as np
from scipy import ndimage

SENTINEL_MIN = -3.0e38  # float32 nodata used by training_features.tif (see data/prepared_manifest.json)
WIN = 32
STRIDE = 4
K_LO, K_HI = 2, 14
LINE_LEN = 21
N_ORIENT = 8
TREND_SIGMA_PX = 50        # 5 km regional detrend
FLAT_TREND_SIGMA_PX = 40   # 4 km regional mean of the flatness field


def _norm_conv(values: np.ndarray, weight: np.ndarray, sigma: float) -> np.ndarray:
    """Gaussian normalised convolution: sum(w*v)/sum(w) with w = footprint."""
    num = ndimage.gaussian_filter(np.where(weight, values, 0.0), sigma, mode="nearest")
    den = ndimage.gaussian_filter(weight.astype(np.float64), sigma, mode="nearest")
    out = np.zeros_like(num)
    ok = den > 1e-6
    out[ok] = num[ok] / den[ok]
    return out


def read_rtp(features_tif, foot: np.ndarray) -> np.ndarray:
    """Read band 2 (``rtp``), replace sentinels with NaN, and return float64 with NaN outside foot."""
    import rasterio

    with rasterio.open(features_tif) as ds:
        if ds.count < 2:
            raise ValueError("training_features.tif has fewer than 2 bands")
        rtp = ds.read(2).astype(np.float64)
    bad = ~np.isfinite(rtp) | (rtp <= SENTINEL_MIN)
    rtp[bad] = np.nan
    rtp[~foot] = np.nan
    return rtp


def detrended_residual(rtp: np.ndarray, foot: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Remove a 5 km regional trend inside the footprint. Returns (residual, valid_mask)."""
    valid = foot & np.isfinite(rtp)
    base = np.where(valid, rtp, 0.0)
    trend = _norm_conv(base, valid, TREND_SIGMA_PX)
    resid = np.where(valid, rtp - trend, 0.0)
    return resid, valid


def _radial_bins(win: int) -> tuple[np.ndarray, int]:
    fy = np.fft.fftfreq(win) * win
    fx = np.fft.fftfreq(win) * win
    kk = np.sqrt(fy[:, None] ** 2 + fx[None, :] ** 2)
    idx = np.rint(kk).astype(int)
    nb = int(idx.max()) + 1
    return idx, nb


def window_beta(resid: np.ndarray, valid: np.ndarray, win: int = WIN, stride: int = STRIDE,
                k_lo: int = K_LO, k_hi: int = K_HI) -> tuple[np.ndarray, np.ndarray]:
    """Log-log spectral slope beta per window, sampled on a stride grid.

    Returns (beta_grid, centres): beta_grid[i, j] is the slope of the window whose top-left
    corner is (ys[i], xs[j]); centres[i, j] is that window's centre (row, col). NaN where the
    window has under 90 % footprint coverage.
    """
    h, w = resid.shape
    ys = np.arange(0, h - win + 1, stride)
    xs = np.arange(0, w - win + 1, stride)
    hann = np.outer(np.hanning(win), np.hanning(win))
    idx, nb = _radial_bins(win)
    flat_idx = idx.ravel()
    bin_sel = [np.nonzero(flat_idx == b)[0] for b in range(nb)]
    ks = np.arange(k_lo, k_hi + 1)
    xk = np.log10(ks.astype(np.float64))
    xk_c = xk - xk.mean()
    denom = float((xk_c ** 2).sum())
    beta = np.full((ys.size, xs.size), np.nan)
    for i, y0 in enumerate(ys):
        # all windows of this row: sliding view gives (win, n_x, win); move the x index first
        wins = np.lib.stride_tricks.sliding_window_view(resid[y0:y0 + win], win, axis=1)[:, ::stride]
        vmask = np.lib.stride_tricks.sliding_window_view(valid[y0:y0 + win], win, axis=1)[:, ::stride]
        wins = np.transpose(wins, (1, 0, 2))
        vmask = np.transpose(vmask, (1, 0, 2))
        cover = vmask.mean(axis=(1, 2))
        ok = cover >= 0.90
        if not ok.any():
            continue
        seg = wins[ok] * hann
        seg = seg - seg.mean(axis=(1, 2), keepdims=True)
        power = (np.abs(np.fft.fft2(seg)) ** 2).reshape(seg.shape[0], -1)
        radial = np.stack([power[:, sel].mean(axis=1) for sel in bin_sel], axis=1)
        yk = np.log10(np.maximum(radial[:, ks], 1e-30))
        slope = ((yk - yk.mean(axis=1, keepdims=True)) * xk_c[None, :]).sum(axis=1) / denom
        beta[i, np.nonzero(ok)[0]] = slope
    cy, cx = np.meshgrid(ys + win // 2, xs + win // 2, indexing="ij")
    return beta, np.stack([cy, cx], axis=-1)


def beta_to_full(beta: np.ndarray, centres: np.ndarray, shape: tuple[int, int], stride: int = STRIDE) -> np.ndarray:
    """Nearest-window-centre upsampling of the window grid to the full raster (no smoothing)."""
    yy, xx = np.indices(shape)
    y0 = int(centres[0, 0, 0])
    x0 = int(centres[0, 0, 1])
    gy = np.clip(np.rint((yy - y0) / stride).astype(int), 0, beta.shape[0] - 1)
    gx = np.clip(np.rint((xx - x0) / stride).astype(int), 0, beta.shape[1] - 1)
    return beta[gy, gx]


def line_integral_surface(z: np.ndarray, valid: np.ndarray, line_len: int = LINE_LEN,
                          n_orient: int = N_ORIENT) -> np.ndarray:
    """Max over orientations of the mean of ``z`` along a line of ``line_len`` px (NaN-free inside)."""
    zf = np.where(valid, z, 0.0)
    vf = valid.astype(np.float64)
    best = np.full(z.shape, -np.inf)
    half = line_len // 2
    for j in range(n_orient):
        th = np.pi * j / n_orient
        ker = np.zeros((line_len, line_len))
        for t in np.linspace(-half, half, 4 * line_len):
            yy = int(round(half + t * np.sin(th)))
            xx = int(round(half + t * np.cos(th)))
            ker[yy, xx] = 1.0
        ker /= ker.sum()
        num = ndimage.convolve(zf, ker, mode="constant", cval=0.0)
        den = ndimage.convolve(vf, ker, mode="constant", cval=0.0)
        mean = np.where(den > 0.9, num / np.maximum(den, 1e-9), -np.inf)
        best = np.maximum(best, mean)
    out = np.where(valid & np.isfinite(best), best, 0.0)
    return out


def compute_surface(features_tif, foot: np.ndarray) -> dict:
    """Full H-S1 surface. Returns dict of arrays and summary numbers for the run card."""
    rtp = read_rtp(features_tif, foot)
    resid, valid = detrended_residual(rtp, foot)
    beta_grid, centres = window_beta(resid, valid)
    beta_full = beta_to_full(beta_grid, centres, foot.shape)
    flat = -beta_full  # higher = flatter spectrum = more high-wavenumber power
    flat_ok = foot & np.isfinite(flat)
    base = np.where(flat_ok, flat, 0.0)
    regional = _norm_conv(base, flat_ok, FLAT_TREND_SIGMA_PX)
    anom = np.where(flat_ok, flat - regional, 0.0)
    mu = anom[flat_ok].mean()
    sd = anom[flat_ok].std()
    z = np.where(flat_ok, (anom - mu) / max(sd, 1e-12), 0.0)
    surf = line_integral_surface(z, flat_ok)
    surf = np.where(foot, surf, 0.0)
    return {
        "rtp": rtp,
        "valid_residual": valid,
        "beta_full": beta_full,
        "flatness_z": np.where(flat_ok, z, np.nan),
        "surface": surf,
        "n_windows_total": int(beta_grid.size),
        "n_windows_valid": int(np.isfinite(beta_grid).sum()),
    }
