#!/usr/bin/env python3
"""Diagnose a TIFF's format/range, using the unmodified shared template validator.

This is NOT a scientific, novelty, authenticity, portal or weekly-slot approval.
It does not repair, clip, sanitize, copy, submit, or write a prediction file.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import rasterio

from audit_priority import ROOT, sha256_file, verified_cached_file
from cache_shared_template import cache_template
from io_safety import validate_output_path
from shared_import import load_shared_module


def inspect(candidate: Path, template: Path, shared_root: Path) -> dict:
    check_variants = load_shared_module(shared_root, "submission").check_variants
    candidate_hash = sha256_file(candidate)
    template_hash = sha256_file(template)
    shared = check_variants(candidate, template)
    with rasterio.open(template) as t, rasterio.open(candidate) as s:
        template_values = t.read(1)
        template_valid = t.read_masks(1) != 0
        if np.isinf(template_values[template_valid]).any():
            raise ValueError("Template contains unmasked infinite values")
        footprint = template_valid & np.isfinite(template_values)
        if not footprint.any():
            raise ValueError("Template has an empty finite, unmasked footprint")
        if (s.count, s.shape, s.crs, s.transform) == (1, t.shape, t.crs, t.transform):
            a = s.read(1)
            invalid_mask = s.read_masks(1) == 0
            inside = a[footprint]
            outside = a[~footprint]
            inside_finite_range = bool(inside.size and np.isfinite(inside).all() and np.all((inside >= 0) & (inside <= 1)))
            inside_masked_count = int(np.count_nonzero(invalid_mask & footprint))
            outside_null_or_nan = bool(np.all(invalid_mask[~footprint] | np.isnan(outside)))
            strict_raw_full_array_range = bool(np.isfinite(a).all() and np.all((a >= 0) & (a <= 1)))
        else:
            inside_finite_range, inside_masked_count = False, None
            outside_null_or_nan, strict_raw_full_array_range = False, False
    if sha256_file(candidate) != candidate_hash or sha256_file(template) != template_hash:
        raise ValueError("Candidate or template changed during inspection")
    requirements = {
        "shared_hard_format_checks": shared["format_valid"],
        "inside_all_finite_and_in_0_1": inside_finite_range,
        "inside_no_masked_pixels": inside_masked_count == 0,
        "outside_null_or_nan_relative_to_template": outside_null_or_nan,
        # Diagnostic only: a NaN-outside file legitimately fails a raw-array range check.
        "strict_raw_full_array_finite_0_1_diagnostic": strict_raw_full_array_range,
    }
    return {
        "schema": "apartgemsdoe3-format-inspection-v1",
        "candidate": str(candidate),
        "candidate_sha256": candidate_hash,
        "template_sha256": template_hash,
        "template_authenticity": "not established by this tool; compare with organizer's authenticated sample",
        "footprint_definition": "Finite and unmasked pixels of the supplied template; authenticity is not established.",
        "shared_template_ref": shared_root.name,
        "shared_validator": shared,
        "diagnostics": requirements,
        "masked_pixels_inside_template_footprint": inside_masked_count,
        "passes_local_textual_checks": all(requirements[key] for key in (
            "shared_hard_format_checks", "inside_all_finite_and_in_0_1",
            "inside_no_masked_pixels", "outside_null_or_nan_relative_to_template")),
        "organizer_acceptance_verified": False,
        "scientific_or_uniqueness_gates_evaluated": False,
        "ok_to_submit": False,
        "warning": "A zero exterior may pass a strict raw range check but does not by itself establish the official null/NaN exterior requirement. A NaN exterior may fail a strict raw range check. The rejection's cause is unverified.",
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("candidate", type=Path)
    p.add_argument("--template", type=Path, help="Local sample; default is the explicitly unverified peer mirror")
    p.add_argument("--offline", action="store_true", help="Use cached shared source and mirror only")
    p.add_argument("--output", type=Path, help="Optional JSON report path")
    args = p.parse_args()
    shared = cache_template(args.offline)
    if args.template:
        template = args.template
    else:
        manifest = json.loads((ROOT / "registry/inputs.json").read_text())
        entry = next(x for x in manifest["inputs"] if x["name"] == "sample_submission")
        template = verified_cached_file(entry, ROOT / ".cache/priority-audit", offline=args.offline)
    if args.output:
        validate_output_path(args.output, (args.candidate, template))
    report = inspect(args.candidate, template, shared)
    text = json.dumps(report, indent=2, allow_nan=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text)
    print(text, end="")
    if not report["passes_local_textual_checks"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
