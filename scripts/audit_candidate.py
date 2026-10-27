#!/usr/bin/env python3
"""Measure a candidate against one pinned lattice witness; never clear a slot.

A single violating reference is sufficient to stop. A passing reference is NOT
proof of uniqueness against the complete parallel registry or of scientific
validity. Reads existing rasters; does not fit a model or produce a GeoTIFF.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

import numpy as np
import rasterio

from audit_prior import ROOT, binary_rank_correlation, load_pinned
from fetch_assets import sha256_file
from gems57 import uniqueness
from validate_submission import check


def run(candidate: Path, cache: Path, source: str, include_history: bool = False) -> dict:
    manifest = json.loads((ROOT / "registry/input_manifest.json").read_text())
    records = {r["id"]: r for r in manifest["files"]}
    sample, grid, _ = load_pinned(records["sample"], cache)
    fp = np.isfinite(sample)
    if not fp.any():
        raise ValueError("empty provisional footprint")
    lattice, _, _ = load_pinned(records["lattice"], cache, grid)
    reference = uniqueness._dots(lattice) & fp
    with rasterio.open(candidate) as src:
        if src.count != 1 or (src.shape, src.crs, src.transform) != grid:
            raise ValueError("candidate band count or grid does not match pinned mirror")
        values = src.read(1)
    dots = uniqueness._dots(values) & fp
    count = int(dots.sum())
    if not count:
        raise ValueError("candidate has no positive finite footprint pixels")
    outside = int((uniqueness._dots(values) & ~fp).sum())
    near_count = int((uniqueness._near(reference) & dots).sum())
    fraction = near_count / count
    rho = binary_rank_correlation(dots, reference, fp)
    history = None
    if include_history:
        history_records = [r for r in manifest["files"] if r.get("group") == "history"]
        if len(history_records) != 9:
            raise ValueError("expected exactly nine pinned historical files")
        history = []
        for record in history_records:
            arr, _, _ = load_pinned(record, cache, grid)
            ref_dots = uniqueness._dots(arr) & fp
            overlap = float(uniqueness._near(ref_dots)[dots].mean())
            history.append({"id": record["id"], "sha256": record["sha256"],
                            "candidate_dot_overlap_within_3px": overlap,
                            "final_binary_support_spearman": binary_rank_correlation(dots, ref_dots, fp),
                            "duplicate_by_overlap": overlap > .70})
    format_report = check(candidate, cache)
    local_checks = format_report["local"]["checks"]
    return {
        "observed_utc": datetime.now(timezone.utc).isoformat(),
        "evidence_class": "LITERAL REGISTRY GEOMETRY AND LOCAL FORMAT, NOT A SCORE",
        "source": source, "candidate_sha256": sha256_file(candidate),
        "candidate_in_footprint_dots": count, "candidate_outside_positive_pixels": outside,
        "reference": {
            "id": records["lattice"]["id"], "sha256": records["lattice"]["sha256"],
            "source": f"https://github.com/{records['lattice']['repo']}/blob/{records['lattice']['ref']}/{records['lattice']['path']}",
        },
        "three_pixel_overlap_count": near_count,
        "three_pixel_overlap_fraction": fraction,
        "final_binary_support_spearman": rho,
        "surface_rank_correlation": None,
        "surface_reason": "Pre-placement surface unavailable; final binary support is not a surface-stage check.",
        "duplicate_by_overlap": bool(fraction > .70),
        "historical_comparisons": history,
        "complete_registry_checked": False,
        "format": {
            "local_format_passed": format_report["format_passed"],
            "in_footprint_all_finite": local_checks["in_footprint_all_finite"],
            "in_footprint_range_0_1": local_checks["in_footprint_range_0_1"],
            "crs": format_report["template"]["crs"],
            "shape": [format_report["template"]["height"], format_report["template"]["width"]],
            "transform": format_report["template"]["transform"],
            "whole_array_finite": local_checks["no_nan_anywhere"],
            "organizer_acceptance": None,
        },
        "scope": "One decisive witness only; third-party mirror footprint unverified, not the complete registry or a portal receipt.",
        "approved_for_weekly_slot": False, "verdict": "negative",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--cache", type=Path, default=ROOT / ".cache/inputs")
    parser.add_argument("--source", default="local file; source not independently provided")
    parser.add_argument("--history", action="store_true", help="Also compare final dots to the nine pinned historical files")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = run(args.candidate, args.cache, args.source, include_history=args.history)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    except (OSError, ValueError, rasterio.errors.RasterioError) as exc:
        print(f"AUDIT FAILED; do not promote: {exc}", file=sys.stderr)
        return 1
    print(f"Wrote {args.out}; duplicate_by_overlap={result['duplicate_by_overlap']}; no candidate clearance or slot approval.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
