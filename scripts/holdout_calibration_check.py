#!/usr/bin/env python3
"""Calibration check: does the repo's HOLDOUT-DTI rank rasters the way the leaderboard does?

Scores every raster in CALIBRATION_SET with the canonical evaluator (`scripts/evaluate_holdout.py`
-> `gems32.holdout`, GEMSDOE32-HIDE-RECOVER-v3.0 and GEMSDOE32-SGMC-CAL-v3.0) and compares the
rank order with the OWNER-REPORT scores copied from the supplied site list. Output is a
calibration diagnostic only. It is NOT a leaderboard projection and NOT an organizer score.

Writes evidence/holdout_calibration_check_20261030.json.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

import evaluate_holdout as ev  # noqa: E402
from gems32.holdout import load_holdout_context  # noqa: E402
from gems32.paths import data_dir  # noqa: E402

# (label, local path, OWNER-REPORT score copied from the supplied site list, source of the score)
CALIBRATION_SET = [
    ("GEMSDOE24", ".cache/registry/GEMSDOE24/docs/downloads/gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan.tif", 0.2477, "site list: GEMSDOE24"),
    ("GEMSDOE25", ".cache/registry/GEMSDOE25/docs/downloads/gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif", 0.2600, "site list: GEMSDOE25"),
    ("GEMSDOE27", ".cache/registry/GEMSDOE27/docs/downloads/gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan.tif", 0.2449, "site list: GEMSDOE27"),
    ("GEMSDOE28", ".cache/registry/GEMSDOE28/docs/downloads/gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif", 0.2710, "site list: GEMSDOE28"),
    ("GEMSDOE30", ".cache/registry/GEMSDOE30/docs/downloads/gemsdoe30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca.tif", 0.2600, "site list: GEMSDOE30"),
    ("GEMSDOE31", ".cache/registry/GEMSDOE31/docs/downloads/gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-nan.tif", 0.2708, "site list: GEMSDOE31"),
    ("GEMSDOE32", ".cache/registry/GEMSDOE32/docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif", 0.2778, "site list: GEMSDOE32"),
    ("GEMSDOE33", ".cache/registry/GEMSDOE33/docs/downloads/GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e.tif", 0.2632, "site list: GEMSDOE33"),
    ("GEMSDOE36", ".cache/registry/GEMSDOE36/docs/downloads/gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif", 0.2750, "site list: GEMSDOE36"),
    ("gems19-h19-5 (scored group)", ".cache/gems_data/scored/gems19-h19-5-powerlaw-budget-multiline-corroborated-20260930-e27054cf-nan.tif", 0.1922, "site list: GEMSDOE19"),
    ("gems19-h19-4 (scored group)", ".cache/gems_data/scored/gems19-h19-4-multiline-corroborated-openness-thermal-pop-20260930-691e4dfa-nan.tif", 0.1894, "site list: GEMSDOE19"),
    ("gems16-h16-1 (scored group)", ".cache/gems_data/scored/gems16-h16-1-topo-geophys-baseline-ridges-20260930-df20f65e-nan.tif", 0.1855, "site list: GEMSDOE16"),
    ("gems28-h27-4-r1-solo (scored group)", ".cache/gems_data/scored/gems28-h27-4-r1-solo-d2-8-20261003-8acb75e1f2cc-allfinite.tif", 0.2708, "site list: GEMSDOE28 (h27-4-r1-solo-d2-8)"),
    ("gems10-h28-dotted-ridge (scored group)", ".cache/gems_data/scored/gems10-h28-dotted-ridge-20260928T020256236880Z-6452ae1d00.tif", 0.1839, "site list: GEMSDOE10"),
    ("gems10-h25-ctx-ridge (scored group)", ".cache/gems_data/scored/gems10-h25-ctx-ridge-20260927T232947704150Z-6452ae1d00.tif", 0.1280, "site list: GEMSDOE10"),
    ("8GEMSDOE Hedge-v2 (scored group)", ".cache/gems_data/scored/8GEMSDOE_Hedge-v2_submission.tif", 0.1563, "site list: 8GEMSDOE"),
    ("13GEMSDOE r13-lattice (scored group)", ".cache/gems_data/scored/13gems_20261001_r13-lattice-s5_v2_nan-outside.tif", 0.0904, "site list: 13GEMSDOE"),
    ("GEMSDOE9 2314b599 (scored group)", ".cache/gems_data/scored/gemsdoe9-PLACEHOLDER-2314b599.tif", 0.0107, "site list: GEMSDOE9 (2314b599)"),
]


def main() -> int:
    ddir = data_dir()
    ctx = load_holdout_context(ddir)  # validates the holdout inputs once; evaluate_path reloads per call
    del ctx
    rows = []
    for label, rel, owner_score, src in CALIBRATION_SET:
        path = ROOT / rel
        if not path.exists():
            raise SystemExit(f"missing raster for {label}: {rel} (run scripts/restore_data.py first)")
        res = ev.evaluate_path(path, ddir=ddir, name=label)
        hr = res["hide_and_recover"]
        sg = res["sgmc_off_catalogue"]
        rows.append(
            {
                "label": label,
                "path": rel,
                "owner_reported_score": owner_score,
                "owner_score_source": src,
                "holdout_dti_pooled": hr["pooled_dti"],
                "holdout_dti_ci95": hr["ci95_cluster_bootstrap"],
                "n_withheld_positives": hr["n_withheld_positives"],
                "sgmc_raw_pooled_dti": sg["sgmc_raw_pooled_dti"],
                "sgmc_prevalence_calibrated_dti": sg["sgmc_prevalence_calibrated_dti"],
                "sgmc_calibrated_ci95": sg["sgmc_calibrated_ci95"],
                "emitted_pixels": res["emitted_pixels"],
                "evaluator_version": hr["evaluator_version"],
            }
        )
        print(f"{label:42s} owner={owner_score:.4f} holdout={hr['pooled_dti']:.6f} sgmc_cal={sg['sgmc_prevalence_calibrated_dti']:.6f}", flush=True)

    owner = [r["owner_reported_score"] for r in rows]
    hold = [r["holdout_dti_pooled"] for r in rows]
    sgmc = [r["sgmc_prevalence_calibrated_dti"] for r in rows]
    rho_h, p_h = spearmanr(owner, hold)
    rho_s, p_s = spearmanr(owner, sgmc)
    focus = [r for r in rows if r["label"].startswith("GEMSDOE") and r["label"][7:].isdigit()]
    f_owner = [r["owner_reported_score"] for r in focus]
    rho_fh, p_fh = spearmanr(f_owner, [r["holdout_dti_pooled"] for r in focus])
    rho_fs, p_fs = spearmanr(f_owner, [r["sgmc_prevalence_calibrated_dti"] for r in focus])
    out = {
        "schema_version": 1,
        "generated_by": "scripts/holdout_calibration_check.py",
        "date_utc": "2026-10-30",
        "purpose": "Rank-calibration diagnostic of HOLDOUT-DTI against OWNER-REPORT leaderboard scores. Not a score projection.",
        "evaluator_versions": {
            "hide_and_recover": rows[0]["evaluator_version"],
            "sgmc_cal": "GEMSDOE32-SGMC-CAL-v3.0",
        },
        "n": len(rows),
        "spearman_owner_vs_holdout_pooled": {"rho": round(float(rho_h), 4), "p_value": round(float(p_h), 4)},
        "spearman_owner_vs_sgmc_prevalence_calibrated": {"rho": round(float(rho_s), 4), "p_value": round(float(p_s), 4)},
        "focus_nine_subset": {
            "labels": [r["label"] for r in focus],
            "n": len(focus),
            "spearman_owner_vs_holdout_pooled": {"rho": round(float(rho_fh), 4), "p_value": round(float(p_fh), 4)},
            "spearman_owner_vs_sgmc_prevalence_calibrated": {"rho": round(float(rho_fs), 4), "p_value": round(float(p_fs), 4)},
        },
        "rows": rows,
        "label_note": "owner_reported_score values are OWNER-REPORT (copied from the supplied site list), not organizer receipts.",
    }
    dest = ROOT / "evidence" / "holdout_calibration_check_20261030.json"
    dest.write_text(json.dumps(out, indent=2) + "\n")
    print(f"spearman owner~holdout rho={rho_h:.4f} p={p_h:.4f}; owner~sgmc_cal rho={rho_s:.4f} p={p_s:.4f}")
    print(f"focus nine (n={len(focus)}): owner~holdout rho={rho_fh:.4f} p={p_fh:.4f}; owner~sgmc_cal rho={rho_fs:.4f} p={p_fs:.4f}")
    print(f"wrote {dest.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
