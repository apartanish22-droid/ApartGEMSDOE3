#!/usr/bin/env python3
"""Recheck one peer research TIFF against the nine examples and lattice.

This is read-only forensics, not a model experiment, holdout replay or upload.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

from audit_priority import ROOT, read_aligned, sha256_file, verified_cached_file, overlap_with_distance
from io_safety import validate_output_path


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--offline", action="store_true")
    p.add_argument("--output", type=Path, default=ROOT / "evidence/peer_reference_audit.json")
    args = p.parse_args()
    cache = ROOT / ".cache/priority-audit"
    def fetch(item):
        return verified_cached_file(item, cache, offline=args.offline)
    manifests = (ROOT / "registry/inputs.json", ROOT / "registry/peer_research_reference.json", ROOT / "registry/focus_sites.json")
    validate_output_path(args.output, manifests)
    input_manifest, peer_manifest, site_manifest = (json.loads(path.read_text()) for path in manifests)
    inputs = {x["name"]: fetch(x) for x in input_manifest["inputs"]}
    peer_entries = {x["name"]: x for x in peer_manifest["files"]}
    peer = {name: fetch(item) for name, item in peer_entries.items()}
    site_paths = {x["site"]: fetch(x) for x in site_manifest["sites"]}
    validate_output_path(args.output, manifests + tuple(inputs.values()) + tuple(peer.values()) + tuple(site_paths.values()))
    peer_card = json.loads(peer["run_card"].read_text())
    holdout = peer_card["holdout"]
    with rasterio.open(inputs["sample_submission"]) as template:
        template_values = template.read(1)
        footprint = np.isfinite(template_values)
        if template.count != 1 or template.crs is None or not footprint.any() or np.isinf(template_values).any():
            raise ValueError("Invalid peer template or footprint")
        expected = (template.shape, template.crs, template.transform, template.count)
    arr, metadata = read_aligned(peer["raster"], expected)
    if not np.isfinite(arr[footprint]).all() or not np.isin(arr[footprint], [0, 1]).all():
        raise ValueError("Reference must be finite binary inside the peer footprint")
    dots = (arr > 0) & footprint
    if not dots.any():
        raise ValueError("Reference has no positive dots")
    comparisons = []
    for entry in site_manifest["sites"]:
        previous, _ = read_aligned(site_paths[entry["site"]], expected)
        if not np.isfinite(previous[footprint]).all() or not np.isin(previous[footprint], [0, 1]).all():
            raise ValueError(f"Invalid historical comparator: {entry['site']}")
        ref = (previous > 0) & footprint
        if not ref.any():
            raise ValueError(f"Empty comparator: {entry['site']}")
        distance = distance_transform_edt(~ref)
        comparisons.append({"reference": entry["site"], "candidate_within_3px_fraction": overlap_with_distance(dots, distance)})
        del previous, ref, distance
    lattice, _ = read_aligned(inputs["lattice"], expected)
    if not np.isfinite(lattice[footprint]).all() or not np.isin(lattice[footprint], [0, 1]).all():
        raise ValueError("Invalid lattice comparator")
    lattice_dots = (lattice > 0) & footprint
    if not lattice_dots.any():
        raise ValueError("Empty lattice is not a valid overlap comparator")
    distance = distance_transform_edt(~lattice_dots)
    lattice_overlap = overlap_with_distance(dots, distance)
    maximum = max(comparisons, key=lambda row: row["candidate_within_3px_fraction"])
    output = {
        "schema": "apartgemsdoe3-peer-research-reference-v1",
        "checked_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "Existing peer TIFF for learning; no new raster, holdout experiment or slot approval.",
        "raster": {
            "name": Path(peer_entries["raster"]["path"]).name,
            "source": f"https://github.com/{peer_entries['raster']['repo']}/blob/{peer_entries['raster']['ref']}/{peer_entries['raster']['path']}",
            "sha256": sha256_file(peer["raster"]),
            "dots": int(dots.sum()),
            "metadata": metadata,
        },
        "recorded_holdout_not_replayed": {
            "source": f"https://github.com/{peer_entries['run_card']['repo']}/blob/{peer_entries['run_card']['ref']}/{peer_entries['run_card']['path']}",
            "source_sha256": sha256_file(peer["run_card"]),
            "label": holdout["label"],
            "evaluator_version": holdout["evaluator_version"],
            "withheld_positive_pixels": holdout["n_withheld_positive_pixels"],
            "value": holdout["arms"]["EXP-2"]["dti"],
            "ci95": holdout["arms"]["EXP-2"]["ci95"],
            "limitation": "Peer-recorded, not replayed; not an organizer score or transferable leaderboard estimate.",
        },
        "candidate_to_historical_nine": comparisons,
        "maximum_vs_historical_nine": maximum,
        "candidate_within_3px_of_lattice": lattice_overlap,
        "literal_lattice_duplicate": lattice_overlap > .70,
        "complete_registry_checked": False,
        "preplacement_surface_replayed": False,
        "new_raster": False,
        "ok_to_submit": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"output": str(args.output), "max_nine_overlap": maximum, "lattice_overlap": lattice_overlap, "ok_to_submit": False}, indent=2))


if __name__ == "__main__":
    main()
