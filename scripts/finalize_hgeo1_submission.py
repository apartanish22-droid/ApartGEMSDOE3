#!/usr/bin/env python3
"""Finalize H-GEO-1 as a proper, audited submission bundle via the shared submission_writer.

Produces (in docs/downloads/):
  - <candidate>-zeros.tif   all 12,279,160 cells finite, in [0,1], 0 outside footprint (portal-safe)
  - <candidate>-nan.tif     NaN outside footprint, in [0,1] inside
  - <candidate>.zip         zip of the zeros GeoTIFF
  - <candidate>-audit.json  full 12-point validator audit + holdout metrics + run-card fields

The bundle is format-valid (check_submission --strict-finite) and unique vs all scored
registry rasters. It is NOT self-authorized: slot_decision is
PENDING-SELECTOR-AUTHORIZATION because organizer receipt / live score is unavailable from this
sandbox (DrivenData is login-walled). The run card verdict records the local holdout result.
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

from gems32 import holdout
from gems32.paths import data_dir, downloads_dir, evidence_dir
from gems32.grid import read_labels, read_footprint

# Load the shared submission_writer by file path (scripts/ is not a package).
_sw_path = ROOT / "scripts" / "submission_writer.py"
_sw_spec = importlib.util.spec_from_file_location("submission_writer", _sw_path)
_sw_mod = importlib.util.module_from_spec(_sw_spec)
_sw_spec.loader.exec_module(_sw_mod)
write_validated_submission = _sw_mod.write_validated_submission

DDIR = data_dir()
CAND_TIF = "docs/downloads/gemsdoe32-hgeo1-crossgrad-37654d-20261031T044952Z-2940f96e-zeros.tif"
SLUG = "hgeo1-crossgrad-37654d"
CANDIDATE_ID = "H-GEO-1-CROSSGRAD-37654"
NOTE = ("Concealed basement relay emission; gravity-magnetics cross-gradient discordance; "
        "off-catalogue B=2; 300 m kernel.")
assert len(NOTE) <= 140, len(NOTE)


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    with rasterio.open(DDIR / "sample_submission.tif") as ds:
        FOOT = np.isfinite(ds.read(1))
    with rasterio.open(CAND_TIF) as ds:
        arr = ds.read(1)
    mask = (arr > 0.5) & FOOT
    print(f"reconstructed mask: {int(mask.sum()):,} dots")

    ctx = holdout.load_holdout_context(DDIR)
    res = holdout.evaluate_hide_and_recover(mask, ctx, b_visible_px=0.0, name=CANDIDATE_ID)
    pooled = float(res["pooled_dti"]); ci = [float(v) for v in res["ci95_cluster_bootstrap"]]
    per_quad = {k: float(v) for k, v in res["per_quadrant_dti"].items()}
    print(f"holdout pooled={pooled:.6f} ci95={ci} per_quad={per_quad}")

    sg = holdout.evaluate_sgmc_with_ci(mask, ctx)
    sgmc_cal = float(sg["sgmc_prevalence_calibrated_dti"])
    sgmc_ci = [float(v) for v in sg["sgmc_calibrated_ci95"]]
    print(f"sgmc_cal={sgmc_cal:.6f} ci95={sgmc_ci}")

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    meta = {
        "candidate_id": CANDIDATE_ID,
        "description": ("H-GEO-1 cross-gradient gravity x magnetics concealed-basement relay "
                        "detector; built 2026-10-31 from hash-restored official bands 2 and 5."),
        "submission_note_zeros": NOTE,
        "submission_note_nan": NOTE,
        "catalogue_hidden_mean": pooled,
        "catalogue_hidden_per_quadrant": per_quad,
        "sgmc_prevalence_calibrated_dti": sgmc_cal,
        "sgmc_prevalence_calibrated_ci95": sgmc_ci,
        "drift_corrected_holdout_mean": pooled,
        "drift_corrected_holdout_std": float(np.std(list(per_quad.values()))),
        "drift_corrected_per_quadrant": per_quad,
        "predicted_leaderboard_dti": None,
        "ei_drift_corrected": None,
        "slot_decision": "PENDING-SELECTOR-AUTHORIZATION",
    }
    bundle = write_validated_submission(
        mask, slug=SLUG, candidate_meta=meta,
        ddir=DDIR, out_dir=downloads_dir(), timestamp_tag=ts,
    )
    zeros_path = downloads_dir() / bundle["zeros_tif"]["filename"]

    # Independent strict-finite format validation.
    from gemsdoe32.submission import validate_submission_geotiff
    report = validate_submission_geotiff(zeros_path, DDIR / "sample_submission.tif",
                                         strict_whole_array_finite=True)
    print(json.dumps(report.to_dict(), indent=2))
    print(f"format passed: {bool(report.passed)}")
    bundle["format_validation"] = report.to_dict()
    bundle["format_validation_passed"] = bool(report.passed)

    # Run card (protocol rule 5).
    incumbent = 0.0045154
    verdict = "promote" if (pooled > incumbent and ci[0] > 0 and bool(report.passed)) else "negative"
    run_card = {
        "hypothesis": "H-GEO-1 cross-gradient gravity x magnetics concealed basement relay",
        "mechanism": "cross-gradient vector discordance grad(g) x grad(m) between gravity (band 5) "
                     "and magnetics (band 2) plus minimum principal curvature of residual gravity; "
                     "targets concealed basement contacts/relay ramps under alluvium absent from "
                     "the USGS/INGENIOUS catalogue",
        "named_non_fault_mimic": "un-faulted buried volcanic flow margins / dikes and lithologic "
                                 "contacts that also produce coincident gravity-magnetic gradients",
        "holdout_dti": pooled,
        "holdout_ci95": ci,
        "evaluator_version": res["evaluator_version"],
        "n_withheld_positives": int(res["n_withheld_positives"]),
        "incumbent_holdout_dti": incumbent,
        "sgmc_prevalence_calibrated_dti": sgmc_cal,
        "sgmc_ci95": sgmc_ci,
        "champion_sgmc_cal": 0.0641209376417646,
        "beats_incumbent_holdout": bool(pooled > incumbent),
        "correlation_overlap_vs_registry": json.loads(
            Path("evidence/hgeo1_lane_audit.json").read_text()),
        "raster_sha256": bundle["zeros_tif"]["sha256"],
        "validator_output": bundle["zeros_tif"],
        "submission_name": f"{CANDIDATE_ID}-{ts}",
        "submission_note": NOTE,
        "verdict": verdict,
        "built_utc": ts,
    }
    rc_path = evidence_dir() / f"H-GEO-1-CROSSGRAD-37654-{ts}-run-card.json"
    rc_path.write_text(json.dumps(run_card, indent=2) + "\n")
    bundle_path = downloads_dir() / f"gemsdoe32-{SLUG}-{ts}-audit.json"
    bundle_path.write_text(json.dumps(bundle, indent=2) + "\n")
    print(f"\nRUN CARD VERDICT: {verdict}")
    print(f"run card: {rc_path}")
    print(f"bundle: {bundle_path}")
    print(f"zeros tif: {zeros_path}  sha256={bundle['zeros_tif']['sha256']}")
    print(f"zip: {bundle['zeros_zip']['path']}")
    return 0 if verdict == "promote" else 1


if __name__ == "__main__":
    raise SystemExit(main())
