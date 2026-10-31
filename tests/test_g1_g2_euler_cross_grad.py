"""Regression tests for G1 (Euler N=1) and G2 (gravity-magnetic coupling), plus release-safety checks
for the 2026-10-31 negative TIF. Synthetic tests run in seconds; the file test needs docs/downloads."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems32 import cross_grad_g2 as G2  # noqa: E402
from gems32 import euler_n1 as G1  # noqa: E402


def test_euler_n1_recovers_synthetic_source():
    """A 1/r source is homogeneous of degree -1 (structural index 1). The solver must recover it."""
    n = 300
    x, y = G1._coords(n, n)
    X, Y = np.meshgrid(x, y)
    x0, y0, z0 = 3.0, -2.0, 1.5
    T = 1.0 / np.sqrt((X - x0) ** 2 + (Y - y0) ** 2 + z0 ** 2)
    sol = G1.euler_n1_solutions(T, np.ones((n, n), bool))
    d = np.hypot(sol["x_km"] - x0, sol["y_km"] - y0)
    near = d < 0.5
    assert near.sum() >= 5
    assert abs(float(np.median(sol["z_km"][near])) - z0) < 0.05          # depth sign and scale
    assert abs(float(np.median(sol["x_km"][near])) - x0) < 0.05          # east positive
    assert abs(float(np.median(sol["y_km"][near])) - y0) < 0.05          # north positive
    assert float(sol["rel_resid"][near].max()) < G1.RESID_MAX


def test_euler_derivatives_sign_convention():
    """Tz (z positive down) must be positive for a source below the surface, and Ty north-positive."""
    n = 200
    x, y = G1._coords(n, n)
    X, Y = np.meshgrid(x, y)
    T = 1.0 / np.sqrt((X - 1.0) ** 2 + (Y - 0.0) ** 2 + 1.0)  # source at north 0, east 1
    tx, ty, tz = G1.derivatives(T)
    # Source at (east 1 km, north 0 km). Row index increases SOUTHWARD: north of the source the field
    # decreases northward (dT/dy < 0); south of it the field increases northward (dT/dy > 0).
    row_north = int(round((n - 1) / 2 - 2.0 / G1.PIXEL_KM))   # y = +2 km
    row_south = int(round((n - 1) / 2 + 2.0 / G1.PIXEL_KM))   # y = -2 km
    col = int(round((n - 1) / 2 + 1.0 / G1.PIXEL_KM))         # x = +1 km
    assert float(ty[row_north, col]) < 0
    assert float(ty[row_south, col]) > 0
    assert float(tz[row_north, col]) > 0                       # field strengthens with depth-down
    assert np.isfinite(tz).all()


def test_cross_gradient_coupling_prefers_shared_edges():
    n = 200
    yy, xx = np.mgrid[0:n, 0:n].astype(float)
    grav = np.where(xx >= 100, 10.0, 0.0) + 0.001 * xx
    mag = np.where(xx >= 100, 5.0, 0.0) + np.where(yy >= 50, 3.0, 0.0) * (xx < 60)
    foot = np.ones((n, n), bool)
    S = G2.coupling_surface(grav, mag, foot, sigma_px=1.0)
    shared = float(S[:, 98:103].max())
    mag_only = float(S[48:53, 10:50].mean())
    background = float(S[150:190, 20:40].mean())
    assert shared > 10 * mag_only
    assert shared > 10 * background


def test_negative_tif_matches_run_card_and_is_labelled():
    card_paths = sorted((ROOT / "evidence").glob("H-G1-EULER-N1-TMI_*_run_card.json"))
    assert card_paths, "G1 run card missing"
    card = json.loads(card_paths[-1].read_text())
    assert len(card["submission_note"]) <= 140
    assert "NEG" in card["submission_note"] and "DO-NOT-SUBMIT" in card["submission_note"]
    tif = ROOT / "docs" / "downloads" / card["submission_file"]
    if not tif.is_file():
        pytest.skip("TIF not present in this checkout")
    digest = hashlib.sha256(tif.read_bytes()).hexdigest()
    assert digest == card["raster_sha256"]


def test_session_card_forbids_download_and_submit():
    card = json.loads((ROOT / "evidence" / "SESSION_20261031_RUN_CARD.json").read_text())
    assert card["candidate"]["download_allowed"] is False
    assert card["candidate"]["submit_allowed"] is False
    assert card["candidate"]["verdict"] == "negative"
    assert card["budget"]["experiments_used"] <= card["budget"]["limit"]
    assert card["controls"]["instrument_valid"] is True
