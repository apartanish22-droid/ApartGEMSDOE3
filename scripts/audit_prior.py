#!/usr/bin/env python3
"""Audit the nine named historical rasters and one lattice witness, not a model.

Fetch with `scripts/fetch_assets.py --groups core history` first. Does not run a
geological experiment, produce a candidate, or imply a complete registry scan.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

import numpy as np
import rasterio
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "vendor"))
sys.path.insert(0, str(ROOT / "scripts"))
from template_utils import verify_template  # noqa: E402
verify_template()  # Never import a missing or modified shared template.
from gems57 import uniqueness  # noqa: E402
from fetch_assets import sha256_file  # noqa: E402


def binary_rank_correlation(a: np.ndarray, b: np.ndarray, footprint: np.ndarray) -> float | None:
    """Exact Spearman for binary values, including ties, on the footprint."""
    n = int(footprint.sum())
    if n == 0:
        raise ValueError("empty footprint")
    na, nb = int((a & footprint).sum()), int((b & footprint).sum())
    den = (na * (n - na) * nb * (n - nb)) ** 0.5
    if not den:
        return None
    both = int((a & b & footprint).sum())
    return float((n * both - na * nb) / den)


def lower_overlap_bound(dot_count: int, uncovered: int) -> float:
    """Pigeonhole bound for distinct, in-footprint positive pixels."""
    if dot_count <= 0 or uncovered < 0:
        raise ValueError("dot_count must be positive and uncovered nonnegative")
    return max(0, dot_count - uncovered) / dot_count


def load_pinned(record: dict, root: Path, expected_grid=None):
    path = root / record["destination"]
    if not path.is_file() or sha256_file(path) != record["sha256"]:
        raise ValueError(f"missing or hash-mismatched: {record['id']}")
    with rasterio.open(path) as dataset:
        if dataset.count != 1:
            raise ValueError(f"not a single band: {record['id']}")
        actual_grid = (dataset.shape, dataset.crs, dataset.transform)
        if expected_grid is not None and actual_grid != expected_grid:
            raise ValueError(f"CRS, shape or transform mismatch: {record['id']}")
        values = dataset.read(1)
        metadata = {
            "shape": list(dataset.shape), "crs": str(dataset.crs),
            "transform": list(dataset.transform)[:6], "dtype": dataset.dtypes[0],
            "nodata": None if dataset.nodata is None else str(dataset.nodata),
        }
    return values, actual_grid, metadata


def describe(values: np.ndarray, footprint: np.ndarray, metadata: dict) -> dict:
    finite = np.isfinite(values)
    bad_range = finite & ((values < 0) | (values > 1))
    return {
        **metadata,
        "positive_footprint_pixels": int((finite & (values > 0) & footprint).sum()),
        "nonfinite_footprint_pixels": int((~finite & footprint).sum()),
        "out_of_range_footprint_pixels": int((bad_range & footprint).sum()),
        "nonfinite_all_pixels": int((~finite).sum()),
        "finite_out_of_range_all_pixels": int(bad_range.sum()),
        "strict_all_finite_and_in_range": bool(finite.all() and not bad_range.any()),
        "inside_footprint_finite_and_in_range": bool((finite | ~footprint).all() and not (bad_range & footprint).any()),
        "all_footprint_values_binary": bool(np.isin(values[footprint], [0, 1]).all()),
    }


def run(cache: Path) -> dict:
    man = json.loads((ROOT / "registry/input_manifest.json").read_text())
    claim = json.loads((ROOT / "registry/user_claims.json").read_text())
    records = {r["id"]: r for r in man["files"]}
    sample, grid, sample_meta = load_pinned(records["sample"], cache)
    footprint = np.isfinite(sample)
    if not footprint.any():
        raise ValueError("the pinned sample has no finite footprint")
    labels, _, label_meta = load_pinned(records["labels"], cache, grid)
    catalogue = labels > 0
    lattice, _, lattice_meta = load_pinned(records["lattice"], cache, grid)
    lattice_dots = uniqueness._dots(lattice) & footprint
    covered = uniqueness._near(lattice_dots)
    uncovered = int((footprint & ~covered).sum())
    certificate = uniqueness.saturation_certificate(
        cache / records["lattice"]["destination"], footprint, expected_grid=grid)
    if certificate["uncovered_allowed_pixels"] != uncovered:
        raise AssertionError("shared certificate disagrees with literal support calculation")
    historic: dict[str, dict] = {}
    masks: dict[str, np.ndarray] = {}
    for ident in claim["claims"]:
        rec = records[ident]
        arr, _, meta = load_pinned(rec, cache, grid)
        desc = describe(arr, footprint, meta)
        if not desc["all_footprint_values_binary"]:
            raise ValueError(f"binary historical comparison not applicable: {ident}")
        mask = uniqueness._dots(arr) & footprint
        masks[ident] = mask
        historic[ident] = {
            "filename": Path(rec["path"]).name,
            "source": f"https://github.com/{rec['repo']}/blob/{rec['ref']}/{rec['path']}",
            "source_commit": rec["ref"], "sha256": rec["sha256"],
            "claimed_score": claim["claims"][ident],
            "claimed_score_evidence": "USER-REPORTED / UNVERIFIED; no organizer receipt located",
            "estimated_organizer_score": None,
            "format_diagnostics": desc,
            "lattice_overlap": float(covered[mask].mean()) if mask.any() else None,
        }
    comparisons = []
    for ref, refmask in masks.items():
        near = uniqueness._near(refmask)  # shared template's literal <=3-px disk
        for name, mask in masks.items():
            if name == ref:
                continue
            overlap = float(near[mask].mean()) if mask.any() else None
            rho = binary_rank_correlation(mask, refmask, footprint)
            comparisons.append({"candidate": name, "reference": ref,
                                "overlap_within_3px": overlap, "spearman_binary": rho,
                                "duplicate": bool((overlap is not None and overlap > .70)
                                                  or (rho is not None and rho > .90))})
    for ident in historic:
        rows = [r for r in comparisons if r["candidate"] == ident]
        worst = max(rows, key=lambda r: r["overlap_within_3px"])
        historic[ident]["nine_site_uniqueness"] = {
            "complete_against_eight_named_history_files": len(rows) == 8,
            "duplicate_against_any": any(r["duplicate"] for r in rows),
            "worst_reference": worst["reference"],
            "worst_overlap_within_3px": worst["overlap_within_3px"],
            "scope": "nine specified historical files only; not the full registry or pre-placement surfaces",
        }
    distance = ndimage.distance_transform_edt(~catalogue)
    d25, d31, h33, p36 = (masks[f"GEMSDOE{i}"] for i in (25, 31, 32, 36))
    forensics = {
        "site25_and_30_identical_positive_support": bool(np.array_equal(d25, masks["GEMSDOE30"])),
        "h33_equals_site25_after_catalogue_distance_gt_2px": bool(np.array_equal(h33, d25 & (distance > 2))),
        "h33_subset_of_site31": bool(np.all(d31[h33])),
        "site31_extra_pixels_over_h33": int((d31 & ~h33).sum()),
        "h33_subset_of_site36": bool(np.all(p36[h33])),
        "site36_extra_pixels_over_h33": int((p36 & ~h33).sum()),
    }
    return {
        "evidence_class": "GEOMETRY-AND-FORMAT-AUDIT, NOT HOLDOUT-DTI OR A LEADERBOARD SCORE",
        "observed_utc": datetime.now(timezone.utc).isoformat(),
        "source_scope": "Pinned third-party mirrors; private submissions, later artifacts and pre-placement surfaces not checked.",
        "experiments_run": 0, "submission_slots_used": 0,
        "reference_grid": sample_meta,
        "sample_footprint_cells": int(footprint.sum()),
        "sample_positive_cells": int(((sample > 0) & footprint).sum()),
        "sample_positive_equals_catalogue": bool(np.array_equal((sample > 0) & footprint, catalogue & footprint)),
        "sample_caveat": "Pinned owner mirror claims to be a sample; it contains catalogue positives despite the official page describing a zero-prediction sample. Official identity is not established.",
        "label_meta": label_meta,
        "lattice": {**certificate, "witness_file": records["lattice"]["path"],
                    "source": f"https://github.com/{records['lattice']['repo']}/blob/{records['lattice']['ref']}/{records['lattice']['path']}",
                    "metadata": lattice_meta,
                    "bound_at_37654_distinct_dots": lower_overlap_bound(37654, uncovered),
                    "maximum_possible_distinct_dots_at_70pct_from_count_bound": (uncovered * 10) // 3,
                    "bound_caveat": "Necessary counting bound only; smaller budgets are not thereby proven unique or scientifically valid."},
        "historic": historic,
        "pairwise": comparisons,
        "forensics": forensics,
        "promotion_status": "negative: no candidate, no holdout, incomplete registry, no selector approval",
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cache", type=Path, default=ROOT / ".cache/inputs")
    ap.add_argument("--out", type=Path, default=ROOT / "evidence/prior_audit.json")
    args = ap.parse_args(argv)
    try:
        report = run(args.cache)
    except (ValueError, OSError, rasterio.errors.RasterioError) as exc:
        print(f"AUDIT FAILED; do not promote: {exc}", file=sys.stderr)
        return 1
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(f"Wrote {args.out}; historical comparison only, no candidate and no score estimate.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
