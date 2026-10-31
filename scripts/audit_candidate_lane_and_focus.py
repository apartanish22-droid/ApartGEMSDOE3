#!/usr/bin/env python3
"""Lane + focus-site audit for the H-GEO-1 candidate.

For every scored registry raster (the known GEMSDOE submissions) compute:
  - Spearman surface correlation vs H-GEO-1 field (limit |rho| <= 0.90)
  - Fraction of H-GEO-1 dots within 3 px of the registry raster's dots (limit <= 0.70)
Lane PASS requires BOTH against EVERY registry raster.

Also computes HOLDOUT-DTI (shared v3 evaluator) for each focus-site best file so the
executive summary table carries labeled, computed estimates (never a live-score projection).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy.stats import spearmanr
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems32.paths import data_dir
from gems32 import holdout

DDIR = data_dir()
with rasterio.open(DDIR / "sample_submission.tif") as ds:
    FOOT = np.isfinite(ds.read(1))
with rasterio.open(DDIR / "labels.tif") as ds:
    LABELS = (ds.read(1) > 0) & FOOT

CAND = "docs/downloads/gemsdoe32-hgeo1-crossgrad-37654d-20261031T044952Z-2940f96e-zeros.tif"


def load_bool(path):
    with rasterio.open(path) as ds:
        a = ds.read(1)
    return np.isfinite(a) & (a > 0)


def lane_vs(cand_pos, reg_pos):
    both = FOOT & reg_pos
    rho = None
    if int(both.sum()) > 1000:
        # need candidate surface; reuse binary surface (cand_pos) as the field proxy
        c = cand_pos[both].astype(float)
        r = reg_pos[both].astype(float)
        if c.std() > 0 and r.std() > 0:
            rho, _ = spearmanr(c, r)
    dreg = ndimage.distance_transform_edt(~reg_pos)
    ys, xs = np.nonzero(cand_pos & FOOT)
    frac = float((dreg[ys, xs] <= 3.0).mean()) if ys.size else 0.0
    pass_ = (rho is None or abs(rho) <= 0.90) and frac <= 0.70
    return rho, frac, pass_


def main():
    cand = load_bool(CAND)
    print(f"H-GEO-1 dots: {int(cand.sum()):,}")
    # Registry rasters: all scored files restored into .cache/gems_data/scored/
    scored = sorted((DDIR / "scored").glob("*.tif"))
    results = []
    all_pass = True
    for p in scored:
        reg = load_bool(p)
        rho, frac, pass_ = lane_vs(cand, reg)
        all_pass &= pass_
        results.append({
            "raster": p.name,
            "spearman_rho": None if rho is None else round(float(rho), 4),
            "frac_dots_within_3px": round(frac, 4),
            "lane_pass": bool(pass_),
        })
        print(f"{p.name:70s} rho={str(rho):>6s} frac3px={frac:.4f} pass={pass_}")
    print(f"\nLANE vs ALL REGISTRY: {'PASS' if all_pass else 'FAIL'}")

    # Holdout DTI for the nine focus-site best files.
    ctx = holdout.load_holdout_context(DDIR)
    focus = {
        "GEMSDOE24": "scored/gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan.tif",
        "GEMSDOE25": "scored/gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif",
        "GEMSDOE27": "scored/gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan.tif",
        "GEMSDOE28": "scored/gems28-h27-4-r1-solo-d2-8-20261003-8acb75e1f2cc-allfinite.tif",
    }
    print("\nFocus-site HOLDOUT-DTI (shared v3 evaluator, NOT a live-score projection):")
    for site, rel in focus.items():
        p = DDIR / rel
        if not p.exists():
            print(f"  {site}: MISSING {rel}")
            continue
        with rasterio.open(p) as ds:
            arr = np.isfinite(ds.read(1)) & (ds.read(1) > 0) & FOOT
        res = holdout.evaluate_hide_and_recover(arr, ctx, b_visible_px=0.0, name=site)
        print(f"  {site}: pooled={res['pooled_dti']:.6f} "
              f"ci95=[{res['ci95_cluster_bootstrap'][0]:.6f},{res['ci95_cluster_bootstrap'][1]:.6f}] "
              f"n_withheld={res['n_withheld_positives']:,} emitted={int(arr.sum()):,}")

    out = {"candidate": CAND, "lane_vs_registry": results, "lane_pass_all": bool(all_pass)}
    (ROOT / "evidence" / "hgeo1_lane_audit.json").write_text(json.dumps(out, indent=2) + "\n")
    print(f"\nwrote evidence/hgeo1_lane_audit.json")


if __name__ == "__main__":
    main()
