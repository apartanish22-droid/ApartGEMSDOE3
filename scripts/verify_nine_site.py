#!/usr/bin/env python3
"""Re-verify the nine focus-site best files from their bytes (no leaderboard claims).

For each site listed in evidence/nine_site_best_files_audit.json this script:
  1. locates the file by SHA-256 on disk, or fetches it from the pinned GitHub ref in
     registry/focus_registry_manifest.json via `gh api` (SHA-256 must match);
  2. runs the repository's format validator (gemsdoe32.submission) in both the default
     and the strict whole-array mode;
  3. counts NaN / out-of-range values and exact positive-pixel counts;
  4. runs the shared holdout evaluator (scripts/evaluate_holdout.py -> gems32.holdout),
     labelled HOLDOUT-DTI with evaluator version, withheld-positive count and 95% CI;
  5. measures catalogue proximity of each site's dots against labels.tif;
  6. computes the 3-px overlap matrix and Spearman correlations versus the owner-reported
     scores.

Every score produced here is a HOLDOUT-DTI or a geometric statistic. Owner-reported
leaderboard values are copied from the audit file and labelled OWNER-REPORT.
Writes evidence/nine_site_verification_<date>.json.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from gemsdoe32.submission import validate_submission_geotiff  # noqa: E402
import evaluate_holdout as eh  # noqa: E402

SEARCH_DIRS = [ROOT / ".cache" / "gems_data", ROOT / ".cache" / "site9", ROOT / "docs" / "downloads"]


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def locate_or_fetch(site: str, sha: str, manifest: dict, fetch_dir: Path) -> Path:
    for d in SEARCH_DIRS:
        if d.is_dir():
            for p in d.rglob("*.tif"):
                if sha256_file(p) == sha:
                    return p
    entries = [r for r in manifest["rasters"] if r["sha256"] == sha]
    if not entries:
        raise FileNotFoundError(f"{site}: sha {sha[:12]} not on disk and not in focus registry manifest")
    r = entries[0]
    fetch_dir.mkdir(parents=True, exist_ok=True)
    out = fetch_dir / Path(r["path"]).name
    owner_repo = f"buffedlizard55-lab/{r['repo']}"
    with out.open("wb") as f:
        subprocess.run(
            ["gh", "api", f"repos/{owner_repo}/contents/{r['path']}?ref={r['ref']}", "-H", "Accept: application/vnd.github.raw"],
            stdout=f,
            stderr=subprocess.PIPE,
            check=True,
        )
    if sha256_file(out) != sha:
        out.unlink()
        raise ValueError(f"{site}: fetched bytes do not match pinned sha {sha[:12]}")
    return out


def raster_facts(p: Path) -> dict:
    with rasterio.open(p) as ds:
        a = ds.read(1)
        crs = str(ds.crs)
        transform = [float(x) for x in ds.transform][:6]
        dtype = ds.dtypes[0]
        shape = list(a.shape)
    fin = np.isfinite(a)
    return {
        "crs": crs,
        "transform": transform,
        "dtype": dtype,
        "shape": shape,
        "nan_count": int(np.isnan(a).sum()),
        "inf_count": int(np.isinf(a).sum()),
        "out_of_range_finite_count": int(((a < 0) | (a > 1))[fin].sum()),
        "positive_count": int((fin & (a > 0)).sum()),
        "_positive_mask": fin & (a > 0),
        "_finite_all": bool(fin.all()),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--date", default="20261030")
    ap.add_argument("--template", type=Path, default=ROOT / ".cache" / "gems_data" / "sample_submission.tif")
    ap.add_argument("--skip-holdout", action="store_true", help="skip the holdout evaluator (fast geometry-only run)")
    args = ap.parse_args()

    audit = json.loads((ROOT / "evidence" / "nine_site_best_files_audit.json").read_text())
    manifest = json.loads((ROOT / "registry" / "focus_registry_manifest.json").read_text())
    fetch_dir = ROOT / ".cache" / "site9"

    sites = []
    for s in audit["sites"]:
        p = locate_or_fetch(s["site"], s["sha256"], manifest, fetch_dir)
        facts = raster_facts(p)
        rep = validate_submission_geotiff(p, args.template, strict_whole_array_finite=True).to_dict()
        rep_default = validate_submission_geotiff(p, args.template, strict_whole_array_finite=False).to_dict()
        row = {
            "site": s["site"],
            "owner_reported_score_OWNER_REPORT": s["published_score_OWNER_REPORT"],
            "leaderboard_name": s["leaderboard_name"],
            "file_name": p.name,
            "sha256": s["sha256"],
            "bytes": p.stat().st_size,
            "sha256_matches_audit": sha256_file(p) == s["sha256"],
            "raster": {k: v for k, v in facts.items() if not k.startswith("_")},
            "validator_default_passed": rep_default["passed"],
            "validator_strict_finite_passed": rep["passed"],
            "validator_failed_checks": [c["name"] for c in rep["checks"] if not c["passed"]] if "checks" in rep else [],
        }
        if not args.skip_holdout:
            ev = eh.evaluate_path(p, name=s["site"])
            hr, sg = ev["hide_and_recover"], ev["sgmc_off_catalogue"]
            row["holdout_dti"] = {
                "label": "HOLDOUT-DTI",
                "evaluator_version": hr["evaluator_version"],
                "withheld_positives": hr["n_withheld_positives"],
                "pooled_dti": hr["pooled_dti"],
                "ci95_cluster_bootstrap": hr["ci95_cluster_bootstrap"],
            }
            row["sgmc_off_catalogue_calibrated"] = {
                "label": "HOLDOUT-DTI",
                "evaluator_version": sg["evaluator_version"],
                "withheld_positives": sg["n_withheld_positives"],
                "calibrated_dti": sg["sgmc_prevalence_calibrated_dti"],
                "ci95": sg["sgmc_calibrated_ci95"],
            }
        sites.append((row, facts["_positive_mask"]))

    # Catalogue proximity (labels.tif positives).
    with rasterio.open(ROOT / ".cache" / "gems_data" / "labels.tif") as ds:
        lab = ds.read(1)
    labpos = np.isfinite(lab) & (lab > 0)
    dcat = distance_transform_edt(~labpos)
    for row, pos in sites:
        d = dcat[pos]
        row["catalogue_proximity"] = {
            "dots": int(pos.sum()),
            "frac_within_2px": float((d <= 2).mean()),
            "frac_within_300m": float((d * 100.0 <= 300).mean()),
            "frac_beyond_1km": float((d * 100.0 > 1000).mean()),
        }

    # Pairwise 3-px overlap: row site's dots within 3 px of column site's dots.
    names = [r["site"] for r, _ in sites]
    pos_by = {r["site"]: pos for r, pos in sites}
    dist_by = {r["site"]: distance_transform_edt(~pos) for r, pos in sites}
    overlap = {}
    for a in names:
        for b in names:
            if a == b:
                continue
            overlap[f"{a}->{b}"] = float((dist_by[b][pos_by[a]] <= 3).mean())
    exact_dupes = []
    for i, a in enumerate(names):
        for b in names[i + 1 :]:
            if np.array_equal(pos_by[a], pos_by[b]):
                exact_dupes.append([a, b])

    owner = [r["owner_reported_score_OWNER_REPORT"] for r, _ in sites]
    corr = {"n": len(owner), "label": "association in 9 OWNER-REPORT values; not causal; not a projection"}
    if not args.skip_holdout:
        hold = [r["holdout_dti"]["pooled_dti"] for r, _ in sites]
        sgm = [r["sgmc_off_catalogue_calibrated"]["calibrated_dti"] for r, _ in sites]
        prox = [r["catalogue_proximity"]["frac_beyond_1km"] for r, _ in sites]
        rho_h, p_h = spearmanr(owner, hold)
        rho_s, p_s = spearmanr(owner, sgm)
        rho_p, p_p = spearmanr(owner, prox)
        corr.update(
            spearman_owner_vs_holdout_dti={"rho": float(rho_h), "p": float(p_h)},
            spearman_owner_vs_sgmc_calibrated={"rho": float(rho_s), "p": float(p_s)},
            spearman_owner_vs_frac_beyond_1km={"rho": float(rho_p), "p": float(p_p)},
        )

    out = {
        "schema_version": 1,
        "date_tag": args.date,
        "purpose": "Re-verification of nine focus-site best files from bytes. Scores are OWNER-REPORT (copied) or HOLDOUT-DTI (computed). Not a leaderboard score and not submission authorization.",
        "template": str(args.template.relative_to(ROOT)) if args.template.is_relative_to(ROOT) else str(args.template),
        "sites": [r for r, _ in sites],
        "pairwise_3px_overlap_row_within_3px_of_column": overlap,
        "exact_duplicate_positive_masks": exact_dupes,
        "correlations": corr,
        "gate_note": "Official format (DrivenData page 967): float32, values in [0,1], outside-bounds null or NaN. Strict repo validator additionally requires whole-array finiteness.",
    }
    dest = ROOT / "evidence" / f"nine_site_verification_{args.date}.json"
    dest.write_text(json.dumps(out, indent=1) + "\n")
    print(f"wrote {dest.relative_to(ROOT)}")
    for r, _ in sites:
        print(r["site"], r["file_name"], "nan=", r["raster"]["nan_count"], "strict=", r["validator_strict_finite_passed"])
    print("exact duplicates:", exact_dupes)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
