#!/usr/bin/env python3
"""Experiment G1 runner: Euler deconvolution, structural index N = 1, on TMI (band 14).

Pipeline (reuses the shared tools; no private fork of the evaluator, writer or audit):
  surface  : gems32.euler_n1 (pre-registered method, see knowledge/10 §6)
  canary   : single-feature leakage canary on the hide-and-recover holdout (AUC; > 0.90 = leakage)
  dots     : build_unique_submission.select_dots (quantile support, 200 m catalogue collar,
             Poisson-disk thinning at 2.8 px, ~30k dots) -- same placement rule as the repo's
             other off-catalogue candidates, so the only new ingredient is the surface
  holdout  : gems32.holdout.evaluate_visible_gated_holdout (HOLDOUT-DTI, alpha 0.2, beta 0.8, 300 m)
  unique   : registry_audit.audit_surface + audit_final_dots over the 451 focus-registry rasters
  writer   : submission_writer.write_validated_submission (strict [0,1], zeros outside footprint)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from gems32 import euler_n1 as G1  # noqa: E402
from gems32 import holdout  # noqa: E402
from gems32 import cross_grad_g2 as G2  # noqa: E402
from gems32 import registry_audit as RA  # noqa: E402
from gems32.paths import data_dir, downloads_dir  # noqa: E402
from build_unique_submission import select_dots, percentile_rank, TARGET_DOTS, MIN_DIST_PX, COLLAR_PX  # noqa: E402
from submission_writer import write_validated_submission  # noqa: E402

HYPOTHESES = {
    "g1": {
        "candidate_id": "H-G1-EULER-N1-TMI",
        "slug": "NEG-DO-NOT-SUBMIT-g1-euler-n1-tmi",
        "note": "NEG DO-NOT-SUBMIT G1 Euler N=1 TMI dots: canary AUC 0.51 (no signal), literal lattice rule fails",
    },
    "g2": {
        "candidate_id": "H-G2-GRAV-MAG-COUPLING",
        "slug": "g2-grav-mag-coupling",
        "note": "G2 gravity-magnetic gradient coupling (bands 13+14) dots, off-catalogue 200m collar, 30k, [0,1] zeros",
    },
}


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def canary_auc(surface: np.ndarray, ctx) -> dict:
    """Single-feature canary: AUC of the surface for withheld-fault pixels vs. far background,
    pooled over the holdout cells. Positives = withheld truth pixels; negatives = active pixels
    more than 3 px from any withheld truth pixel."""
    ys, ss = [], []
    rng = np.random.default_rng(7)
    per_cell = []
    for cell in ctx.cells:
        sl = cell.bbox
        s_sub = surface[sl]
        pos_mask = np.zeros(s_sub.shape, bool)
        pos_mask[cell.truth_coords] = True
        # k_dg_sub = kernel(distance to withheld truth): 0 for d >= 3 px, so negatives are far background
        neg_mask = cell.active_sub & ~pos_mask & (cell.k_dg_sub <= 0.0)
        p = s_sub[pos_mask & np.isfinite(s_sub)]
        n = s_sub[neg_mask & np.isfinite(s_sub)]
        if p.size == 0 or n.size == 0:
            continue
        if n.size > 20 * p.size:
            n = rng.choice(n, 20 * p.size, replace=False)
        yy = np.concatenate([np.ones(p.size), np.zeros(n.size)])
        ss_ = np.concatenate([p, n])
        ys.append(yy)
        ss.append(ss_)
        per_cell.append(float(roc_auc_score(yy, ss_)))
    y = np.concatenate(ys)
    s = np.concatenate(ss)
    return {
        "pooled_auc": float(roc_auc_score(y, s)),
        "per_cell_auc_min": float(min(per_cell)),
        "per_cell_auc_max": float(max(per_cell)),
        "per_cell_auc_mean": float(np.mean(per_cell)),
        "n_cells": len(per_cell),
        "n_pos": int((y == 1).sum()),
        "n_neg": int((y == 0).sum()),
        "leakage_flag_above_0p90": bool(max(per_cell) > 0.90),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data-dir", type=Path, default=None)
    ap.add_argument("--out-dir", type=Path, default=None)
    ap.add_argument("--skip-holdout", action="store_true")
    ap.add_argument("--skip-unique", action="store_true")
    ap.add_argument("--dry-run", action="store_true", help="do not write the submission GeoTIFF")
    ap.add_argument("--hypothesis", choices=sorted(HYPOTHESES), default="g1")
    args = ap.parse_args()
    H = HYPOTHESES[args.hypothesis]
    CANDIDATE_ID, SLUG, NOTE = H["candidate_id"], H["slug"], H["note"]
    if len(NOTE) > 140:
        raise SystemExit("note too long")

    ddir = args.data_dir or data_dir()
    out_dir = args.out_dir or downloads_dir()
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    card: dict = {"candidate_id": CANDIDATE_ID, "generated_utc": ts, "stages": {}}

    with rasterio.open(ddir / "sample_submission.tif") as ds:
        foot = np.isfinite(ds.read(1))
        template_tif = ddir / "sample_submission.tif"
    with rasterio.open(ddir / "labels.tif") as ds:
        labels = (ds.read(1) > 0) & foot
    with rasterio.open(ddir / "training_features.tif") as ds:
        tmi_raw = ds.read(14)
        assert ds.tags(14)["description"].startswith("Total magnetic intensity - total strength"), "band 14 is not TMI"
        grav_raw = ds.read(13) if args.hypothesis == "g2" else None
        if grav_raw is not None:
            assert ds.tags(13)["description"].startswith("Isostatic gravity anomaly - gravity after"), "band 13 changed"
    tmi = G1.fill_nodata(tmi_raw, foot)
    print(f"[data] footprint={int(foot.sum())} labels={int(labels.sum())} tmi_median={np.median(tmi[foot]):.3f}")

    if args.hypothesis == "g1":
        # 1. Euler N = 1 solutions
        sol = G1.euler_n1_solutions(tmi, foot)
        card["stages"]["euler"] = {
            "structural_index": G1.N_INDEX, "window_px": G1.WIN_PX, "stride_px": G1.STRIDE_PX,
            "depth_km": [G1.Z_MIN_KM, G1.Z_MAX_KM], "rel_resid_max": G1.RESID_MAX,
            "windows_on_footprint": sol["n_windows_on_footprint"], "accepted": sol["n_accepted"],
            "accepted_fraction": sol["n_accepted"] / max(1, sol["n_windows_on_footprint"]),
            "depth_median_km": float(np.median(sol["z_km"])) if sol["z_km"].size else None,
        }
        print("[euler]", json.dumps(card["stages"]["euler"]))
        dens = G1.solutions_to_density(sol, foot.shape, foot)
    else:
        grav = G1.fill_nodata(grav_raw, foot)
        dens = G2.coupling_surface(grav, tmi, foot)
        card["stages"]["coupling"] = {"bands": [13, 14], "sigma_px": 2.0,
                                      "score": "min(normg,normm)*(1-sin_theta), normalised by footprint p95"}
    prop = percentile_rank(np.where(foot, dens, np.nan))
    prop = np.where(foot, prop, np.nan)
    assert np.isfinite(prop[foot]).all()

    # 2. dots (shared placement rule)
    dots, q = select_dots(prop, foot, labels, TARGET_DOTS, MIN_DIST_PX, COLLAR_PX)
    on_cat = int((dots & labels).sum())
    card["stages"]["dots"] = {"n": int(dots.sum()), "quantile": float(q), "on_catalogue": on_cat,
                              "share_on_catalogue_is_zero_by_construction": on_cat == 0}

    # 3. canary + holdout
    ctx = holdout.load_holdout_context(ddir)
    if not args.skip_holdout:
        card["stages"]["leakage_canary"] = canary_auc(prop, ctx)
        print("[canary]", json.dumps(card["stages"]["leakage_canary"]))
        hr = holdout.evaluate_visible_gated_holdout(dots, ctx, b_gate_px=float(COLLAR_PX), name=CANDIDATE_ID)
        card["stages"]["holdout"] = {
            "evaluator": holdout.HOLDOUT_EVALUATOR_VERSION,
            "pooled_dti": float(hr["pooled_dti"]), "ci95": [float(hr["ci95"][0]), float(hr["ci95"][1])],
            "n_withheld_positives": int(hr["n_withheld_positives"]),
            "sgmc_off_catalogue": {
                "n_withheld_positives": int(hr["sgmc_off_catalogue"]["n_withheld_positives"]),
                "raw_pooled_dti": float(hr["sgmc_off_catalogue"]["raw_pooled_dti"]),
                "raw_ci95": [float(x) for x in hr["sgmc_off_catalogue"]["raw_ci95"]],
                "prevalence_calibrated_dti": float(hr["sgmc_off_catalogue"]["prevalence_calibrated_dti"]),
            },
        }
        card["stages"]["holdout"]["per_cell_dti"] = {k: float(v["dti"]) for k, v in hr["cells"].items()}
        print("[holdout]", json.dumps(card["stages"]["holdout"]))

    # 4. uniqueness vs the 451 focus-registry rasters (literal rules, no exemptions)
    manifest = RA.load_manifest(ROOT / "registry" / "focus_registry_manifest.json")
    if not args.skip_unique:
        a1 = RA.audit_surface(prop.astype(np.float32), foot, manifest, root=ROOT, template_tif=template_tif)
        a2 = RA.audit_final_dots(prop.astype(np.float32), dots, foot, manifest, root=ROOT, template_tif=template_tif)
        card["stages"]["uniqueness"] = {
            "n_registry_rasters": len(manifest["rasters"]),
            "surface_summary": {k: v for k, v in a1.items() if k != "rows"},
            "final_dots_summary": {k: v for k, v in a2.items() if k != "rows"},
        }
        rows_path = ROOT / "evidence" / f"{CANDIDATE_ID}_{ts}_uniqueness_rows.json"
        rows_path.write_text(json.dumps({"surface": a1.get("comparisons", []), "final_dots": a2.get("comparisons", [])},
                                        default=str, indent=1) + "\n")
        card["stages"]["uniqueness"]["rows_file"] = str(rows_path.relative_to(ROOT))
        print("[unique-surface]", json.dumps(card["stages"]["uniqueness"]["surface_summary"], default=str)[:800])
        print("[unique-dots]", json.dumps(card["stages"]["uniqueness"]["final_dots_summary"], default=str)[:800])

    if args.dry_run:
        print(json.dumps(card, indent=2, default=str))
        return 0

    # 5. writer (strict [0,1], zeros outside footprint, no NaN)
    meta = {"candidate_id": CANDIDATE_ID, "description": NOTE, "submission_note_zeros": NOTE,
            "submission_note_nan": NOTE, "slot_decision": "HOLD-PENDING-GATES"}
    bundle = write_validated_submission(dots, slug=SLUG, candidate_meta=meta, ddir=ddir, out_dir=out_dir,
                                        timestamp_tag=ts)
    zname = bundle["zeros_tif"]["filename"]
    card["submission_file"] = zname
    card["raster_sha256"] = bundle["zeros_tif"]["sha256"]
    card["validator"] = bundle.get("validator", bundle.get("audit", None))
    card["submission_note"] = NOTE
    run_card = ROOT / "evidence" / f"{CANDIDATE_ID}_{ts}_run_card.json"
    run_card.write_text(json.dumps(card, indent=2, default=str) + "\n")
    print("[written]", zname, "sha256", card["raster_sha256"])
    print("[run card]", run_card)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
