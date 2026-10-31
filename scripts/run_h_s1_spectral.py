#!/usr/bin/env python3
"""H-S1 experiment driver (2026-10-31): spectral roll-off line-integral candidate.

Pre-registered in docs/research/h-candidates-20261031.md. Uses the shared tools only:
  - gems32.spectral_rolloff (method; surface only, label-free)
  - gems32.emission.dot_thin_matched (dot layout, fixed target count = champion's 37,654)
  - gems32.holdout (hide-and-recover context for the feature canary)
  - scripts/evaluate_holdout.py (HOLDOUT-DTI, evaluator GEMSDOE32-HIDE-RECOVER-v3.0 and SGMC-CAL)
  - scripts/submission_writer.py (writes the validated single-band float32 GeoTIFF, zeros outside)

Writes:
  docs/downloads/<name>.tif (+ .zip) and evidence/H-S1-SPECTRAL-ROLLOFF_run_card.json
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems32 import emission, holdout, spectral_rolloff  # noqa: E402
from gems32.paths import data_dir  # noqa: E402

N_DOTS = 37654          # same count as the champion family, so the comparison is at equal mass
MIN_DIST = 2.8          # px, same Poisson-disk rule as the shared emitter
SLUG = "h-specroll-h1"
NOTE = "H-S1 spectral roll-off line integral, 37654 dots, 100m, no catalogue input, NaN-free"
TS = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _load_writer():
    spec = importlib.util.spec_from_file_location("submission_writer", ROOT / "scripts" / "submission_writer.py")
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def _load_eval():
    spec = importlib.util.spec_from_file_location("evaluate_holdout", ROOT / "scripts" / "evaluate_holdout.py")
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canary_auc(values: np.ndarray, ctx, stride: int = 4) -> float:
    """Single-feature leakage canary on the hide-and-recover holdout (seed-20 draw), two-polarity."""
    pos_mask = np.zeros(ctx.foot.shape, dtype=bool)
    neg_mask = np.zeros(ctx.foot.shape, dtype=bool)
    for cell in ctx.cells:
        if cell.seed != 20:
            continue
        sl = cell.bbox
        sub_t = np.zeros(cell.active_sub.shape, dtype=bool)
        sub_t[cell.truth_coords] = True
        pos_mask[sl] |= sub_t
        neg_mask[sl] |= cell.active_sub & ~sub_t
    py, px = np.nonzero(pos_mask)
    ny, nx = np.nonzero(neg_mask)
    ny, nx = ny[::stride], nx[::stride]
    y = np.concatenate([np.ones(py.size, dtype=np.int8), np.zeros(ny.size, dtype=np.int8)])
    v = np.concatenate([values[py, px], values[ny, nx]]).astype(np.float64)
    v = np.nan_to_num(v, nan=0.0, posinf=0.0, neginf=0.0)
    if np.ptp(v) <= 1e-12:
        return 0.5
    auc = float(roc_auc_score(y, v))
    return max(auc, 1.0 - auc)


def eta_squared(values: np.ndarray, groups: np.ndarray, valid: np.ndarray) -> float:
    """Between-group share of variance (flight-line / acquisition-block artefact control)."""
    v = values[valid]
    g = groups[valid]
    if v.size == 0:
        return float("nan")
    mu = v.mean()
    ss_tot = float(((v - mu) ** 2).sum())
    labels, inv = np.unique(g, return_inverse=True)
    sums = np.bincount(inv, weights=v)
    counts = np.bincount(inv)
    ss_between = float((counts * ((sums / counts) - mu) ** 2).sum())
    return ss_between / ss_tot if ss_tot > 0 else float("nan")


def main() -> int:
    ddir = data_dir()
    with rasterio.open(ddir / "sample_submission.tif") as ds:
        foot = np.isfinite(ds.read(1))
    with rasterio.open(ddir / "labels.tif") as ds:
        labels = (ds.read(1) > 0) & foot

    out = spectral_rolloff.compute_surface(ddir / "training_features.tif", foot)
    surf = out["surface"]
    z = out["flatness_z"]
    rtp = out["rtp"]

    # Dot layout: footprint-only, fixed count, Poisson-disk thinning (shared emitter)
    dots = emission.dot_thin_matched(np.where(foot, surf, 0.0), N_DOTS, foot, min_dist=MIN_DIST)
    n_dots_pre_labels = int(dots.sum())
    dots_out = dots & foot & ~labels
    n_dots = int(dots_out.sum())

    # Feature-alone leakage canary on the hide-and-recover holdout
    ctx = holdout.load_holdout_context(ddir)
    rtp_fill = np.where(out["valid_residual"], rtp, 0.0)
    canaries = {
        "rtp_band2_raw": canary_auc(rtp_fill, ctx),
        "spectral_flatness_z": canary_auc(np.nan_to_num(z, nan=0.0), ctx),
        "h_s1_surface": canary_auc(surf, ctx),
    }

    # Mimic controls: acquisition-block artefact share and amplitude dependence
    blk_path = ddir / "external" / "acquisition_block_id_100m.tif"
    with rasterio.open(blk_path) as ds:
        blk = ds.read(1)
    eta_block = eta_squared(surf, blk, foot)
    amp = np.abs(out["rtp"] - np.nanmean(out["rtp"][foot]))
    amp_std = np.where(foot, np.nan_to_num(amp, nan=0.0), 0.0)
    from scipy.stats import spearmanr

    sub = np.flatnonzero(foot.ravel())[:: max(1, int(foot.sum()) // 200000)]
    rho_amp = float(spearmanr(surf.ravel()[sub], amp_std.ravel()[sub]).statistic)

    # Write the candidate through the shared writer
    writer = _load_writer()
    prob = dots_out.astype(np.float32)
    meta = {
        "candidate_id": "H-S1-SPECTRAL-ROLLOFF",
        "description": "H-S1 oriented line-integral of local magnetic spectral roll-off (rtp only)",
        "submission_note_zeros": NOTE,
        "submission_note_nan": NOTE,
        "slot_decision": "HOLD-DO-NOT-SUBMIT",
    }
    bundle = writer.write_validated_submission(prob, slug=SLUG, candidate_meta=meta, ddir=ddir,
                                               out_dir=ROOT / "docs" / "downloads", timestamp_tag=TS)
    zeros_path = ROOT / "docs" / "downloads" / bundle["zeros_tif"]["filename"]

    # Holdout evaluation of the saved bytes, with the shared evaluator
    ev = _load_eval()
    hold = ev.evaluate_path(zeros_path, b_visible_px=0.0, ddir=ddir, name="H-S1-SPECTRAL-ROLLOFF")

    # Mirror of the champion evaluation for paired comparison (same evaluator, same context)
    champ = ev.evaluate_path(ROOT / "docs" / "downloads" / "gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif",
                             b_visible_px=0.0, ddir=ddir, name="GEMSDOE32-champion")

    card = {
        "run_id": f"H-S1-SPECTRAL-ROLLOFF-{TS}",
        "date_utc": TS,
        "lane": "NOT ASSIGNED (no method paragraph in prompt or checkout). Self-declared research run; cannot be cleared for a weekly slot.",
        "hypothesis": "Oriented 2-km line integrals of the local flatness anomaly of the 3.2-km-window magnetic (rtp) power-spectrum slope mark linear damage-zone texture not visible as edges.",
        "mechanism": "Fracture damage zones add high-wavenumber power, flattening the local spectral slope; the 8-orientation max-of-line-means keeps only linear responses.",
        "named_non_fault_mimic": "Magnetite-heterogeneous lithology and GeoDAWN flight-line artefacts (controlled by acquisition-block eta-squared and rtp-amplitude Spearman, below).",
        "single_feature_canary_auc_holdout_seed20": canaries,
        "canary_threshold": 0.90,
        "canary_passed": bool(max(canaries.values()) <= 0.90),
        "controls": {
            "acquisition_block_eta_squared_surface": eta_block,
            "spearman_surface_vs_rtp_amplitude": rho_amp,
        },
        "surface_stats": {
            "n_windows_total": out["n_windows_total"],
            "n_windows_valid": out["n_windows_valid"],
            "surface_min": float(surf[foot].min()),
            "surface_max": float(surf[foot].max()),
            "surface_all_finite_in_footprint": bool(np.isfinite(surf[foot]).all()),
        },
        "dots_before_label_mask": n_dots_pre_labels,
        "dots_after_label_mask": n_dots,
        "candidate_file": str(zeros_path.relative_to(ROOT)),
        "candidate_sha256": sha256(zeros_path),
        "candidate_zip": bundle.get("zeros_zip", {}).get("filename"),
        "submission_name": SLUG.upper(),
        "submission_note": NOTE,
        "note_chars": len(NOTE),
        "validator": bundle.get("zeros_tif", {}).get("audit", bundle.get("zeros_tif", {}).get("validator", "see bundle")),
        "holdout_candidate": hold,
        "holdout_champion_GEMSDOE32": champ,
        "score_label": "HOLDOUT-DTI (evaluator GEMSDOE32-HIDE-RECOVER-v3.0 and GEMSDOE32-SGMC-CAL-v3.0). Live score: NOT ESTIMABLE.",
        "verdict": "pending_gates",
    }
    out_path = ROOT / "evidence" / "H-S1-SPECTRAL-ROLLOFF_run_card.json"
    out_path.write_text(json.dumps(card, indent=2, default=float) + "\n")
    print(json.dumps({k: card[k] for k in ("candidate_file", "candidate_sha256", "dots_after_label_mask",
                                          "single_feature_canary_auc_holdout_seed20", "controls")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
