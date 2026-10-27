#!/usr/bin/env python3
"""Re-open and format-check a TIFF using the unmodified shared template.

This is NOT scientific, novelty, portal, or weekly-slot authorization. It
requires hash-pinned reference mirrors from scripts/fetch_assets.py.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import sys

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "vendor"))
sys.path.insert(0, str(ROOT / "scripts"))
from template_utils import verify_template  # noqa: E402
verify_template()  # Never import a missing or modified shared template.
from fetch_assets import sha256_file  # noqa: E402
from gems57 import gates, validate  # noqa: E402


def json_safe(value):
    """Preserve nonfinite diagnostics as strings in standards-compliant JSON.

    This only serializes metadata; it never alters the TIFF or changes a failed
    validation into a pass. A NaN nodata tag is rejected by the shared gate.
    """
    if isinstance(value, dict):
        return {key: json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]
    if isinstance(value, np.generic):
        return json_safe(value.item())
    if isinstance(value, float) and not math.isfinite(value):
        return "NaN" if math.isnan(value) else ("Infinity" if value > 0 else "-Infinity")
    return value


def check(path: Path, cache: Path) -> dict:
    manifest = json.loads((ROOT / "registry/input_manifest.json").read_text())
    rec = {r["id"]: r for r in manifest["files"]}
    sample = cache / rec["sample"]["destination"]
    labels = cache / rec["labels"]["destination"]
    for name, ref in (("sample", sample), ("labels", labels)):
        if not ref.is_file() or sha256_file(ref) != rec[name]["sha256"]:
            raise ValueError(f"missing or hash-mismatched {name} reference")
    with rasterio.open(sample) as src:
        fp = np.isfinite(src.read(1))
        expected = (src.shape, src.crs, src.transform)
    with rasterio.open(labels) as src:
        if (src.shape, src.crs, src.transform) != expected:
            raise ValueError("label reference grid differs from sample reference")
        catalogue = (src.read(1) > 0) & fp
    template = gates.format_report(path, sample, footprint=fp)
    local = validate.validate(path, fp, catalogue)
    passed = bool(template["ok"] and local["all_checks_passed"])
    return json_safe({
        "observed_utc": datetime.now(timezone.utc).isoformat(),
        "file": str(path), "sha256": sha256_file(path),
        "evidence_class": "LOCAL-FORMAT-VALIDATION (not organizer acceptance)",
        "reference_provenance": "hash-pinned third-party mirror, not authenticated organizer sample",
        "format_passed": passed, "template": template, "local": local,
        "public_specification_caveat": "The public page says data outside bounds is null/NaN; this strict all-finite project check does not establish organizer acceptance or settle outside-footprint encoding.",
        "uniqueness_checked": False, "holdout_checked": False,
        "approved_for_weekly_slot": False, "verdict": "negative",
    })


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("file", type=Path)
    ap.add_argument("--cache", type=Path, default=ROOT / ".cache/inputs")
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args(argv)
    try:
        report = check(args.file, args.cache)
    except (ValueError, OSError, rasterio.errors.RasterioError) as exc:
        print(f"FORMAT CHECK FAILED: {exc}", file=sys.stderr)
        return 1
    text = json.dumps(report, indent=2, allow_nan=False) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    print(text)
    return 0 if report["format_passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
