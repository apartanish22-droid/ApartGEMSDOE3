"""G1 · Euler deconvolution with structural index N = 1 on total magnetic intensity (band 14 ``tmi``).

Pre-registered in knowledge/10_calibration_finding_and_next_candidates_20261030.md §6.
Method (exactly as pre-registered, plus the implementation details recorded here):

  1. Fill nodata (-3.4e38 sentinel / non-finite) with the footprint median so FFT derivatives are
     defined on the whole grid (footprint only is used for every output).
  2. Derivatives from the grid by FFT: Tx, Ty (horizontal, north-positive y) and Tz = dT/dz with
     z positive DOWN (spectral |k|). Coordinates are kilometres, relative to the grid centre.
  3. Euler homogeneity with N = 1 and observation plane z = 0, solved by least squares in sliding
     windows (side ``WIN_PX`` px, centres every ``STRIDE_PX`` px):
         x0*Tx + y0*Ty + z0*Tz + N*B = x*Tx + y*Ty + N*T
  4. Keep solutions with depth 0.4-6 km, source inside the window, and relative residual
     RSS / sum(b^2) <= 0.10 (fixed a priori; not tuned on holdout), and windows that are fully
     inside the footprint.
  5. Density of accepted solutions on the 100 m grid, Gaussian smoothed (sigma 2 px), then
     percentile-ranked inside the footprint to give a surface in [0, 1].

Memory is bounded by processing the grid in row bands (the grid is 12.3 M cells on a 3 GB host).
"""
from __future__ import annotations

import numpy as np
from scipy.fft import next_fast_len
from scipy.ndimage import gaussian_filter, uniform_filter

PIXEL_KM = 0.1          # 100 m grid
N_INDEX = 1.0           # structural index (pre-registered)
Z_MIN_KM, Z_MAX_KM = 0.4, 6.0
WIN_PX = 21             # 2.1 km window
STRIDE_PX = 4
RESID_MAX = 0.10
FILL_PAD = 128          # px of edge padding before FFT


def fill_nodata(a: np.ndarray, foot: np.ndarray) -> np.ndarray:
    """Replace non-finite / sentinel values with the footprint median (float64)."""
    out = np.asarray(a, dtype=np.float64).copy()
    bad = ~np.isfinite(out) | (out < -1e30) | ~foot
    good = foot & ~bad
    if not good.any():
        raise ValueError("no valid data in footprint")
    out[bad] = float(np.median(out[good]))
    return out


def derivatives(t: np.ndarray, pix_km: float = PIXEL_KM):
    """Return (Tx, Ty, Tz) by FFT on an edge-padded grid. Ty is north-positive; Tz is z-down."""
    nr, nc = t.shape
    pr, pc = next_fast_len(nr + 2 * FILL_PAD, True), next_fast_len(nc + 2 * FILL_PAD, True)
    pad_r = (pr - nr) // 2
    pad_c = (pc - nc) // 2
    tp = np.pad(t, ((pad_r, pr - nr - pad_r), (pad_c, pc - nc - pad_c)), mode="edge")
    f = np.fft.rfft2(tp)
    kr = 2 * np.pi * np.fft.fftfreq(pr, d=pix_km)            # cycles per km along rows (south-positive)
    kc = 2 * np.pi * np.fft.rfftfreq(pc, d=pix_km)           # along cols (east-positive)
    KR, KC = np.meshgrid(kr, kc, indexing="ij")
    KMAG = np.sqrt(KR ** 2 + KC ** 2)
    tx = np.fft.irfft2(1j * KC * f, s=(pr, pc))
    d_row = np.fft.irfft2(1j * KR * f, s=(pr, pc))
    tz = np.fft.irfft2(KMAG * f, s=(pr, pc))
    sl = (slice(pad_r, pad_r + nr), slice(pad_c, pad_c + nc))
    return tx[sl], -d_row[sl], tz[sl]                        # Ty = dT/dNorth = -dT/drow


def _coords(nr: int, nc: int, pix_km: float = PIXEL_KM):
    rc, cc = (nr - 1) / 2.0, (nc - 1) / 2.0
    x = (np.arange(nc) - cc) * pix_km                         # east, km
    y = -(np.arange(nr) - rc) * pix_km                        # north, km
    return x, y


def euler_n1_solutions(t_filled: np.ndarray, foot: np.ndarray, *, band_rows: int = 256,
                       win_px: int = WIN_PX, stride_px: int = STRIDE_PX, n_index: float = N_INDEX):
    """Return dict of arrays for accepted solutions plus diagnostics. ``t_filled`` must be nodata-free."""
    nr, nc = t_filled.shape
    tx, ty, tz = derivatives(t_filled)
    x_all, y_all = _coords(nr, nc)
    fin = foot.astype(np.float64)
    h = win_px // 2 + 2
    cen_rows_all = np.arange(0, nr, stride_px)
    cen_cols = np.arange(0, nc, stride_px)
    out_x, out_y, out_z, out_rr, out_r, out_c = [], [], [], [], [], []
    n_windows = 0
    n_inside = 0
    for r0 in range(0, nr, band_rows):
        r1 = min(nr, r0 + band_rows)
        s0, s1 = max(0, r0 - h), min(nr, r1 + h)
        sub = slice(s0, s1)
        X = np.broadcast_to(x_all[None, :], (s1 - s0, nc))
        Y = np.broadcast_to(y_all[sub][:, None], (s1 - s0, nc))
        Tx, Ty, Tz, T = tx[sub], ty[sub], tz[sub], t_filled[sub]
        b = X * Tx + Y * Ty + n_index * T
        def bs(a):
            return uniform_filter(a, size=win_px, mode="constant", cval=0.0)
        sTxTx = bs(Tx * Tx); sTxTy = bs(Tx * Ty); sTxTz = bs(Tx * Tz)
        sTyTy = bs(Ty * Ty); sTyTz = bs(Ty * Tz); sTzTz = bs(Tz * Tz)
        sTx = bs(Tx); sTy = bs(Ty); sTz = bs(Tz)
        sTxb = bs(Tx * b); sTyb = bs(Ty * b); sTzb = bs(Tz * b)
        sb = bs(b); sbb = bs(b * b)
        sfin = bs(fin[sub])
        # centres of this band that are on the stride grid
        rows = cen_rows_all[(cen_rows_all >= r0) & (cen_rows_all < r1)]
        if rows.size == 0:
            continue
        lr = rows - s0
        ii, jj = np.meshgrid(lr, cen_cols, indexing="ij")
        ii = ii.ravel(); jj = jj.ravel()
        gr = (ii + s0); gc = jj
        ok = (foot[gr, gc]) & (sfin[ii, jj] >= 0.999)
        n_windows += int(ok.sum())
        ii, jj, gr, gc = ii[ok], jj[ok], gr[ok], gc[ok]
        if ii.size == 0:
            continue
        # normal equations for unknowns (x0, y0, z0, B) with design row a = [Tx, Ty, Tz, N]
        N = n_index
        M = np.empty((ii.size, 4, 4))
        v = np.empty((ii.size, 4))
        M[:, 0, 0] = sTxTx[ii, jj]; M[:, 0, 1] = M[:, 1, 0] = sTxTy[ii, jj]
        M[:, 0, 2] = M[:, 2, 0] = sTxTz[ii, jj]; M[:, 0, 3] = M[:, 3, 0] = N * sTx[ii, jj]
        M[:, 1, 1] = sTyTy[ii, jj]; M[:, 1, 2] = M[:, 2, 1] = sTyTz[ii, jj]
        M[:, 1, 3] = M[:, 3, 1] = N * sTy[ii, jj]
        M[:, 2, 2] = sTzTz[ii, jj]; M[:, 2, 3] = M[:, 3, 2] = N * sTz[ii, jj]
        M[:, 3, 3] = N * N * float(win_px * win_px)
        v[:, 0] = sTxb[ii, jj]; v[:, 1] = sTyb[ii, jj]; v[:, 2] = sTzb[ii, jj]; v[:, 3] = N * sb[ii, jj]
        # tiny ridge for conditioning (relative to the matrix scale)
        scale = np.trace(M, axis1=1, axis2=2) / 4.0 + 1e-30
        M_r = M + (1e-9 * scale)[:, None, None] * np.eye(4)[None]
        try:
            th = np.linalg.solve(M_r, v[..., None])[..., 0]
        except np.linalg.LinAlgError:
            th = np.full((ii.size, 4), np.nan)
        rss = sbb[ii, jj] - 2.0 * np.einsum("ni,ni->n", th, v) + np.einsum("ni,nij,nj->n", th, M, th)
        bb = sbb[ii, jj]
        rel = rss / np.maximum(bb, 1e-30)
        x0, y0, z0 = th[:, 0], th[:, 1], th[:, 2]
        xc, yc = x_all[gc], y_all[gr]
        half = (win_px // 2) * PIXEL_KM
        keep = (np.isfinite(th).all(axis=1) & np.isfinite(rel) & (rel >= 0) & (rel <= RESID_MAX)
                & (z0 >= Z_MIN_KM) & (z0 <= Z_MAX_KM)
                & (np.abs(x0 - xc) <= half) & (np.abs(y0 - yc) <= half))
        n_inside += int(keep.sum())
        out_x.append(x0[keep]); out_y.append(y0[keep]); out_z.append(z0[keep])
        out_rr.append(rel[keep]); out_r.append(gr[keep]); out_c.append(gc[keep])
    cat = lambda L: np.concatenate(L) if L else np.zeros(0)
    return {
        "x_km": cat(out_x), "y_km": cat(out_y), "z_km": cat(out_z), "rel_resid": cat(out_rr),
        "win_row": cat(out_r).astype(int), "win_col": cat(out_c).astype(int),
        "n_windows_on_footprint": n_windows, "n_accepted": n_inside,
    }


def solutions_to_density(sol: dict, shape: tuple[int, int], foot: np.ndarray, sigma_px: float = 2.0) -> np.ndarray:
    """Place accepted (x0, y0) solutions on the grid and smooth. Returns float64 density (0 outside foot)."""
    nr, nc = shape
    rc, cc = (nr - 1) / 2.0, (nc - 1) / 2.0
    col = np.rint(sol["x_km"] / PIXEL_KM + cc).astype(int)
    row = np.rint(-sol["y_km"] / PIXEL_KM + rc).astype(int)
    m = (row >= 0) & (row < nr) & (col >= 0) & (col < nc)
    dens = np.zeros(shape, dtype=np.float64)
    np.add.at(dens, (row[m], col[m]), 1.0)
    dens = gaussian_filter(dens, sigma=sigma_px, mode="constant")
    dens[~foot] = 0.0
    return dens
