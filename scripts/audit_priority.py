#!/usr/bin/env python3
"""Read-only, pinned-file nine-site forensic audit. No fitting or submissions.

Run: .venv/bin/python scripts/audit_priority.py
All historical rasters are comparison-only; the mirror is not organizer-authenticated.
The script stops on an integrity/grid error and never reports a new candidate.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt
from io_safety import validate_output_path

ROOT = Path(__file__).resolve().parents[1]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_blob_file(path: Path) -> str:
    """Compute Git's blob object ID, without trusting downloaded headers."""
    h = hashlib.sha1(usedforsecurity=False)  # Git object identity, not security.
    h.update(f"blob {path.stat().st_size}\0".encode())
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def verified_cached_file(entry: dict, cache: Path, *, offline: bool = False) -> Path:
    cache.mkdir(parents=True, exist_ok=True)
    path = cache / f"{entry['git_blob']}.tif"

    def correct(candidate: Path) -> bool:
        return (
            candidate.is_file()
            and candidate.stat().st_size == entry["size"]
            and git_blob_file(candidate) == entry["git_blob"]
        )

    if correct(path):
        return path
    if offline:
        raise FileNotFoundError(f"Missing or invalid cached blob: {entry['repo']}/{entry['path']}")
    # A fixed commit and expected blob hash protect against mutable branch heads.
    endpoint = f"repos/{entry['repo']}/contents/{quote(entry['path'], safe='/')}?ref={entry['ref']}"
    fd, temporary = tempfile.mkstemp(prefix="fetch-", suffix=".tmp", dir=cache)
    tmp = Path(temporary)
    try:
        with os.fdopen(fd, "wb") as dest:
            result = subprocess.run(
                ["gh", "api", "-H", "Accept: application/vnd.github.raw+json", endpoint],
                stdout=dest, stderr=subprocess.PIPE, check=False,
            )
        if result.returncode:
            raise RuntimeError(f"GitHub fetch failed for {endpoint}: {result.stderr.decode(errors='replace')}")
        if not correct(tmp):
            raise ValueError(f"Size/blob mismatch for {entry['repo']}/{entry['path']}")
        tmp.replace(path)
    finally:
        tmp.unlink(missing_ok=True)
    return path


def read_aligned(path: Path, expected: tuple) -> tuple[np.ndarray, dict]:
    with rasterio.open(path) as dataset:
        got = (dataset.shape, dataset.crs, dataset.transform, dataset.count)
        if got != expected:
            raise ValueError(f"Grid or band count mismatch: {path.name}: {got} vs {expected}")
        values = dataset.read(1)
        metadata = {
            "dtype": dataset.dtypes[0],
            "nodata": None if dataset.nodata is None or np.isnan(dataset.nodata) else float(dataset.nodata),
            "nodata_is_nan": bool(dataset.nodata is not None and np.isnan(dataset.nodata)),
        }
    return values, metadata


def binary_rho(a_count: int, b_count: int, intersection: int, n: int) -> float | None:
    """Full-footprint Spearman for binary masks (tied average ranks)."""
    if n <= 0 or not 0 <= intersection <= min(a_count, b_count) or max(a_count, b_count) > n:
        raise ValueError("Invalid binary contingency counts")
    denominator = (a_count * (n - a_count) * b_count * (n - b_count)) ** 0.5
    return None if denominator == 0 else float((n * intersection - a_count * b_count) / denominator)


def overlap_with_distance(candidate: np.ndarray, distance_to_reference: np.ndarray) -> float | None:
    if candidate.shape != distance_to_reference.shape:
        raise ValueError("Candidate/reference grid mismatch")
    n = int(candidate.sum())
    return None if not n else float(np.count_nonzero(distance_to_reference[candidate] <= 3.0) / n)


def overlap_lower_bound(candidate_count: int, uncovered_count: int) -> dict:
    """Necessary overlap under the *literal* >70% rule, not a novelty pass."""
    if candidate_count <= 0 or uncovered_count < 0:
        raise ValueError("Positive candidate count and nonnegative uncovered count required")
    must_overlap = max(0, candidate_count - uncovered_count)
    return {
        "candidate_dots": candidate_count,
        "uncovered_pixels": uncovered_count,
        "minimum_overlap_dots": must_overlap,
        "minimum_overlap_fraction": must_overlap / candidate_count,
        "necessarily_exceeds_70_percent": 10 * must_overlap > 7 * candidate_count,
    }


def run(offline: bool = False, output: Path | None = None) -> dict:
    manifests = (ROOT / "registry/focus_sites.json", ROOT / "registry/inputs.json")
    if output:
        validate_output_path(output, manifests)
    manifest, input_manifest = (json.loads(path.read_text()) for path in manifests)
    cache = ROOT / ".cache/priority-audit"
    inputs = {x["name"]: verified_cached_file(x, cache, offline=offline) for x in input_manifest["inputs"]}
    site_paths = {x["site"]: verified_cached_file(x, cache, offline=offline) for x in manifest["sites"]}
    if output:
        validate_output_path(output, manifests + tuple(inputs.values()) + tuple(site_paths.values()))
    with rasterio.open(inputs["sample_submission"]) as sample:
        if sample.count != 1 or sample.crs is None:
            raise ValueError("Mirror template must be a georeferenced single band")
        expected = (sample.shape, sample.crs, sample.transform, sample.count)
        sample_array = sample.read(1)
        template_info = {
            "sha256": sha256_file(inputs["sample_submission"]),
            "shape": list(sample.shape),
            "crs": sample.crs.to_string(),
            "transform": list(sample.transform)[:6],
            "source": "peer-mirrored template, NOT authenticated as organizer sample",
        }
    footprint = np.isfinite(sample_array)
    if not footprint.any() or np.isinf(sample_array).any():
        raise ValueError("Invalid footprint in mirror")
    labels, _ = read_aligned(inputs["labels"], expected)
    if not np.isin(labels[footprint], [0, 1]).all():
        raise ValueError("Non-binary label values within mirror footprint")
    labels_mask = (labels == 1) & footprint
    sample_one = (sample_array == 1) & footprint
    contamination = {
        "sample_sha256": template_info["sha256"],
        "labels_sha256": sha256_file(inputs["labels"]),
        "sample_positive_pixels": int(sample_one.sum()),
        "label_positive_pixels": int(labels_mask.sum()),
        "positive_intersection": int((sample_one & labels_mask).sum()),
        "sample_values_equal_labels_on_footprint": bool(np.array_equal(sample_array[footprint], labels[footprint])),
        "warning": "Mirror sample contains label values; use its finite mask/grid only, never prediction values as a feature or prediction. Organizer sample authenticity unverified.",
    }
    template_info["footprint_pixels"] = int(footprint.sum())
    template_info["footprint_sha256"] = hashlib.sha256(np.packbits(footprint.ravel(), bitorder="big").tobytes()).hexdigest()
    del sample_array, sample_one

    lattice_values, lattice_meta = read_aligned(inputs["lattice"], expected)
    if not np.isfinite(lattice_values[footprint]).all() or not np.isin(lattice_values[footprint], [0, 1]).all():
        raise ValueError("Lattice comparator is not binary and finite inside footprint")
    lattice = (lattice_values > 0) & footprint
    if not lattice.any():
        raise ValueError("Empty lattice is not a valid overlap comparator")
    lattice_distance = distance_transform_edt(~lattice)
    covered = int(np.count_nonzero(footprint & (lattice_distance <= 3.0)))
    uncovered = int(footprint.sum()) - covered
    lattice_report = {
        "repo": "buffedlizard55-lab/13GEMSDOE",
        "source": next(x for x in input_manifest["inputs"] if x["name"] == "lattice"),
        "sha256": sha256_file(inputs["lattice"]),
        "metadata": lattice_meta,
        "positive_pixels": int(lattice.sum()),
        "within_3px_footprint_pixels": covered,
        "outside_3px_footprint_pixels": uncovered,
        "within_3px_footprint_fraction": covered / int(footprint.sum()),
        "maximum_dot_budget_not_ruled_out_by_bound": (10 * uncovered) // 3,
        "note": "A necessary overlap bound, not an actual candidate or novelty pass. Never tune around uncovered cells.",
    }
    del lattice_values, lattice

    artifacts, masks = {}, {}
    for row in manifest["sites"]:
        path = site_paths[row["site"]]
        values, metadata = read_aligned(path, expected)
        inside = values[footprint]
        finite = np.isfinite(inside)
        if not finite.all() or np.any((inside < 0) | (inside > 1)):
            raise ValueError(f"Invalid in-footprint values in {row['site']}")
        binary = bool(np.isin(inside, [0, 1]).all())
        if not binary:
            raise ValueError(f"Historical file is not a binary dot raster: {row['site']}")
        mask = (values > 0) & footprint
        if not mask.any():
            raise ValueError(f"Empty historical comparator: {row['site']}")
        masks[row["site"]] = mask
        global_finite_range = bool(np.isfinite(values).all() and np.all((values >= 0) & (values <= 1)))
        outside_all_nan = bool(np.isnan(values[~footprint]).all())
        with rasterio.open(path) as raster:
            null_mask = raster.read_masks(1) == 0
        outside_null_or_nan = bool(np.all(null_mask[~footprint] | np.isnan(values[~footprint])))
        inside_masked = int(np.count_nonzero(null_mask & footprint))
        metadata.update({
            "grid_matches_peer_mirror": True,
            "in_footprint_nan_or_inf": int((~finite).sum()),
            "in_footprint_min": float(inside.min()),
            "in_footprint_max": float(inside.max()),
            "single_band_float32": metadata["dtype"] == "float32",
            "whole_array_finite_in_0_1": global_finite_range,
            "outside_footprint_all_nan": outside_all_nan,
            "outside_footprint_null_or_nan": outside_null_or_nan,
            "masked_pixels_inside_mirrored_footprint": inside_masked,
            "organizer_template_authenticity_verified": False,
            "portal_acceptance_verified": False,
        })
        count = int(mask.sum())
        artifacts[row["site"]] = {
            "file": Path(row["path"]).name,
            "source_url": row["source_url"],
            "sha256": sha256_file(path),
            "git_blob": git_blob_file(path),
            "bytes": path.stat().st_size,
            "positive_mask_sha256": hashlib.sha256(np.packbits(mask.ravel(), bitorder="big").tobytes()).hexdigest(),
            "positive_pixels": count,
            "positive_on_mirrored_catalogue": int((mask & labels_mask).sum()),
            "historical_user_reported_value_unverified": row["historical_value"],
            "value_status": "USER-REPORTED / UNVERIFIED; no organizer receipt",
            "estimated_organizer_score": None,
            "validator": metadata,
            "candidate_overlap_with_lattice_within_3px": overlap_with_distance(mask, lattice_distance),
            "lattice_lower_bound": overlap_lower_bound(count, uncovered),
            "ok_to_submit": False,
        }
        del values, inside

    del lattice_distance
    pairs = []
    sites = [x["site"] for x in manifest["sites"]]
    n = int(footprint.sum())
    for reference_site in sites:
        reference = masks[reference_site]
        if not reference.any():
            raise ValueError(f"Empty comparator {reference_site}")
        distance = distance_transform_edt(~reference)
        for candidate_site in sites:
            if candidate_site == reference_site:
                continue
            candidate = masks[candidate_site]
            intersection = int(np.count_nonzero(candidate & reference))
            a, b = artifacts[candidate_site]["positive_pixels"], artifacts[reference_site]["positive_pixels"]
            overlap = overlap_with_distance(candidate, distance)
            rho = binary_rho(a, b, intersection, n)
            pairs.append({
                "candidate": candidate_site, "reference": reference_site,
                "candidate_within_3px_fraction": overlap,
                "full_footprint_binary_spearman": rho,
                "common_positive_pixels": intersection,
                "candidate_only": a - intersection,
                "reference_only": b - intersection,
                "literal_duplicate": bool((overlap is not None and overlap > .70) or (rho is not None and abs(rho) > .90)),
            })
        del distance

    for site in sites:
        own = [x for x in pairs if x["candidate"] == site]
        strongest = max(own, key=lambda x: x["candidate_within_3px_fraction"])
        artifacts[site]["highest_historical_overlap"] = {
            "reference": strongest["reference"],
            "fraction": strongest["candidate_within_3px_fraction"],
        }
        artifacts[site]["unique_vs_eight_historical_rasters"] = not any(x["literal_duplicate"] for x in own)

    # Verify the asserted ancestry directly from the saved pixels, not filenames.
    cat_distance = distance_transform_edt(~labels_mask)
    d28, h33, solo, anderson = (masks[s] for s in ("GEMSDOE25", "GEMSDOE32", "GEMSDOE31", "GEMSDOE36"))
    predicted_h33 = d28 & (cat_distance > 2.0)
    lineage = {
        "source": "pixel-exact comparison of the pinned historical TIFFs and peer-mirrored label raster",
        "d28_equals_gemsdoe30_on_footprint": bool(np.array_equal(d28, masks["GEMSDOE30"])),
        "h33_equals_d28_after_removing_at_most_2px_from_mirrored_catalogue": bool(np.array_equal(h33, predicted_h33)),
        "d28_dots_removed_by_2px_rule": int(np.count_nonzero(d28 & (cat_distance <= 2.0))),
        "h33_new_dots_vs_d28": int(np.count_nonzero(h33 & ~d28)),
        "h33_new_dots_vs_solo": int(np.count_nonzero(h33 & ~solo)),
        "solo_dots_removed_to_h33": int(np.count_nonzero(solo & ~h33)),
        "anderson_contains_all_h33_dots": bool(np.all(~h33 | anderson)),
        "anderson_dots_not_in_h33": int(np.count_nonzero(anderson & ~h33)),
        "limitation": "Geometry does not reveal hidden truth, causal score changes, or an organizer receipt.",
    }
    report = {
        "schema": "apartgemsdoe3-historical-forensics-v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "Nine pinned historical rasters plus one lattice; read-only geometry and file inspection, not an experiment, complete registry, scientific validation, or score receipt.",
        "template": template_info,
        "mirror_sample_label_contamination": contamination,
        "lattice_geometry": lattice_report,
        "lineage": lineage,
        "artifacts": artifacts,
        "pairwise_directional_comparisons": pairs,
        "experiments_run": 0,
        "weekly_slots_used": 0,
        "new_rasters_generated": 0,
        "surface_novelty_checked": False,
        "candidate_novelty_checked": False,
        "submission_authorized": False,
    }
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--offline", action="store_true", help="Use already-verified local cache only")
    parser.add_argument("--output", type=Path, default=ROOT / "evidence/historical_audit.json")
    args = parser.parse_args()
    report = run(offline=args.offline, output=args.output)
    print(json.dumps({
        "output": str(args.output),
        "artifacts": len(report["artifacts"]),
        "directional_comparisons": len(report["pairwise_directional_comparisons"]),
        "lattice_uncovered_pixels": report["lattice_geometry"]["outside_3px_footprint_pixels"],
        "sample_equals_labels": report["mirror_sample_label_contamination"]["sample_values_equal_labels_on_footprint"],
        "submission_authorized": False,
    }, indent=2))


if __name__ == "__main__":
    main()
