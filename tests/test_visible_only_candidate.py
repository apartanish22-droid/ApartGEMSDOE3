"""Unit checks for the VO-LEARN candidate helpers (dot budget, NMS placement, control selection)."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("vo_candidate", ROOT / "scripts/run_visible_only_candidate.py")
vo = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(vo)


def test_nms_select_returns_exact_budget_inside_candidates():
    rng = np.random.default_rng(1)
    surface = rng.random((60, 60)).astype(np.float32)
    candidate = np.zeros((60, 60), bool)
    candidate[10:50, 10:50] = True
    dots = vo.nms_select(surface, candidate, 40)
    assert dots.sum() == 40
    assert not (dots & ~candidate).any()


def test_nms_select_suppresses_neighbours_of_a_single_peak():
    surface = np.zeros((20, 20), np.float32)
    surface[10, 10] = 0.9   # global peak
    surface[10, 11] = 0.8   # direct neighbour inside the 5x5 window: must be suppressed
    surface[3, 3] = 0.5     # isolated peak far away
    candidate = np.ones((20, 20), bool)
    dots = vo.nms_select(surface, candidate, 2)
    assert dots[10, 10] and dots[3, 3]
    assert not dots[10, 11]


def test_nms_falls_back_to_all_candidates_when_peaks_are_too_few():
    surface = np.zeros((10, 10), np.float32)
    surface[5, 5] = 1.0
    candidate = np.zeros((10, 10), bool)
    candidate[2:8, 2:8] = True
    dots = vo.nms_select(surface, candidate, 5)
    assert dots.sum() == 5
    assert not (dots & ~candidate).any()


def test_fold_budget_matches_pre_registered_fraction_on_full_footprint():
    footprint_px = 5_167_373  # sample_submission.tif finite pixels (pinned in data/prepared_manifest.json)
    assert round(vo.FRAC * footprint_px) == 38_755
    assert round(0.015 * footprint_px) == 77_511
    assert vo.NMS_RADIUS == 2 and vo.PSEUDO_RADIUS == 3
