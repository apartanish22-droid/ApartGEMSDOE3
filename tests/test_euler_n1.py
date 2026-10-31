"""Method canary for the E1 Euler N=1 implementation (src/gems32/euler_n1.py).

An analytic point-source field T = 1/R with R = sqrt(rho^2 + d^2) is homogeneous of degree -1 and
satisfies the Euler equation exactly with N = 1, B = 0. The solver must recover the true x0, y0 and
depth d. These tests guard the sign convention of the positive-downward vertical derivative.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gems32 import euler_n1 as e  # noqa: E402

PIX = 100.0
H = W = 200
X0_M, Y0_M, D_M = 10_000.0, 10_000.0, 600.0


def _grid():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float64)
    return xx * PIX, yy * PIX


def _analytic():
    X, Y = _grid()
    dx, dy = X - X0_M, Y - Y0_M
    R = np.sqrt(dx * dx + dy * dy + D_M * D_M)
    T = 1.0 / R
    Tx = -dx / R**3
    Ty = -dy / R**3
    Tz = D_M / R**3  # positive-downward derivative at z = 0 for a source at z0 = D_M
    return T, Tx, Ty, Tz


def test_fft_vertical_derivative_matches_analytic_sign_and_magnitude():
    T, Tx_a, Ty_a, Tz_a = _analytic()
    Tx, Ty, Tz = e.derivatives_fft(T)
    # Compare only where the true signal is strong (>= 10 % of peak). Far-field pixels are
    # dominated by reflect-padding edge effects of a non-periodic grid and are not informative.
    strong = Tz_a > 0.10 * Tz_a.max()
    assert strong.sum() > 20
    ratio = Tz[strong] / Tz_a[strong]
    assert np.median(ratio) > 0.9 and np.median(ratio) < 1.1, np.median(ratio)  # sign AND scale
    assert np.corrcoef(Tz[strong], Tz_a[strong])[0, 1] > 0.99
    strong_x = np.abs(Tx_a) > 0.10 * np.abs(Tx_a).max()
    assert np.corrcoef(Tx[strong_x], Tx_a[strong_x])[0, 1] > 0.99


def test_euler_recovers_point_source_from_analytic_derivatives():
    T, Tx, Ty, Tz = _analytic()
    x0, y0, z0, B = e.euler_n1_solutions(T, Tx, Ty, Tz, N=1.0, valid=np.ones((H, W), bool))
    assert len(x0) >= 10, len(x0)  # only windows containing the source yield solutions
    assert abs(np.median(z0) - D_M) < 60.0, np.median(z0)
    assert abs(np.median(x0) - X0_M) < 150.0 and abs(np.median(y0) - Y0_M) < 150.0
    assert abs(np.median(B)) < 1e-3 * np.max(np.abs(T)) or abs(np.median(B)) < 1e-6


def test_end_to_end_fft_path_recovers_depth():
    T, _, _, _ = _analytic()
    Tx, Ty, Tz = e.derivatives_fft(T)
    x0, y0, z0, _ = e.euler_n1_solutions(T, Tx, Ty, Tz, N=1.0, valid=np.ones((H, W), bool))
    assert len(x0) >= 10, len(x0)
    assert abs(np.median(z0) - D_M) < 150.0, np.median(z0)
    assert abs(np.median(x0) - X0_M) < 300.0 and abs(np.median(y0) - Y0_M) < 300.0


def test_density_and_top_dots_respect_footprint():
    fp = np.zeros((H, W), bool)
    fp[20:180, 20:180] = True
    dens = np.zeros((H, W))
    dens[100, 100] = 5.0
    dots = e.top_dots(dens, fp, n=10)
    assert dots.sum() == 10
    assert not (dots & ~fp).any()
