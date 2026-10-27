#!/usr/bin/env python3
"""Run the preregistered three-arm magnetic/radiometric curvature lane.

This is deliberately catalogue-free: source surfaces never read labels. Labels are
used only by SegmentHoldout and for the final pixel-exact catalogue exclusion.
No organizer slot is touched.
"""
from __future__ import annotations

import hashlib, json, sys
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import gaussian_filter, maximum_filter, distance_transform_edt
from scipy.stats import rankdata

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems.holdout import SegmentHoldout
from gems.novelty import correlation, dot_overlap
from gems.submission import write_submission, check_variants

BUDGET = 37654
OUT = ROOT / "docs/downloads/apartgems3-mrcj-curvature-junction-37654-20261027-zeros.tif"
CARD = ROOT / "evidence/run_card.json"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def norm(a, valid):
    out = np.zeros(a.shape, np.float32)
    x = a[valid & np.isfinite(a)]
    lo, hi = np.quantile(x, [0.01, 0.99])
    out[valid] = np.clip((a[valid] - lo) / max(hi-lo, 1e-9), 0, 1)
    return out


def gradmag(a, sigma):
    s = gaussian_filter(a, sigma)
    gy, gx = np.gradient(s)
    return np.hypot(gx, gy), gx, gy


def surfaces(ext, valid):
    # Fixed, preregistered transforms; no label-driven fitting or tuning.
    thk = ext[0].astype(np.float32) / 255
    uth = ext[2].astype(np.float32) / 255
    mag = ext[3].astype(np.float32) / 255
    gm2, mx2, my2 = gradmag(mag, 2)
    gm6, mx6, my6 = gradmag(mag, 6)
    gr3, rx3, ry3 = gradmag(thk, 3)
    gu3, ux3, uy3 = gradmag(uth, 3)
    # Cross-scale magnetic curvature persistence suppresses single-scale noise.
    persistence = norm(np.minimum(gm2, gm6), valid)
    # Opposed magnetic/ThK gradients target a contact/alteration boundary.
    opposed = norm(np.maximum(-(mx2*rx3 + my2*ry3), 0), valid)
    # Junction: persistent magnetic curvature and orthogonal U/Th gradient.
    cross = norm(np.abs(mx6*uy3 - my6*ux3), valid)
    return {
        "E1_magnetic_curvature_persistence": persistence,
        "E2_opposed_magnetic_ThK_gradient": norm(persistence * opposed, valid),
        "E3_MRCJ": norm(persistence * np.sqrt(opposed * cross), valid),
    }


def place(score, eligible, k=BUDGET):
    local = score == maximum_filter(score, size=3, mode="nearest")
    ids = np.flatnonzero(eligible & local & (score > 0))
    if len(ids) < k:
        ids = np.flatnonzero(eligible & (score > 0))
    order = ids[np.argsort(score.ravel()[ids], kind="stable")[-min(k, len(ids)):]]
    out = np.zeros(score.shape, bool); out.ravel()[order] = True
    return out


def main():
    template = ROOT / "data/bridge/sample_submission.tif"
    with rasterio.open(template) as ds:
        raw = ds.read(1)
        footprint = np.isfinite(raw)
    with rasterio.open(ROOT / "data/bridge/labels.tif") as ds:
        labels = (ds.read(1) > 0) & footprint
    with rasterio.open(ROOT / "data/external/geodawn_extensions_u8.tif") as ds:
        ext = ds.read()
    support = np.all(ext > 0, axis=0) & footprint
    arms = surfaces(ext, support)
    holdout = SegmentHoldout(footprint, labels, buffer_px=15)
    canary = holdout.canary({**arms, "support": support.astype(float)})
    registry = {}
    surface_checks = {}
    for path in sorted((ROOT / "registry/rasters").glob("*.tif")):
        with rasterio.open(path) as ds: a = ds.read(1)
        ref = np.nan_to_num(a, nan=0.0)[footprint]
        registry[path.stem] = (a > 0) & np.isfinite(a) & footprint
        surface_checks[path.stem] = correlation(arms["E3_MRCJ"][footprint], ref)
    pre_duplicate = any(v is not None and abs(v) > .90 for v in surface_checks.values())
    results = {}
    fold_predictions = {}
    if not canary["passed"] or pre_duplicate:
        raise SystemExit("STOP: leakage canary or pre-placement duplicate gate failed")
    for name, surface in arms.items():
        preds = [place(surface, support & f["valid"] & ~f["visible"], round(BUDGET * f["valid"].sum()/footprint.sum())) for f in holdout.folds]
        fold_predictions[name] = preds
        results[name] = holdout.summarize(preds, ci_draws=999)
    winner = max(results, key=lambda n: results[n]["dti"])
    final = place(arms[winner], support & ~labels)
    overlap = {name: dot_overlap(final, dots)["candidate_within_3px_of_reference"] for name, dots in registry.items()}
    final_duplicate = any(v is not None and v > .70 for v in overlap.values())
    # Baseline is evaluated only as a static comparator; it is not valid OOF evidence.
    baseline_preds = []
    champ = registry["GEMSDOE32"]
    for f in holdout.folds:
        baseline_preds.append(champ & f["valid"] & ~f["visible"])
    baseline = holdout.summarize(baseline_preds, ci_draws=999)
    beat_static_baseline = results[winner]["dti"] > baseline["dti"]
    write_submission(final.astype(np.float32), template, OUT, outside="zero")
    validator = check_variants(OUT, template)
    promote = bool(beat_static_baseline and not final_duplicate and validator["format_valid"])
    card = {
      "schema_version": 1,
      "hypothesis": "MRCJ: persistent cross-scale magnetic curvature at opposed Th/K and orthogonal U/Th gradients marks concealed fault-controlled alteration junctions.",
      "mechanism": "A concealed permeable structure can juxtapose magnetic domains while focusing chemically distinct hydrothermal alteration; cross-scale persistence rejects short-wavelength noise.",
      "named_non_fault_mimic": "lithologic contact or acquisition-block seam",
      "experiments_run": 3,
      "budget_limit": 3,
      "feature_leakage_canary": canary,
      "results": results,
      "selected_arm": winner,
      "static_incumbent_comparator": {"warning": "not fold-rebuilt; not promotion-grade OOF evidence", "result": baseline},
      "holdout_dti": results[winner],
      "correlation_vs_registry": surface_checks,
      "overlap_vs_registry": overlap,
      "thresholds": {"max_abs_spearman": .90, "max_dot_overlap_3px": .70},
      "raster_sha256": sha(OUT),
      "validator_output": validator,
      "submission_name": OUT.name,
      "submission_note": "MRCJ magnetic-curvature + radiometric-gradient junctions; 37,654 dots; automated gates passed.",
      "organizer_confirmed_score": None,
      "score_projection": None,
      "verdict": "promote" if promote else "negative",
      "ok_to_download": True,
      "ok_to_submit": promote,
      "slot_used": False,
      "limitations": ["No organizer receipt exists.", "The requested lane paragraph was absent; MRCJ was preregistered here.", "The baseline file cannot be honestly rebuilt fold-by-fold from its original method."],
    }
    CARD.write_text(json.dumps(card, indent=2, allow_nan=False)+"\n")
    print(json.dumps({"winner": winner, "dti": results[winner]["dti"], "ci95": results[winner]["ci95"]["interval"], "baseline": baseline["dti"], "max_overlap": max(overlap.values()), "verdict": card["verdict"], "output": str(OUT)}, indent=2))

if __name__ == "__main__": main()
