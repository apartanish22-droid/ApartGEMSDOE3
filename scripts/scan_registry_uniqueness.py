#!/usr/bin/env python3
"""Full-registry uniqueness scan (Parallel-Run Protocol Rule 1) for one candidate.

Compares a candidate's pre-placement surface (optional .npy) and its final dots (the GeoTIFF
positive pixels) against every restored registry raster:
  - focus manifest   registry/focus_registry_manifest.json            (451 rasters)
  - extra scored     registry/extra_scored_manifest.json              (37 rasters)
  - sibling orgs     .cache/sibling_orgs/manifest.json                (715 rasters)
Uses gems32.registry_audit.audit_surface and audit_final_dots unchanged (no private fork).
Writes a JSON report; the gate verdict is in report["gate"].

Usage:
  scripts/restore_pinned_registry.py --jobs 6   # restores .cache/registry, .cache/extra, .cache/sibling_orgs
  scripts/scan_registry_uniqueness.py candidate.tif --surface work.npy --out evidence/x.json
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems32 import registry_audit  # noqa: E402
from gems32.paths import data_dir  # noqa: E402


def build_manifest() -> dict:
    rows: list[dict] = []
    focus = json.loads((ROOT / "registry" / "focus_registry_manifest.json").read_text())
    rows += [r for r in focus["rasters"] if r.get("status") == "ok"]
    extra = json.loads((ROOT / "registry" / "extra_scored_manifest.json").read_text())
    rows += [r for r in extra["rasters"] if r.get("local")]
    sib = json.loads((ROOT / ".cache" / "sibling_orgs" / "manifest.json").read_text())
    rows += [r for r in sib if r.get("status") == "ok"]
    present, missing = [], []
    for r in rows:
        if r.get("local") and (ROOT / r["local"]).is_file():
            present.append(r)
        else:
            missing.append(r.get("local") or r.get("path"))
    # de-duplicate by sha256 so identical files are compared once
    seen, uniq = set(), []
    for r in present:
        key = r.get("sha256")
        if key in seen:
            continue
        seen.add(key)
        uniq.append(r)
    return {"rasters": uniq, "n_rows": len(rows), "n_present": len(present),
            "n_missing": len(missing), "missing_sample": missing[:10]}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("candidate", type=Path, help="zeros GeoTIFF (float32, [0,1], NaN-free)")
    ap.add_argument("--surface", type=Path, default=None, help="optional continuous surface .npy (footprint grid)")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--data-dir", type=Path, default=None)
    args = ap.parse_args()

    ddir = args.data_dir or data_dir()
    template = ddir / "sample_submission.tif"
    with rasterio.open(template) as ds:
        foot = np.isfinite(ds.read(1))
    with rasterio.open(args.candidate) as ds:
        vals = ds.read(1).astype(np.float32)
    dots = (vals > 0) & foot
    manifest = build_manifest()

    report = {
        "scanned_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "candidate": str(args.candidate.relative_to(ROOT)) if args.candidate.is_relative_to(ROOT) else str(args.candidate),
        "candidate_sha256": registry_audit.hashlib.sha256(args.candidate.read_bytes()).hexdigest(),
        "candidate_dots": int(dots.sum()),
        "registry_manifest": {k: v for k, v in manifest.items() if k != "rasters"} | {"n_unique_sha256": len(manifest["rasters"])},
    }
    final = registry_audit.audit_final_dots(
        vals, dots, foot, manifest, root=ROOT, template_tif=template,
        candidate_values=vals,
    )
    report["final_dots"] = final
    gate = {"final_dots_literal_passed": bool(final.get("literal_rule_passed"))}
    if args.surface is not None:
        surf = np.load(args.surface)
        surf_res = registry_audit.audit_surface(surf, foot, manifest, root=ROOT, template_tif=template)
        report["surface"] = surf_res
        # audit_surface reports its literal surface-stage result under "passed" (src/gems32/registry_audit.py);
        # reading a missing "literal_rule_passed" key here made every surface stage look failed (IR-20261031-15).
        gate["surface_literal_passed"] = bool(surf_res.get("passed"))
    gate["all_literal_checks_passed"] = all(v for k, v in gate.items() if k.endswith("passed"))
    report["gate"] = gate
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, default=float) + "\n")
    print(json.dumps({"gate": gate, "candidate_dots": report["candidate_dots"],
                      "final": {k: final.get(k) for k in ("registry_rasters", "worst_abs_spearman",
                                                          "worst_within_3px_fraction", "worst_within_3px_raster",
                                                          "literal_rule_passed")}}, indent=2, default=float))
    return 0 if gate["all_literal_checks_passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
