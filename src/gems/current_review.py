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
from scipy.stats import rankdata

from .novelty import dot_overlap, rank_correlation
from .selector import verify_selector
from .submission import check_variants

SITES = ("GEMSDOE24", "GEMSDOE25", "GEMSDOE27", "GEMSDOE28", "GEMSDOE30", "GEMSDOE31", "GEMSDOE32", "GEMSDOE33", "GEMSDOE36")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _recorded_lattice_audit(root: Path, artifact_sha: str, dot_count: int) -> dict[str, Any]:
    """Read the separately reproduced witness only if its input identities agree.

    This endpoint does not recompute the lattice itself. A missing or inconsistent
    record is explicitly unavailable; it never turns an incomplete scan into a pass.
    """
    try:
        audit_path = root / "evidence/mrcj_audit.json"
        audit = json.loads(audit_path.read_text(encoding="utf-8"))
        manifest = json.loads((root / "registry/input_manifest.json").read_text(encoding="utf-8"))
        pins = {item["id"]: item for item in manifest["files"]}
        count, overlap = audit["three_pixel_overlap_count"], audit["three_pixel_overlap_fraction"]
        if (audit["candidate_sha256"] != artifact_sha
                or audit["reference"]["sha256"] != pins["lattice"]["sha256"]
                or _sha256(root / "data/bridge/sample_submission.tif") != pins["sample"]["sha256"]
                or audit["candidate_in_footprint_dots"] != dot_count
                or type(count) is not int or type(dot_count) is not int
                or not 0 <= count <= dot_count or dot_count <= 0
                or not math.isclose(overlap, count / dot_count, rel_tol=0, abs_tol=1e-12)):
            raise ValueError("lattice record or input identities disagree")
        return {"status": "recorded independent measurement; not rerun in this endpoint",
                "observed_utc": audit["observed_utc"], "report": "evidence/mrcj_audit.json",
                "reference_sha256": pins["lattice"]["sha256"], "overlapping_dots": count,
                "candidate_dots": dot_count, "overlap_fraction": overlap,
                "duplicate_by_overlap": overlap > .70, "complete_registry_checked": False}
    except (OSError, ValueError, KeyError, TypeError, ZeroDivisionError):
        return {"status": "unavailable or inconsistent; not a uniqueness pass",
                "duplicate_by_overlap": None, "complete_registry_checked": False}


def review_current_best(root: Path) -> dict[str, Any]:
    """Return a current exact-file review; the verdict is negative-only."""
    root = Path(root).resolve()
    card_path = root / "evidence/run_card.json"
    card = json.loads(card_path.read_text(encoding="utf-8"))
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
    # The candidate is the same in every comparison: compute its average
    # Spearman ranks once instead of sorting ~5 million pixels nine times.
    prediction_ranks = rankdata(prediction_surface[footprint])

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
        rho = rank_correlation(prediction_ranks, np.nan_to_num(reference, nan=0.0)[footprint])
        overlap = dot_overlap(prediction_dots, reference_dots)["candidate_within_3px_of_reference"]
        surface_rho[site] = rho
        dot_overlaps[site] = overlap
        if not math.isclose(rho, recorded_rho.get(site), rel_tol=0.0, abs_tol=1e-12):
            raise ValueError(f"Pre-placement surface comparison differs from recorded card: {site}")
        if not math.isclose(overlap, recorded_overlap.get(site), rel_tol=0.0, abs_tol=1e-12):
            raise ValueError(f"Final-dot comparison differs from recorded card: {site}")

    normalized_card = {
        "submission_name": name,
        "raster_sha256": card["raster_sha256"],
        "note": card.get("submission_note"),
        "experiments_run": card.get("experiments_run"),
        "submission_slots_used": 0 if card.get("slot_used") is False else None,
        "leakage_canary": card.get("feature_leakage_canary"),
        "holdout": card.get("holdout_dti"),
        # The historic static-comparator result has no paired replay and cannot
        # stand in for the missing same-protocol current-best comparison.
        "baseline_reproduced": False,
    }
    selector = verify_selector(artifact, template_path, normalized_card)
    # This read-only endpoint cannot silently become an upload-authorization
    # path if the selector changes in a future revision.
    if selector.get("ok_to_submit") is not False or selector.get("decision") != "DO_NOT_SUBMIT":
        raise ValueError("Review-only endpoint cannot authorize promotion")
    holdout = card["holdout_dti"]
    if holdout.get("label") != "HOLDOUT-DTI":
        raise ValueError("Stored research result is missing its HOLDOUT-DTI evidence label")
    lattice_audit = _recorded_lattice_audit(root, card["raster_sha256"], int(np.count_nonzero(prediction_dots)))

    return {
        "schema_version": "apartgemsdoe3-current-review-v3",
        "reviewed_at_utc": datetime.now(timezone.utc).isoformat(),
        "review_scope": "Read-only exact artifact, shared format validator, nine focus-site comparisons and a separately recorded lattice audit; no new experiment or holdout replay",
        "source_run_card": "evidence/run_card.json",
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
            "evidence_label": "PINNED-LATTICE-GEOMETRY; SEE SEPARATE AUDIT RECORD",
            "source_url": "https://buffedlizard55-lab.github.io/GEMSDOE28/",
            "reported_rule": "A 3-pixel calibration lattice leaves 6,649 footprint cells uncovered on the pinned mirror grid.",
            "conditional_minimum_candidate_overlap": max(0, int(np.count_nonzero(prediction_dots)) - 6649) / int(np.count_nonzero(prediction_dots)),
            "threshold": 0.70,
            "interpretation": "The bound is corroborated on the pinned inputs; the independently recorded actual dot overlap is 100% when the hash-bound audit record is available. This review does not rerun that audit or check the full registry.",
        },
        "independent_lattice_audit": lattice_audit,
        "novel_vs_each_focus_raster_under_thresholds": all(
            value is not None and abs(value) <= 0.90 for value in surface_rho.values()
        ) and all(value is not None and value <= 0.70 for value in dot_overlaps.values()),
        "raster_sha256": _sha256(artifact),
        "validator_output": validator,
        "selector": selector,
        "submission_name": name,
        "submission_note": "MRCJ research only; 100% overlap with registered lattice. DO NOT SUBMIT." if lattice_audit.get("duplicate_by_overlap") else "MRCJ research only; independent uniqueness is not established. DO NOT SUBMIT.",
        "ok_to_download_for_research": True,
        "ok_to_submit": False,
        "new_experiments": 0,
        "submission_slots_used": 0,
        "verdict": "negative",
        "verdict_reason": ("Independent recorded lattice audit triggers the >70% final-dot stop; " if lattice_audit.get("duplicate_by_overlap") else "Full-registry novelty is unresolved; ") + "the paired current-best, exact-file C2ST and independently verified quota/replay evidence are also missing. Exterior zeros differ from one strict reading of the competition page's null/NaN-outside instruction; portal acceptance is unknown. No submission is authorized.",
    }
