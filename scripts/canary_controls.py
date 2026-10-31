#!/usr/bin/env python3
"""Experiment 3 (instrument check): does the single-feature canary in run_g1_euler_n1.py separate
signal from noise? Positive control = oracle surface built from the WITHHELD truth (should be ~1.0).
Negative control = i.i.d. uniform noise (should be ~0.5). Null results in G1/G2 are only meaningful
if the positive control passes."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from scipy.ndimage import distance_transform_edt
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems32 import holdout  # noqa: E402
from gems32.metric import kernel  # noqa: E402
from gems32.paths import data_dir  # noqa: E402


def cell_auc(sub: np.ndarray, cell, rng) -> float | None:
    pos_mask = np.zeros(sub.shape, bool)
    pos_mask[cell.truth_coords] = True
    neg_mask = cell.active_sub & ~pos_mask & (cell.k_dg_sub <= 0.0)
    p = sub[pos_mask & np.isfinite(sub)]
    n = sub[neg_mask & np.isfinite(sub)]
    if p.size == 0 or n.size == 0:
        return None
    if n.size > 20 * p.size:
        n = rng.choice(n, 20 * p.size, replace=False)
    y = np.concatenate([np.ones(p.size), np.zeros(n.size)])
    return float(roc_auc_score(y, np.concatenate([p, n])))


def main() -> int:
    ddir = data_dir()
    ctx = holdout.load_holdout_context(ddir)
    rng = np.random.default_rng(11)
    out = {"experiment": 3, "purpose": "canary instrument check (positive and negative control)"}
    # Positive control: oracle surface = kernel(distance to withheld truth) inside each cell's bbox
    pos_aucs, neg_aucs = [], []
    for cell in ctx.cells:
        truth_sub = np.zeros(cell.active_sub.shape, bool)
        truth_sub[cell.truth_coords] = True
        oracle = kernel(distance_transform_edt(~truth_sub)).astype(np.float64)
        a = cell_auc(oracle + 1e-9 * rng.random(oracle.shape), cell, rng)
        if a is not None:
            pos_aucs.append(a)
        # Negative control: uniform noise over the same bbox
        noise = rng.random(cell.active_sub.shape)
        b = cell_auc(noise, cell, rng)
        if b is not None:
            neg_aucs.append(b)
    out["positive_control_oracle_auc_mean"] = float(np.mean(pos_aucs))
    out["positive_control_oracle_auc_min"] = float(np.min(pos_aucs))
    out["negative_control_noise_auc_mean"] = float(np.mean(neg_aucs))
    out["negative_control_noise_auc_min"] = float(np.min(neg_aucs))
    out["n_cells"] = len(pos_aucs)
    out["instrument_valid"] = bool(out["positive_control_oracle_auc_min"] > 0.95
                                   and 0.4 < out["negative_control_noise_auc_mean"] < 0.6)
    print(json.dumps(out, indent=2))
    (ROOT / "evidence" / "G-CANARY-CONTROLS_experiment3.json").write_text(json.dumps(out, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
