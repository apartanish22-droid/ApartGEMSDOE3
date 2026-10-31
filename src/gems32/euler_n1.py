"""E1 (pre-registered, docs/research/preregistration-euler-n1-tmi-20261031.md): Euler N=1 solution density on TMI.

Lane: windowed Euler deconvolution with structural index N = 1 on a single continuous field
(training_features band 14, `tmi`). No catalogue layer is read by feature construction.

Convention: x, y, z in metres; z positive DOWNWARD from the observation plane (z = 0 at the
surface). Euler homogeneity equation for a source at (x0, y0, z0) with index N and background B:

    (x - x0) Tx + (y - y0) Ty + (z - z0) Tz = N (B - T),   with z = 0 on the grid.

Rearranged as a linear system in u = (x0, y0, z0, B) with a = (Tx, Ty, Tz, N) and
b = x Tx + y Ty + z Tz + N T:  a . u = b.

Vertical derivative with z positive downward: dT/dz_down = IFFT(|k| FFT(T)) (harmonic field from
sources below the plane). Canary tests in tests/test_euler_n1.py verify this sign on an analytic 1/R
field before any real data are used.
"""
from __future__ import annotations

import numpy as np
from scipy.ndimage import uniform_filter
from scipy.fft import fft2, ifft2, next_fast_len
from scipy.ndimage import distance_transform_edt, gaussian_filter

PIXEL_M = 100.0
WINDOW_PX = 15          # 1.5 km square window
STEP_PX = 3             # window step
DEPTH_M_LO = 200.0      # 2 px
DEPTH_M_HI = 3000.0     # 30 px
DOTS = 37654            # identical dot budget to the GEMSDOE32 champion


def fill_invalid_nearest(field: np.ndarray, valid: np.ndarray) -> np.ndarray:
    """Replace invalid cells with the nearest valid value (no catalogue input)."""
    field = np.asarray(field, np.float64).copy()
    valid = np.asarray(valid, bool)
    if valid.all():
        return field
    _, (ri, ci) = distance_transform_edt(~valid, return_indices=True)
    out = field[ri, ci]
    return out


def derivatives_fft(field: np.ndarray, pixel_m: float = PIXEL_M):
    """Return (Tx, Ty, Tz) in units per metre. Tz is positive-downward (|k| filter)."""
    H, W = field.shape
    ph = next_fast_len(H + 2 * 256, real=False)
    pw = next_fast_len(W + 2 * 256, real=False)
    pad = np.pad(field, ((256, ph - H - 256), (256, pw - W - 256)), mode="reflect")
    F = fft2(pad)
    ky = 2 * np.pi * np.fft.fftfreq(ph, d=pixel_m)[:, None]
    kx = 2 * np.pi * np.fft.fftfreq(pw, d=pixel_m)[None, :]
    kmag = np.sqrt(kx * kx + ky * ky)
    Tx = ifft2(1j * kx * F).real[256:256 + H, 256:256 + W]
    Ty = ifft2(1j * ky * F).real[256:256 + H, 256:256 + W]
    Tz = ifft2(kmag * F).real[256:256 + H, 256:256 + W]
    return Tx, Ty, Tz


def euler_n1_solutions(T, Tx, Ty, Tz, *, N: float = 1.0, window: int = WINDOW_PX, step: int = STEP_PX,
                       pixel_m: float = PIXEL_M, depth_lo: float = DEPTH_M_LO, depth_hi: float = DEPTH_M_HI,
                       valid: np.ndarray | None = None, rows_per_chunk: int = 64):
    """Windowed Euler solutions. Returns (x0, y0, z0, B) arrays of accepted solutions in metres."""
    H, W = T.shape
    half = window // 2
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float64)
    X = xx * pixel_m
    Y = yy * pixel_m
    # Scale every derivative by one common constant so the 4x4 systems are well conditioned.
    scale = 1.0 / max(np.std(Tz[valid] if valid is not None else Tz), 1e-30)
    Tx, Ty, Tz, Tt = Tx * scale, Ty * scale, Tz * scale, T * scale
    # z = 0 on the observation grid, so the z*Tz term of b vanishes.
    a = [Tx, Ty, Tz, np.full_like(Tx, N)]
    b = X * Tx + Y * Ty + N * Tt

    def box(arr):
        return uniform_filter(arr, size=window, mode="constant", cval=0.0) * (window * window)

    # Window sums are only needed at the step-grid centres, so compute them there (memory-bounded).
    cy = np.arange(half, H - half, step)
    cx = np.arange(half, W - half, step)
    # Box sums at full resolution, then subsampled; computed per coefficient pair to keep RAM low.
    Mfull = {}
    for i in range(4):
        for j in range(i, 4):
            Mfull[(i, j)] = box(a[i] * a[j])[np.ix_(cy, cx)]
    rfull = [box(a[i] * b)[np.ix_(cy, cx)] for i in range(4)]
    Msub_all = np.empty((len(cy), len(cx), 4, 4))
    for (i, j), v in Mfull.items():
        Msub_all[..., i, j] = v
        Msub_all[..., j, i] = v
    rsub_all = np.stack(rfull, axis=-1)
    out_x, out_y, out_z, out_b = [], [], [], []
    for r0 in range(0, len(cy), rows_per_chunk):
        sl = slice(r0, r0 + rows_per_chunk)
        rows = cy[sl]
        Msub = Msub_all[sl]
        rsub = rsub_all[sl]
        det = np.linalg.det(Msub)
        tr = np.abs(np.trace(Msub, axis1=-2, axis2=-1))
        ok = np.isfinite(det) & (np.abs(det) > 1e-12 * np.maximum(tr ** 4, 1e-300))
        if not ok.any():
            continue
        Mo = Msub[ok]
        ro = rsub[ok]
        try:
            u = np.linalg.solve(Mo, ro[..., None])[..., 0]
        except np.linalg.LinAlgError:
            continue
        xc = np.broadcast_to(X[np.ix_(rows, cx)], ok.shape)[ok]
        yc = np.broadcast_to(Y[np.ix_(rows, cx)], ok.shape)[ok]
        x0, y0, z0, B = u[:, 0], u[:, 1], u[:, 2], u[:, 3]
        in_win = (np.abs(x0 - xc) <= half * pixel_m) & (np.abs(y0 - yc) <= half * pixel_m)
        in_depth = (z0 >= depth_lo) & (z0 <= depth_hi)
        keep = in_win & in_depth & np.isfinite(x0) & np.isfinite(y0) & np.isfinite(z0)
        out_x.append(x0[keep]); out_y.append(y0[keep]); out_z.append(z0[keep]); out_b.append(B[keep])
    if not out_x:
        return (np.array([]),) * 4
    return (np.concatenate(out_x), np.concatenate(out_y), np.concatenate(out_z), np.concatenate(out_b))


def solution_density(x0, y0, shape, pixel_m: float = PIXEL_M, sigma_px: float = 2.0) -> np.ndarray:
    """Accumulate solutions into the grid and smooth. Returns a float64 density raster."""
    H, W = shape
    counts = np.zeros(shape, np.float64)
    if len(x0):
        ci = np.clip(np.round(np.asarray(x0) / pixel_m).astype(int), 0, W - 1)
        ri = np.clip(np.round(np.asarray(y0) / pixel_m).astype(int), 0, H - 1)
        np.add.at(counts, (ri, ci), 1.0)
    return gaussian_filter(counts, sigma=sigma_px)


def top_dots(density: np.ndarray, footprint: np.ndarray, n: int = DOTS) -> np.ndarray:
    """Top-n footprint cells by density (ties broken by raster order). Returns boolean dots."""
    fp = np.asarray(footprint, bool)
    d = np.where(fp, density, -np.inf).ravel()
    order = np.argsort(-d, kind="stable")
    keep = order[:n]
    keep = keep[np.isfinite(d[keep])]
    out = np.zeros(d.shape, bool)
    out[keep] = True
    return out.reshape(density.shape)
