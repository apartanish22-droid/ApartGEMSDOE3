"""Read-only, fail-closed audit of the previously generated MRCJ artifact.

This rechecks bytes, format, and the nine requested focus-site registry rasters.
It does not rerun geological experiments, replay HOLDOUT-DTI, estimate a
leaderboard score, verify the live submission quota, or authorize an upload.
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import rasterio

from .novelty import correlation, dot_overlap
from .selector import verify_selector
from .submission import check_variants

SITES = ("GEMSDOE24", "GEMSDOE25", "GEMSDOE27", "GEMSDOE28", "GEMSDOE30", "GEMSDOE31", "GEMSDOE32", "GEMSDOE33", "GEMSDOE36")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def review_current_best(root: Path) -> dict[str, Any]:
    """Return a current exact-file review; the verdict is negative-only."""
    root = Path(root).resolve()
    # Preserve the original scientific receipt separately from the current
    # negative release card. Its historical promote field is not authorization.
    card_path = root / "evidence/parallel_mrcj_original.json"
    card = json.loads(card_path.read_text(encoding="utf-8"))
    lattice_audit = json.loads((root / "evidence/parallel_mrcj_audit.json").read_text(encoding="utf-8"))
    if (lattice_audit.get("raster", {}).get("sha256") != card.get("raster_sha256")
            or lattice_audit.get("registered_lattice", {}).get("duplicate_under_literal_rule") is not True
            or lattice_audit.get("ok_to_submit") is not False):
        raise ValueError("Independent lattice review is missing or inconsistent")
    name = card.get("submission_name")
    if not isinstance(name, str) or Path(name).name != name or not name.endswith("-zeros.tif"):
        raise ValueError("Recorded research artifact must be a plain zero-outside TIFF filename")
    artifact = root / "docs/downloads" / name
    template_path = root / "data/bridge/sample_submission.tif"
    if not artifact.is_file() or _sha256(artifact) != card.get("raster_sha256"):
        raise ValueError("Research artifact bytes do not match the immutable experiment card")

    validator = check_variants(artifact, template_path)
    if validator.get("format_valid") is not True:
        raise ValueError("Shared exact-file format validator failed")

    # Recompute the exact MRCJ surface and final-dot comparisons against the
    # requested focus-site registry. This is a registry audit, not model fitting.
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from scripts.run_experiments import surfaces

    with rasterio.open(template_path) as ds:
        template = ds.read(1)
        footprint = np.isfinite(template)
        template_crs = ds.crs
        template_shape = ds.shape
        template_transform = ds.transform
    with rasterio.open(root / "data/external/geodawn_extensions_u8.tif") as ds:
        extensions = ds.read()
    support = np.all(extensions > 0, axis=0) & footprint
    prediction_surface = surfaces(extensions, support)["E3_MRCJ"]
    with rasterio.open(artifact) as ds:
        prediction = ds.read(1)
        if (
            ds.count != 1
            or ds.dtypes != ("float32",)
            or ds.crs != template_crs
            or ds.shape != template_shape
            or ds.transform != template_transform
        ):
            raise ValueError("Research artifact metadata no longer matches the sample template")
    prediction_dots = (prediction > 0) & footprint

    recorded_rho = card.get("correlation_vs_registry", {})
    recorded_overlap = card.get("overlap_vs_registry", {})
    surface_rho: dict[str, float | None] = {}
    dot_overlaps: dict[str, float | None] = {}
    for site in SITES:
        registry_path = root / "registry/rasters" / f"{site}.tif"
        if not registry_path.is_file():
            raise FileNotFoundError(f"Required focus registry raster is missing: {registry_path}")
        with rasterio.open(registry_path) as ds:
            reference = ds.read(1)
            if ds.shape != template_shape or ds.transform != template_transform or ds.crs != template_crs:
                raise ValueError(f"Focus registry raster grid mismatch: {site}")
        reference_dots = (reference > 0) & np.isfinite(reference) & footprint
        rho = correlation(prediction_surface[footprint], np.nan_to_num(reference, nan=0.0)[footprint])
        overlap = dot_overlap(prediction_dots, reference_dots)["candidate_within_3px_of_reference"]
        surface_rho[site] = rho
        dot_overlaps[site] = overlap
        if not math.isclose(rho, recorded_rho.get(site), rel_tol=0.0, abs_tol=1e-12):
            raise ValueError(f"Pre-placement surface comparison differs from recorded card: {site}")
        if not math.isclose(overlap, recorded_overlap.get(site), rel_tol=0.0, abs_tol=1e-12):
            raise ValueError(f"Final-dot comparison differs from recorded card: {site}")

    current_card = json.loads((root / "evidence/run_card.json").read_text(encoding="utf-8"))
    if (current_card.get("raster_sha256") != card["raster_sha256"] or current_card.get("verdict") != "negative"
            or current_card.get("ok_to_submit") is not False):
        raise ValueError("Current release card must be negative and match the archived file")
    normalized_card = {
        "submission_name": name,
        "raster_sha256": card["raster_sha256"],
        "note": current_card.get("submission_note"),
        "experiments_run": card.get("experiments_run"),
        "submission_slots_used": 0 if card.get("slot_used") is False else None,
        "leakage_canary": card.get("feature_leakage_canary"),
        "holdout": card.get("holdout_dti"),
        # The historic static-comparator result has no paired replay and cannot
        # stand in for the missing same-protocol current-best comparison.
        "baseline_reproduced": False,
    }
    selector = verify_selector(artifact, template_path, normalized_card)
    holdout = card["holdout_dti"]
    if holdout.get("label") != "HOLDOUT-DTI":
        raise ValueError("Stored research result is missing its HOLDOUT-DTI evidence label")

    return {
        "schema_version": "apartgemsdoe3-current-review-v2",
        "reviewed_at_utc": datetime.now(timezone.utc).isoformat(),
        "review_scope": "Read-only exact artifact, shared format validator, and nine focus-site registry audit; no new experiment",
        "source_run_card": "evidence/parallel_mrcj_original.json",
        "source_run_card_sha256": _sha256(card_path),
        "hypothesis": card.get("hypothesis"),
        "mechanism": card.get("mechanism"),
        "named_non_fault_mimic": card.get("named_non_fault_mimic"),
        "holdout_dti": {
            "label": "HOLDOUT-DTI",
            "evaluator_version": holdout.get("evaluator_version"),
            "value": holdout.get("dti"),
            "withheld_positive_count": holdout.get("n_withheld_positive_pixels"),
            "ci_95": holdout.get("ci95", {}).get("interval"),
            "provenance": "Recorded prior experiment card; not replayed in this review.",
            "interpretation": "Internal hide-and-recover evidence only; not a leaderboard estimate.",
        },
        "static_h33_comparator": {
            "label": "HOLDOUT-DTI",
            "evaluator_version": card.get("static_incumbent_comparator", {}).get("result", {}).get("evaluator_version"),
            "value": card.get("static_incumbent_comparator", {}).get("result", {}).get("dti"),
            "withheld_positive_count": card.get("static_incumbent_comparator", {}).get("result", {}).get("n_withheld_positive_pixels"),
            "ci_95": card.get("static_incumbent_comparator", {}).get("result", {}).get("ci95", {}).get("interval"),
            "limitation": "Static comparison only; not fold-rebuilt, paired, or promotion-grade current-best evidence.",
        },
        "score_estimate": None,
        "organizer_confirmed_score": None,
        "surface_spearman_vs_focus_registry": surface_rho,
        "final_dot_overlap_within_3px_vs_focus_registry": dot_overlaps,
        "focus_registry_count": len(SITES),
        "focus_registry_scope": "The nine requested GEMSDOE site rasters only; this is not a claim that all concurrent/global submissions are covered.",
        "external_registry_hazard": {
            "evidence_label": "INDEPENDENT EXACT-FILE LATTICE AUDIT; FULL REGISTRY NOT CHECKED",
            "source_url": "evidence/parallel_mrcj_audit.json",
            "reported_rule": "Registered lattice dots within 3 pixels of the candidate dots; stop above 70%.",
            "conditional_minimum_candidate_overlap": max(0, int(np.count_nonzero(prediction_dots)) - 6649) / int(np.count_nonzero(prediction_dots)),
            "measured_candidate_overlap": lattice_audit["registered_lattice"]["candidate_within_3px_fraction"],
            "threshold": 0.70,
            "interpretation": "Independent exact-file audit measured 100% lattice overlap, so the literal duplicate rule fails. Complete registry and lattice surface checks remain unavailable.",
        },
        "novel_vs_each_focus_raster_under_thresholds": all(
            value is not None and abs(value) <= 0.90 for value in surface_rho.values()
        ) and all(value is not None and value <= 0.70 for value in dot_overlaps.values()),
        "raster_sha256": _sha256(artifact),
        "validator_output": validator,
        "selector": selector,
        "submission_name": name,
        "submission_note": current_card.get("submission_note"),
        "ok_to_download_for_research": True,
        "ok_to_submit": False,
        "new_experiments": 0,
        "submission_slots_used": 0,
        "verdict": "negative",
        "verdict_reason": "Independent audit measured 100% final-dot overlap with the registered lattice, above the 70% stop rule. The paired current-best, full registry, independent replay and live quota are missing; exterior zeros differ from null/NaN-outside text. No submission is authorized.",
    }
