#!/usr/bin/env python3
"""Visible-only learned fault-likeness candidate (lane VO-LEARN) with a same-evaluator baseline.

Lane declaration (the assigned method paragraph is absent from the session prompt, so the lane is
declared here and recorded in the run card rather than inferred from elsewhere):

  VO-LEARN: a gradient-boosted (or logistic control) classifier trained per withheld fold on the
  19-band competition stack.  Positives are pixels within 3 px of VISIBLE catalogue faults outside
  the test quadrant and its 15 px collar; negatives are pixels farther than 3 px from ANY catalogue
  trace outside the collar.  Dots are the top-K non-maximum-suppressed (5x5) pixels of the
  out-of-fold surface, with K = frac * footprint / 4 per fold.

Control (incumbent): VO-NEAR, the K nearest in-domain pixels to VISIBLE catalogue faults per fold
(a "stay near mapped faults" baseline that uses no learned model).

Holdout is the shared evaluator `gems32.holdout.evaluate_hide_and_recover` (visible-only masking,
15 px collar, pooled DTI alpha 0.2 / beta 0.8, 300 m triangular kernel, cluster-bootstrap 95% CI).
Paired CI: candidate and control share the same spatial clusters and bootstrap resamples, so the
difference of their bootstrap replicates is a paired interval.

Modes:
  --mode holdout  : per-fold out-of-fold masks -> .npz, evaluation, canaries, run card
  --mode final    : fit on all labels, write the full-footprint GeoTIFF through the shared writer
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt, maximum_filter
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from gems32 import holdout  # noqa: E402
from gems32.paths import data_dir, evidence_dir, work_dir  # noqa: E402

FRAC = 0.0075          # pre-registered dot budget: fraction of footprint pixels
NMS_RADIUS = 2         # 5x5 non-maximum suppression
PSEUDO_RADIUS = 3      # 300 m = 3 px kernel radius
MAX_NEG = 400_000
LANE = "VO-LEARN"


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def build_stack(ddir: Path):
    with rasterio.open(ddir / "sample_submission.tif") as ds:
        foot = np.isfinite(ds.read(1))
    labels = holdout.read_binary(ddir / "labels.tif") & foot
    with rasterio.open(ddir / "training_features.tif") as ds:
        names = [str(d).split(" - ")[0] for d in ds.descriptions]
        cols = []
        for i in range(1, ds.count + 1):
            a = ds.read(i).astype(np.float32, copy=False)
            a = np.where(a <= -3.0e38, np.nan, a)
            cols.append(a[foot])
    X = np.stack(cols, axis=1).astype(np.float32)
    idx_map = np.full(foot.shape, -1, dtype=np.int64)
    idx_map[foot] = np.arange(X.shape[0])
    return foot, labels, X, idx_map, names


def sample_training(pos_mask, neg_mask, idx_map, rng):
    pr = idx_map[pos_mask]
    nr = idx_map[neg_mask]
    pr = pr[pr >= 0]
    nr = nr[nr >= 0]
    n_neg = int(min(nr.size, max(2 * pr.size, 1000), MAX_NEG))
    if nr.size > n_neg:
        nr = rng.choice(nr, n_neg, replace=False)
    rows = np.concatenate([pr, nr])
    y = np.concatenate([np.ones(pr.size, np.int8), np.zeros(nr.size, np.int8)])
    return rows, y


def fit_model(learner: str, Xtr: np.ndarray, ytr: np.ndarray, seed: int):
    if learner == "hgb":
        m = HistGradientBoostingClassifier(
            max_iter=200, learning_rate=0.08, max_leaf_nodes=63,
            min_samples_leaf=200, l2_regularization=1.0, random_state=seed,
        )
        m.fit(Xtr, ytr)
        return ("hgb", m, None, None, None)
    if learner == "logreg":
        med = np.nanmedian(Xtr, axis=0)
        Xi = np.where(np.isnan(Xtr), med, Xtr)
        mu, sd = Xi.mean(axis=0), Xi.std(axis=0) + 1e-9
        m = LogisticRegression(max_iter=500, C=1.0)
        m.fit((Xi - mu) / sd, ytr)
        return ("logreg", m, med, mu, sd)
    raise ValueError(learner)


def predict_model(fitted, X: np.ndarray) -> np.ndarray:
    kind, m, med, mu, sd = fitted
    if kind == "hgb":
        return m.predict_proba(X)[:, 1].astype(np.float32)
    Xi = np.where(np.isnan(X), med, X)
    return m.predict_proba((Xi - mu) / sd)[:, 1].astype(np.float32)


def nms_select(surface: np.ndarray, candidate: np.ndarray, k: int) -> np.ndarray:
    """Top-k candidate pixels after 5x5 non-maximum suppression on the surface."""
    size = 2 * NMS_RADIUS + 1
    is_peak = (surface >= maximum_filter(surface, size=size)) & (surface > 0)
    pool = np.flatnonzero(candidate & is_peak)
    if pool.size < k:  # fall back to all candidates rather than emitting fewer dots
        pool = np.flatnonzero(candidate)
    vals = surface.ravel()[pool]
    take = pool if pool.size <= k else pool[np.argpartition(-vals, k - 1)[:k]]
    out = np.zeros(surface.shape, bool)
    out.ravel()[take] = True
    return out


def canaries(X, names, idx_map, cells, foot, rng, n_neg=300_000):
    """Feature-alone holdout AUC per band (all cells). AUC > 0.90 is leakage until proven otherwise."""
    table = {n: [] for n in names}
    for cell in cells:
        r0, c0 = int(cell.bbox[0].start), int(cell.bbox[1].start)
        truth = np.zeros(foot.shape, bool)
        ty, tx = cell.truth_coords
        if ty.size == 0:
            continue
        truth[ty + r0, tx + c0] = True
        act = np.zeros(foot.shape, bool)
        act[cell.bbox] = cell.active_sub
        neg = act & ~truth & foot
        pr, nr = idx_map[truth & act], idx_map[neg]
        pr, nr = pr[pr >= 0], nr[nr >= 0]
        if nr.size > n_neg:
            nr = rng.choice(nr, n_neg, replace=False)
        rows = np.concatenate([pr, nr])
        y = np.concatenate([np.ones(pr.size), np.zeros(nr.size)])
        for b, n in enumerate(names):
            v = X[rows, b].astype(np.float64)
            med = np.nanmedian(v) if np.isfinite(v).any() else 0.0
            v = np.where(np.isfinite(v), v, med)
            if np.ptp(v) == 0:
                table[n].append(0.5)
                continue
            table[n].append(float(roc_auc_score(y, v)))
    out = {}
    for n in names:
        a = np.array(table[n]) if table[n] else np.array([0.5])
        out[n] = {"auc_mean_over_cells": float(a.mean()),
                  "auc_max_abs_dev_from_0p5": float(np.max(np.abs(a - 0.5)) + 0.5),
                  "leak_flag_gt_0p90": bool(np.max(np.maximum(a, 1 - a)) > 0.90)}
    return out


def run_holdout(args):
    ddir = args.data_dir
    t0 = time.time()
    foot, labels, X, idx_map, names = build_stack(ddir)
    ctx = holdout.load_holdout_context(ddir)
    H, W = foot.shape
    d_lab = distance_transform_edt(~labels)
    quad = ctx.quad
    rng = np.random.default_rng(args.seed)
    k_fold = int(round(args.frac * foot.sum() / 4.0))

    cand_cells, base_cells, cell_rows = {}, {}, []
    for cell in ctx.cells:
        visible = ctx.visible_by_cell[cell.key]
        fold = cell.fold
        test_q = (quad == fold) & foot
        collar = holdout.binary_dilation(test_q, structure=np.ones((3, 3), bool),
                                         iterations=holdout.COLLAR_PX)
        train_region = foot & ~collar
        d_vis = distance_transform_edt(~visible)
        pos = train_region & (d_vis <= PSEUDO_RADIUS)
        neg = train_region & (d_lab > PSEUDO_RADIUS)
        act = np.zeros(foot.shape, bool)
        act[cell.bbox] = cell.active_sub
        act &= foot

        rows, y = sample_training(pos, neg, idx_map, rng)
        fitted = fit_model(args.learner, X[rows], y, args.seed + 10 * cell.seed + fold)
        test_mask = test_q & (idx_map >= 0)
        surf = np.zeros(foot.shape, np.float32)
        surf[test_mask] = predict_model(fitted, X[idx_map[test_mask]])
        cand_mask = np.zeros(foot.shape, bool)
        cand_mask[cell.bbox] = cell.active_sub
        cand_mask &= test_q
        dots = nms_select(surf, cand_mask, k_fold)
        cand_cells[cell.key] = dots

        # Control VO-NEAR: nearest in-domain pixels to visible catalogue faults (no learning).
        jitter = rng.random(foot.shape) * 1e-3
        near_score = np.where(cand_mask, d_vis + jitter, np.inf)
        flat = np.flatnonzero(cand_mask)
        pick = flat[np.argsort(near_score.ravel()[flat])[:k_fold]]
        base = np.zeros(foot.shape, bool)
        base.ravel()[pick] = True
        base_cells[cell.key] = base

        cell_rows.append({
            "cell": cell.key, "train_pos": int(y.sum()), "train_neg": int((y == 0).sum()),
            "k_dots": int(k_fold), "candidate_dots": int(dots.sum()), "control_dots": int(base.sum()),
            "n_withheld_positives": int(cell.n_truth),
            "candidate_within3px_of_visible": float((distance_transform_edt(~visible)[dots] <= 3).mean()),
            "visible_faults_px": int(visible.sum()),
        })
        print(f"{cell.key}: pos={int(y.sum())} neg={int((y==0).sum())} dots={int(dots.sum())} "
              f"withheld={cell.n_truth} t={time.time()-t0:.0f}s", flush=True)

    tag = args.tag
    out_dir = work_dir() / "experiments"
    out_dir.mkdir(parents=True, exist_ok=True)
    cand_path = out_dir / f"{tag}_cells.npz"
    base_path = out_dir / f"{tag}_control_cells.npz"
    np.savez_compressed(cand_path, **cand_cells)
    np.savez_compressed(base_path, **base_cells)

    res_c = holdout.evaluate_hide_and_recover(cand_cells, ctx, name=tag)
    res_b = holdout.evaluate_hide_and_recover(base_cells, ctx, name=f"{tag}-VO-NEAR-control")
    bc, bb = np.asarray(res_c["_boots"]), np.asarray(res_b["_boots"])
    diff = bc - bb
    paired = [float(np.percentile(diff, 2.5)), float(np.percentile(diff, 97.5))]

    can = canaries(X, names, idx_map, ctx.cells, foot, rng)
    leak = [n for n, v in can.items() if v["leak_flag_gt_0p90"]]

    def strip(r):
        return {k: v for k, v in r.items() if not k.startswith("_") and k != "folds"}

    card = {
        "lane": LANE,
        "lane_note": "Assigned method paragraph absent from session prompt; lane declared by this run.",
        "hypothesis": "A fold-refit classifier on the 19-band stack, trained only on visible catalogue traces, "
                      "ranks withheld catalogue-segment pixels above the rest of the domain.",
        "mechanism": "Learned multi-field signature (magnetic, gravity, radiometric, topographic, cover depth) "
                     "that co-occurs with mapped faults; withheld segments share it.",
        "named_non_fault_mimic": "Lithologic/magnetic contacts, intrusions, and cover-thickness steps of "
                                 "non-fault origin that share the same multi-band signature.",
        "learner": args.learner,
        "frac_of_footprint": args.frac,
        "nms_radius_px": NMS_RADIUS,
        "evaluator": holdout.HIDE_RECOVER_EVALUATOR_VERSION,
        "candidate_holdout": strip(res_c),
        "control_holdout_VO_NEAR": strip(res_b),
        "paired_candidate_minus_control_ci95": paired,
        "paired_candidate_minus_control_mean": float(diff.mean()),
        "per_cell": cell_rows,
        "feature_alone_canary_auc": can,
        "features_flagged_leakage_gt_0p90": leak,
        "npz_candidate": str(cand_path),
        "npz_candidate_sha256": sha256_file(cand_path),
        "npz_control": str(base_path),
        "npz_control_sha256": sha256_file(base_path),
        "runtime_s": round(time.time() - t0, 1),
    }
    ev = evidence_dir() / f"{tag}_holdout.json"
    ev.write_text(json.dumps(card, indent=2) + "\n")
    print(f"CANDIDATE pooled={res_c['pooled_dti']:.6f} CI={res_c['ci95_cluster_bootstrap']} "
          f"withheld={res_c['n_withheld_positives']}")
    print(f"CONTROL   pooled={res_b['pooled_dti']:.6f} CI={res_b['ci95_cluster_bootstrap']}")
    print(f"PAIRED delta CI95={paired} leak_flags={leak}")
    print(f"wrote {ev}")
    return card


def run_final(args):
    ddir = args.data_dir
    foot, labels, X, idx_map, names = build_stack(ddir)
    d_lab = distance_transform_edt(~labels)
    pos = foot & (d_lab <= PSEUDO_RADIUS)
    neg = foot & (d_lab > PSEUDO_RADIUS)
    rng = np.random.default_rng(args.seed)
    rows, y = sample_training(pos, neg, idx_map, rng)
    fitted = fit_model(args.learner, X[rows], y, args.seed)
    surf = np.zeros(foot.shape, np.float32)
    surf[foot] = predict_model(fitted, X)
    k_total = int(round(args.frac * foot.sum()))
    cand = foot & ~labels
    dots = nms_select(surf, cand, k_total)
    out_dir = work_dir() / "experiments"
    out_dir.mkdir(parents=True, exist_ok=True)
    np.save(out_dir / f"{args.tag}_final_surface.npy", surf)
    np.save(out_dir / f"{args.tag}_final_dots.npy", dots)
    print(f"final dots={int(dots.sum())} k_total={k_total} train_pos={int(y.sum())} "
          f"train_neg={int((y == 0).sum())}")
    return dots, surf


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--mode", choices=["holdout", "final"], required=True)
    ap.add_argument("--learner", choices=["hgb", "logreg"], default="hgb")
    ap.add_argument("--frac", type=float, default=FRAC)
    ap.add_argument("--seed", type=int, default=20261030)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--data-dir", type=Path, default=None)
    args = ap.parse_args()
    args.data_dir = args.data_dir or data_dir()
    if args.mode == "holdout":
        run_holdout(args)
    else:
        run_final(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
