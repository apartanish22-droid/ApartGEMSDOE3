#!/usr/bin/env python3
"""Fail-closed format preflight for a DOE GEMS prediction GeoTIFF.

This checks the official file contract against a supplied sample/template. It
never estimates a competition score and never authorizes a submission slot.
Requires numpy and rasterio (see requirements.txt).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

try:
    import numpy as np
    import rasterio
except ImportError as exc:  # pragma: no cover - depends on runtime environment
    print(
        "Missing dependency. Install with: python -m pip install -r requirements.txt\n"
        f"Import detail: {exc}",
        file=sys.stderr,
    )
    raise SystemExit(2)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def check_submission(candidate_path: Path, template_path: Path) -> dict[str, Any]:
    """Return an auditable format report; ``pass`` is format-only evidence."""
    if not candidate_path.is_file():
        raise FileNotFoundError(f"Candidate GeoTIFF does not exist: {candidate_path}")
    if not template_path.is_file():
        raise FileNotFoundError(f"Template GeoTIFF does not exist: {template_path}")

    checks: dict[str, bool] = {}
    problems: list[str] = []
    with rasterio.open(template_path) as template, rasterio.open(candidate_path) as candidate:
        checks["single_band"] = candidate.count == 1
        checks["float32"] = candidate.dtypes == ("float32",)
        checks["crs_is_epsg_32611"] = (
            template.crs is not None
            and template.crs.to_epsg() == 32611
            and candidate.crs == template.crs
        )
        checks["shape_matches"] = (
            candidate.width == template.width and candidate.height == template.height
        )
        checks["transform_matches"] = candidate.transform == template.transform
        checks["template_has_crs"] = template.crs is not None

        if not checks["single_band"]:
            problems.append(f"candidate has {candidate.count} bands; expected one")
        if not checks["float32"]:
            problems.append(f"candidate dtype is {candidate.dtypes}; expected ('float32',)")
        if not checks["crs_is_epsg_32611"]:
            problems.append("candidate CRS must equal the template CRS and be EPSG:32611")
        if not checks["shape_matches"]:
            problems.append("candidate width/height do not match the template")
        if not checks["transform_matches"]:
            problems.append("candidate geotransform does not exactly match the template")

        # The organizer's sample/template defines the authoritative footprint.
        template_mask = template.dataset_mask() != 0
        template_values = template.read(1, masked=False)
        footprint = template_mask & np.isfinite(template_values)
        outside = ~footprint

        candidate_values = candidate.read(1, masked=False)
        candidate_masked = candidate.read_masks(1) == 0

        inside_masked = footprint & candidate_masked
        inside_nonfinite = footprint & ~candidate_masked & ~np.isfinite(candidate_values)
        inside_finite = footprint & ~candidate_masked & np.isfinite(candidate_values)
        inside_out_of_range = inside_finite & (
            (candidate_values < 0.0) | (candidate_values > 1.0)
        )
        # Outside is required to be null/NaN. A valid data mask or NaN is null;
        # infinities and finite sentinel values without a nodata mask are not.
        outside_not_null = outside & ~candidate_masked & ~np.isnan(candidate_values)

        inside_count = int(np.count_nonzero(footprint))
        checks["no_nan_inside_footprint"] = (
            np.count_nonzero(inside_masked) == 0
            and np.count_nonzero(inside_nonfinite) == 0
        )
        checks["inside_values_in_0_1"] = np.count_nonzero(inside_out_of_range) == 0
        checks["outside_is_null_or_nan"] = np.count_nonzero(outside_not_null) == 0
        checks["nonempty_template_footprint"] = inside_count > 0

        if not checks["no_nan_inside_footprint"]:
            problems.append(
                "template footprint contains masked or non-finite candidate cells "
                f"(masked={int(np.count_nonzero(inside_masked))}, "
                f"nonfinite={int(np.count_nonzero(inside_nonfinite))})"
            )
        if not checks["inside_values_in_0_1"]:
            problems.append(
                "candidate has finite in-footprint values outside [0, 1]: "
                f"{int(np.count_nonzero(inside_out_of_range))} cell(s)"
            )
        if not checks["outside_is_null_or_nan"]:
            problems.append(
                "candidate has finite values or infinities outside the footprint "
                "without a nodata mask: "
                f"{int(np.count_nonzero(outside_not_null))} cell(s)"
            )
        if not checks["nonempty_template_footprint"]:
            problems.append("template mask/finite data define an empty footprint")

        finite_inside_values = candidate_values[inside_finite]
        min_value = (
            float(np.min(finite_inside_values)) if finite_inside_values.size else None
        )
        max_value = (
            float(np.max(finite_inside_values)) if finite_inside_values.size else None
        )
        raster_metadata = {
            "width": int(candidate.width),
            "height": int(candidate.height),
            "band_count": int(candidate.count),
            "dtype": list(candidate.dtypes),
            "crs": candidate.crs.to_string() if candidate.crs else None,
            "template_crs": template.crs.to_string() if template.crs else None,
            "transform": list(candidate.transform)[:6],
            "template_transform": list(template.transform)[:6],
            "footprint_pixels": inside_count,
            "outside_pixels": int(np.count_nonzero(outside)),
            "minimum_finite_inside_value": min_value,
            "maximum_finite_inside_value": max_value,
            "in_footprint_nan_or_inf_count": int(np.count_nonzero(inside_nonfinite)),
            "in_footprint_masked_count": int(np.count_nonzero(inside_masked)),
            "in_footprint_out_of_range_count": int(np.count_nonzero(inside_out_of_range)),
            "outside_not_null_count": int(np.count_nonzero(outside_not_null)),
        }

    passed = all(checks.values())
    return {
        "schema": "apartgemsdoe3-format-preflight-v1",
        "candidate": str(candidate_path),
        "template": str(template_path),
        "candidate_sha256": sha256_file(candidate_path),
        "status": "PASS_FORMAT_ONLY" if passed else "FAIL",
        "format_pass": passed,
        "submission_authorized": False,
        "checks": checks,
        "raster": raster_metadata,
        "problems": problems,
        "limitations": [
            "Does not measure HOLDOUT-DTI or estimate an organizer score.",
            "Does not check registry uniqueness, leakage, scientific merit, or weekly slot approval.",
            "Footprint is inferred from the supplied template's dataset mask and finite values; verify this matches the organizer template semantics.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate", type=Path, help="candidate single-band GeoTIFF")
    parser.add_argument("--template", required=True, type=Path, help="official sample/template GeoTIFF")
    parser.add_argument("--json", type=Path, help="also write the JSON report to this path")
    args = parser.parse_args()

    try:
        report = check_submission(args.candidate, args.template)
    except Exception as exc:
        print(f"Preflight could not complete: {exc}", file=sys.stderr)
        return 2

    rendered = json.dumps(report, indent=2, sort_keys=True, allow_nan=False)
    print(rendered)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(rendered + "\n", encoding="utf-8")
    return 0 if report["format_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
