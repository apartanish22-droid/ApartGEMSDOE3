#!/usr/bin/env python3
"""Recheck existing files only. Passing format alone never authorizes a submission."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from gemsdoe32.submission import validate_submission_geotiff  # noqa: E402


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def audit(template: Path, registry: Path, candidate: Path) -> dict:
    """Reject missing/misaligned data. Overlap is directional, candidate to registry."""
    format_result = validate_submission_geotiff(candidate, template, strict_whole_array_finite=True).to_dict()
    with rasterio.open(candidate) as c, rasterio.open(registry) as r:
        if c.count != 1 or r.count != 1 or c.shape != r.shape or c.crs != r.crs or c.transform != r.transform:
            raise ValueError('candidate and registry grid, CRS, transform and band count must match')
        candidate_values = c.read(1)
        registry_values = r.read(1)
    if not np.isfinite(candidate_values).all():
        raise ValueError('candidate contains nonfinite values')
    # Ignore NaN/nodata in the historic lattice rather than treating them as dots.
    dots = candidate_values > 0
    ref_dots = np.isfinite(registry_values) & (registry_values > 0)
    if not dots.any() or not ref_dots.any():
        raise ValueError('both masks must contain positive pixels')
    overlap = float((distance_transform_edt(~ref_dots)[dots] <= 3).mean())
    return {
        'candidate': str(candidate.relative_to(ROOT)) if candidate.is_relative_to(ROOT) else str(candidate),
        'candidate_sha256': sha256(candidate), 'candidate_dots': int(dots.sum()),
        'template_sha256': sha256(template), 'registry_sha256': sha256(registry),
        'registry_dots': int(ref_dots.sum()), 'directional_within_3px': overlap,
        'literal_dot_gate_passed': overlap <= 0.70,
        'format': format_result, 'ok_to_submit': False,
        'reason': 'Partial registry check only; not a complete release or slot authorization.'
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--template', type=Path, required=True)
    p.add_argument('--registry', type=Path, required=True)
    p.add_argument('candidates', type=Path, nargs='+')
    args = p.parse_args()
    results = [audit(args.template, args.registry, c) for c in args.candidates]
    print(json.dumps({'scope': 'one pinned registry raster, not a full uniqueness scan', 'results': results}, indent=2))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
