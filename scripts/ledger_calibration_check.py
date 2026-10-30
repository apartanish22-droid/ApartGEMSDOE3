#!/usr/bin/env python3
"""Experiment 3 (budget-final): does HOLDOUT-DTI track owner-reported live scores at scale?

PRE-REGISTERED (written before the run):
  H0  Hide-and-recover HOLDOUT-DTI and the SGMC-calibrated off-catalogue DTI both have no
      rank relationship with the OWNER-REPORT live scores across the live ledger.
  H1a Spearman(HOLDOUT-DTI pooled, owner score) < 0 with 95% CI excluding 0.  (n=18 gave -0.55.)
  H1b Spearman(SGMC-cal DTI, owner score) > 0 with 95% CI excluding 0.       (n=18 gave +0.69.)
  Falsification: if the sign of either correlation flips, or its CI spans 0, the n=18 result
  (note 10, F1) is not supported at scale and the calibration conclusion is withdrawn.
  Scope: unique rasters (by SHA-256) from evidence/live_ledger_rasters.json with status "ok".
  Every fetched file must match the ledger SHA-256. Mismatches are excluded and listed.

Inputs: evidence/live_ledger_rasters.json (OWNER-REPORT scores), the pinned GitHub refs in that
file, and the restored holdout inputs (labels, sample_submission, external SGMC raster).
Output: evidence/ledger_calibration_check_20261030.json.
Labels: scores are OWNER-REPORT; DTI values are HOLDOUT-DTI with evaluator version and CI.
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

import rasterio  # noqa: E402

import restore_data as rd  # noqa: E402
from gems32 import holdout  # noqa: E402
from gems32.paths import data_dir  # noqa: E402

OWNER = "buffedlizard55-lab"
CACHE = ROOT / ".cache" / "ledger"
PARTIAL = ROOT / ".cache" / "gems_work" / "ledger_calib_partial.jsonl"


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch_verified(row: dict) -> tuple[Path | None, str]:
    dest = CACHE / row["repo"] / row["path"]
    if dest.exists() and sha256_file(dest) == row["sha256"]:
        return dest, "cached"
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        rd.fetch(f"{OWNER}/{row['repo']}", row["ref"], row["path"], dest)
    except Exception as exc:  # network or 404: record, do not guess another owner
        dest.unlink(missing_ok=True)
        return None, f"fetch_error: {type(exc).__name__}"
    got = sha256_file(dest)
    if got != row["sha256"]:
        dest.unlink(missing_ok=True)
        return None, f"sha_mismatch: {got[:12]}"
    return dest, "fetched"


def main() -> int:
    t0 = time.time()
    ledger = json.loads((ROOT / "evidence" / "live_ledger_rasters.json").read_text())["rows"]
    ok_rows = [r for r in ledger if r.get("status") == "ok"]

    # Unique rasters by SHA-256. Keep every owner score seen for the same bytes.
    by_sha: dict[str, dict] = {}
    scores_by_sha: dict[str, list[float]] = {}
    for r in ok_rows:
        by_sha.setdefault(r["sha256"], r)
        scores_by_sha.setdefault(r["sha256"], []).append(float(r["score"]))

    ddir = data_dir()
    ctx = holdout.load_holdout_context(ddir)
    with rasterio.open(ddir / "sample_submission.tif") as ds:
        foot_shape = ds.read(1).shape
    assert foot_shape == ctx.foot.shape

    PARTIAL.parent.mkdir(parents=True, exist_ok=True)
    done: dict[str, dict] = {}
    if PARTIAL.exists():
        for line in PARTIAL.read_text().splitlines():
            if line.strip():
                rec = json.loads(line)
                done[rec["sha256"]] = rec

    excluded: list[dict] = []
    rows_out: list[dict] = []
    for sha, r in by_sha.items():
        if sha in done:
            rows_out.append(done[sha])
            continue
        path, status = fetch_verified(r)
        if path is None:
            excluded.append({"submission": r["submission"], "repo": r["repo"], "reason": status})
            continue
        with rasterio.open(path) as ds:
            arr = ds.read(1)
        if arr.shape != ctx.foot.shape:
            excluded.append({"submission": r["submission"], "repo": r["repo"], "reason": "shape"})
            continue
        mask = np.isfinite(arr) & (arr > 0) & ctx.foot
        hr = holdout.evaluate_hide_and_recover(mask, ctx, b_visible_px=0.0, name=r["submission"])
        sg = holdout.evaluate_sgmc_with_ci(mask, ctx, name=r["submission"])
        rec = {
            "sha256": sha,
            "submission": r["submission"],
            "site": r["site"],
            "repo": r["repo"],
            "owner_reported_score": float(r["score"]),
            "owner_scores_for_same_bytes": scores_by_sha[sha],
            "emitted_pixels": int(mask.sum()),
            "holdout_dti_pooled": float(hr["pooled_dti"]),
            "holdout_dti_ci95": [float(x) for x in hr["ci95_cluster_bootstrap"]],
            "hide_and_recover_evaluator": hr["evaluator_version"],
            "n_withheld_positives": int(hr["n_withheld_positives"]),
            "sgmc_prevalence_calibrated_dti": float(sg["sgmc_prevalence_calibrated_dti"]),
            "sgmc_calibrated_ci95": [float(x) for x in sg["sgmc_calibrated_ci95"]],
            "sgmc_evaluator": sg["evaluator_version"],
        }
        with PARTIAL.open("a") as f:
            f.write(json.dumps(rec) + "\n")
        rows_out.append(rec)
        print(f"{len(rows_out):3d} {r['submission'][:48]:48s} owner={rec['owner_reported_score']:.4f} "
              f"holdout={rec['holdout_dti_pooled']:.6f} sgmc={rec['sgmc_prevalence_calibrated_dti']:.6f} "
              f"[{time.time() - t0:.0f}s]", flush=True)

    owner = np.array([r["owner_reported_score"] for r in rows_out])
    hold = np.array([r["holdout_dti_pooled"] for r in rows_out])
    sgmc = np.array([r["sgmc_prevalence_calibrated_dti"] for r in rows_out])
    rho_h, p_h = spearmanr(owner, hold)
    rho_s, p_s = spearmanr(owner, sgmc)

    # 95% CI for Spearman rho by bootstrap over rasters (fixed seed for reproducibility).
    rng = np.random.default_rng(20261030)
    bh, bs = [], []
    n = len(owner)
    for _ in range(2000):
        idx = rng.integers(0, n, n)
        if len(set(owner[idx])) < 3:
            continue
        bh.append(spearmanr(owner[idx], hold[idx])[0])
        bs.append(spearmanr(owner[idx], sgmc[idx])[0])
    ci_h = [float(np.nanpercentile(bh, 2.5)), float(np.nanpercentile(bh, 97.5))]
    ci_s = [float(np.nanpercentile(bs, 2.5)), float(np.nanpercentile(bs, 97.5))]

    verdict_h = "H1a supported" if (rho_h < 0 and ci_h[1] < 0) else "H1a NOT supported (sign or CI)"
    verdict_s = "H1b supported" if (rho_s > 0 and ci_s[0] > 0) else "H1b NOT supported (sign or CI)"
    out = {
        "schema_version": 1,
        "generated_by": "scripts/ledger_calibration_check.py",
        "date_utc": "2026-10-30",
        "purpose": "Experiment 3: rank calibration of HOLDOUT-DTI and SGMC-CAL against OWNER-REPORT live scores at scale. Not a projection.",
        "preregistration": "Docstring of scripts/ledger_calibration_check.py (written before the run).",
        "evaluator_versions": {"hide_and_recover": "GEMSDOE32-HIDE-RECOVER-v3.0", "sgmc_cal": "GEMSDOE32-SGMC-CAL-v3.0"},
        "score_label": "OWNER-REPORT (live ledger; no organizer receipts)",
        "n_ledger_rows_ok": len(ok_rows),
        "n_unique_rasters": len(by_sha),
        "n_scored": int(n),
        "n_excluded": len(excluded),
        "excluded": excluded,
        "spearman_owner_vs_holdout_pooled": {"rho": round(float(rho_h), 4), "p_value": round(float(p_h), 6),
                                             "bootstrap_ci95": [round(ci_h[0], 4), round(ci_h[1], 4)]},
        "spearman_owner_vs_sgmc_prevalence_calibrated": {"rho": round(float(rho_s), 4), "p_value": round(float(p_s), 6),
                                                         "bootstrap_ci95": [round(ci_s[0], 4), round(ci_s[1], 4)]},
        "verdict": {"H1a": verdict_h, "H1b": verdict_s},
        "runtime_seconds": round(time.time() - t0, 1),
        "rows": sorted(rows_out, key=lambda r: -r["owner_reported_score"]),
    }
    dest = ROOT / "evidence" / "ledger_calibration_check_20261030.json"
    dest.write_text(json.dumps(out, indent=2) + "\n")
    print(f"n={n} excluded={len(excluded)}")
    print(f"owner~holdout rho={rho_h:.4f} p={p_h:.4g} CI={ci_h} -> {verdict_h}")
    print(f"owner~sgmc_cal rho={rho_s:.4f} p={p_s:.4g} CI={ci_s} -> {verdict_s}")
    print(f"wrote {dest.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
