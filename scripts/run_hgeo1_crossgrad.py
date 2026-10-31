#!/usr/bin/env python3
"""Experiment 2: H-GEO-1 Cross-gradient tensor curvature of gravity and magnetics for concealed fault relays.

Lane (single method paragraph):
  Concealed basement step-over / relay detection: cross-gradient vector discordance
  grad(g) x grad(m) between Bouguer gravity (band 5 iso_grav_anom_slope gradient) and
  magnetics (band 2 rtp gradient), combined with the minimum principal curvature of the
  residual gravity field, masked to off-catalogue ground (B >= 2 px from labels.tif) and
  packed to 37,654 dots at matched mass. Targets basement density/magnetization contact
  curvature beneath 50-200 m of Quaternary alluvium where no surface scarp exists.

Hypothesis registry position: H-GEO-1 (rank 3 of prior round-6 shortlist), registered but
only partially evaluated; not yet run as a standalone emission on the canonical v3 holdout.
All bands on disk; no external data.

Mechanism: where a fault offsets pre-Cenozoic basement, density and magnetization interfaces
are displaced in different directions; their gradient vectors become discordant (cross-gradient
magnitude spikes) exactly at concealed contacts/relay ramps that a surface catalogue misses.

Named non-fault mimic: un-faulted buried volcanic flow margins / dikes and lithologic contacts
that also produce coincident gravity-magnetic gradients without a fault.

Differs from repo: prior arms used 1D gradient magnitudes or scalar tilt; none computed the
cross-gradient vector product grad(g) x grad(m) as a structural discordance field.

Leakage canary: bands 2 and 5 only; nothing derived from labels.tif.
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems32 import holdout, emission
from gems32.paths import data_dir, downloads_dir, evidence_dir
from gems32.grid import read_footprint, read_labels, read_band, NODATA_F32

DDIR = data_dir()
N_TARGET = 37654
B_GATE_PX = 2.0
MIN_DIST = 2.8


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _fill_nearest(raw, valid):
    filled = raw.astype(np.float32, copy=True)
    bad = ~valid
    if bad.any():
        _, idx = ndimage.distance_transform_edt(~valid, return_distances=True, return_indices=True)
        filled[bad] = filled[idx[0][bad], idx[1][bad]]
    return filled


def _valid(a):
    return np.isfinite(a) & (a > NODATA_F32 * np.float32(0.5))


def build_field(features_path, foot):
    with rasterio.open(features_path) as s:
        grav = s.read(5).astype(np.float32)   # iso_grav_anom_slope
        mag = s.read(2).astype(np.float32)    # rtp
    gv, mv = _valid(grav), _valid(mag)
    grav = _fill_nearest(grav, gv)
    mag = _fill_nearest(mag, mv)
    # Gradients of the two potential fields.
    gg = ndimage.gaussian_gradient_magnitude(grav, 1.5, mode="nearest").astype(np.float32)
    mg = ndimage.gaussian_gradient_magnitude(mag, 1.5, mode="nearest").astype(np.float32)
    # Cross-gradient discordance: gradient vectors point in different directions.
    gx, gy = np.gradient(grav); mx, my = np.gradient(mag)
    cross = np.abs(gx * my - gy * mx).astype(np.float32)
    # Minimum principal curvature of residual gravity (Hessian smaller |eigenvalue|).
    axx = ndimage.gaussian_filter(grav, 1.0, order=(0, 2), mode="nearest")
    ayy = ndimage.gaussian_filter(grav, 1.0, order=(2, 0), mode="nearest")
    axy = ndimage.gaussian_filter(grav, 1.0, order=(1, 1), mode="nearest")
    tmp = np.sqrt(np.maximum(((axx - ayy) * 0.5) ** 2 + axy ** 2, 0.0))
    l1 = (axx + ayy) * 0.5 + tmp; l2 = (axx + ayy) * 0.5 - tmp
    small = np.where(np.abs(l1) >= np.abs(l2), l2, l1)
    mincurv = np.abs(small).astype(np.float32)
    field = cross * (1.0 + mincurv) * (1.0 + gg) * (1.0 + mg)
    return np.where(foot, field, 0.0).astype(np.float32)


def main() -> int:
    features_path = DDIR / "training_features.tif"
    labels_path = DDIR / "labels.tif"
    with rasterio.open(DDIR / "sample_submission.tif") as ds:
        foot = np.isfinite(ds.read(1))
    labels = read_labels(labels_path) & foot
    ctx = holdout.load_holdout_context(DDIR)
    field = build_field(features_path, foot)
    d_cat = ndimage.distance_transform_edt(~labels)
    support = foot & (field > 0.0) & (d_cat > B_GATE_PX)
    print(f"support pixels: {int(support.sum()):,}")
    vals = field[support]
    lo, hi = 0.0, 1.0
    best = None
    for _ in range(20):
        q = 0.5 * (lo + hi)
        tau = np.quantile(vals, 1.0 - q)
        sup = support & (field >= tau)
        m = emission.dot_thin(sup, MIN_DIST)
        n = int(m.sum())
        if best is None or abs(n - N_TARGET) < abs(best[0] - N_TARGET):
            best = (n, m.copy(), tau)
        if n > N_TARGET * 1.05:
            hi = q
        elif n < N_TARGET * 0.95:
            lo = q
        else:
            break
    n, mask, tau = best
    print(f"emitted dots: {n:,}  tau={tau:.6f}  on-catalogue px: {int((mask & labels).sum())}")
    res = holdout.evaluate_hide_and_recover(mask, ctx, b_visible_px=0.0, name="H-GEO-1-crossgrad")
    pooled = res["pooled_dti"]; ci = res["ci95_cluster_bootstrap"]
    print(f"HOLDOUT-DTI pooled={pooled:.6f} ci95=[{ci[0]:.6f},{ci[1]:.6f}] n_withheld={res['n_withheld_positives']:,}")
    incumbent = 0.0045154
    beats = pooled > incumbent
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    slug = f"hgeo1-crossgrad-{N_TARGET}d"
    out_dir = downloads_dir()
    digest8 = hashlib.sha256(np.packbits(mask > 0.5)).hexdigest()[:8]
    zeros_name = f"gemsdoe32-{slug}-{ts}-{digest8}-zeros.tif"
    zeros_path = out_dir / zeros_name
    with rasterio.open(DDIR / "sample_submission.tif") as tpl:
        profile = tpl.profile.copy()
    profile.update(driver="GTiff", dtype="float32", count=1, compress="deflate", predictor=3,
                   zlevel=9, tiled=True, blockxsize=256, blockysize=256, nodata=None)
    arr = np.where(foot, np.clip(mask.astype(np.float32), 0.0, 1.0), 0.0).astype(np.float32)
    with rasterio.open(zeros_path, "w", **profile) as dst:
        dst.write(arr, 1)
    from gemsdoe32.submission import validate_submission_geotiff
    report = validate_submission_geotiff(zeros_path, DDIR / "sample_submission.tif", strict_whole_array_finite=True)
    fmt_ok = bool(report.passed)
    print(f"format audit: {'PASS' if fmt_ok else 'FAIL'}")
    verdict = "promote" if (beats and fmt_ok and ci[0] > 0) else "negative"
    reasons = []
    if not fmt_ok: reasons.append("format audit failed")
    if not beats: reasons.append(f"holdout {pooled:.6f} not above incumbent {incumbent}")
    if ci[0] <= 0: reasons.append("holdout 95% CI lower bound not > 0")
    summary = {
        "hypothesis": "H-GEO-1 cross-gradient gravity x magnetics concealed basement relay",
        "mechanism": "cross-gradient vector discordance grad(g) x grad(m) between gravity (band 5) "
                     "and magnetics (band 2) plus minimum principal curvature of residual gravity; "
                     "targets concealed basement contacts/relay ramps under alluvium",
        "non_fault_mimic": "un-faulted buried volcanic flow margins / dikes and lithologic contacts",
        "differs_from_repo": "prior arms used 1D gradient magnitudes or scalar tilt; none computed "
                             "the cross-gradient vector product grad(g) x grad(m)",
        "layers": ["band 5 iso_grav_anom_slope", "band 2 rtp"],
        "signature": "cross-gradient magnitude x (1+min principal curvature) x (1+gravity grad) x (1+magnetic grad)",
        "expected_dti_improvement": "medium; cost low-medium (bands on disk)",
        "rank": 2,
        "evaluator_version": res["evaluator_version"],
        "pooled_holdout_dti": float(pooled),
        "ci95": [float(ci[0]), float(ci[1])],
        "n_withheld_positives": int(res["n_withheld_positives"]),
        "incumbent_holdout_dti": incumbent,
        "beats_incumbent": bool(beats),
        "emitted_pixels": int(mask.sum()),
        "on_catalogue_pixels": int((mask & labels).sum()),
        "field_threshold": float(tau),
        "format_audit_passed": fmt_ok,
        "format_report": report.to_dict(),
        "raster_sha256": sha256_file(zeros_path),
        "raster_path": str(zeros_path),
        "submission_name": f"H-GEO-1-CROSSGRAD-{N_TARGET}",
        "note": "Concealed basement relay emission; gravity-magnetics cross-gradient discordance; off-catalogue B=2; 300 m kernel.",
        "verdict": verdict,
        "reasons": reasons,
        "built_utc": ts,
    }
    assert len(summary["note"]) <= 140
    evidence_path = evidence_dir() / f"H-GEO-1-crossgrad-{ts}-run-card.json"
    evidence_path.write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({k: v for k, v in summary.items() if k != "format_report"}, indent=2))
    print(f"run card: {evidence_path}")
    print(f"raster: {zeros_path} sha256={summary['raster_sha256']}")
    return 0 if verdict == "promote" else 1


if __name__ == "__main__":
    from datetime import datetime
    raise SystemExit(main())
