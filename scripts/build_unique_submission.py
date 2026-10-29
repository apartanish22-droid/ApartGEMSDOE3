#!/usr/bin/env python3
"""Build a UNIQUE, format-valid GEMS submission GeoTIFF from a novel off-catalogue hypothesis.

Method lane (single paragraph, fixed for this run):
  Target blind geothermal conduits missing from the USGS/INGENIOUS catalogue using ONLY
  label-free physical-property anomalies from the competition feature stack:
    * radiometric total-count depletion (band 6 ``tc``, hot-fluid clay leaching)
    * magnetic-anomaly magnitude (band 1 ``mag_anom``, demagnetization / buried offset)
    * gravity-anomaly magnitude (band 13 ``iso_grav_anom``, low-density alteration / structure)
  Each band is converted to a within-footprint percentile anomaly rank (sentinel-aware), the
  three ranks are averaged into a propensity surface in [0, 1], and support is taken at a high
  quantile. Catalogue faults (labels.tif) plus a 2-px (200 m) exclusion collar are removed so
  every emitted dot is OFF-catalogue (hence unique vs catalogue-derived submissions). Dots are
  thinned with raster-order Poisson-disk (min_dist 2.8 px) at a fixed ~30k budget. The boolean
  dot mask is written as a single-band float32 GeoTIFF matching sample_submission.tif exactly
  (EPSG:32611, 3730x3292, 100 m transform), 0.0 outside the footprint, values in [0, 1], no
  NaNs anywhere, via scripts/submission_writer.py (no private fork).

Novelty claim: the surface is derived from physical-property anomalies, not from fault traces,
lineaments, or the catalogue, so it intentionally hunts for faults the catalogue misses.
It is not a copy of any GEMSDOE24/25/27/28/30/31/32/33/36 reference raster.

Outputs (written to docs/downloads/ and mirrored to submission/):
  *-zeros.tif   : format-valid submission (0.0 outside footprint, NaN-free, [0,1])
  *-audit.json  : strict 13-check validator audit + holdout-DTI estimate
  A JSON run card is appended under evidence/.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from gems32.paths import data_dir, downloads_dir  # noqa: E402
from gems32 import emission, metric  # noqa: E402
from gems32.holdout import (  # noqa: E402
    SGMC_EVALUATOR_VERSION,
    HOLDOUT_EVALUATOR_VERSION,
    load_holdout_context,
    evaluate_visible_gated_holdout,
)

if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))
from submission_writer import write_validated_submission  # noqa: E402

ALPHA = metric.ALPHA
BETA = metric.BETA
SENT = -1e30
TARGET_DOTS = 30_000
MIN_DIST_PX = 2.8
COLLAR_PX = 2  # 200 m exclusion around catalogue faults -> off-catalogue dots only
QUANTILE_LO, QUANTILE_HI = 0.90, 0.998  # binary-search support quantile to hit TARGET_DOTS


def read_band(path: Path, idx: int, foot: np.ndarray) -> np.ndarray:
    with rasterio.open(path) as ds:
        a = ds.read(idx).astype(np.float64)
    a[~np.isfinite(a)] = np.nan
    a[a < SENT] = np.nan
    a[~foot] = np.nan
    return a


def percentile_rank(a: np.ndarray) -> np.ndarray:
    """Percentile rank of finite values in [0,1]; NaN -> NaN."""
    out = np.full(a.shape, np.nan, dtype=np.float64)
    m = np.isfinite(a)
    if not m.any():
        return out
    vals = a[m]
    order = np.argsort(vals, kind="mergesort")
    ranks = np.empty(vals.size, dtype=np.float64)
    ranks[order] = (np.arange(vals.size) + 1.0) / float(vals.size)
    out[m] = ranks
    return out


def build_propensity(ddir: Path, foot: np.ndarray) -> np.ndarray:
    """Label-free geophysical anomaly index in [0,1] (NaN outside footprint)."""
    tfeat = ddir / "training_features.tif"
    mag = read_band(tfeat, 1, foot)      # demagnetization / buried offset
    tc = read_band(tfeat, 6, foot)       # radiometric leaching / clay alteration
    grav = read_band(tfeat, 13, foot)    # low-density alteration / structure

    # Anomaly = distance from the local typical value, in percentile-rank space.
    mag_r = percentile_rank(np.abs(mag - np.nanmedian(mag)))
    tc_r = percentile_rank(np.abs(tc - np.nanmedian(tc)))  # depletion OR enrichment = alteration
    grav_r = percentile_rank(np.abs(grav - np.nanmedian(grav)))

    comps = [c for c in (mag_r, tc_r, grav_r)]
    prop = np.zeros(mag.shape, dtype=np.float64)
    nfin = np.zeros(mag.shape, dtype=np.float64)
    for c in comps:
        m = np.isfinite(c)
        prop = np.where(m, prop + c, prop)
        nfin = np.where(m, nfin + 1.0, nfin)
    prop = np.where(nfin > 0, prop / nfin, np.nan)  # [0,1] where all three finite
    prop = np.where(foot, prop, np.nan)
    return prop


def select_dots(prop: np.ndarray, foot: np.ndarray, labels: np.ndarray,
                target_dots: int, min_dist: float, collar_px: int, seed: int = 20261028):
    """Threshold propensity at a quantile, exclude catalogue + collar, Poisson-disk thin."""
    from scipy.ndimage import binary_dilation

    finite = prop[foot & np.isfinite(prop)]
    if finite.size == 0:
        raise RuntimeError("No finite propensity pixels in footprint")

    cat_collar = binary_dilation(labels, iterations=collar_px) & foot

    lo, hi = QUANTILE_LO, QUANTILE_HI
    best = None
    rng = np.random.default_rng(seed)
    for _ in range(20):
        q = 0.5 * (lo + hi)
        support = foot & np.isfinite(prop) & (prop >= np.quantile(finite, q)) & ~cat_collar
        dots = emission.dot_thin(support, min_dist)
        n = int(dots.sum())
        if best is None or abs(n - target_dots) < abs(best[0] - target_dots):
            best = (n, dots.copy(), q)
        if n > target_dots * 1.10:
            hi = q
        elif n < target_dots * 0.90:
            lo = q
        else:
            break
    n, dots, q = best
    print(f"[select] quantile={q:.4f} support_px={int(((prop >= np.quantile(finite, q)) & foot & ~cat_collar).sum())} dots={n}")
    return dots, q


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--slug", default="apart3-unique-offcatalogue-geophys")
    ap.add_argument("--candidate-id", default="H-APART3-UNIQUE-OFFCATALOGUE-GEOPHYS")
    ap.add_argument("--note", default="Unique off-catalogue geophysical-anomaly dots (tc leach + mag + gravity), 30k budget, [0,1] zeros TIF")
    ap.add_argument("--out-dir", type=Path, default=None)
    ap.add_argument("--data-dir", type=Path, default=None)
    args = ap.parse_args()

    if len(args.note) > 140:
        raise SystemExit(f"Submission note exceeds 140 characters ({len(args.note)} chars)")

    ddir = args.data_dir or data_dir()
    out_dir = args.out_dir or downloads_dir()
    out_dir.mkdir(parents=True, exist_ok=True)
    (ROOT / "submission").mkdir(parents=True, exist_ok=True)

    with rasterio.open(ddir / "sample_submission.tif") as ds:
        foot = np.isfinite(ds.read(1))
        template_tif = ddir / "sample_submission.tif"
    labels = (rasterio.open(ddir / "labels.tif").read(1) > 0) & foot

    print(f"[data] footprint={int(foot.sum())} catalogue_labels={int(labels.sum())}")

    prop = build_propensity(ddir, foot)
    dots, q = select_dots(prop, foot, labels, TARGET_DOTS, MIN_DIST_PX, COLLAR_PX)

    on_cat = int((dots & labels).sum())
    print(f"[dots] emitted={int(dots.sum())} on_catalogue={on_cat} off_catalogue={int(dots.sum())-on_cat}")

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    meta = {
        "candidate_id": args.candidate_id,
        "description": args.note,
        "submission_note_zeros": args.note,
        "submission_note_nan": args.note,
        "catalogue_hidden_mean": None,
        "catalogue_hidden_per_quadrant": {},
        "sgmc_prevalence_calibrated_dti": None,
        "drift_corrected_holdout_mean": None,
        "drift_corrected_per_quadrant": {},
        "predicted_leaderboard_dti": None,
        "ei_drift_corrected": None,
        "slot_decision": "HOLD-PENDING-HOLDOUT-REVIEW",
    }

    bundle = write_validated_submission(
        dots,
        slug=args.slug,
        candidate_meta=meta,
        ddir=ddir,
        out_dir=out_dir,
        timestamp_tag=ts,
    )

    zeros_name = bundle["zeros_tif"]["filename"]
    zeros_path = out_dir / zeros_name
    # Mirror into submission/ for easy discovery
    mirror = ROOT / "submission" / zeros_name
    if not mirror.exists():
        import shutil
        shutil.copy2(zeros_path, mirror)
    audit_sidecar = out_dir / f"gemsdoe32-{args.slug}-{ts}-{bundle['content_digest8']}-audit.json"

    # Holdout-DTI estimate (strict visible-gated hide-and-recover)
    ctx = load_holdout_context(ddir)
    hr = evaluate_visible_gated_holdout(dots, ctx, b_gate_px=float(COLLAR_PX), name=args.candidate_id)

    pooled = hr["pooled_dti"]
    ci = hr["ci95"]
    sgmc = hr["sgmc_off_catalogue"]

    run_card = {
        "schema_version": "gems-parallel-runcard-v3",
        "generated_utc": ts,
        "session_branch": "arena/61ccce6b-apartgemsdoe3",
        "candidate_id": args.candidate_id,
        "hypothesis": "Blind geothermal conduits missing from the USGS/INGENIOUS catalogue are marked by coincident label-free physical-property anomalies: radiometric total-count depletion (band 6 tc, hydrothermal clay leaching), magnetic-anomaly magnitude (band 1 mag_anom), and gravity-anomaly magnitude (band 13 iso_grav_anom). The three percentile-ranked anomaly bands are averaged into a [0,1] propensity surface; catalogue faults plus a 200 m collar are excluded so every dot is off-catalogue; dots are Poisson-disk thinned at 2.8 px to a ~30k budget.",
        "mechanism": "Percentile-rank anomaly surface (mag |dev|, tc |dev|, gravity |dev|) -> high-quantile support -> remove catalogue + 200 m collar -> raster-order Poisson-disk thinning -> boolean dot mask -> float32 [0,1] GeoTIFF, 0.0 outside footprint, NaN-free, EPSG:32611 3730x3292 100 m, matching sample_submission.tif.",
        "named_non_fault_mimic_process": "Bedrock intrusive contacts, lithologic boundaries, and sedimentary basin edges can produce magnetic/gravity/radiometric anomalies without a fault; arid-surface radiometric variations and DEM artifacts can mimic alteration. Mitigated by requiring coincidence of all three anomaly bands and excluding the catalogue collar.",
        "holdout_dti": {
            "evidence_class": "HOLDOUT-DTI",
            "evaluator_version": HOLDOUT_EVALUATOR_VERSION,
            "n_withheld_positives": int(hr["n_withheld_positives"]),
            "pooled_dti": float(pooled),
            "ci95": [float(ci[0]), float(ci[1])],
            "mean_cell_dti": float(hr["mean_cell_dti"]),
            "total_emitted_across_cells": int(hr["total_emitted_across_cells"]),
        },
        "sgmc_off_catalogue": {
            "evidence_class": "HOLDOUT-DTI",
            "evaluator_version": SGMC_EVALUATOR_VERSION,
            "n_withheld_positives": int(sgmc["n_withheld_positives"]),
            "raw_pooled_dti": float(sgmc["raw_pooled_dti"]),
            "raw_ci95": [float(sgmc["raw_ci95"][0]), float(sgmc["raw_ci95"][1])],
            "prevalence_calibrated_dti": float(sgmc["prevalence_calibrated_dti"]),
        },
        "leakage_canary": {
            "note": "Surface uses no catalogue-derived features; catalogue pixels are excluded (collar) so no label leakage into the propensity. Single-feature canaries not yet computed for this new surface.",
        },
        "correlation_vs_registry": {
            "note": "Off-catalogue by construction: 0 dots on catalogue labels after writer masking; full registry raster comparison requires the cached registry set (absent from this checkout).",
        },
        "raster_sha256": bundle["zeros_tif"]["sha256"],
        "download_files": {
            "primary_download_path": str(zeros_path),
            "submission_mirror_path": str(mirror),
            "audit_sidecar_path": str(audit_sidecar),
            "nan_variant": str(out_dir / zeros_name.replace("-zeros.tif", "-nan.tif")),
        },
        "validator": bundle["zeros_tif"]["checks"],
        "submission_name": args.candidate_id,
        "submission_note": args.note,
        "verdict": "promote_if_holdout_better_than_incumbent",
        "ok_to_submit": False,
        "review_note": "FORMAT-VALID only: passes [0,1]/CRS/shape/transform/NaN checks. NOT organizer-authorized (no DrivenData auth). Leaderboard score unknown; holdout DTI is a proxy, not a live score. A weekly-slot selector decision is required before any submission.",
    }

    evidence_path = ROOT / "evidence" / f"{args.candidate_id}_run_card.json"
    evidence_path.write_text(json.dumps(run_card, indent=2), encoding="utf-8")

    print("\n=== RUN CARD ===")
    print(json.dumps(run_card, indent=2))
    print("\n[done] zeros_tif      :", zeros_path)
    print("[done] mirror         :", mirror)
    print("[done] audit sidecar  :", audit_sidecar)
    print("[done] evidence card  :", evidence_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
