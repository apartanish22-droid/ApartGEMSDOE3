#!/usr/bin/env python3
"""Audit the nine focus sites' highest-stated files: bytes, format, and shared-evaluator holdout.

For each site the file named in the session prompt is located in the pinned registry (or docs/ for
GEMSDOE32), hashed, format-checked, and passed through the shared evaluator `scripts/evaluate_holdout.py`.

IMPORTANT: these are FIXED rasters built from the full catalogue. The shared hide-and-recover holdout
only measures a method that is refit per fold, so a fixed raster's holdout DTI is expected to be near
zero. The output documents that mismatch; it is not a leaderboard estimate and must not be read as a
ranking of the sites.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from evaluate_holdout import evaluate_path  # noqa: E402
from gems32.paths import data_dir  # noqa: E402

REG = ROOT / ".cache" / "registry"
TARGETS = [
    # site, prompt-stated name, stated score (OWNER-REPORT), file relative to .cache/registry/<site>/
    ("GEMSDOE24", "h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan", 0.2477,
     "docs/downloads/gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan.tif"),
    ("GEMSDOE25", "dotted-h19-5-d2-8-20261002-e56ea318af89-nan", 0.2600,
     "docs/downloads/gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif"),
    ("GEMSDOE27", "topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan", 0.2449,
     "docs/downloads/gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan.tif"),
    ("GEMSDOE28", "h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan", 0.2710,
     "docs/downloads/gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif"),
    ("GEMSDOE30", "d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca", 0.2600,
     "docs/downloads/gemsdoe30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca.tif"),
    ("GEMSDOE31", "h27-4-solo-d28-20261004-8acb75e1-nan", 0.2708,
     "docs/downloads/gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-nan.tif"),
    ("GEMSDOE32", "h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros", 0.2778,
     "docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif"),
    ("GEMSDOE33", "h33d-analog-tip-stepover-r30-20261004-cb490425926e", 0.2632,
     "docs/downloads/GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e.tif"),
    ("GEMSDOE36", "anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros", 0.2750,
     "docs/downloads/gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif"),
]


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def locate(site: str, rel: str) -> Path:
    if site == "GEMSDOE32":
        return ROOT / rel
    return REG / site / rel


def main() -> int:
    ddir = data_dir()
    with rasterio.open(ddir / "sample_submission.tif") as ds:
        foot = np.isfinite(ds.read(1))
    rows = []
    for site, name, stated, rel in TARGETS:
        p = locate(site, rel)
        if not p.is_file():
            rows.append({"site": site, "name": name, "status": "MISSING", "path": str(p)})
            continue
        with rasterio.open(p) as ds:
            a = ds.read(1)
            info = {
                "shape": list(a.shape), "crs": str(ds.crs), "transform_matches_template": bool(
                    ds.transform == rasterio.open(ddir / "sample_submission.tif").transform),
                "nan_inside_footprint": int(np.isnan(a[foot]).sum()),
                "nan_anywhere": int(np.isnan(a).sum()),
                "min_inside": float(np.nanmin(a[foot])), "max_inside": float(np.nanmax(a[foot])),
                "positive_pixels": int((np.nan_to_num(a) > 0).sum()),
            }
        ev = evaluate_path(p, ddir=ddir, name=name)
        hr = ev["hide_and_recover"]
        sg = ev["sgmc_off_catalogue"]
        rows.append({
            "site": site, "name": name, "stated_score_OWNER_REPORT": stated,
            "file": str(p.relative_to(ROOT)) if str(p).startswith(str(ROOT)) else str(p),
            "bytes": p.stat().st_size, "sha256": sha256(p), "format": info,
            "holdout_hide_recover": {
                "evaluator_version": hr["evaluator_version"], "score_label": "HOLDOUT-DTI",
                "pooled_dti": hr["pooled_dti"], "ci95": hr["ci95_cluster_bootstrap"],
                "n_withheld_positives": hr["n_withheld_positives"],
            },
            "holdout_sgmc_calibrated": {
                "evaluator_version": sg["evaluator_version"], "score_label": "HOLDOUT-DTI",
                "prevalence_calibrated_dti": sg["sgmc_prevalence_calibrated_dti"],
                "ci95": sg["sgmc_calibrated_ci95"], "n_withheld_positives": sg["n_withheld_positives"],
            },
            "status": "measured",
        })

    shas = {}
    for r in rows:
        if "sha256" in r:
            shas.setdefault(r["sha256"], []).append(r["site"])
    out = {
        "schema_version": 1,
        "purpose": "Nine-site fixed-file audit: bytes, format, and shared-evaluator holdout.",
        "interpretation": ("Fixed rasters are built from the full catalogue; hide-and-recover holdout is "
                           "not designed to score them. Values are diagnostic only, not leaderboard estimates."),
        "rows": rows,
        "cross_site_byte_duplicates": [v for v in shas.values() if len(v) > 1],
    }
    dest = ROOT / "evidence" / "nine_site_fixed_file_audit_20261030.json"
    dest.write_text(json.dumps(out, indent=2, default=float) + "\n")
    for r in rows:
        if r.get("status") == "measured":
            print(f"{r['site']}: stated={r['stated_score_OWNER_REPORT']} holdout={r['holdout_hide_recover']['pooled_dti']:.5f} "
                  f"CI={r['holdout_hide_recover']['ci95']} sha={r['sha256'][:12]}")
        else:
            print(r)
    print("duplicates:", out["cross_site_byte_duplicates"])
    print("wrote", dest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
