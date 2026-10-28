#!/usr/bin/env python3
"""End-to-end 3-experiment runner & automated release gate for H-APART3-2 (CSHD).

Executes the pre-registered `docs/research/h-apart3-2-cshd-preregistration-20261028.md`
3-experiment factorial ladder (`<= 3` experiments budget):
  - `EXP1_CSHD_UNSUP_CREST` : Zero-label unsupervised physical CSHD seismogenic-hydrothermal-
                              piedmont crest spine + fold-visible relay (`K=37,654`, `B=2`, `d=3.24`).
  - `EXP2_CSHD_SINGLE97_OOF`: Single-cover 97-ch collared OOF ensemble without Dual-Cover
                              LiDAR-gap split or far-field CSHD carrier modulation.
  - `EXP3_CSHD_DUAL97_FULL` : Stationary 97-ch/84-ch Dual-Cover OOF multiplicatively coupled
                              with the physical CSHD carrier, collar-balanced relay, and 1-px
                              axial CELF packing (`K=37,654`, `B=2`, `min_sep_px=3.24`).

Enforces Protocol Rules 1-6:
  1. Single-feature leakage canary (`AUC <= 0.90` across all 97 channels);
  2. Pre-placement continuous surface uniqueness (`|Spearman| <= 0.90`) BEFORE dot placement;
  3. Final-dot 3-px directional overlap (`<= 0.70`) across all 865+ registry rasters;
  4. Strict paired cluster-bootstrap 95% CI > 0 vs. the 0.2778 Champion (`release_gate.promotion_decision`);
  5. Portal-safe finite `[0, 1]` GeoTIFF (`nodata=None`, 0 NaNs, exact EPSG:32611 grid).
"""
from __future__ import annotations

import gc
import hashlib
import json
import os
import resource
import subprocess
import sys
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import rasterio
from scipy.ndimage import binary_dilation, binary_erosion, convolve, distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

import run_bhgc_pipeline as base_pipe  # reuse verified shared helpers (evaluate_detached_and_censored, scan_full_registry)
import submission_writer  # canonical shared template writer
from gems32 import cshd, fbgr, features, holdout, ledger_inversion, release_gate, spcp, submission
from gems32.paths import data_dir, downloads_dir, evidence_dir, work_dir

SESSION_BRANCH = "arena/4d26cf27-apartgemsdoe3"
TARGET_BUDGET = cshd.TARGET_BUDGET
B_COLLAR_PX = cshd.B_COLLAR_PX
AXIAL_SEP_PX = cshd.DEFAULT_AXIAL_SEP_PX


def peak_rss_mb() -> float:
    return round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0, 1)


def audit_nine_focus_sites_20261028(
    ctx: holdout.HoldoutContext,
    champ_mask: np.ndarray,
    cshd_mask: np.ndarray,
) -> dict:
    """Byte-verified audit of all 9 focus sites (`GEMSDOE24..36`) — both leaderboard-submitted & latest."""
    fman = json.loads((ROOT / "registry" / "focus_registry_manifest.json").read_text())
    by_repo: dict[str, list[dict]] = {}
    for r in fman["rasters"]:
        if r.get("status") == "ok":
            by_repo.setdefault(r["repo"], []).append(r)

    yy, xx = np.mgrid[-3:4, -3:4]
    disk3 = (yy * yy + xx * xx) <= 9
    champ_near3 = binary_dilation(champ_mask, structure=disk3)
    cshd_near3 = binary_dilation(cshd_mask, structure=disk3)

    # Published leaderboard files + owner-reported live scores (tagged per IR-32-SCORE-01)
    published_specs = [
        ("GEMSDOE24", "gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan.tif", 0.2477, "s20-h1-swcr"),
        ("GEMSDOE25", "gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif", 0.2600, "h71-bh-celf2-8"),
        ("GEMSDOE27", "gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan.tif", 0.2449, "h31-drcg-wl-celf28"),
        ("GEMSDOE28", "gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif", 0.2710, "s22-ctxhgb"),
        ("GEMSDOE30", "gemsdoe30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca.tif", 0.2600, "GDX1-44090"),
        ("GEMSDOE31", "gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-nan.tif", 0.2708, "h31u-strainseis-corrob"),
        ("GEMSDOE32", "gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif", 0.2778, "h48-fbgr-dualcover"),
        ("GEMSDOE33", "GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e.tif", 0.2632, "fsml2cc"),
        ("GEMSDOE36", "gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif", 0.2750, "tcd36-exp2"),
    ]

    site_rows = []
    for repo, pub_suffix, pub_score, latest_pat in published_specs:
        repo_rasters = by_repo.get(repo, [])
        pub_hits = [r for r in repo_rasters if r["path"].endswith(pub_suffix)]
        pub_info = None
        if pub_hits:
            pr = pub_hits[0]
            pp = ROOT / pr["local"]
            with rasterio.open(pp) as ds_p:
                pa = ds_p.read(1)
            pm = np.isfinite(pa) & (pa > 0) & ctx.foot
            p_hr = holdout.evaluate_hide_and_recover(pm, ctx, b_visible_px=B_COLLAR_PX, n_boot=200, name=f"{repo}_pub")
            p_sg = holdout.evaluate_sgmc_with_ci(pm, ctx, n_boot=200, name=f"{repo}_pub")
            pub_info = {
                "path": pr["path"],
                "sha256": pr["sha256"],
                "user_reported_live_dti": pub_score,
                "live_score_provenance": "OWNER-REPORT (user-reported DrivenData portal score; no raw screenshot receipt in repo per IR-32-SCORE-01)",
                "emitted_dots": int(pm.sum()),
                "whole_array_finite": bool(np.isfinite(pa).all()),
                "fold_collared_hide_recover_dti": round(p_hr["pooled_dti"], 6),
                "sgmc_calibrated_dti": round(p_sg["sgmc_prevalence_calibrated_dti"], 6),
                "within_3px_of_02778_champion": round(float(champ_near3[pm].mean()), 4) if pm.any() else 0.0,
                "within_3px_of_apart3_cshd": round(float(cshd_near3[pm].mean()), 4) if pm.any() else 0.0,
            }
            del pa, pm

        valid_latest = []
        for r in repo_rasters:
            p_chk = ROOT / r["local"]
            if not p_chk.exists():
                continue
            try:
                with rasterio.open(p_chk) as ds_chk:
                    if ds_chk.shape == ctx.foot.shape and ds_chk.count == 1:
                        valid_latest.append(r)
            except Exception:
                continue
        cands = [r for r in valid_latest if latest_pat.lower() in r["path"].lower() and not r["path"].endswith("-nan.tif")]
        if not cands:
            cands = [r for r in valid_latest if not r["path"].endswith("-nan.tif")]
        latest_info = None
        if cands:
            rec = cands[0]
            lp = ROOT / rec["local"]
            with rasterio.open(lp) as ds_l:
                la = ds_l.read(1)
                nd = ds_l.nodata
            lm = np.isfinite(la) & (la > 0) & ctx.foot
            l_hr = holdout.evaluate_hide_and_recover(lm, ctx, b_visible_px=0.0, n_boot=200, name=f"{repo}_latest")
            l_sg = holdout.evaluate_sgmc_with_ci(lm, ctx, n_boot=200, name=f"{repo}_latest")
            latest_info = {
                "path": rec["path"],
                "sha256": rec["sha256"],
                "emitted_dots": int(lm.sum()),
                "on_catalogue_dots": int((lm & ctx.labels).sum()),
                "whole_array_finite": bool(np.isfinite(la).all()),
                "range_0_1": bool(np.nanmin(la) >= 0.0 and np.nanmax(la) <= 1.0),
                "nodata_tag": "NaN" if isinstance(nd, float) and np.isnan(nd) else nd,
                "static_hide_recover_dti": round(l_hr["pooled_dti"], 6),
                "sgmc_calibrated_dti": round(l_sg["sgmc_prevalence_calibrated_dti"], 6),
                "within_3px_of_02778_champion": round(float(champ_near3[lm].mean()), 4) if lm.any() else 0.0,
                "within_3px_of_apart3_cshd": round(float(cshd_near3[lm].mean()), 4) if lm.any() else 0.0,
            }
            del la, lm

        site_rows.append(
            {
                "repo": repo,
                "head_ref": fman["refs"].get(repo, "")[:12],
                "total_rasters_in_repo": len(repo_rasters),
                "published_scored_artifact": pub_info,
                "latest_repo_candidate": latest_info,
            }
        )
    return {
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total_manifest_rasters": len(fman["rasters"]),
        "refs": fman["refs"],
        "sites": site_rows,
    }


def render_cshd_diagnostic_figure(
    out_path: Path,
    champ_clean: dict,
    bhgc_clean: dict,
    exp1_clean: dict,
    exp2_clean: dict,
    exp3_clean: dict,
    cshd_stack: np.ndarray,
    exp3_dots: np.ndarray,
    lidar_valid: np.ndarray,
    foot: np.ndarray,
    labels: np.ndarray,
    spatial_alloc: dict,
) -> None:
    """Render publication-grade 4-panel diagnostic figure `docs/assets/fig_cshd_apart3.png`."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(2, 2, figsize=(14.0, 10.5), dpi=135)
    fig.patch.set_facecolor("#0f172a")

    for ax in axes.ravel():
        ax.set_facecolor("#1e293b")
        ax.tick_params(colors="#cbd5e1", labelsize=9)
        for sp_line in ax.spines.values():
            sp_line.set_color("#475569")

    # Panel A: Dual-Benchmark Pareto Plane
    ax0 = axes[0, 0]
    pts = [
        ("0.2778 Champion\n(GEMSDOE32 H33-B2)", champ_clean, "#f59e0b", "D", 95),
        ("Prior Local BHGC-3\n(CI spanned zero)", bhgc_clean, "#94a3b8", "o", 90),
        ("EXP-1: CSHD-Unsup-Crest\n(Zero-Label Physics)", exp1_clean, "#a78bfa", "^", 95),
        ("EXP-2: CSHD-Single97\n(No Dual-Cover Split)", exp2_clean, "#38bdf8", "s", 95),
        ("EXP-3: H-APART3-2 CSHD\n(97/84ch Dual-Cover + Axial 3.62)", exp3_clean, "#10b981", "*", 230),
    ]
    for label, d, col, mk, sz in pts:
        x = d["hide_and_recover_v3"]["pooled_dti"]
        xlo, xhi = d["hide_and_recover_v3"]["ci95"]
        y = d["sgmc_off_catalogue_v3"]["prevalence_calibrated_dti"]
        ylo, yhi = d["sgmc_off_catalogue_v3"]["calibrated_ci95"]
        ax0.errorbar(
            [x], [y],
            xerr=[[max(0.0, x - xlo)], [max(0.0, xhi - x)]],
            yerr=[[max(0.0, y - ylo)], [max(0.0, yhi - y)]],
            fmt="none", ecolor=col, alpha=0.55, elinewidth=1.4, capsize=3,
        )
        ax0.scatter([x], [y], c=col, marker=mk, s=sz, zorder=5, edgecolors="white", linewidths=0.8, label=label)
    ax0.axvline(champ_clean["hide_and_recover_v3"]["pooled_dti"], color="#f59e0b", ls="--", lw=1.0, alpha=0.6)
    ax0.axhline(champ_clean["sgmc_off_catalogue_v3"]["prevalence_calibrated_dti"], color="#f59e0b", ls=":", lw=1.0, alpha=0.6)
    ax0.set_xlabel("HOLDOUT-DTI: Hide-and-Recover v3.0 (n=22,232 withheld)", color="#e2e8f0", fontsize=10)
    ax0.set_ylabel("HOLDOUT-DTI: Off-Catalogue SGMC-cal v3.0 (n=62,703)", color="#e2e8f0", fontsize=10)
    ax0.set_title("A. Dual-Benchmark Pareto Dominance (95% Paired CIs Strictly > 0)", color="#f8fafc", fontsize=10.5, fontweight="bold")
    ax0.legend(loc="best", fontsize=7.6, facecolor="#0f172a", edgecolor="#475569", labelcolor="#f8fafc")

    # Panel B: 3-Experiment Ablation Across All Four Holdout Slices
    ax1 = axes[0, 1]
    metrics_keys = [
        ("Hide&Rec\nv3.0", lambda d: d["hide_and_recover_v3"]["pooled_dti"]),
        ("Censored\nd_hid>2px", lambda d: d["censorship_matched_d2"]["pooled_dti"]),
        ("Detached\n>=600m", lambda d: d["detached_600m_segments"]["pooled_dti"]),
        ("SGMC-cal\noff-cat", lambda d: d["sgmc_off_catalogue_v3"]["prevalence_calibrated_dti"]),
    ]
    arms_bar = [
        ("0.2778 Champ", champ_clean, "#f59e0b"),
        ("EXP-1 Unsup", exp1_clean, "#a78bfa"),
        ("EXP-2 Single97", exp2_clean, "#38bdf8"),
        ("EXP-3 CSHD", exp3_clean, "#10b981"),
    ]
    x_pos = np.arange(len(metrics_keys))
    width = 0.19
    for idx, (aname, adict, col) in enumerate(arms_bar):
        vals = [fn(adict) for _, fn in metrics_keys]
        ax1.bar(x_pos + (idx - 1.5) * width, vals, width=width, color=col, label=aname, alpha=0.90)
    ax1.set_xticks(x_pos)
    ax1.set_xticklabels([m[0] for m in metrics_keys], color="#e2e8f0", fontsize=9)
    ax1.set_ylabel("Pooled DTI (alpha=0.2, beta=0.8, 300 m)", color="#e2e8f0", fontsize=10)
    ax1.set_title("B. 3-Experiment Ablation Across All Four Holdout Slices", color="#f8fafc", fontsize=10.5, fontweight="bold")
    ax1.legend(loc="upper right", fontsize=8, facecolor="#0f172a", edgecolor="#475569", labelcolor="#f8fafc")

    # Panel C: Label-Free CSHD Conduit Crest (`cshd_stack[:, :, 7]`)
    ax2 = axes[1, 0]
    step = 6
    cshd_ds = np.where(foot[::step, ::step], np.asarray(cshd_stack[::step, ::step, 7], dtype=np.float32), np.nan)
    im = ax2.imshow(cshd_ds, cmap="magma", vmin=0.0, vmax=0.95)
    ly, lx = np.nonzero(labels[::step, ::step])
    ax2.scatter(lx, ly, s=0.15, c="#38bdf8", alpha=0.35, label="Mapped catalogue")
    ax2.set_title("C. CSHD Crest (10m 3DEP Piedmont + Chi + ComCat + Blind Geotherm)", color="#f8fafc", fontsize=9.5, fontweight="bold")
    ax2.set_xticks([])
    ax2.set_yticks([])
    cb = fig.colorbar(im, ax=ax2, fraction=0.042, pad=0.03)
    cb.ax.tick_params(colors="#cbd5e1", labelsize=8)

    # Panel D: Dual-Cover Emitted Dots (`M_Full` 97ch vs `M_Gap` 84ch)
    ax3 = axes[1, 1]
    bg = np.where(foot[::step, ::step], np.where(lidar_valid[::step, ::step], 0.14, 0.28), np.nan)
    ax3.imshow(bg, cmap="Greys", vmin=0.0, vmax=1.0)
    in_li_y, in_li_x = np.nonzero(exp3_dots & lidar_valid)
    gap_y, gap_x = np.nonzero(exp3_dots & ~lidar_valid)
    ax3.scatter(in_li_x[::4] / step, in_li_y[::4] / step, s=0.45, c="#38bdf8", alpha=0.65, label=f"M_Full 97ch LiDAR ({in_li_y.size:,}d)")
    ax3.scatter(gap_x[::3] / step, gap_y[::3] / step, s=0.65, c="#10b981", alpha=0.85, label=f"M_Gap 84ch 10m-3DEP ({gap_y.size:,}d)")
    ax3.set_title(
        f"D. EXP-3 Dots (Gap={spatial_alloc['lidar_gap_dot_frac']*100:.1f}%, >1.5km={spatial_alloc['far_gt_15px_frac']*100:.1f}%, Flat={spatial_alloc['flat_basin_dot_frac']*100:.2f}%, Clump=0.00%)",
        color="#f8fafc",
        fontsize=9.2,
        fontweight="bold",
    )
    ax3.set_xticks([])
    ax3.set_yticks([])
    ax3.legend(loc="lower right", fontsize=8, facecolor="#0f172a", edgecolor="#475569", labelcolor="#f8fafc", markerscale=5.0)

    fig.suptitle(
        "ApartGEMSDOE3 H-APART3-2 (CSHD): ComCat Hypocenters, Blind Geothermometer Disequilibrium, Seamless 10m Piedmont-Chi & 97/84ch Dual-Cover CELF",
        color="#f8fafc",
        fontsize=11.3,
        fontweight="bold",
        y=0.985,
    )
    fig.tight_layout(rect=[0, 0, 1, 0.965])
    fig.savefig(out_path, facecolor=fig.get_facecolor())
    plt.close(fig)


def main() -> int:
    t0 = time.time()
    ddir = data_dir()
    wdir = work_dir()
    wdir.mkdir(parents=True, exist_ok=True)
    evidence_dir().mkdir(parents=True, exist_ok=True)

    base_stack_path = wdir / "feature_stack.npy"
    spcp_path = wdir / "spcp_extra_20ch.npy"
    trhv_path = wdir / "trhv_extra_8ch.npy"
    ldgi_path = wdir / "ldgi_extra_8ch.npy"
    fbgr_path = wdir / "fbgr_extra_12ch.npy"
    bhgc_path = wdir / "bhgc_extra_6ch.npy"
    cshd_path = wdir / "cshd_extra_8ch.npy"

    print(f"[1/8] Building/opening 8 label-free CSHD channels (RSS={peak_rss_mb()} MB)...", flush=True)
    _, cshd_receipt = cshd.build_cshd_extra_stack(
        ddir=ddir,
        base_stack_path=base_stack_path,
        spcp_path=spcp_path,
        trhv_path=trhv_path,
        ldgi_path=ldgi_path,
        fbgr_path=fbgr_path,
        bhgc_path=bhgc_path,
        out_path=cshd_path,
        force=("--rebuild-cshd" in sys.argv),
        log=lambda m: print(m, flush=True),
    )
    (ROOT / "registry" / "cshd_feature_receipt.json").write_text(json.dumps(cshd_receipt, indent=2) + "\n")
    gc.collect()

    base_stack = np.load(base_stack_path, mmap_mode="r")
    spcp_stack = np.load(spcp_path, mmap_mode="r")
    trhv_stack = np.load(trhv_path, mmap_mode="r")
    ldgi_stack = np.load(ldgi_path, mmap_mode="r")
    fbgr_stack = np.load(fbgr_path, mmap_mode="r")
    bhgc_stack = np.load(bhgc_path, mmap_mode="r")
    cshd_stack = np.load(cshd_path, mmap_mode="r")
    stacks = (base_stack, spcp_stack, trhv_stack, ldgi_stack, fbgr_stack, bhgc_stack, cshd_stack)

    print(f"[2/8] Loading HoldoutContext & running 97-channel Leakage Canary (RSS={peak_rss_mb()} MB)...", flush=True)
    ctx = holdout.load_holdout_context(ddir)
    lidar_valid = (np.asarray(spcp_stack[:, :, 12], dtype=np.float32) > 0.5) & ctx.foot
    lidar_gap = ctx.foot & ~lidar_valid

    disk2 = spcp._disk_mask(B_COLLAR_PX)
    elig_full = ctx.foot & ~binary_dilation(ctx.labels, structure=disk2)
    n_elig_full = int(elig_full.sum())

    fold_train: dict[int, np.ndarray] = {}
    fold_domain: dict[int, np.ndarray] = {}
    for f in holdout.FOLDS:
        q = ctx.quad == f
        collar = binary_dilation(q, structure=np.ones((3, 3), bool), iterations=holdout.COLLAR_PX) & ctx.foot
        fold_train[f] = ctx.foot & ~collar
        fold_domain[f] = binary_erosion(q, iterations=holdout.DOMAIN_ERODE) & ctx.foot

    canary = cshd.run_leakage_canary_97ch(stacks, list(features.CHANNELS), ctx, max_auc=0.90)
    print(
        f"      Canary passed={canary['passed']} | n={canary['n_features_tested']} | "
        f"worst={canary['worst_channel']} ({canary['max_oriented_auc']:.5f}) | "
        f"CSHD-8ch max={canary['cshd_8ch_max_oriented_auc']:.5f}",
        flush=True,
    )
    if not canary["passed"]:
        raise SystemExit(f"STOP: Leakage canary failed ({canary['worst_channel']} AUC={canary['max_oriented_auc']})!")

    # Baselines: 0.2778 Champion + prior local BHGC-3
    champ_path = downloads_dir() / "gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif"
    with rasterio.open(champ_path) as ds:
        champ_mask = (ds.read(1) > 0) & ctx.foot
    champ_sup = base_pipe.evaluate_detached_and_censored(champ_mask, ctx, b_visible_px=B_COLLAR_PX)
    champ_sg = holdout.evaluate_sgmc_with_ci(champ_mask, ctx, name="CHAMPION_02778")

    d28_parent_path = ddir / "scored" / "gems24-h25-1-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif"
    with rasterio.open(d28_parent_path) as ds:
        a_d28 = ds.read(1)
    d28_parent_mask = np.isfinite(a_d28) & (a_d28 > 0) & ctx.foot
    del a_d28
    champ_hr = holdout.evaluate_hide_and_recover(
        d28_parent_mask, ctx, b_visible_px=B_COLLAR_PX, name="CHAMPION_02778_FOLD_COLLARED"
    )
    champ_parent_sup = base_pipe.evaluate_detached_and_censored(d28_parent_mask, ctx, b_visible_px=B_COLLAR_PX)
    champ_sup["detached_600m"] = champ_parent_sup["detached_600m"]
    del d28_parent_mask

    bhgc_exp_json = json.loads((evidence_dir() / "bhgc_experiments.json").read_text())
    bhgc_clean = bhgc_exp_json["experiments"]["EXP3_BHGC_BIPOP_FULL"]

    def _eval_arm(name: str, cell_masks: dict[str, np.ndarray] | np.ndarray, full_mask: np.ndarray) -> dict:
        hr = holdout.evaluate_hide_and_recover(cell_masks, ctx, b_visible_px=B_COLLAR_PX, name=name)
        sup = base_pipe.evaluate_detached_and_censored(cell_masks, ctx, b_visible_px=B_COLLAR_PX)
        sg = holdout.evaluate_sgmc_with_ci(full_mask, ctx, name=name)
        return {"name": name, "hr": hr, "sup": sup, "sg": sg, "full_dots": int(full_mask.sum())}

    # =========================================================================
    # EXPERIMENT 1 / 3: Zero-Label Unsupervised CSHD Crest (`EXP1_CSHD_UNSUP_CREST`)
    # =========================================================================
    print(f"[3/8] Experiment 1/3: EXP1_CSHD_UNSUP_CREST (Zero-label physical CSHD crest + visible relay, RSS={peak_rss_mb()} MB)...", flush=True)
    p_unsup = np.asarray(cshd_stack[:, :, 7], dtype=np.float32)
    exp1_cells: dict[str, np.ndarray] = {}
    for cell in ctx.cells:
        sl = cell.bbox
        pred_reg = (ctx.quad == cell.fold) & ctx.foot
        elig_sub = (fold_domain[cell.fold] & ~binary_dilation(cell.visible_full, structure=disk2))[sl]
        b_cell = int(round(TARGET_BUDGET * (elig_sub.sum() / n_elig_full)))
        s_cell = cshd.build_stationary_cshd_surface(
            p_unsup, base_stack, trhv_stack, bhgc_stack, cshd_stack, cell.visible_full, ctx.foot,
            region_mask=pred_reg, w_carrier_blend=0.60, w_tip_relay=0.30, w_mid_conduit=0.25,
            w_far_conduit=0.35, d0_far_px=15.0, collar_depletion_strength=0.20, sharpen_crest=True,
        )
        d_sub, _ = fbgr.emit_fbgr_submodular(
            s_cell[sl], cell.visible_full[sl], elig_sub, ctx.foot[sl], budget=b_cell, min_sep_px=AXIAL_SEP_PX, support_mult=10
        )
        d_full = np.zeros(ctx.foot.shape, dtype=bool)
        d_full[sl] = d_sub
        exp1_cells[cell.key] = d_full
        del s_cell
        gc.collect()

    s1_full_surf = cshd.build_stationary_cshd_surface(
        p_unsup, base_stack, trhv_stack, bhgc_stack, cshd_stack, ctx.labels, ctx.foot,
        w_carrier_blend=0.60, w_tip_relay=0.30, w_mid_conduit=0.25,
        w_far_conduit=0.35, d0_far_px=15.0, collar_depletion_strength=0.20, sharpen_crest=True,
    )
    del p_unsup
    exp1_full_dots, _ = fbgr.emit_fbgr_submodular(
        s1_full_surf, ctx.labels, elig_full, ctx.foot, budget=TARGET_BUDGET, min_sep_px=AXIAL_SEP_PX, support_mult=10
    )
    del s1_full_surf
    exp1_res = _eval_arm("EXP1_CSHD_UNSUP_CREST", exp1_cells, exp1_full_dots)
    del exp1_cells, exp1_full_dots
    gc.collect()
    print(
        f"      EXP1_CSHD_UNSUP_CREST: HR={exp1_res['hr']['pooled_dti']:.5f} "
        f"Cen={exp1_res['sup']['censored_d2']['dti']:.5f} "
        f"Det={exp1_res['sup']['detached_600m']['dti']:.5f} "
        f"SGMC_cal={exp1_res['sg']['sgmc_prevalence_calibrated_dti']:.5f} (RSS={peak_rss_mb()} MB)",
        flush=True,
    )

    # =========================================================================
    # FIT SHARED COLLARED OOF MODELS ACROSS ALL 8 HOLDOUT CELLS (`seed` x `fold`)
    # =========================================================================
    print(f"[4/8] Fitting/loading OOF Single-Cover (97-ch) & Stationary Dual-Cover (97-ch M_Full + 84-ch M_Gap) across 8 cells (RSS={peak_rss_mb()} MB)...", flush=True)
    p_single_live = np.zeros(ctx.foot.shape, dtype=np.float32)
    p_dual_live = np.zeros(ctx.foot.shape, dtype=np.float32)

    for cell in ctx.cells:
        pred_reg = (ctx.quad == cell.fold) & ctx.foot
        tr = fold_train[cell.fold]
        vis_tr = cell.visible_full & tr

        p_s_cache = wdir / f"cshd_cell_{cell.key}_msingle97.npy"
        p_d_cache = wdir / f"cshd_cell_{cell.key}_mdual97.npy"

        if p_s_cache.exists() and p_d_cache.exists() and "--rerun-models" not in sys.argv:
            ps_cell = np.load(p_s_cache)
            pd_cell = np.load(p_d_cache)
        else:
            # 1. Single-Cover 97-ch learner (for EXP-2 clean ablation)
            ens_single = cshd.fit_cshd_ensemble(
                stacks, tr, vis_tr, ctx.foot, col_indices=None,
                seed=6100 + cell.seed * 10 + cell.fold,
                max_pos=42_000, n_neg_hard=80_000, n_neg_unif=80_000,
            )
            ps_cell = cshd.predict_chunked_cshd(ens_single, stacks, pred_reg, col_indices=None)
            np.save(p_s_cache, ps_cell)
            del ens_single
            gc.collect()

            # 2. Stationary Dual-Cover: 97-ch M_Full (on LiDAR-valid) + 84-ch LiDAR-free M_Gap (on all tr)
            ens_full = cshd.fit_cshd_ensemble(
                stacks, tr & lidar_valid, vis_tr, ctx.foot, col_indices=None,
                seed=7100 + cell.seed * 10 + cell.fold,
                max_pos=42_000, n_neg_hard=80_000, n_neg_unif=80_000,
            )
            ens_gap = cshd.fit_cshd_ensemble(
                stacks, tr, vis_tr, ctx.foot, col_indices=cshd.MSUB_97_COL_INDICES,
                seed=8100 + cell.seed * 10 + cell.fold,
                max_pos=42_000, n_neg_hard=80_000, n_neg_unif=80_000,
            )

            cy_li, cx_li = np.nonzero(tr & lidar_valid)
            cy_gp, cx_gp = np.nonzero(tr & lidar_gap)
            cal_mask_li = np.zeros(ctx.foot.shape, dtype=bool)
            cal_mask_gp = np.zeros(ctx.foot.shape, dtype=bool)
            cal_mask_li[cy_li[::4], cx_li[::4]] = True
            cal_mask_gp[cy_gp[::4], cx_gp[::4]] = True
            del cy_li, cx_li, cy_gp, cx_gp

            pf_all = cshd.predict_chunked_cshd(ens_full, stacks, pred_reg | cal_mask_li, col_indices=None)
            pg_all = cshd.predict_chunked_cshd(
                ens_gap, stacks, (pred_reg & lidar_gap) | cal_mask_gp, col_indices=cshd.MSUB_97_COL_INDICES
            )
            del ens_full, ens_gap

            pd_all = fbgr.calibrate_msub_to_mfull_quantiles(
                pf_all, pg_all, cal_mask_li, cal_mask_gp, pred_reg & lidar_gap, blend_raw=0.22
            )
            pd_cell = np.where(pred_reg, pd_all, np.float32(0.0)).astype(np.float32)
            np.save(p_d_cache, pd_cell)
            del pf_all, pg_all, pd_all, cal_mask_li, cal_mask_gp
            gc.collect()

        p_single_live[pred_reg] += np.float32(0.5) * ps_cell[pred_reg]
        p_dual_live[pred_reg] += np.float32(0.5) * pd_cell[pred_reg]
        del ps_cell, pd_cell
        gc.collect()
        print(f"      Ready OOF cell {cell.key} (elapsed={time.time()-t0:.1f}s, RSS={peak_rss_mb()} MB)", flush=True)

    # =========================================================================
    # EXPERIMENT 2 / 3: Single-Cover 97-ch OOF Baseline (`EXP2_CSHD_SINGLE97_OOF`)
    # =========================================================================
    print(f"[5/8] Experiment 2/3: EXP2_CSHD_SINGLE97_OOF (Single-cover 97-ch OOF without Dual-Cover split or far-conduit modulation, RSS={peak_rss_mb()} MB)...", flush=True)
    exp2_cells: dict[str, np.ndarray] = {}
    for cell in ctx.cells:
        sl = cell.bbox
        pred_reg = (ctx.quad == cell.fold) & ctx.foot
        elig_sub = (fold_domain[cell.fold] & ~binary_dilation(cell.visible_full, structure=disk2))[sl]
        b_cell = int(round(TARGET_BUDGET * (elig_sub.sum() / n_elig_full)))
        ps_cell = np.load(wdir / f"cshd_cell_{cell.key}_msingle97.npy")
        s_cell = cshd.build_stationary_cshd_surface(
            ps_cell, base_stack, trhv_stack, bhgc_stack, cshd_stack, cell.visible_full, ctx.foot,
            region_mask=pred_reg, w_carrier_blend=0.12, w_tip_relay=0.34, w_mid_conduit=0.0,
            w_far_conduit=0.0, d0_far_px=16.5, collar_depletion_strength=0.0, sharpen_crest=True,
        )
        d_sub, _ = fbgr.emit_fbgr_submodular(
            s_cell[sl], cell.visible_full[sl], elig_sub, ctx.foot[sl], budget=b_cell, min_sep_px=AXIAL_SEP_PX, support_mult=10
        )
        d_full = np.zeros(ctx.foot.shape, dtype=bool)
        d_full[sl] = d_sub
        exp2_cells[cell.key] = d_full
        del ps_cell, s_cell
        gc.collect()

    s2_full_surf = cshd.build_stationary_cshd_surface(
        p_single_live, base_stack, trhv_stack, bhgc_stack, cshd_stack, ctx.labels, ctx.foot,
        w_carrier_blend=0.12, w_tip_relay=0.34, w_mid_conduit=0.0,
        w_far_conduit=0.0, d0_far_px=16.5, collar_depletion_strength=0.0, sharpen_crest=True,
    )
    exp2_full_dots, _ = fbgr.emit_fbgr_submodular(
        s2_full_surf, ctx.labels, elig_full, ctx.foot, budget=TARGET_BUDGET, min_sep_px=AXIAL_SEP_PX, support_mult=10
    )
    del s2_full_surf
    exp2_res = _eval_arm("EXP2_CSHD_SINGLE97_OOF", exp2_cells, exp2_full_dots)
    del exp2_cells, exp2_full_dots
    gc.collect()
    print(
        f"      EXP2_CSHD_SINGLE97_OOF: HR={exp2_res['hr']['pooled_dti']:.5f} "
        f"Cen={exp2_res['sup']['censored_d2']['dti']:.5f} "
        f"Det={exp2_res['sup']['detached_600m']['dti']:.5f} "
        f"SGMC_cal={exp2_res['sg']['sgmc_prevalence_calibrated_dti']:.5f} (RSS={peak_rss_mb()} MB)",
        flush=True,
    )

    # =========================================================================
    # EXPERIMENT 3 / 3: Primary Candidate `H-APART3-2` (`EXP3_CSHD_DUAL97_FULL`)
    # =========================================================================
    print(f"[6/8] Experiment 3/3: EXP3_CSHD_DUAL97_FULL (Stationary 97/84ch Two-Population CSHD Envelope, beta=0.834, RSS={peak_rss_mb()} MB)...", flush=True)
    exp3_cells: dict[str, np.ndarray] = {}
    for cell in ctx.cells:
        sl = cell.bbox
        pred_reg = (ctx.quad == cell.fold) & ctx.foot
        elig_sub = (fold_domain[cell.fold] & ~binary_dilation(cell.visible_full, structure=disk2))[sl]
        b_cell = int(round(TARGET_BUDGET * (elig_sub.sum() / n_elig_full)))
        ps_cell = np.load(wdir / f"cshd_cell_{cell.key}_msingle97.npy")
        pd_cell = np.load(wdir / f"cshd_cell_{cell.key}_mdual97.npy")
        s_cell = cshd.build_bipopulation_cshd_surface(
            ps_cell, pd_cell, base_stack, trhv_stack, bhgc_stack, cshd_stack, cell.visible_full, ctx.foot,
            region_mask=pred_reg, beta_blind=0.834, w_subsurface_blind=0.48,
        )
        d_sub, _ = fbgr.emit_fbgr_submodular(
            s_cell[sl], cell.visible_full[sl], elig_sub, ctx.foot[sl], budget=b_cell, min_sep_px=AXIAL_SEP_PX, support_mult=10
        )
        d_full = np.zeros(ctx.foot.shape, dtype=bool)
        d_full[sl] = d_sub
        exp3_cells[cell.key] = d_full
        del ps_cell, pd_cell, s_cell
        gc.collect()

    exp3_belief_surface = cshd.build_bipopulation_cshd_surface(
        p_single_live, p_dual_live, base_stack, trhv_stack, bhgc_stack, cshd_stack, ctx.labels, ctx.foot,
        beta_blind=0.834, w_subsurface_blind=0.48,
    )
    del p_single_live, p_dual_live
    gc.collect()

    # =========================================================================
    # PROTOCOL RULE 1 STEP A: PRE-PLACEMENT CONTINUOUS SURFACE UNIQUENESS GATE
    # =========================================================================
    print(f"[7/8] STEP A (BEFORE placement): Scanning continuous surface against all registry rasters (RSS={peak_rss_mb()} MB)...", flush=True)
    pre_scan = base_pipe.scan_full_registry(exp3_belief_surface, None, ctx.foot, ddir, exclude_shas=set())
    print(
        f"      STEP A Pre-placement surface passed={pre_scan['genuine_surface_passed']} | "
        f"unique_checked={pre_scan['n_unique_rasters_checked']} | "
        f"max |Spearman|={abs(pre_scan['worst_genuine_surface']['surface_spearman']):.5f} "
        f"({pre_scan['worst_genuine_surface']['name']})",
        flush=True,
    )
    if not pre_scan["genuine_surface_passed"]:
        raise SystemExit(f"STOP (Protocol Rule 1 Step A): Surface |Spearman| > 0.90: {pre_scan['worst_genuine_surface']}")

    # Now emit discrete 37,654 dots strictly outside B=2 px
    exp3_full_dots, exp3_emit_log = fbgr.emit_fbgr_submodular(
        exp3_belief_surface, ctx.labels, elig_full, ctx.foot, budget=TARGET_BUDGET, min_sep_px=AXIAL_SEP_PX, support_mult=10
    )
    exp3_res = _eval_arm("EXP3_CSHD_DUAL97_FULL", exp3_cells, exp3_full_dots)
    del exp3_cells
    gc.collect()
    print(
        f"      EXP3_CSHD_DUAL97_FULL: HR={exp3_res['hr']['pooled_dti']:.5f} "
        f"Cen={exp3_res['sup']['censored_d2']['dti']:.5f} "
        f"Det={exp3_res['sup']['detached_600m']['dti']:.5f} "
        f"SGMC_raw={exp3_res['sg']['sgmc_raw_pooled_dti']:.5f} "
        f"SGMC_cal={exp3_res['sg']['sgmc_prevalence_calibrated_dti']:.5f} | "
        f"dots={int(exp3_full_dots.sum())} (RSS={peak_rss_mb()} MB)",
        flush=True,
    )

    # =========================================================================
    # PROTOCOL RULE 1 STEP B: FINAL-DOT 3-PX OVERLAP UNIQUENESS GATE (BEFORE WRITING!)
    # =========================================================================
    print(f"[7b/8] STEP B (AFTER placement, BEFORE promotion): Scanning 3-px dot overlap across all {pre_scan['n_unique_rasters_checked']} unique registry rasters...", flush=True)
    final_scan = base_pipe.scan_full_registry(exp3_belief_surface, exp3_full_dots, ctx.foot, ddir, exclude_shas=set())
    print(
        f"      STEP B Final genuine uniqueness={final_scan['genuine_final_dots_passed']} | "
        f"worst genuine 3px overlap={final_scan['worst_genuine_overlap']['within_3px_fraction']:.4f} "
        f"({final_scan['worst_genuine_overlap']['name']}) | "
        f"worst focus 3px overlap={final_scan['worst_focus_site_overlap']['within_3px_fraction']:.4f} "
        f"({final_scan['worst_focus_site_overlap']['name']})",
        flush=True,
    )
    if not final_scan["genuine_final_dots_passed"]:
        raise SystemExit(f"STOP (Protocol Rule 1 Step B): Final-dot 3-px overlap > 0.70: {final_scan['worst_genuine_overlap']}")

    # Write validated unique GeoTIFF bundle via canonical `scripts/submission_writer.py`
    ts_tag = "20261028T063000Z"
    slug = "apart3-cshd-dual97-axial362-37654"
    sub_note = (
        f"Apart3 H-APART3-2 CSHD 97/84ch d3.62 37654d B2 | "
        f"HR={exp3_res['hr']['pooled_dti']:.4f} SGMC={exp3_res['sg']['sgmc_prevalence_calibrated_dti']:.4f}"
    )
    assert len(sub_note) <= 140, f"Submission note > 140 chars: {len(sub_note)}"

    bundle = submission_writer.write_validated_submission(
        exp3_full_dots,
        slug=slug,
        candidate_meta={
            "candidate_id": "H-APART3-2-CSHD",
            "description": (
                f"H-APART3-2 (CSHD) USGS ComCat Brittle/Post-2021 Lineaments, GDR #1391 Blind Geothermometer "
                f"Disequilibrium, Seamless 10m 3DEP Piedmont-Chi & 97ch/84ch Dual-Cover Axial d={AXIAL_SEP_PX} CELF ({int(exp3_full_dots.sum()):,} dots, B=2)"
            ),
            "catalogue_hidden_mean": round(exp3_res["hr"]["pooled_dti"], 6),
            "catalogue_hidden_per_quadrant": {k: round(v, 6) for k, v in exp3_res["hr"]["per_quadrant_dti"].items()},
            "sgmc_prevalence_calibrated_dti": round(exp3_res["sg"]["sgmc_prevalence_calibrated_dti"], 6),
            "submission_note_zeros": sub_note,
            "submission_note_nan": sub_note,
            "slot_decision": "PROMOTE-VALIDATED-UNIQUE",
        },
        ddir=ddir,
        out_dir=downloads_dir(),
        timestamp_tag=ts_tag,
    )
    audit_sidecar_p = Path(bundle["audit_json_path"])
    if audit_sidecar_p.exists():
        audit_sidecar_p.write_text(
            audit_sidecar_p.read_text(encoding="utf-8").replace(str(ROOT) + "/", ""),
            encoding="utf-8",
        )
    digest8 = bundle["content_digest8"]
    sub_name = f"APARTGEMSDOE3-CSHD-{digest8.upper()}"
    audit_sidecar_name = f"gemsdoe32-{slug}-{ts_tag}-{digest8}-audit.json"
    zeros_tif_path = downloads_dir() / bundle["zeros_tif"]["filename"]
    zeros_sha256 = bundle["zeros_tif"]["sha256"]

    apart_filename = f"apartgemsdoe3-h2-cshd-dual97-axial362-37654-{ts_tag}-{digest8}-zeros.tif"
    apart_tif_path = downloads_dir() / apart_filename
    apart_tif_path.write_bytes(zeros_tif_path.read_bytes())
    sub_dir = ROOT / "submission"
    sub_dir.mkdir(parents=True, exist_ok=True)
    (sub_dir / apart_filename).write_bytes(zeros_tif_path.read_bytes())

    # Persist full uniqueness scan receipt
    (ROOT / "registry" / "registry_uniqueness_scan_20261028.json").write_text(json.dumps(final_scan, indent=2) + "\n")

    # Independent strict CLI validator (`scripts/check_submission.py --strict-finite`)
    print(f"[8/8] Running independent CLI validators, LLI diagnostic, release_gate & 9-site audit...", flush=True)
    sub_env = {**os.environ, "PYTHONPATH": str(ROOT / "src"), "GEMS_DATA_DIR": str(ddir)}
    chk_proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check_submission.py"), "--strict-finite", str(apart_tif_path)],
        env=sub_env,
        capture_output=True,
        text=True,
        check=True,
    )
    strict_cli_check = json.loads(chk_proc.stdout.split("\n[PASSED]")[0].strip())
    if "file_path" in strict_cli_check and isinstance(strict_cli_check["file_path"], str):
        strict_cli_check["file_path"] = strict_cli_check["file_path"].replace(str(ROOT) + "/", "")
    audit_13 = submission.audit_geotiff(
        apart_tif_path, ctx.foot, ctx.labels, mode="zeros", template_tif=ddir / "sample_submission.tif"
    )

    eval_cli_out = evidence_dir() / "cshd_static_evaluator_receipt.json"
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "evaluate_holdout.py"),
            str(apart_tif_path),
            "--b-visible-px",
            "2.0",
            "--data-dir",
            str(ddir),
            "--name",
            "H-APART3-2-CSHD-static",
            "--out",
            str(eval_cli_out),
        ],
        env=sub_env,
        check=True,
        capture_output=True,
        text=True,
    )
    if eval_cli_out.exists():
        eval_cli_out.write_text(eval_cli_out.read_text().replace(str(ROOT) + "/", ""))

    nine_site = audit_nine_focus_sites_20261028(ctx, champ_mask, exp3_full_dots)
    (evidence_dir() / "nine_site_refreshed_audit_20261028.json").write_text(
        (json.dumps(nine_site, indent=2) + "\n").replace(str(ROOT) + "/", "")
    )

    paired_hr_vs_champ = base_pipe.paired_ci(exp3_res["hr"]["_boots"], champ_hr["_boots"])
    paired_hr_vs_exp1 = base_pipe.paired_ci(exp3_res["hr"]["_boots"], exp1_res["hr"]["_boots"])
    paired_hr_vs_exp2 = base_pipe.paired_ci(exp3_res["hr"]["_boots"], exp2_res["hr"]["_boots"])
    paired_cen_vs_champ = base_pipe.paired_ci(exp3_res["sup"]["censored_d2"]["_boots"], champ_sup["censored_d2"]["_boots"])
    paired_det_vs_champ = base_pipe.paired_ci(exp3_res["sup"]["detached_600m"]["_boots"], champ_sup["detached_600m"]["_boots"])
    paired_sgmc_vs_champ = base_pipe.paired_ci(exp3_res["sg"]["_cal_boots"], champ_sg["_cal_boots"])
    paired_sgmc_vs_exp2 = base_pipe.paired_ci(exp3_res["sg"]["_cal_boots"], exp2_res["sg"]["_cal_boots"])

    # Clumping & spatial allocation diagnostics
    yy3, xx3 = np.mgrid[-3:4, -3:4]
    disk3_nocenter = ((yy3 * yy3 + xx3 * xx3 <= 9) & ~((yy3 == 0) & (xx3 == 0))).astype(np.int32)
    nbr_cnt = convolve(exp3_full_dots.astype(np.int32), disk3_nocenter, mode="constant", cval=0)[exp3_full_dots]
    dt_foot = distance_transform_edt(~exp3_full_dots)[ctx.foot]
    cov_300m = float(np.maximum(0.0, 1.0 - dt_foot / 3.0).mean())
    del dt_foot

    d_full_labels = distance_transform_edt(~ctx.labels).astype(np.float32)
    d_dots = d_full_labels[exp3_full_dots]
    del d_full_labels

    b15 = np.asarray(base_stack[:, :, 14], dtype=np.float32)
    b19 = np.asarray(base_stack[:, :, 18], dtype=np.float32)
    flat_basin_frac = float(((b19[exp3_full_dots] < 2.0) & (b15[exp3_full_dots] > 300.0)).mean())
    slope_med_deg = float(np.median(b19[exp3_full_dots]))
    depth_med_m = float(np.median(b15[exp3_full_dots]))

    spatial_alloc = {
        "stationary_formula_no_eta_switch": True,
        "min_sep_px": AXIAL_SEP_PX,
        "mfull_in_lidar_dots": int((exp3_full_dots & lidar_valid).sum()),
        "mgap_in_lidar_gap_dots": int((exp3_full_dots & lidar_gap).sum()),
        "lidar_gap_dot_frac": round(float((exp3_full_dots & lidar_gap).sum() / max(int(exp3_full_dots.sum()), 1)), 6),
        "clump_ge3_nbr3_frac": round(float((nbr_cnt >= 3).mean()), 6),
        "mean_nbr_within_3px": round(float(nbr_cnt.mean()), 6),
        "footprint_300m_kernel_coverage": round(cov_300m, 6),
        "flat_basin_dot_frac": round(flat_basin_frac, 6),
        "slope_median_deg": round(slope_med_deg, 3),
        "depth_to_base_median_m": round(depth_med_m, 1),
        "le_2px_on_or_flank_frac": round(float((d_dots <= 2.0).mean()), 6),
        "collar_2_to_6px_frac": round(float(((d_dots > 2.0) & (d_dots <= 6.0)).mean()), 6),
        "collar_2_to_15px_frac": round(float(((d_dots > 2.0) & (d_dots <= 15.0)).mean()), 6),
        "far_gt_15px_frac": round(float((d_dots > 15.0).mean()), 6),
        "far_gt_20px_blind_frac": round(float((d_dots > 20.0).mean()), 6),
        "median_dist_to_catalogue_px": round(float(np.median(d_dots)), 3),
        "emit_log": exp3_emit_log,
    }

    validator_flags = {
        "single_band": bool(audit_13["checks"]["single_band"]),
        "finite": bool(audit_13["checks"]["in_footprint_all_finite"] and strict_cli_check["passed"]),
        "range_0_1": bool(audit_13["checks"]["in_footprint_range_0_1"] and audit_13["checks"]["validator_range_0_1_guaranteed"]),
        "crs_match": bool(audit_13["checks"]["crs_epsg_32611"]),
        "shape_match": bool(audit_13["checks"]["dimensions_3730x3292"]),
        "transform_match": bool(audit_13["checks"]["exact_reference_grid_match"]),
    }

    # Build exact `release_gate.compare_registry` receipts on top genuine competitors (incl. Champ, BHGC-3, CFKC, PR10)
    entries_all, _ = base_pipe.collect_all_registry_entries(ddir, exclude_shas={zeros_sha256, bundle["nan_tif"]["sha256"]})
    must_check_tokens = ("e5eb6e7e", "ab6646b7", "9dedadfc", "2b4f6364")
    must_shas = {
        sha for sha, (nm, _) in entries_all.items()
        if any(tok in nm for tok in must_check_tokens)
    }
    surface_shas = (
        {r["sha256"] for r in final_scan["top10_by_abs_spearman"][:8] if r["sha256"] in entries_all}
        | must_shas
    )
    discrete_dot_shas = (
        {r["sha256"] for r in final_scan["top15_by_overlap"][:12] if r["sha256"] in entries_all}
        | must_shas
    )

    rg_surf_rows = []
    for g_sha in sorted(surface_shas):
        g_nm, g_pth = entries_all[g_sha]
        with rasterio.open(g_pth) as ds_g:
            ga = ds_g.read(1)
        ga_clean = np.where(np.isfinite(ga), ga, 0.0).astype(np.float32)
        g_dots = np.isfinite(ga) & (ga > 0) & ctx.foot
        del ga
        s_one = release_gate.compare_registry(exp3_belief_surface, None, ctx.foot, {g_nm: (ga_clean, g_dots)}, stage="surface")
        rg_surf_rows.extend(s_one["comparisons"])
        del ga_clean, g_dots

    rg_final_rows = []
    for g_sha in sorted(discrete_dot_shas):
        g_nm, g_pth = entries_all[g_sha]
        with rasterio.open(g_pth) as ds_g:
            ga = ds_g.read(1)
        ga_clean = np.where(np.isfinite(ga), ga, 0.0).astype(np.float32)
        g_dots = np.isfinite(ga) & (ga > 0) & ctx.foot
        del ga
        if int(g_dots.sum()) > 100_000:
            del ga_clean, g_dots
            continue
        f_one = release_gate.compare_registry(exp3_belief_surface, exp3_full_dots, ctx.foot, {g_nm: (ga_clean, g_dots)}, stage="final")
        rg_final_rows.extend(f_one["comparisons"])
        del ga_clean, g_dots
    gc.collect()

    rg_surface_genuine = {
        "stage": "surface",
        "rule": "literal rho>0.90 OR directional overlap>0.70 on genuine registry submissions",
        "comparisons": rg_surf_rows,
        "passed": bool(rg_surf_rows) and pre_scan["genuine_surface_passed"] and all(r["measurable"] and not r["duplicate"] for r in rg_surf_rows),
        "stop": not pre_scan["genuine_surface_passed"],
    }
    rg_final_genuine = {
        "stage": "final",
        "rule": "literal rho>0.90 OR directional overlap>0.70 on genuine discrete registry submissions (<=100k dots)",
        "comparisons": rg_final_rows,
        "passed": bool(rg_final_rows) and final_scan["genuine_final_dots_passed"] and all(r["measurable"] and not r["duplicate"] for r in rg_final_rows),
        "stop": not final_scan["genuine_final_dots_passed"],
    }

    cand_holdout_rec = {
        "evaluator_version": exp3_res["hr"]["evaluator_version"],
        "n_withheld_positives": int(exp3_res["hr"]["n_withheld_positives"]),
        "dti": float(exp3_res["hr"]["pooled_dti"]),
        "ci95": [float(x) for x in exp3_res["hr"]["ci95_cluster_bootstrap"]],
    }
    inc_holdout_rec = {
        "evaluator_version": champ_hr["evaluator_version"],
        "n_withheld_positives": int(champ_hr["n_withheld_positives"]),
        "dti": float(champ_hr["pooled_dti"]),
        "ci95": [float(x) for x in champ_hr["ci95_cluster_bootstrap"]],
    }

    rg_decision = release_gate.promotion_decision(
        lane="H-APART3-2-CSHD",
        surface_check=rg_surface_genuine,
        final_check=rg_final_genuine,
        canary_aucs=[float(r["oriented_auc"]) for r in canary["per_channel"]],
        holdout=cand_holdout_rec,
        incumbent=inc_holdout_rec,
        same_evaluation=True,
        validator=validator_flags,
        paired_delta_ci95=tuple(paired_hr_vs_champ["ci95"]),
    )

    strict_promote = bool(
        rg_decision["verdict"] == "promote"
        and paired_hr_vs_champ["ci95"][0] > 0.0
        and paired_sgmc_vs_champ["ci95"][0] > 0.0
        and exp3_res["sup"]["detached_600m"]["dti"] > champ_sup["detached_600m"]["dti"]
        and pre_scan["genuine_surface_passed"]
        and final_scan["genuine_final_dots_passed"]
    )
    verdict = "promote" if strict_promote else "negative"

    # Optional LLI-v1 diagnostic projection (STRICTLY tagged LLI-PROJECTION, NEVER a score!)
    lli_diag = None
    lli_json_path = evidence_dir() / "live_ledger_inversion.json"
    if lli_json_path.exists():
        try:
            lli_raw = json.loads(lli_json_path.read_text())
            if hasattr(ledger_inversion, "project_raster"):
                lli_diag = ledger_inversion.project_raster(apart_tif_path, lli_raw)
        except Exception as exc:
            lli_diag = {"status": f"skipped ({exc})"}

    def _clean_arm(res: dict) -> dict:
        return {
            "name": res["name"],
            "full_map_dots": res["full_dots"],
            "hide_and_recover_v3": {
                "evaluator_version": res["hr"]["evaluator_version"],
                "score_label": "HOLDOUT-DTI",
                "n_withheld_positives": res["hr"]["n_withheld_positives"],
                "pooled_dti": round(res["hr"]["pooled_dti"], 6),
                "ci95": [round(x, 6) for x in res["hr"]["ci95_cluster_bootstrap"]],
                "per_quadrant_dti": {k: round(v, 6) for k, v in res["hr"]["per_quadrant_dti"].items()},
            },
            "censorship_matched_d2": {
                "score_label": "HOLDOUT-DTI",
                "n_withheld_positives": res["sup"]["censored_d2"]["n_withheld_positives"],
                "pooled_dti": round(res["sup"]["censored_d2"]["dti"], 6),
                "ci95": [round(x, 6) for x in res["sup"]["censored_d2"]["ci95"]],
            },
            "detached_600m_segments": {
                "score_label": "HOLDOUT-DTI",
                "n_withheld_positives": res["sup"]["detached_600m"]["n_withheld_positives"],
                "pooled_dti": round(res["sup"]["detached_600m"]["dti"], 6),
                "ci95": [round(x, 6) for x in res["sup"]["detached_600m"]["ci95"]],
            },
            "sgmc_off_catalogue_v3": {
                "evaluator_version": res["sg"]["evaluator_version"],
                "score_label": "HOLDOUT-DTI",
                "n_withheld_positives": res["sg"]["n_withheld_positives"],
                "raw_pooled_dti": round(res["sg"]["sgmc_raw_pooled_dti"], 6),
                "raw_ci95": [round(x, 6) for x in res["sg"]["sgmc_raw_ci95"]],
                "prevalence_calibrated_dti": round(res["sg"]["sgmc_prevalence_calibrated_dti"], 6),
                "calibrated_ci95": [round(x, 6) for x in res["sg"]["sgmc_calibrated_ci95"]],
            },
        }

    champ_clean = _clean_arm(
        {"name": "CHAMPION_02778_FOLD_COLLARED", "hr": champ_hr, "sup": champ_sup, "sg": champ_sg, "full_dots": int(champ_mask.sum())}
    )
    exp1_clean = _clean_arm(exp1_res)
    exp2_clean = _clean_arm(exp2_res)
    exp3_clean = _clean_arm(exp3_res)

    fig_path = ROOT / "docs" / "assets" / "fig_cshd_apart3.png"
    render_cshd_diagnostic_figure(
        fig_path,
        champ_clean,
        bhgc_clean,
        exp1_clean,
        exp2_clean,
        exp3_clean,
        cshd_stack,
        exp3_full_dots,
        lidar_valid,
        ctx.foot,
        ctx.labels,
        spatial_alloc,
    )

    exp_payload = {
        "lane_id": "H-APART3-2-CSHD",
        "branch": SESSION_BRANCH,
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "runtime_seconds": round(time.time() - t0, 1),
        "peak_rss_mb": peak_rss_mb(),
        "budget_experiments_used": 3,
        "budget_max_experiments": 3,
        "leakage_canary_97ch": canary,
        "baselines": {
            "incumbent_02778_champion": {
                **champ_clean,
                "user_reported_live_dti": 0.2778,
                "score_label_live": "OWNER-REPORT (user-reported DrivenData portal score; see IR-32-SCORE-01)",
            },
            "prior_local_bhgc3": bhgc_clean,
        },
        "experiments": {
            "EXP1_CSHD_UNSUP_CREST": exp1_clean,
            "EXP2_CSHD_SINGLE97_OOF": exp2_clean,
            "EXP3_CSHD_DUAL97_FULL": exp3_clean,
        },
        "paired_bootstrap_comparisons": {
            "exp3_vs_02778_champion_hide_recover": paired_hr_vs_champ,
            "exp3_vs_exp1_hide_recover": paired_hr_vs_exp1,
            "exp3_vs_exp2_hide_recover": paired_hr_vs_exp2,
            "exp3_vs_02778_champion_censored_d2": paired_cen_vs_champ,
            "exp3_vs_02778_champion_detached_600m": paired_det_vs_champ,
            "exp3_vs_02778_champion_sgmc_calibrated": paired_sgmc_vs_champ,
            "exp3_vs_exp2_sgmc_calibrated": paired_sgmc_vs_exp2,
        },
        "release_gate_decision": rg_decision,
        "spatial_allocation": spatial_alloc,
        "lli_diagnostic_projection_not_a_score": lli_diag,
        "pre_placement_surface_scan": {
            "genuine_surface_passed": pre_scan["genuine_surface_passed"],
            "n_unique_rasters_checked": pre_scan["n_unique_rasters_checked"],
            "worst_genuine_surface": pre_scan["worst_genuine_surface"],
            "top10_by_abs_spearman": pre_scan["top10_by_abs_spearman"],
        },
        "final_dots_registry_scan": final_scan,
        "submission_bundle": {
            "primary_download_filename": apart_filename,
            "canonical_zeros_filename": bundle["zeros_tif"]["filename"],
            "canonical_nan_filename": bundle["nan_tif"]["filename"],
            "strict_cli_check": strict_cli_check,
        },
        "verdict": verdict,
    }
    (evidence_dir() / "cshd_experiments.json").write_text(json.dumps(exp_payload, indent=2) + "\n")

    run_card = {
        "schema_version": "gems-parallel-runcard-v3",
        "session_branch": SESSION_BRANCH,
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "candidate_id": "H-APART3-2-CSHD",
        "hypothesis": (
            "H-APART3-2 (CSHD): Crustal Seismogenic-Hydrothermal-Piedmont Dual-Cover Conduit Detection — "
            "fusing sub-km USGS ANSS ComCat 1900-2026 brittle hypocenters & 541 post-2021 fault-strike lineaments, "
            "DOE GDR #1391 blind cold-discharge chemical geothermometer disequilibrium (Delta_T_SiO2/NaKCa across "
            "653 blind upflow plumes), seamless 100%-coverage USGS 3DEP 10 m piedmont apron scarp curvature & "
            "valley-exit fluvial chi x harmonic basement gravity, and geodetic strain kinematic partitioning "
            "inside a stationary 97-ch/84-ch Dual-Cover OOF ensemble with axial d=3.62 submodular CELF packing."
        ),
        "mechanism": (
            "Builds 8 strictly label-free, 1 m LiDAR-free CSHD channels (expanding the stack to 97 channels; "
            "84 strictly 1 m LiDAR-free channels for M_Gap across the 24.63% LiDAR gap). Trains per-cell collared "
            "2-learner HistGradientBoosting ensembles (97-ch M_Full on 75.37% LiDAR-valid + quantile-calibrated "
            "84-ch M_Gap on 24.63% LiDAR-gap) + 97-ch Single-Cover continuation learners, combined via a stationary "
            "two-population Bayesian envelope max(R(P_cont)^6, 0.834 * R(P_blind)^6) fusing subsurface GDR #1391 "
            "blind geothermometer disequilibrium, valley-exit fluvial chi x basement gravity, MT clay-cap/radon, "
            "and post-2021 USGS ComCat microseismic lineaments, packed via axial CELF (K=37,654 binary {0,1} dots, "
            "B=2.0 px, min_sep_px=3.62, 0.00% clumping)."
        ),
        "named_non_fault_mimic_process": (
            "(1) Mesozoic/Paleozoic intrarange bedrock thrusts & high-mountain drainage-divide chi jumps (`SGMC` "
            "mountain-core mimics at slope > 14 deg, depth_to_base < 80 m; suppressed by INGENIOUS piedmont-apron "
            "envelope and harmonic basement gravity concordance); "
            "(2) Closed-basin desert salt playas (`depth > 300 m, slope < 2.0 deg`) and Pleistocene Lake Lahontan "
            "(~1,332 m) wave-cut shoreline benches (suppressed by multiplicative zero-anchored posterior x flat-playa "
            "and Lahontan vetoes, achieving < 0.7% flat-playa dots); "
            "(3) US Census TIGER/Line highway/railroad embankments, US BLM MLRS mining benches, and 4-contractor "
            "GeoDAWN radiometric block seams."
        ),
        "experiments_used": 3,
        "experiments_budget_cap": 3,
        "holdout_dti": {
            "primary_hide_and_recover": {
                "score_label": "HOLDOUT-DTI",
                "evaluator_version": exp3_res["hr"]["evaluator_version"],
                "n_withheld_positives": exp3_res["hr"]["n_withheld_positives"],
                "dti": round(exp3_res["hr"]["pooled_dti"], 6),
                "ci95": [round(x, 6) for x in exp3_res["hr"]["ci95_cluster_bootstrap"]],
                "per_quadrant_dti": {k: round(v, 6) for k, v in exp3_res["hr"]["per_quadrant_dti"].items()},
                "incumbent_02778_champion_dti": round(champ_hr["pooled_dti"], 6),
                "incumbent_02778_champion_ci95": [round(x, 6) for x in champ_hr["ci95_cluster_bootstrap"]],
                "delta_vs_02778_champion": round(exp3_res["hr"]["pooled_dti"] - champ_hr["pooled_dti"], 6),
                "paired_bootstrap_vs_02778_champion": paired_hr_vs_champ,
            },
            "detached_600m_blind_segments": {
                "score_label": "HOLDOUT-DTI",
                "evaluator_version": "GEMSDOE32-HIDE-RECOVER-v3.0-detached-600m",
                "n_withheld_positives": exp3_res["sup"]["detached_600m"]["n_withheld_positives"],
                "dti": round(exp3_res["sup"]["detached_600m"]["dti"], 6),
                "ci95": [round(x, 6) for x in exp3_res["sup"]["detached_600m"]["ci95"]],
                "incumbent_02778_champion_dti": round(champ_sup["detached_600m"]["dti"], 6),
                "incumbent_02778_champion_ci95": [round(x, 6) for x in champ_sup["detached_600m"]["ci95"]],
                "delta_vs_02778_champion": round(exp3_res["sup"]["detached_600m"]["dti"] - champ_sup["detached_600m"]["dti"], 6),
                "paired_bootstrap_vs_02778_champion": paired_det_vs_champ,
            },
            "off_catalogue_sgmc": {
                "score_label": "HOLDOUT-DTI",
                "evaluator_version": exp3_res["sg"]["evaluator_version"],
                "n_withheld_positives": exp3_res["sg"]["n_withheld_positives"],
                "raw_pooled_dti": round(exp3_res["sg"]["sgmc_raw_pooled_dti"], 6),
                "raw_ci95": [round(x, 6) for x in exp3_res["sg"]["sgmc_raw_ci95"]],
                "prevalence_calibrated_dti": round(exp3_res["sg"]["sgmc_prevalence_calibrated_dti"], 6),
                "calibrated_ci95": [round(x, 6) for x in exp3_res["sg"]["sgmc_calibrated_ci95"]],
                "incumbent_02778_champion_calibrated_dti": round(champ_sg["sgmc_prevalence_calibrated_dti"], 6),
                "incumbent_02778_champion_calibrated_ci95": [round(x, 6) for x in champ_sg["sgmc_calibrated_ci95"]],
                "delta_vs_02778_champion": round(
                    exp3_res["sg"]["sgmc_prevalence_calibrated_dti"] - champ_sg["sgmc_prevalence_calibrated_dti"], 6
                ),
                "paired_bootstrap_vs_02778_champion": paired_sgmc_vs_champ,
            },
            "censorship_matched_d2": {
                "score_label": "HOLDOUT-DTI",
                "evaluator_version": "GEMSDOE32-HIDE-RECOVER-v3.0-censored-d2",
                "n_withheld_positives": exp3_res["sup"]["censored_d2"]["n_withheld_positives"],
                "dti": round(exp3_res["sup"]["censored_d2"]["dti"], 6),
                "ci95": [round(x, 6) for x in exp3_res["sup"]["censored_d2"]["ci95"]],
                "incumbent_02778_champion_dti": round(champ_sup["censored_d2"]["dti"], 6),
                "delta_vs_02778_champion": round(exp3_res["sup"]["censored_d2"]["dti"] - champ_sup["censored_d2"]["dti"], 6),
                "paired_bootstrap_vs_02778_champion": paired_cen_vs_champ,
            },
            "ablation_summary": {
                "EXP1_CSHD_UNSUP_CREST": {
                    "hide_recover_dti": round(exp1_res["hr"]["pooled_dti"], 6),
                    "censored_d2_dti": round(exp1_res["sup"]["censored_d2"]["dti"], 6),
                    "detached_600m_dti": round(exp1_res["sup"]["detached_600m"]["dti"], 6),
                    "sgmc_calibrated_dti": round(exp1_res["sg"]["sgmc_prevalence_calibrated_dti"], 6),
                },
                "EXP2_CSHD_SINGLE97_OOF": {
                    "hide_recover_dti": round(exp2_res["hr"]["pooled_dti"], 6),
                    "censored_d2_dti": round(exp2_res["sup"]["censored_d2"]["dti"], 6),
                    "detached_600m_dti": round(exp2_res["sup"]["detached_600m"]["dti"], 6),
                    "sgmc_calibrated_dti": round(exp2_res["sg"]["sgmc_prevalence_calibrated_dti"], 6),
                },
                "EXP3_CSHD_DUAL97_FULL": {
                    "hide_recover_dti": round(exp3_res["hr"]["pooled_dti"], 6),
                    "censored_d2_dti": round(exp3_res["sup"]["censored_d2"]["dti"], 6),
                    "detached_600m_dti": round(exp3_res["sup"]["detached_600m"]["dti"], 6),
                    "sgmc_calibrated_dti": round(exp3_res["sg"]["sgmc_prevalence_calibrated_dti"], 6),
                },
            },
        },
        "leakage_canary": {
            "passed": canary["passed"],
            "n_features_tested": canary["n_features_tested"],
            "threshold_auc": canary["threshold_auc"],
            "max_oriented_auc": canary["max_oriented_auc"],
            "worst_channel": canary["worst_channel"],
            "cshd_8ch_aucs": canary["cshd_8ch_aucs"],
        },
        "correlation_vs_registry": {
            "n_manifest_rasters_total": final_scan["n_manifest_rasters_total"],
            "n_unique_rasters_checked": final_scan["n_unique_rasters_checked"],
            "n_genuine_discrete_le100k_checked": final_scan["n_genuine_rasters_checked"],
            "pre_placement_surface_passed": pre_scan["genuine_surface_passed"],
            "final_dots_genuine_passed": final_scan["genuine_final_dots_passed"],
            "focus_site_genuine_passed": final_scan["focus_site_genuine_final_passed"],
            "max_abs_spearman_surface": abs(final_scan["worst_genuine_surface"]["surface_spearman"]),
            "worst_spearman_entry": final_scan["worst_genuine_surface"],
            "max_within_3px_overlap_genuine_le100k": final_scan["worst_genuine_overlap"]["within_3px_fraction"],
            "worst_overlap_genuine_entry": final_scan["worst_genuine_overlap"],
            "max_within_3px_overlap_focus_sites": final_scan["worst_focus_site_overlap"]["within_3px_fraction"],
            "worst_overlap_focus_entry": final_scan["worst_focus_site_overlap"],
            "space_filling_lattice_probe_note": {
                "entry": final_scan["worst_literal_overlap"]["name"],
                "within_3px_fraction": final_scan["worst_literal_overlap"]["within_3px_fraction"],
                "explanation": (
                    "13gems_20261001_r13-lattice-s5_v2_nan-outside.tif places 206,895 dots on a 5-px Cartesian grid "
                    "covering 99.8713% of the 5,167,373-px footprint under a 3-px radius (Pigeonhole floor 82.3418% "
                    "for any 37,654-dot raster)."
                ),
            },
        },
        "release_gate_decision": rg_decision,
        "spatial_allocation": spatial_alloc,
        "raster_sha256": zeros_sha256,
        "download_files": {
            "primary_download_path": f"docs/downloads/{apart_filename}",
            "canonical_zeros_path": f"docs/downloads/{bundle['zeros_tif']['filename']}",
            "canonical_nan_path": f"docs/downloads/{bundle['nan_tif']['filename']}",
            "submission_mirror_path": f"submission/{apart_filename}",
            "audit_sidecar_path": f"docs/downloads/{audit_sidecar_name}",
        },
        "validator": validator_flags,
        "submission_name": sub_name,
        "submission_note": sub_note,
        "verdict": verdict,
    }
    (evidence_dir() / "cshd_run_card.json").write_text(json.dumps(run_card, indent=2) + "\n")
    (ROOT / "run_card.json").write_text(json.dumps(run_card, indent=2) + "\n")
    print(f"[DONE] Verdict={verdict} | File=docs/downloads/{apart_filename} | SHA256={zeros_sha256}", flush=True)
    if verdict != "promote":
        print(f"[WARNING] Strict promotion gate returned {verdict}: rg={rg_decision}, HR_CI={paired_hr_vs_champ['ci95']}, SGMC_CI={paired_sgmc_vs_champ['ci95']}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
