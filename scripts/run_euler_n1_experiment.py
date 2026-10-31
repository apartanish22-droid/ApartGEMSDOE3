#!/usr/bin/env python3
"""E1 runner: Euler N=1 solution density on TMI (pre-registered in docs/research/preregistration-euler-n1-tmi-20261031.md).

Writes a candidate GeoTIFF to .cache/candidates/ (NOT docs/downloads) and a run card to evidence/.
Gates are evaluated separately; this script does not authorize download or submission.
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

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems32 import euler_n1 as E  # noqa: E402
from gems32.paths import data_dir  # noqa: E402

BAND_TMI = 14  # 1-based, training_features.tif: "Total magnetic intensity"
NAME = "E1-EULER-N1-TMI-37654"


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def auc_rank(score: np.ndarray, label: np.ndarray) -> float:
    """Mann-Whitney AUC without sklearn."""
    from scipy.stats import rankdata
    s = np.asarray(score, float).ravel()
    y = np.asarray(label, bool).ravel()
    n1, n0 = int(y.sum()), int((~y).sum())
    if n1 == 0 or n0 == 0:
        return float("nan")
    r = rankdata(s)
    return float((r[y].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=ROOT / ".cache" / "candidates" / f"{NAME}.tif")
    ap.add_argument("--run-card", type=Path, default=ROOT / "evidence" / "euler_n1_E1_run_card.json")
    args = ap.parse_args()
    t0 = time.time()
    ddir = data_dir()

    with rasterio.open(ddir / "sample_submission.tif") as tmpl:
        footprint = np.isfinite(tmpl.read(1))
        profile = tmpl.profile.copy()
    with rasterio.open(ddir / "training_features.tif") as src:
        raw = src.read(BAND_TMI).astype(np.float64)
        band_name = src.tags(BAND_TMI).get("description", "")
    valid = np.isfinite(raw) & (raw > -1e30)
    tmi = E.fill_invalid_nearest(np.where(valid, raw, np.nan), valid)
    tmi = np.where(np.isfinite(tmi), tmi, 0.0)

    Tx, Ty, Tz = E.derivatives_fft(tmi)
    x0, y0, z0, B = E.euler_n1_solutions(tmi, Tx, Ty, Tz, N=1.0, valid=valid)
    n_sol = int(len(x0))
    dens = E.solution_density(x0, y0, tmi.shape)
    dots = E.top_dots(dens, footprint, E.DOTS)
    raster = np.where(footprint, dots.astype(np.float32), 0.0).astype(np.float32)

    # Single-feature leakage canary: density vs catalogue labels (labels.tif, >0 = known fault).
    with rasterio.open(ddir / "labels.tif") as lab:
        labels = lab.read(1)
    known = (labels == 1) & footprint
    auc = auc_rank(dens[footprint], known[footprint])

    args.out.parent.mkdir(parents=True, exist_ok=True)
    profile.update(dtype="float32", count=1, nodata=None, compress="deflate")
    with rasterio.open(args.out, "w", **profile) as dst:
        dst.write(raster, 1)

    card = {
        "experiment": "E1",
        "name": NAME,
        "preregistration": "docs/research/preregistration-euler-n1-tmi-20261031.md",
        "lane": "Euler N=1 windowed solution density on TMI band 14",
        "hypothesis": "Clusters of N=1 Euler solutions at 0.2-3 km depth on TMI mark buried magnetic boundaries without a catalogue trace.",
        "mechanism": "Windowed (15 px) Euler N=1 solves on FFT derivatives; solutions accepted if inside window and at 200-3000 m depth; density gaussian sigma 2 px; top 37,654 footprint cells.",
        "named_non_fault_mimic": "Magnetic dikes, mafic intrusions, magnetic basement lithology contacts.",
        "band_1based": BAND_TMI,
        "band_description": band_name,
        "n_euler_solutions_accepted": n_sol,
        "median_solution_depth_m": float(np.median(z0)) if n_sol else None,
        "emitted_pixels": int(dots.sum()),
        "values": sorted(np.unique(raster).tolist()),
        "leakage_canary_auc_density_vs_catalogue": auc,
        "leakage_canary_rule": "AUC > 0.90 means leakage until proven otherwise",
        "candidate_path": str(args.out.relative_to(ROOT)),
        "candidate_sha256": sha256(args.out),
        "holdout": "NOT RUN in this script - see evaluate step",
        "runtime_s": round(time.time() - t0, 1),
        "verdict": "pending gates",
    }
    args.run_card.parent.mkdir(parents=True, exist_ok=True)
    args.run_card.write_text(json.dumps(card, indent=2) + "\n")
    print(json.dumps(card, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
