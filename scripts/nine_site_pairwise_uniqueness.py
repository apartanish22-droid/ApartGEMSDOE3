#!/usr/bin/env python3
"""Pairwise uniqueness for each nine-site best file against every OTHER registry raster.

For each target (the file named in the session prompt for GEMSDOE24/25/27/28/30/31/32/33/36):
  - byte-identical registry files (same SHA-256) are listed separately;
  - all other registry rasters are compared with the shared `gems32.registry_audit.audit_final_dots`
    (full-footprint |Spearman| and directional <=3 px dot overlap; literal rule, no exemptions);
  - the worst comparison is reported with its repo and path, including calibration probes.

Reads only the pinned registry manifest and the cached registry rasters. Writes evidence JSON.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from gems32 import registry_audit as ra  # noqa: E402
from audit_nine_site_fixed_files import TARGETS, locate  # noqa: E402

MANIFEST = ROOT / "registry" / "focus_registry_manifest_20261030.json"
TEMPLATE = ROOT / ".cache" / "gems_data" / "sample_submission.tif"


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    manifest = ra.load_manifest(MANIFEST)
    with rasterio.open(TEMPLATE) as ds:
        foot = np.isfinite(ds.read(1))
        tpl = {"shape": ds.shape, "crs": ds.crs, "transform": ds.transform}
    results = []
    for site, name, stated, rel in TARGETS:
        p = locate(site, rel)
        if not p.is_file():
            results.append({"site": site, "name": name, "status": "MISSING"})
            continue
        sha = sha256(p)
        byte_dups = [f"{e['repo']}:{e['path']}" for e in manifest["rasters"]
                     if e.get("sha256") == sha and not (e["repo"] == site and p.name == Path(e["path"]).name)]
        with rasterio.open(p) as ds:
            arr = ds.read(1)
        dots = (np.nan_to_num(arr, nan=0.0) > 0) & foot
        surface = np.where(foot, np.nan_to_num(arr, nan=0.0), 0.0).astype(np.float32)
        # exclude the target's own registry entry (same bytes) from the comparison set
        others = {"rasters": [e for e in manifest["rasters"] if e.get("sha256") != sha]}
        res = ra.audit_final_dots(surface, dots, foot, others, root=ROOT, template_tif=TEMPLATE,
                                  candidate_values=np.where(dots, surface, 0.0))
        comps = [c for c in res["comparisons"] if c.get("within_3px_fraction") is not None]
        worst_ov = max(comps, key=lambda c: c["within_3px_fraction"]) if comps else None
        worst_rho = max((c for c in comps if c.get("spearman") is not None), key=lambda c: abs(c["spearman"]), default=None)
        results.append({
            "site": site, "name": name, "stated_score_OWNER_REPORT": stated,
            "file": str(p.relative_to(ROOT)), "sha256": sha, "dots": int(dots.sum()),
            "byte_identical_other_registry_files": byte_dups,
            "comparisons_against_other_registry_rasters": len(comps),
            "malformed_or_missing_in_comparison": int(res["malformed_or_missing"]),
            "worst_within_3px": None if worst_ov is None else {
                "repo": worst_ov["repo"], "path": worst_ov["path"],
                "within_3px_fraction": worst_ov["within_3px_fraction"]},
            "worst_abs_spearman": None if worst_rho is None else {
                "repo": worst_rho["repo"], "path": worst_rho["path"], "spearman": worst_rho["spearman"]},
            "literal_duplicates_excluding_self": [
                {"repo": d["repo"], "path": d["path"], "within_3px_fraction": d.get("within_3px_fraction"),
                 "spearman": d.get("spearman")} for d in res["duplicates"]],
            "literal_rule_passed_vs_others": bool(res["literal_rule_passed"]),
        })
        print(site, "byte_dups", len(byte_dups), "literal_pass", res["literal_rule_passed"],
              "worst_ov", None if worst_ov is None else round(worst_ov["within_3px_fraction"], 4), flush=True)
    out = {
        "schema_version": 1,
        "manifest": str(MANIFEST.relative_to(ROOT)),
        "manifest_rasters": len(manifest["rasters"]),
        "rule": "literal: full-footprint |Spearman| <= 0.90 and directional <=3 px overlap <= 0.70 vs every other registry raster",
        "results": results,
    }
    dest = ROOT / "evidence" / "nine_site_pairwise_uniqueness_20261030.json"
    dest.write_text(json.dumps(out, indent=2, default=float) + "\n")
    print("wrote", dest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
