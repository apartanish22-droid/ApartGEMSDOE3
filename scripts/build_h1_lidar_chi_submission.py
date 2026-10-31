#!/usr/bin/env python3
"""Build a UNIQUE, format-valid GEMS submission from H1: LiDAR scarp + DEM10 chi.

Method lane (single paragraph):
  Target blind geothermal conduits missing from the USGS/INGENIOUS catalogue by requiring
  coincidence of two label-free physical signatures: (1) LiDAR-derived scarp/edge strength
  (external/lidar_scarp_features_u8.tif) marking metre-scale fault-line scarps, and
  (2) 10 m DEM stream-power chi anomaly (external/dem10_chi_100m_i16.tif) marking
  knickzones from active tilting. Each band is converted to a within-footprint percentile
  rank (sentinel-aware), multiplied into a coincidence propensity in [0, 1], and support is
  taken at a high quantile. Catalogue faults (labels.tif) plus a 2-px (200 m) exclusion
  collar are removed so every emitted dot is OFF-catalogue. Dots are thinned with
  raster-order Poisson-disk (min_dist 2.8 px) at a fixed ~30k budget via the template's
  emission.dot_thin (no private fork). The boolean dot mask is written as a single-band
  float32 GeoTIFF matching sample_submission.tif exactly (EPSG:32611, 3730x3292, 100 m
  transform), 0.0 outside the footprint, values in [0, 1], no NaNs anywhere, via
  scripts/submission_writer.py.

Novelty: no existing submission combines LiDAR scarp edge strength with DEM chi. The
surface is derived from topographic fault geomorphology, not fault traces, lineaments, or
the catalogue, so it intentionally hunts for faults the catalogue misses. Not a copy of any
GEMSDOE24/25/27/28/30/31/32/33/36 reference raster.

Outputs:
  *-zeros.tif   : format-valid submission (0.0 outside footprint, NaN-free, [0,1])
  *-nan.tif     : NaN outside footprint variant
  *-audit.json  : strict validator audit + holdout-DTI estimate
  evidence/H1-..._run_card.json : JSON run card (protocol rule 5)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from gems32.paths import data_dir, downloads_dir, evidence_dir  # noqa: E402
from gems32 import emission  # noqa: E402
from gems32.holdout import (  # noqa: E402
    SGMC_EVALUATOR_VERSION,
    HOLDOUT_EVALUATOR_VERSION,
    load_holdout_context,
    evaluate_visible_gated_holdout,
)

if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))
from submission_writer import write_validated_submission  # noqa: E402

SENT = -1e30
TARGET_DOTS = 30_000
MIN_DIST_PX = 2.8
COLLAR_PX = 2  # 200 m exclusion around catalogue faults -> off-catalogue dots only
QUANTILE_LO, QUANTILE_HI = 0.90, 0.998


def read_band(path: Path, idx: int, foot: np.ndarray) -> np.ndarray:
    with rasterio.open(path) as ds:
        a = ds.read(idx).astype(np.float64)
    a[~np.isfinite(a)] = np.nan
    a[a < SENT] = np.nan
    a[~foot] = np.nan
    return a


def percentile_rank(a: np.ndarray) -> np.ndarray:
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


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--slug", default="h1-lidar-scarp-dem-chi")
    ap.add_argument("--candidate-id", default="H1-LIDAR-SCARP-DEM-CHI")
    ap.add_argument("--note", default="H1 LiDAR scarp + DEM10 chi blind-fault dots, 30k, off-catalogue, [0,1] zeros TIF")
    ap.add_argument("--out-dir", type=Path, default=None)
    ap.add_argument("--data-dir", type=Path, default=None)
    args = ap.parse_args()

    if len(args.note) > 140:
        raise SystemExit(f"Submission note exceeds 140 characters ({len(args.note)} chars)")

    ddir = args.data_dir or data_dir()
    out_dir = args.out_dir or downloads_dir()
    out_dir.mkdir(parents=True, exist_ok=True)
    (ROOT / "submission").mkdir(parents=True, exist_ok=True)
    evidence_dir().mkdir(parents=True, exist_ok=True)

    with rasterio.open(ddir / "sample_submission.tif") as ds:
        foot = np.isfinite(ds.read(1))
        template_tif = ddir / "sample_submission.tif"
    labels = (rasterio.open(ddir / "labels.tif").read(1) > 0) & foot

    print(f"[data] footprint={int(foot.sum())} catalogue_labels={int(labels.sum())}")

    # --- Build H1 propensity surface ---
    lidar = read_band(ddir / "external" / "lidar_scarp_features_u8.tif", 1, foot)
    chi = read_band(ddir / "external" / "dem10_chi_100m_i16.tif", 1, foot)

    print(f"[lidar] finite={int(np.isfinite(lidar).sum())} max={np.nanmax(lidar):.1f}")
    print(f"[chi]   finite={int(np.isfinite(chi).sum())} max={np.nanmax(chi):.1f}")

    lidar_r = percentile_rank(lidar)
    chi_r = percentile_rank(chi)

    # Coincidence: both must be high. Multiply ranks so low in either suppresses.
    prop = np.zeros(lidar.shape, dtype=np.float64)
    m = np.isfinite(lidar_r) & np.isfinite(chi_r)
    prop[m] = lidar_r[m] * chi_r[m]
    prop = np.where(foot & m, prop, np.nan)

    finite_prop = prop[foot & np.isfinite(prop)]
    print(f"[prop] finite px={int(finite_prop.size)} max={finite_prop.max():.4f}")

    # --- Select dots via template dot_thin (binary search quantile for target count) ---
    from scipy.ndimage import binary_dilation

    cat_collar = binary_dilation(labels, iterations=COLLAR_PX) & foot
    lo, hi = QUANTILE_LO, QUANTILE_HI
    best = None
    for _ in range(24):
        q = 0.5 * (lo + hi)
        support = foot & np.isfinite(prop) & (prop >= np.quantile(finite_prop, q)) & ~cat_collar
        dots = emission.dot_thin(support, MIN_DIST_PX)
        n = int(dots.sum())
        if best is None or abs(n - TARGET_DOTS) < abs(best[0] - TARGET_DOTS):
            best = (n, dots.copy(), q)
        if n > TARGET_DOTS * 1.10:
            hi = q
        elif n < TARGET_DOTS * 0.90:
            lo = q
        else:
            break
    n, dots, q = best
    print(f"[select] quantile={q:.4f} support_px={int(((prop >= np.quantile(finite_prop, q)) & foot & ~cat_collar).sum())} dots={n}")

    on_cat = int((dots & labels).sum())
    print(f"[dots] emitted={n} on_catalogue={on_cat} off_catalogue={n - on_cat}")

    # --- Write validated submission ---
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
        dots, slug=args.slug, candidate_meta=meta, ddir=ddir, out_dir=out_dir, timestamp_tag=ts
    )

    zeros_name = bundle["zeros_tif"]["filename"]
    zeros_path = out_dir / zeros_name
    mirror = ROOT / "submission" / zeros_name
    if not mirror.exists():
        shutil.copy2(zeros_path, mirror)

    # --- Holdout-DTI evaluation (strict visible-gated hide-and-recover) ---
    ctx = load_holdout_context(ddir)
    hr = evaluate_visible_gated_holdout(dots, ctx, b_gate_px=float(COLLAR_PX), name=args.candidate_id)

    pooled = hr["pooled_dti"]
    ci = hr["ci95"]
    sgmc = hr["sgmc_off_catalogue"]

    run_card = {
        "schema_version": "gems-parallel-runcard-v3",
        "generated_utc": ts,
        "session_branch": "arena/d20ee5aa-apartgemsdoe3",
        "lane": "H1 - LiDAR scarp + DEM10 chi coincidence surface, off-catalogue dots",
        "candidate_id": args.candidate_id,
        "hypothesis": "Blind geothermal conduits missing from the USGS/INGENIOUS catalogue are marked by coincident LiDAR scarp edge strength (metre-scale fault-line scarps) and DEM10 stream-power chi anomaly (knickzones from active tilting). Requiring both catches faults with recent surface displacement absent from the catalogue.",
        "mechanism": "Percentile-rank lidar_scarp_features * percentile-rank dem10_chi -> [0,1] coincidence propensity -> high-quantile support -> remove catalogue + 200 m collar -> Poisson-disk thin 2.8 px -> ~30k boolean dots -> float32 [0,1] GeoTIFF, 0.0 outside footprint, NaN-free, EPSG:32611 3730x3292 100 m, matching sample_submission.tif.",
        "named_non_fault_mimic_process": "Relict landslide scarps, terrace risers, and lithologic channel knickzones can produce scarps or high chi without a fault. Mitigated by requiring coincidence of both signatures and excluding the catalogue collar.",
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
            "note": "Propensity uses no catalogue-derived features; catalogue pixels excluded via collar. Single-feature canary: scarp-only and chi-only surfaces each scored separately on holdout; AUC > 0.90 would indicate leakage (required before promotion).",
        },
        "correlation_vs_registry": {
            "note": "Off-catalogue by construction: 0 dots on catalogue labels after writer masking. Full registry raster comparison (Spearman <= 0.90, <=70% within 3 px) requires the cached registry set; pairwise check vs the nine focus files is in evidence/focus_site_evaluation_*.json.",
        },
        "raster_sha256": bundle["zeros_tif"]["sha256"],
        "download_files": {
            "primary_download_path": str(zeros_path),
            "submission_mirror_path": str(mirror),
            "audit_sidecar_path": str(out_dir / f"gemsdoe32-{args.slug}-{ts}-{bundle['content_digest8']}-audit.json"),
            "nan_variant": str(out_dir / zeros_name.replace("-zeros.tif", "-nan.tif")),
        },
        "validator": bundle["zeros_tif"]["checks"],
        "submission_name": args.candidate_id,
        "submission_note": args.note,
        "verdict": "promote_if_holdout_and_sgmc_pass",
        "ok_to_submit": False,
        "review_note": "FORMAT-VALID only: passes [0,1]/CRS/shape/transform/NaN checks. NOT organizer-authorized. Leaderboard score unknown; holdout DTI and SGMC cal are proxies, not live scores. Weekly-slot selector decision required before any submission.",
    }

    evidence_path = evidence_dir() / f"{args.candidate_id}_run_card.json"
    evidence_path.write_text(json.dumps(run_card, indent=2), encoding="utf-8")

    print("\n=== RUN CARD ===")
    print(json.dumps(run_card, indent=2))
    print("\n[done] zeros_tif      :", zeros_path)
    print("[done] mirror         :", mirror)
    print("[done] audit sidecar  :", out_dir / f"gemsdoe32-{args.slug}-{ts}-{bundle['content_digest8']}-audit.json")
    print("[done] evidence card  :", evidence_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
