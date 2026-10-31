#!/usr/bin/env python3
"""H-M1 experiment driver (2026-10-31): magnetic-gravity co-gradient alignment candidate.

Same gates, same shared writer/evaluator, same canary and controls as scripts/run_h_s1_spectral.py
(helpers imported from that file so both experiments are scored by identical code).
Writes docs/downloads/<name>.tif (+zip) and evidence/H-M1-CROSSGRAD-MG_run_card.json.
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

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems32 import emission, holdout  # noqa: E402
from gems32.crossgrad_mg import build_hm1  # noqa: E402
from gems32.paths import data_dir  # noqa: E402
from gems32.spectral_rolloff import SENTINEL_MIN  # noqa: E402

_spec = importlib.util.spec_from_file_location("run_h_s1", ROOT / "scripts" / "run_h_s1_spectral.py")
H1 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(H1)  # provides canary_auc, eta_squared, _load_writer, _load_eval

N_DOTS = H1.N_DOTS
MIN_DIST = H1.MIN_DIST
SLUG = "h-crossgrad-mg-h2"
NOTE = "H-M1 magnetic-gravity co-gradient alignment, 37654 dots, 100m, no catalogue input, NaN-free"
TS = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def main() -> int:
    ddir = data_dir()
    with rasterio.open(ddir / "sample_submission.tif") as ds:
        foot = np.isfinite(ds.read(1))
    with rasterio.open(ddir / "labels.tif") as ds:
        labels = (ds.read(1) > 0) & foot
    with rasterio.open(ddir / "training_features.tif") as ds:
        rtp_raw = ds.read(2).astype(np.float64)   # band 2 rtp
        grav_raw = ds.read(13).astype(np.float64) # band 13 iso_grav_anom
    surf = build_hm1(rtp_raw, grav_raw, foot)
    surf = np.where(foot, surf, 0.0).astype(np.float32)
    if not np.isfinite(surf[foot]).all():
        raise SystemExit("non-finite H-M1 surface inside footprint")

    dots = emission.dot_thin_matched(surf, N_DOTS, foot, min_dist=MIN_DIST)
    dots_out = dots & foot & ~labels
    n_dots = int(dots_out.sum())

    ctx = holdout.load_holdout_context(ddir)
    from gems32.spectral_rolloff import detrended_residual
    rtp_resid, rtp_valid = detrended_residual(np.where(rtp_raw <= SENTINEL_MIN, np.nan, rtp_raw), foot)
    grav_resid, _ = detrended_residual(np.where(grav_raw <= SENTINEL_MIN, np.nan, grav_raw), foot)
    canaries = {
        "rtp_band2_residual": H1.canary_auc(np.where(rtp_valid, rtp_resid, 0.0), ctx),
        "iso_grav_band13_residual": H1.canary_auc(np.where(foot, grav_resid, 0.0), ctx),
        "h_m1_surface": H1.canary_auc(surf, ctx),
    }

    with rasterio.open(ddir / "external" / "acquisition_block_id_100m.tif") as ds:
        blk = ds.read(1)
    eta_block = H1.eta_squared(surf, blk, foot)

    writer = H1._load_writer()
    meta = {
        "candidate_id": "H-M1-CROSSGRAD-MG",
        "description": "H-M1 magnetic (rtp) x gravity (iso_grav_anom) co-gradient alignment (H35-C form, new layer pair)",
        "submission_note_zeros": NOTE,
        "submission_note_nan": NOTE,
        "slot_decision": "HOLD-DO-NOT-SUBMIT",
    }
    bundle = writer.write_validated_submission(dots_out.astype(np.float32), slug=SLUG, candidate_meta=meta,
                                               ddir=ddir, out_dir=ROOT / "docs" / "downloads", timestamp_tag=TS)
    zeros_path = ROOT / "docs" / "downloads" / bundle["zeros_tif"]["filename"]

    ev = H1._load_eval()
    hold = ev.evaluate_path(zeros_path, b_visible_px=0.0, ddir=ddir, name="H-M1-CROSSGRAD-MG")

    card = {
        "run_id": f"H-M1-CROSSGRAD-MG-{TS}",
        "date_utc": TS,
        "lane": "NOT ASSIGNED (no method paragraph in prompt or checkout). Self-declared research run; cannot be cleared for a weekly slot.",
        "hypothesis": "Co-located, co-oriented magnetic (rtp) and gravity (iso_grav_anom) edges mark offsets that cut both fields.",
        "mechanism": "A fault that juxtaposes contrasting magnetic and density blocks produces aligned gradients in both fields; the H35-C functional form scores that coincidence.",
        "named_non_fault_mimic": "Intrusive or lithologic contacts with both a magnetic and a density contrast (the cross-gradient mimic).",
        "single_feature_canary_auc_holdout_seed20": canaries,
        "canary_threshold": 0.90,
        "canary_passed": bool(max(canaries.values()) <= 0.90),
        "controls": {"acquisition_block_eta_squared_surface": eta_block},
        "dots_before_label_mask": int(dots.sum()),
        "dots_after_label_mask": n_dots,
        "candidate_file": str(zeros_path.relative_to(ROOT)),
        "candidate_sha256": H1.sha256(zeros_path),
        "candidate_zip": bundle.get("zeros_zip", {}).get("filename"),
        "submission_name": SLUG.upper(),
        "submission_note": NOTE,
        "note_chars": len(NOTE),
        "holdout_candidate": hold,
        "holdout_champion_GEMSDOE32": None,
        "score_label": "HOLDOUT-DTI (evaluator GEMSDOE32-HIDE-RECOVER-v3.0 and GEMSDOE32-SGMC-CAL-v3.0). Live score: NOT ESTIMABLE.",
        "verdict": "pending_gates",
    }
    out_path = ROOT / "evidence" / "H-M1-CROSSGRAD-MG_run_card.json"
    out_path.write_text(json.dumps(card, indent=2, default=float) + "\n")
    print(json.dumps({k: card[k] for k in ("candidate_file", "candidate_sha256", "dots_after_label_mask",
                                          "single_feature_canary_auc_holdout_seed20", "controls")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
