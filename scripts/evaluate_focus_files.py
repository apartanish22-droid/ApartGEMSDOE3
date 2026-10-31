#!/usr/bin/env python3
"""Evaluate the nine focus-site submissions with the current holdout evaluator
and check pairwise uniqueness (overlap + rank correlation) between them.

Outputs JSON to evidence/focus_site_evaluation_<ts>.json and prints a summary
table suitable for the executive summary.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import binary_dilation
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from gems32.holdout import (  # noqa: E402
    load_holdout_context,
    evaluate_visible_gated_holdout,
)
from gems32.paths import data_dir  # noqa: E402

# (site, local_path, owner-reported score, source_note, available_locally)
FOCUS = [
    (
        "GEMSDOE24",
        ".cache/gems_data/scored/gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan.tif",
        0.2477,
        "buffedlizard55-lab/GEMSDOE24",
        True,
    ),
    (
        "GEMSDOE25",
        ".cache/gems_data/scored/gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif",
        0.2600,
        "buffedlizard55-lab/GEMSDOE25",
        True,
    ),
    (
        "GEMSDOE27",
        ".cache/gems_data/scored/gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan.tif",
        0.2449,
        "buffedlizard55-lab/GEMSDOE27",
        True,
    ),
    (
        "GEMSDOE28",
        ".cache/gems_data/scored/gems28-h27-4-r1-solo-d2-8-20261003-8acb75e1f2cc-allfinite.tif",
        0.2710,
        "buffedlizard55-lab/GEMSDOE28",
        True,
    ),
    (
        "GEMSDOE30",
        ".cache/gems_data/scored/gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif",
        0.2600,
        "GEMSDOE30 == GEMSDOE25 file (identical hash 91eae1ca)",
        True,
    ),
    (
        "GEMSDOE31",
        "docs/downloads/MISSING_GEMSDOE31_file.tif",
        0.2708,
        "buffedlizard55-lab/GEMSDOE31 - file NOT in restore manifest, not available locally",
        False,
    ),
    (
        "GEMSDOE32",
        "docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif",
        0.2778,
        "buffedlizard55-lab/GEMSDOE32",
        True,
    ),
    (
        "GEMSDOE33",
        "docs/downloads/MISSING_GEMSDOE33_file.tif",
        0.2632,
        "buffedlizard55-lab/GEMSDOE33 - file NOT in restore manifest, not available locally",
        False,
    ),
    (
        "GEMSDOE36",
        "docs/downloads/MISSING_GEMSDOE36_file.tif",
        0.2750,
        "buffedlizard55-lab/GEMSDOE36 - file NOT in restore manifest, not available locally",
        False,
    ),
]


def load_raster_mask(path: Path, foot: np.ndarray) -> np.ndarray:
    with rasterio.open(path) as ds:
        arr = ds.read(1).astype(np.float64)
    return np.isfinite(arr) & (arr > 0) & foot


def dots_overlap(a: np.ndarray, b: np.ndarray) -> float:
    """Fraction of a's dots within 3 px of b's dots (300 m)."""
    if not a.any() or not b.any():
        return 0.0
    b_dil = binary_dilation(b, iterations=3)
    return float((a & b_dil).sum() / max(a.sum(), 1))


def rank_corr(a: np.ndarray, b: np.ndarray) -> float:
    if not a.any() or not b.any():
        return 0.0
    try:
        rho, _ = spearmanr(a.astype(np.float64).ravel(), b.astype(np.float64).ravel())
        return float(rho) if rho is not None and np.isfinite(rho) else 0.0
    except Exception:
        return 0.0


def main() -> int:
    ddir = data_dir()
    with rasterio.open(ddir / "sample_submission.tif") as ds:
        foot = np.isfinite(ds.read(1))

    ctx = load_holdout_context(ddir)

    results = []
    masks = {}
    for site, path_str, score, source, available in FOCUS:
        p = Path(path_str)
        if not available or not p.exists():
            print(f"[SKIP] {site}: {path_str} not available locally")
            results.append(
                {
                    "site": site,
                    "file": Path(path_str).name if available else "NOT AVAILABLE LOCALLY",
                    "path": str(p),
                    "owner_reported_score": score,
                    "evidence_class": "OWNER-REPORT",
                    "source": source,
                    "available_locally": False,
                    "emitted_pixels": None,
                    "holdout_dti": None,
                    "holdout_ci95": None,
                    "evaluator_version": "GEMSDOE32-HOLDOUT-v3-visible-gated",
                    "n_withheld_positives": None,
                    "sgmc_raw_dti": None,
                    "sgmc_cal_dti": None,
                    "ok_to_submit": False,
                }
            )
            continue
        mask = load_raster_mask(p, foot)
        masks[site] = mask
        print(f"[EVAL] {site}: {path_str}  dots={int(mask.sum())}")
        hr = evaluate_visible_gated_holdout(
            mask, ctx, b_gate_px=2.0, name=f"{site}-{p.stem}"
        )
        results.append(
            {
                "site": site,
                "file": p.name,
                "path": str(p),
                "owner_reported_score": score,
                "evidence_class": "OWNER-REPORT",
                "source": source,
                "available_locally": True,
                "emitted_pixels": int(mask.sum()),
                "holdout_dti": float(hr["pooled_dti"]),
                "holdout_ci95": [float(hr["ci95"][0]), float(hr["ci95"][1])],
                "evaluator_version": hr["evaluator_version"],
                "n_withheld_positives": int(hr["n_withheld_positives"]),
                "sgmc_raw_dti": float(hr["sgmc_off_catalogue"]["raw_pooled_dti"]),
                "sgmc_cal_dti": float(hr["sgmc_off_catalogue"]["prevalence_calibrated_dti"]),
                "ok_to_submit": False,
            }
        )

    # Pairwise uniqueness among locally available files
    sites = [r["site"] for r in results if r.get("available_locally")]
    uniqueness = {}
    for i, s1 in enumerate(sites):
        for s2 in sites[i + 1 :]:
            overlap = dots_overlap(masks[s1], masks[s2])
            rho = rank_corr(masks[s1], masks[s2])
            uniqueness[f"{s1} vs {s2}"] = {
                "overlap_within_3px_of_s1": overlap,
                "spearman_rank_corr": rho,
                "unique": overlap <= 0.70 and abs(rho) <= 0.90,
            }

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = {
        "generated_utc": ts,
        "evaluator_version": "GEMSDOE32-HOLDOUT-v3-visible-gated",
        "results": results,
        "uniqueness": uniqueness,
        "note": "Owner-reported scores are OWNER-REPORT, not organizer receipts. Holdout DTI is HOLDOUT-DTI, not a leaderboard score projection. No file is authorized for submission.",
    }
    out_path = ROOT / "evidence" / f"focus_site_evaluation_{ts}.json"
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")

    # Print summary table
    print("\n" + "=" * 130)
    print(
        f"{'Site':<10} {'File':<52} {'OwnerScore':>10} {'HoldoutDTI':>10} {'95% CI':>18} {'SGMCcal':>8} {'Dots':>7} {'OK2Submit'}"
    )
    print("-" * 130)
    for r in results:
        if r.get("available_locally"):
            ci = r["holdout_ci95"]
            print(
                f"{r['site']:<10} {r['file']:<52} {r['owner_reported_score']:>10.4f} "
                f"{r['holdout_dti']:>10.4f} [{ci[0]:.4f}, {ci[1]:.4f}]  "
                f"{r['sgmc_cal_dti']:>8.4f} {r['emitted_pixels']:>7} NO"
            )
        else:
            print(f"{r['site']:<10} {r['file']:<52} {r['owner_reported_score']:>10.4f} "
                  f"{'N/A':>10} {'N/A':>18} {'N/A':>8} {'N/A':>7} NO")
    print("\nPairwise uniqueness (overlap <=0.70 and |rho| <=0.90 => UNIQUE):")
    for pair, u in uniqueness.items():
        flag = "UNIQUE" if u["unique"] else "DUPLICATE"
        print(f"  {pair:<40} overlap={u['overlap_within_3px_of_s1']:.3f} rho={u['spearman_rank_corr']:+.3f}  {flag}")
    print(f"\nEvidence written to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
