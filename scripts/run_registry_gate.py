#!/usr/bin/env python3
"""Literal duplicate gate for a candidate: surface (pre-placement) and final dots vs every registry raster.

Uses the shared `gems32.registry_audit` functions with NO density exemption (space_filling_coverage=None):
  - surface: full-footprint |Spearman| > 0.90 against any registry raster => duplicate (stop)
  - final dots: |Spearman| > 0.90 OR > 70% of candidate dots within 3 px of any one registry raster
    => duplicate (stop); mass-weighted overlap also reported and gated at 0.70.
Also checks the exact SHA-256 of the candidate raster against every registry file (byte duplicates).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems32 import registry_audit as ra  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--surface", type=Path, required=True)
    ap.add_argument("--dots", type=Path, required=True, help="Final binary dot raster (.npy) on footprint grid")
    ap.add_argument("--candidate-tif", type=Path, required=True)
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--template", type=Path, default=ROOT / ".cache" / "gems_data" / "sample_submission.tif")
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    with rasterio.open(args.template) as ds:
        foot = np.isfinite(ds.read(1))
    surface = np.load(args.surface).astype(np.float32)
    dots = np.load(args.dots).astype(bool)
    manifest = ra.load_manifest(args.manifest)

    surf_res = ra.audit_surface(surface, foot, manifest, root=ROOT, template_tif=args.template)
    final_res = ra.audit_final_dots(
        surface, dots, foot, manifest, root=ROOT, template_tif=args.template,
        candidate_values=np.where(dots, surface, 0.0),
    )

    sha_c = hashlib.sha256(args.candidate_tif.read_bytes()).hexdigest()
    byte_dups = []
    for entry in manifest["rasters"]:
        if entry.get("sha256") == sha_c:
            byte_dups.append(f"{entry['repo']}:{entry['path']}")

    def slim(r):
        return {k: v for k, v in r.items() if k != "comparisons"}

    def top(res, key, n=8):
        rows = [c for c in res["comparisons"] if c.get(key) is not None]
        rows.sort(key=lambda c: -abs(c[key]))
        return [{"repo": c.get("repo"), "path": c.get("path"), key: c[key]} for c in rows[:n]]

    # Diagnostics (report-only, never change the literal verdict):
    #  (a) worst overlap excluding calibration probes, to show what the lattice is blocking;
    #  (b) the repo's space-filling variant (IR-47-LATTICE-FIX), labelled informational.
    non_cal = [c for c in final_res["comparisons"]
               if "calibration" not in str(c.get("path", "")).lower() and c.get("within_3px_fraction") is not None]
    worst_non_cal = max(non_cal, key=lambda c: c["within_3px_fraction"]) if non_cal else None
    cal_rows = [c for c in final_res["comparisons"] if "calibration" in str(c.get("path", "")).lower()]
    sf_res = ra.audit_final_dots(
        surface, dots, foot, manifest, root=ROOT, template_tif=args.template,
        candidate_values=np.where(dots, surface, 0.0), space_filling_coverage=0.70,
    )

    out = {
        "comparisons_surface": surf_res["comparisons"],
        "comparisons_final": final_res["comparisons"],
        "diagnostics_report_only": {
            "literal_lattice_or_calibration_rows": [
                {k: c.get(k) for k in ("repo", "path", "within_3px_fraction", "footprint_coverage_3px", "spearman")}
                for c in cal_rows if (c.get("within_3px_fraction") or 0) > 0.70],
            "worst_non_calibration_within_3px": None if worst_non_cal is None else {
                k: worst_non_cal.get(k) for k in ("repo", "path", "within_3px_fraction", "spearman")},
            "space_filling_variant_IR47_informational": {
                "passed": sf_res["passed"], "literal_passed": sf_res["literal_rule_passed"],
                "duplicates": [{k: d.get(k) for k in ("repo", "path", "within_3px_fraction", "spearman")}
                               for d in sf_res["duplicates"]],
                "note": "Owner has not adopted this variant; it is reported only to show the decision at stake.",
            },
        },
        "manifest": str(args.manifest),
        "manifest_registry_rasters": len(manifest["rasters"]),
        "candidate_tif": str(args.candidate_tif),
        "candidate_sha256": sha_c,
        "byte_identical_registry_files": byte_dups,
        "surface_gate": slim(surf_res) | {"top_abs_spearman": top(surf_res, "spearman")},
        "final_dot_gate": slim(final_res) | {
            "top_within_3px": top(final_res, "within_3px_fraction"),
            "top_abs_spearman": top(final_res, "spearman"),
        },
        "passed_literal_gate": bool(surf_res["passed"] and final_res["passed"] and not byte_dups),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=2, default=float) + "\n")
    print(json.dumps({k: out[k] for k in ("candidate_sha256", "byte_identical_registry_files", "passed_literal_gate")}, indent=2))
    print("surface worst |rho|:", surf_res["worst_abs_spearman"], surf_res["worst_raster"])
    print("final worst overlap:", final_res.get("worst_literal_overlap"), "worst |rho|:", final_res.get("worst_abs_spearman"))
    return 0 if out["passed_literal_gate"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
