#!/usr/bin/env python3
"""Independently recheck an existing parallel-run TIFF, not run a new experiment.

The archived promotion claim is superseded by the literal lattice failure. This
read-only audit does not replay the pre-placement surface, features or holdout.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

from audit_priority import ROOT, binary_rho, overlap_with_distance, read_aligned, sha256_file, verified_cached_file
from cache_shared_template import cache_template
from inspect_submission import inspect
from io_safety import validate_output_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--output", type=Path, default=ROOT / "evidence/parallel_mrcj_audit.json")
    args = parser.parse_args()
    manifest_paths = (ROOT / "registry/inputs.json", ROOT / "registry/focus_sites.json", ROOT / "registry/parallel_mrcj.json")
    validate_output_path(args.output, manifest_paths)
    inputs_manifest, site_manifest, prior_manifest = (json.loads(path.read_text()) for path in manifest_paths)
    cache = ROOT / ".cache/priority-audit"

    def fetch(item):
        return verified_cached_file(item, cache, offline=args.offline)

    inputs = {item["name"]: fetch(item) for item in inputs_manifest["inputs"]}
    prior_entries = {item["name"]: item for item in prior_manifest["files"]}
    prior = {name: fetch(item) for name, item in prior_entries.items()}
    references = {item["site"]: fetch(item) for item in site_manifest["sites"]}
    validate_output_path(args.output, manifest_paths + tuple(inputs.values()) + tuple(prior.values()) + tuple(references.values()))
    card = json.loads(prior["run_card"].read_text())
    with rasterio.open(inputs["sample_submission"]) as template:
        values = template.read(1)
        footprint = np.isfinite(values) & (template.read_masks(1) != 0)
        if template.count != 1 or template.crs is None or not footprint.any() or np.isinf(values).any():
            raise ValueError("Invalid peer template or footprint")
        expected = (template.shape, template.crs, template.transform, template.count)
    candidate, metadata = read_aligned(prior["raster"], expected)
    if not np.isfinite(candidate[footprint]).all() or not np.isin(candidate[footprint], [0, 1]).all():
        raise ValueError("Prior TIFF is not finite binary inside the peer footprint")
    dots = (candidate > 0) & footprint
    n_dots = int(dots.sum())
    if not n_dots:
        raise ValueError("Prior TIFF contains no dots")
    source_sha = sha256_file(prior["raster"])
    if source_sha != card["raster_sha256"]:
        raise ValueError("Prior raster and prior run card disagree on SHA-256")
    comparisons = []
    for site, path in references.items():
        values, _ = read_aligned(path, expected)
        if not np.isfinite(values[footprint]).all() or not np.isin(values[footprint], [0, 1]).all():
            raise ValueError(f"Invalid historical comparator: {site}")
        ref = (values > 0) & footprint
        if not ref.any():
            raise ValueError(f"Empty historical comparator: {site}")
        distance = distance_transform_edt(~ref)
        comparisons.append({
            "reference": site,
            "final_dot_spearman": binary_rho(n_dots, int(ref.sum()), int((dots & ref).sum()), int(footprint.sum())),
            "candidate_within_3px_fraction": overlap_with_distance(dots, distance),
        })
        del values, ref, distance
    values, _ = read_aligned(inputs["lattice"], expected)
    if not np.isfinite(values[footprint]).all() or not np.isin(values[footprint], [0, 1]).all():
        raise ValueError("Invalid lattice")
    lattice = (values > 0) & footprint
    if not lattice.any():
        raise ValueError("Empty lattice comparator")
    distance = distance_transform_edt(~lattice)
    lattice_overlap = overlap_with_distance(dots, distance)
    lattice_rho = binary_rho(n_dots, int(lattice.sum()), int((dots & lattice).sum()), int(footprint.sum()))
    diagnostic = inspect(prior["raster"], inputs["sample_submission"], cache_template(offline=args.offline))
    h = card["holdout_dti"]
    entry = prior_entries["raster"]
    source_url = f"https://github.com/{entry['repo']}/blob/{entry['ref']}/{entry['path']}"
    result = {
        "schema": "apartgemsdoe3-parallel-mrcj-review-v1",
        "checked_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "Read-only exact-file review of a parallel run; no new experiment, upload or promotion.",
        "raster": {"file": Path(entry["path"]).name, "source": source_url, "sha256": source_sha,
                   "dots": n_dots, "metadata": metadata},
        "recorded_holdout_not_replayed": {
            "label": h["label"], "evaluator_version": h["evaluator_version"],
            "withheld_positive_pixels": h["n_withheld_positive_pixels"], "value": h["dti"],
            "ci95": h["ci95"]["interval"],
            "source": "evidence/parallel_mrcj_original.json",
            "limitation": "Recorded by the parallel run; not independently replayed, not an organizer score, and not compared with a verified fold-rebuilt best.",
        },
        "original_claim": {"verdict": card["verdict"], "ok_to_submit": card["ok_to_submit"],
                           "scope": "Only nine selected site rasters; the literal registered lattice was omitted.",
                           "status": "Superseded: not approved by this review."},
        "final_dots_vs_historical_nine": comparisons,
        "maximum_final_overlap_vs_historical_nine": max(comparisons, key=lambda row: row["candidate_within_3px_fraction"]),
        "registered_lattice": {"candidate_within_3px_fraction": lattice_overlap,
                               "final_dot_spearman": lattice_rho,
                               "duplicate_under_literal_rule": lattice_overlap > .70},
        "preplacement_surface_replayed": False,
        "complete_registry_checked": False,
        "format_inspection": diagnostic,
        "verdict": "negative",
        "ok_to_submit": False,
        "weekly_slot_used_in_this_review": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"file": entry["path"], "sha256": source_sha, "dots": n_dots,
                      "overlap_vs_lattice": lattice_overlap, "verdict": "negative", "ok_to_submit": False}, indent=2))


if __name__ == "__main__":
    main()
