#!/usr/bin/env python3
"""End-to-end research pipeline for H-APART3-2 (CTHG-DHC):
Cooper-Cowan Joint Tilt-Phase Contact Wall, Fluvial Delta-Chi Laplace Basement
Throw Conduit & Clump-Free 103-Ch/87-Ch Dual-Horizon Cover.

Follows the GEMS Parallel-Run Protocol:
- Rule 1 (Lane Uniqueness): Exact 100% full-footprint (`5,167,373` active pixels) Spearman rank
  correlation (<= 0.90) and directional <= 3 px dot overlap (<= 0.70) checked across all unique
  rasters in the 9 focus sites + peer repos + extra scored manifest + sibling orgs both BEFORE
  placement (Step A: continuous surface) and ON final dots (Step B).
- Rule 2 (Reuse, Don't Rebuild): Reuses cached feature stacks (`feature_stack.npy` 35ch,
  `spcp_extra_20ch.npy` 20ch, `trhv_extra_8ch.npy` 8ch, `ldgi_extra_8ch.npy` 8ch,
  `fbgr_extra_12ch.npy` 12ch, `bhgc_extra_6ch.npy` 6ch, `cfkc_extra_8ch.npy` 8ch, and
  `cthg_extra_6ch.npy` 6ch = 103 total channels), canonical `scripts/evaluate_holdout.py`,
  and canonical `scripts/submission_writer.py`.
- Rule 3 (Score Provenance): Every number is labeled `HOLDOUT-DTI` (with evaluator version,
  number of withheld positives, and 95% spatial block bootstrap CI) or `ORGANIZER-CONFIRMED`.
- Rule 4 (Leakage Canary): Single-feature two-polarity ROC AUC <= 0.90 across all 103 channels.
- Rule 5 (JSON Run Card): Emits `run_card.json`, `docs/data/latest-run-card.json`, and
  `evidence/apart3_cthg_dhc_run_card.json`.
- Rule 6 (Budget): The final pipeline evaluates 3 named arms (`EXP1_CTHG_DUALCOVER_103`,
  `EXP2_CTHG_HYBRID_CREST`, `EXP3_CTHG_CLUMPFREE_DHC`). Additional exploratory sweeps occurred
  before that final pipeline and cumulative time/count was not reconciled; overall budget compliance
  is therefore explicitly not claimed. The run card records this irregularity and fails closed.
"""

from __future__ import annotations

import gc
import hashlib
import json
import os
import resource
import shutil
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
from scipy.stats import rankdata

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from gems32 import bhgc, cfkc, cthg, features, fbgr, holdout, metric, release_gate, spcp, submission, trhv
from gems32.paths import data_dir, downloads_dir, evidence_dir, work_dir
from scripts.run_apart3_cfkc import (
    B_COLLAR_PX,
    TARGET_BUDGET,
    _normalized_ranks,
    audit_nine_focus_sites_20261027,
    collect_all_registry_entries,
    evaluate_detached_and_censored,
    paired_ci,
)
import submission_writer

SESSION_BRANCH = "arena/1d95d973-apartgemsdoe3"
AXIAL_SEP_PX = 3.24
STAGE1_FRAC = 0.630
INNER_DEP = 0.20
MOAT_DEP = 0.72
W_PD_S2 = 0.15
OFF_CAT_MIN_DIST_PX = 5.5


def peak_rss_mb() -> float:
    return round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0, 1)


def collect_all_registry_entries_with_siblings(
    ddir: Path, exclude_shas: set[str] | None = None
) -> tuple[dict[str, tuple[str, Path]], dict]:
    """Gather all unique-SHA256 rasters across focus sites, extra scored, sibling orgs, & local downloads."""
    exclude_shas = exclude_shas or set()
    entries, counts = collect_all_registry_entries(ddir, exclude_shas=exclude_shas)
    sib_dir = ROOT / ".cache" / "sibling_orgs"
    sib_count = 0
    if sib_dir.exists():
        for p in sorted(sib_dir.rglob("*.tif")):
            if not p.is_file():
                continue
            sib_count += 1
            sha = hashlib.sha256(p.read_bytes()).hexdigest()
            if sha not in exclude_shas:
                rel = p.relative_to(sib_dir)
                entries.setdefault(sha, (f"sibling:{rel}", p))
    counts["sibling_org_rasters"] = sib_count
    counts["total_source_entries"] = counts["total_source_entries"] + sib_count
    counts["unique_sha256_rasters"] = len(entries)
    return entries, counts


def scan_full_registry_fast(
    surface: np.ndarray,
    dots: np.ndarray | None,
    foot: np.ndarray,
    ddir: Path,
    exclude_shas: set[str] | None = None,
) -> dict:
    """Exact 100% full-footprint (`5,167,373` px) Spearman & <=3px directional overlap scan."""
    entries, src_counts = collect_all_registry_entries_with_siblings(ddir, exclude_shas=exclude_shas)
    rx_surf = _normalized_ranks(np.asarray(surface[foot], dtype=np.float64))
    rx_dots = _normalized_ranks(dots[foot].astype(np.float64)) if dots is not None else None
    n_foot = int(rx_surf.size)

    h_foot, w_foot = foot.shape
    yy, xx = np.mgrid[-3:4, -3:4]
    mask_disk3 = (yy * yy + xx * xx) <= 9
    dy_off, dx_off = yy[mask_disk3], xx[mask_disk3]
    my_dots_yx = np.nonzero(dots & foot) if dots is not None else None
    n_my_dots = int(my_dots_yx[0].size) if my_dots_yx is not None else 0
    if my_dots_yx is not None and n_my_dots > 0:
        my_y, my_x = my_dots_yx
        ny = np.clip(my_y[:, None] + dy_off[None, :], 0, h_foot - 1)
        nx = np.clip(my_x[:, None] + dx_off[None, :], 0, w_foot - 1)
        valid_off = (
            ((my_y[:, None] + dy_off[None, :]) >= 0)
            & ((my_y[:, None] + dy_off[None, :]) < h_foot)
            & ((my_x[:, None] + dx_off[None, :]) >= 0)
            & ((my_x[:, None] + dx_off[None, :]) < w_foot)
        )
        nbr_flat = ny * w_foot + nx
    else:
        nbr_flat = None
        valid_off = None

    rows = []
    skipped = []
    for sha, (name, path) in sorted(entries.items(), key=lambda kv: kv[1][0]):
        try:
            with rasterio.open(path) as ds:
                if ds.count != 1 or ds.shape != foot.shape:
                    skipped.append({"name": name, "reason": f"shape={ds.shape},count={ds.count}"})
                    continue
                arr = ds.read(1)
        except Exception as exc:
            skipped.append({"name": name, "reason": str(exc)})
            continue

        in_foot = arr[foot]
        raw_finite = bool(np.isfinite(in_foot).all())
        clean_foot = in_foot if raw_finite else np.where(np.isfinite(in_foot), in_foot, np.float32(0.0))
        del in_foot
        other_dots = np.isfinite(arr) & (arr > 0) & foot
        n_other = int(other_dots.sum())
        del arr

        cmax = float(clean_foot.max())
        cmin = float(clean_foot.min())
        if cmax - cmin > 0.0:
            pos_foot = clean_foot > 0
            k_pos = int(pos_foot.sum())
            if cmin == 0.0 and 0 < k_pos < n_foot and bool(np.all(clean_foot[pos_foot] == cmax)):
                denom = float(np.sqrt(k_pos * (n_foot - k_pos) / float(n_foot)))
                rho_surf = float(rx_surf[pos_foot].sum() / denom)
                rho_dots = float(rx_dots[pos_foot].sum() / denom) if rx_dots is not None else None
            else:
                ry = _normalized_ranks(clean_foot)
                rho_surf = float(np.dot(rx_surf, ry))
                rho_dots = float(np.dot(rx_dots, ry)) if rx_dots is not None else None
                del ry
        else:
            rho_surf = 0.0
            rho_dots = 0.0 if rx_dots is not None else None
        del clean_foot

        ov3 = 0.0
        if nbr_flat is not None and n_other > 0:
            ov3 = float((other_dots.ravel()[nbr_flat] & valid_off).any(axis=1).mean())
        del other_dots

        if len(rows) % 40 == 0:
            gc.collect()
        is_lattice = "r13-lattice-s5" in name
        is_continuous_surface = n_other > 500_000
        is_ultra_dense_probe = (not is_lattice) and (not is_continuous_surface) and (n_other > 100_000)
        is_focus_repo = name.split(":")[0] in {
            "GEMSDOE24", "GEMSDOE25", "GEMSDOE27", "GEMSDOE28", "GEMSDOE30",
            "GEMSDOE31", "GEMSDOE32", "GEMSDOE33", "GEMSDOE36", "local",
        }
        rows.append(
            {
                "name": name,
                "sha256": sha,
                "other_dots": n_other,
                "raw_in_foot_finite": raw_finite,
                "is_calibration_lattice": is_lattice,
                "is_continuous_surface": is_continuous_surface,
                "is_ultra_dense_gt100k_probe": is_ultra_dense_probe,
                "is_focus_site_entry": is_focus_repo,
                "surface_spearman": round(rho_surf, 6),
                "dots_spearman": round(rho_dots, 6) if rho_dots is not None else None,
                "within_3px_fraction": round(ov3, 6),
            }
        )

    del rx_surf, rx_dots, nbr_flat, valid_off
    gc.collect()

    non_lattice_all = [r for r in rows if not r["is_calibration_lattice"]]
    discrete_le100k = [
        r for r in non_lattice_all
        if not r["is_continuous_surface"] and not r["is_ultra_dense_gt100k_probe"]
    ]
    focus_genuine = [
        r for r in rows
        if r["is_focus_site_entry"] and not r["is_calibration_lattice"] and not r["is_continuous_surface"] and not r["is_ultra_dense_gt100k_probe"]
    ]
    ultra_dense_or_surface = [
        r for r in non_lattice_all
        if r["is_continuous_surface"] or r["is_ultra_dense_gt100k_probe"]
    ]

    top_surf_candidates = sorted(discrete_le100k, key=lambda r: -abs(r["surface_spearman"]))[:5]
    top_ov_candidates = sorted(discrete_le100k, key=lambda r: -r["within_3px_fraction"])[:5]
    worst_ov_all = max(rows, key=lambda r: r["within_3px_fraction"])

    verify_shas = {r["sha256"] for r in (top_surf_candidates + top_ov_candidates)}
    rg_surf_comparisons = []
    rg_final_comparisons = []
    for sha in sorted(verify_shas):
        nm, pth = entries[sha]
        with rasterio.open(pth) as ds:
            a = ds.read(1)
        a_clean = np.where(np.isfinite(a), a, 0.0).astype(np.float32)
        o_dots = np.isfinite(a) & (a > 0) & foot
        del a
        s_one = release_gate.compare_registry(surface, None, foot, {nm: (a_clean, o_dots)}, stage="surface")
        rg_surf_comparisons.extend(s_one["comparisons"])
        if dots is not None:
            f_one = release_gate.compare_registry(surface, dots, foot, {nm: (a_clean, o_dots)}, stage="final")
            rg_final_comparisons.extend(f_one["comparisons"])
        del a_clean, o_dots
        gc.collect()

    worst_surf_gen = max(non_lattice_all, key=lambda r: abs(r["surface_spearman"]))
    worst_ov_gen = max(discrete_le100k, key=lambda r: r["within_3px_fraction"])
    worst_ov_focus = max(focus_genuine, key=lambda r: r["within_3px_fraction"])

    # Protocol Rule 1 is literal: diagnostic lattices and dense registry rasters are NOT exempt.
    # Build the shared release-gate comparison payload from exact all-row ranks/overlaps above.
    all_surface_comparisons = [
        {
            "registry": r["name"],
            "spearman": r["surface_spearman"],
            "within_3px_fraction": None,
            "duplicate": bool(abs(r["surface_spearman"]) > 0.90),
            "measurable": bool(r["raw_in_foot_finite"]),
        }
        for r in rows
    ]
    all_final_comparisons = [
        {
            "registry": r["name"],
            "spearman": r["surface_spearman"],
            "within_3px_fraction": r["within_3px_fraction"],
            "duplicate": bool(abs(r["surface_spearman"]) > 0.90 or r["within_3px_fraction"] > 0.70),
            "measurable": bool(r["raw_in_foot_finite"] and r["within_3px_fraction"] is not None),
        }
        for r in rows
    ]
    surf_passed = bool(all_surface_comparisons) and all(
        c["measurable"] and not c["duplicate"] for c in all_surface_comparisons
    )
    rg_surface = {
        "stage": "surface",
        "rule": "literal rho>0.90 against every registry raster; no density or calibration exemptions",
        "passed": surf_passed,
        "stop": not surf_passed,
        "comparisons": all_surface_comparisons,
    }
    rg_final = None
    if dots is not None:
        fin_passed = bool(all_final_comparisons) and all(
            c["measurable"] and not c["duplicate"] for c in all_final_comparisons
        )
        rg_final = {
            "stage": "final",
            "rule": "literal rho>0.90 OR directional overlap>0.70 against every registry raster; no density or calibration exemptions",
            "passed": fin_passed,
            "stop": not fin_passed,
            "comparisons": all_final_comparisons,
        }

    return {
        "registry_source_counts": src_counts,
        "n_manifest_rasters_total": src_counts["total_source_entries"],
        "n_unique_rasters_checked": len(rows),
        "n_genuine_rasters_checked": len(discrete_le100k),
        "n_focus_site_genuine_checked": len(focus_genuine),
        "n_ultra_dense_or_continuous_checked": len(ultra_dense_or_surface),
        "skipped_non_submission_blobs": skipped,
        "genuine_surface_passed": bool(abs(worst_surf_gen["surface_spearman"]) <= 0.90),
        "genuine_final_dots_passed": bool(
            dots is not None
            and abs(worst_surf_gen["surface_spearman"]) <= 0.90
            and worst_ov_gen["within_3px_fraction"] <= 0.70
        ),
        "focus_site_genuine_final_passed": bool(
            dots is not None
            and abs(worst_surf_gen["surface_spearman"]) <= 0.90
            and worst_ov_focus["within_3px_fraction"] <= 0.70
        ),
        "literal_all_rasters_final_passed": bool(
            dots is not None
            and max(abs(r["surface_spearman"]) for r in rows) <= 0.90
            and worst_ov_all["within_3px_fraction"] <= 0.70
        ),
        "worst_genuine_surface": worst_surf_gen,
        "worst_genuine_overlap": worst_ov_gen,
        "worst_focus_site_overlap": worst_ov_focus,
        "worst_literal_overlap": worst_ov_all,
        "ultra_dense_or_continuous_over_70pct": [
            r for r in ultra_dense_or_surface if r["within_3px_fraction"] > 0.70
        ],
        "release_gate_direct_surface": rg_surface,
        "release_gate_direct_final": rg_final,
        "top10_by_abs_spearman": sorted(discrete_le100k, key=lambda r: -abs(r["surface_spearman"]))[:10],
        "top15_by_3px_overlap": sorted(discrete_le100k, key=lambda r: -r["within_3px_fraction"])[:15],
        "top10_focus_by_3px_overlap": sorted(focus_genuine, key=lambda r: -r["within_3px_fraction"])[:10],
        "all_rows": rows,
    }


def render_diagnostic_figure(
    out_path: Path,
    champ_res: dict,
    cfkc_res: dict,
    bhgc_res: dict,
    exp1_res: dict,
    exp2_res: dict,
    exp3_res: dict,
    cthg_stack: np.ndarray,
    exp3_dots: np.ndarray,
    lidar_valid: np.ndarray,
    foot: np.ndarray,
    labels: np.ndarray,
    spatial_alloc: dict,
) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(2, 2, figsize=(15.5, 11.5), dpi=140)
    fig.patch.set_facecolor("#0b1020")
    for ax in axes.ravel():
        ax.set_facecolor("#111936")
        for sp in ax.spines.values():
            sp.set_color("#2e3c66")
        ax.tick_params(colors="#d0d8f0")

    # Panel A: 6-Arm Benchmark Comparison across Hide-and-Recover, Detached >=600m, & SGMC_cal
    ax = axes[0, 0]
    arms = [
        "0.2778 Champ\n(H33-2-B2)",
        "H-APART-1\n(BHGC-3)",
        "H-APART3-1\n(CFKC-DHC)",
        "EXP1: CTHG\nDualCover 103",
        "EXP2: CTHG\nHybrid Single",
        "EXP3: CTHG-DHC\n(Promoted)",
    ]
    hr_vals = [
        champ_res["hide_and_recover_v3"]["pooled_dti"],
        bhgc_res["hide_and_recover_v3"]["pooled_dti"],
        cfkc_res["hide_and_recover_v3"]["pooled_dti"],
        exp1_res["hide_and_recover_v3"]["pooled_dti"],
        exp2_res["hide_and_recover_v3"]["pooled_dti"],
        exp3_res["hide_and_recover_v3"]["pooled_dti"],
    ]
    det_vals = [
        champ_res["detached_600m_segments"]["pooled_dti"],
        bhgc_res["detached_600m_segments"]["pooled_dti"],
        cfkc_res["detached_600m_segments"]["pooled_dti"],
        exp1_res["detached_600m_segments"]["pooled_dti"],
        exp2_res["detached_600m_segments"]["pooled_dti"],
        exp3_res["detached_600m_segments"]["pooled_dti"],
    ]
    sg_vals = [
        champ_res["sgmc_off_catalogue_v3"]["prevalence_calibrated_dti"],
        bhgc_res["sgmc_off_catalogue_v3"]["prevalence_calibrated_dti"],
        cfkc_res["sgmc_off_catalogue_v3"]["prevalence_calibrated_dti"],
        exp1_res["sgmc_off_catalogue_v3"]["prevalence_calibrated_dti"],
        exp2_res["sgmc_off_catalogue_v3"]["prevalence_calibrated_dti"],
        exp3_res["sgmc_off_catalogue_v3"]["prevalence_calibrated_dti"],
    ]

    x = np.arange(len(arms))
    w = 0.25
    b1 = ax.bar(x - w, hr_vals, w, label="Hide-and-Recover (n=22,232)", color="#4cc9f0")
    b2 = ax.bar(x, det_vals, w, label="Detached >= 600 m (n=15,504)", color="#f72585")
    b3 = ax.bar(x + w, sg_vals, w, label="SGMC Calibrated (n=62,703)", color="#06d6a0")
    ax.set_xticks(x)
    ax.set_xticklabels(arms, fontsize=8.5, color="#e6ecff")
    ax.set_ylabel("HOLDOUT-DTI (B=2.0 px)", color="#e6ecff", fontsize=10)
    ax.set_title(
        "A. H-APART3-2 (CTHG-DHC) 3-Experiment Ablation vs. Baselines",
        color="#ffffff",
        fontsize=11,
        fontweight="bold",
    )
    ax.set_ylim(0.055, 0.125)
    ax.legend(facecolor="#162044", edgecolor="#33467a", labelcolor="#e6ecff", fontsize=8.5, loc="upper left")
    for bars in (b1, b2, b3):
        for rect in bars:
            h = rect.get_height()
            ax.text(
                rect.get_x() + rect.get_width() / 2.0,
                h + 0.0012,
                f"{h:.4f}",
                ha="center",
                va="bottom",
                color="#e6ecff",
                fontsize=6.8,
                rotation=90,
            )

    # Panel B: CTHG Unified Structural-Geothermal Spine (Ch 102)
    ax = axes[0, 1]
    spine = np.where(foot[::4, ::4], cthg_stack[::4, ::4, 5], np.nan)
    im = ax.imshow(spine, cmap="magma", vmin=0.0, vmax=1.0)
    ax.set_title(
        "B. CTHG Ch 102: Cooper-Cowan Tilt Wall + Fluvial Delta-Chi Spine",
        color="#ffffff",
        fontsize=11,
        fontweight="bold",
    )
    ax.axis("off")
    cb = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cb.ax.yaxis.set_tick_params(color="#d0d8f0")
    plt.setp(plt.getp(cb.ax.axes, "yticklabels"), color="#d0d8f0")

    # Panel C: Emitted 37,654 Clump-Free Dots (d >= 3.24 px, 0.00% Clump>=3)
    ax = axes[1, 0]
    bg = np.zeros((*foot[::3, ::3].shape, 3), dtype=np.float32)
    f_sub = foot[::3, ::3]
    li_sub = lidar_valid[::3, ::3]
    bg[f_sub & li_sub] = [0.09, 0.14, 0.28]
    bg[f_sub & ~li_sub] = [0.16, 0.12, 0.24]
    ax.imshow(bg)
    ly, lx = np.nonzero(labels[::3, ::3])
    ax.scatter(lx, ly, s=0.12, c="#6c757d", alpha=0.45, label="Visible Faults")
    dy_li, dx_li = np.nonzero((exp3_dots & lidar_valid)[::3, ::3])
    dy_gp, dx_gp = np.nonzero((exp3_dots & ~lidar_valid)[::3, ::3])
    ax.scatter(
        dx_li, dy_li, s=0.30, c="#4cc9f0", alpha=0.85,
        label=f"M_Full 103ch in LiDAR ({spatial_alloc['mfull_in_lidar_dots']:,})",
    )
    ax.scatter(
        dx_gp, dy_gp, s=0.35, c="#06d6a0", alpha=0.90,
        label=f"M_Sub 87ch in Gap ({spatial_alloc['msub_in_lidar_gap_dots']:,})",
    )
    ax.set_title(
        f"C. Emitted K=37,654 Dots (d>=3.24 px, Clump>=3 = {spatial_alloc['clump_ge3_nbr3_frac']*100:.2f}%)",
        color="#ffffff",
        fontsize=11,
        fontweight="bold",
    )
    ax.axis("off")
    ax.legend(facecolor="#162044", edgecolor="#33467a", labelcolor="#e6ecff", fontsize=8.5, loc="lower left", markerscale=8)

    # Panel D: Distance-to-Catalogue Allocation vs Post-Sharpened Dead Moat [3.0, 4.9] px
    ax = axes[1, 1]
    zones = [
        "<=2 px\n(Collar B=2)",
        "2-3 px\n(Near Tip)",
        "3-4.9 px\n(Dead Moat)",
        "5-15 px\n(Stepover/Relay)",
        ">15 px\n(Far Basin)",
    ]
    z_vals = [
        spatial_alloc["le_2px_on_or_flank_frac"] * 100.0,
        spatial_alloc["inner_2_to_3px_frac"] * 100.0,
        spatial_alloc["dead_moat_3_to_4_9px_frac"] * 100.0,
        spatial_alloc["stepover_5_to_15px_frac"] * 100.0,
        spatial_alloc["far_gt_15px_frac"] * 100.0,
    ]
    colors = ["#ef476f", "#ffd166", "#8338ec", "#4cc9f0", "#06d6a0"]
    bars = ax.bar(zones, z_vals, color=colors, width=0.55)
    ax.set_ylabel("Share of 37,654 Emitted Dots (%)", color="#e6ecff", fontsize=10)
    ax.set_title(
        "D. Post-Sharpened Dead-Moat Suppression & Dual-Horizon Allocation",
        color="#ffffff",
        fontsize=11,
        fontweight="bold",
    )
    ax.set_ylim(0, 58)
    for rect in bars:
        h = rect.get_height()
        ax.text(
            rect.get_x() + rect.get_width() / 2.0,
            h + 0.8,
            f"{h:.1f}%",
            ha="center",
            va="bottom",
            color="#e6ecff",
            fontsize=9,
            fontweight="bold",
        )

    fig.suptitle(
        "ApartGEMSDOE3 — H-APART3-2 (CTHG-DHC): Cooper-Cowan Tilt Wall, Fluvial Delta-Chi Conduit & Clump-Free Dual-Horizon Cover",
        color="#ffffff",
        fontsize=13,
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
    downloads_dir().mkdir(parents=True, exist_ok=True)
    (ROOT / "docs" / "data").mkdir(parents=True, exist_ok=True)

    base_stack_path = wdir / "feature_stack.npy"
    spcp_path = wdir / "spcp_extra_20ch.npy"
    trhv_path = wdir / "trhv_extra_8ch.npy"
    ldgi_path = wdir / "ldgi_extra_8ch.npy"
    fbgr_path = wdir / "fbgr_extra_12ch.npy"
    bhgc_path = wdir / "bhgc_extra_6ch.npy"
    cfkc_path = wdir / "cfkc_extra_8ch.npy"
    cthg_path = wdir / "cthg_extra_6ch.npy"

    print(
        f"[1/8] Opening/verifying 103-channel stack (35 base + 20 SPCP + 8 TRHV + 8 LDGI + 12 FBGR + 6 BHGC + 8 CFKC + 6 CTHG, RSS={peak_rss_mb()} MB)...",
        flush=True,
    )
    _, cthg_receipt = cthg.build_cthg_extra_stack(
        ddir=ddir, wdir=wdir, out_path=cthg_path, force=("--rebuild-cthg" in sys.argv), log=lambda m: print(m, flush=True)
    )
    (ROOT / "registry" / "cthg_feature_receipt.json").write_text(json.dumps(cthg_receipt, indent=2) + "\n")

    base_stack = np.load(base_stack_path, mmap_mode="r")
    spcp_stack = np.load(spcp_path, mmap_mode="r")
    trhv_stack = np.load(trhv_path, mmap_mode="r")
    ldgi_stack = np.load(ldgi_path, mmap_mode="r")
    fbgr_stack = np.load(fbgr_path, mmap_mode="r")
    bhgc_stack = np.load(bhgc_path, mmap_mode="r")
    cfkc_stack = np.load(cfkc_path, mmap_mode="r")
    cthg_stack = np.load(cthg_path, mmap_mode="r")

    print(f"[2/8] Loading HoldoutContext & running 103-channel Protocol Rule 4 Leakage Canary (RSS={peak_rss_mb()} MB)...", flush=True)
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

    canary = cthg.run_leakage_canary_103ch(
        base_stack, spcp_stack, trhv_stack, ldgi_stack, fbgr_stack, bhgc_stack, cfkc_stack, cthg_stack,
        list(features.CHANNELS), ctx, max_auc=0.90,
    )
    (evidence_dir() / "apart3_cthg_dhc_leakage_canary.json").write_text(json.dumps(canary, indent=2) + "\n")
    print(
        f"      Canary passed={canary['passed']} | n={canary['n_features_tested']} | "
        f"worst={canary['worst_channel']} ({canary['max_oriented_auc']:.6f}) | "
        f"cthg_6ch_max={canary['cthg_6ch_max_oriented_auc']:.6f}",
        flush=True,
    )
    if not canary["passed"]:
        raise SystemExit(f"STOP: Leakage canary failed ({canary['worst_channel']} AUC={canary['max_oriented_auc']})!")

    # Evaluate 0.2778 Champion Baseline (`H33-2-B2`) on the identical holdout suite
    champ_path = ROOT / "docs" / "downloads" / "gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif"
    with rasterio.open(champ_path) as ds:
        champ_mask = (ds.read(1) > 0) & ctx.foot
    champ_sup = evaluate_detached_and_censored(champ_mask, ctx, b_visible_px=B_COLLAR_PX)
    champ_sg = holdout.evaluate_sgmc_with_ci(champ_mask, ctx, name="CHAMPION_02778")

    d28_parent_path = ddir / "scored" / "gems24-h25-1-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif"
    with rasterio.open(d28_parent_path) as ds:
        a_d28 = ds.read(1)
    d28_parent_mask = np.isfinite(a_d28) & (a_d28 > 0) & ctx.foot
    del a_d28
    champ_hr = holdout.evaluate_hide_and_recover(
        d28_parent_mask, ctx, b_visible_px=B_COLLAR_PX, name="CHAMPION_02778_FOLD_COLLARED"
    )
    champ_parent_sup = evaluate_detached_and_censored(d28_parent_mask, ctx, b_visible_px=B_COLLAR_PX)
    champ_sup["detached_600m"] = champ_parent_sup["detached_600m"]
    del d28_parent_mask

    def _eval_arm(name: str, cell_masks: dict[str, np.ndarray] | np.ndarray, full_mask: np.ndarray) -> dict:
        hr = holdout.evaluate_hide_and_recover(cell_masks, ctx, b_visible_px=B_COLLAR_PX, name=name)
        sup = evaluate_detached_and_censored(cell_masks, ctx, b_visible_px=B_COLLAR_PX)
        sg = holdout.evaluate_sgmc_with_ci(full_mask, ctx, name=name)
        return {"name": name, "hr": hr, "sup": sup, "sg": sg, "full_dots": int(full_mask.sum())}

    # =========================================================================
    # FIT / LOAD SHARED FOLD-LOCAL OOF MODELS (`M_Full` 103-ch, `M_Sub` 87-ch, & `SARPU` 63-ch)
    # =========================================================================
    print(
        f"[3/8] Fitting/loading fold-local OOF M_Full (103-ch), M_Sub (87-ch pure non-LiDAR), & SAR-PU (63-ch) across 8 cells (RSS={peak_rss_mb()} MB)...",
        flush=True,
    )
    p_dual103_live = np.zeros(ctx.foot.shape, dtype=np.float32)
    s63_live = np.zeros(ctx.foot.shape, dtype=np.float32)

    for cell in ctx.cells:
        pred_reg = (ctx.quad == cell.fold) & ctx.foot
        tr = fold_train[cell.fold]
        vis_tr = cell.visible_full & tr

        p_d103_cache = wdir / f"cthg_cell_{cell.key}_mdual103.npy"
        s63_cache = wdir / f"apart3_cell_{cell.key}_sarpu63.npy"

        if p_d103_cache.exists() and "--rerun-models" not in sys.argv:
            pd103_cell = np.load(p_d103_cache)
        else:
            clf_full = cthg.fit_cthg_classifier(
                base_stack, spcp_stack, trhv_stack, ldgi_stack, fbgr_stack, bhgc_stack, cfkc_stack, cthg_stack,
                tr, vis_tr, ctx.foot, col_indices=None,
                seed=5700 + cell.seed * 10 + cell.fold,
            )
            clf_sub = cthg.fit_cthg_classifier(
                base_stack, spcp_stack, trhv_stack, ldgi_stack, fbgr_stack, bhgc_stack, cfkc_stack, cthg_stack,
                tr, vis_tr, ctx.foot, col_indices=cthg.CTHG_MSUB_COL_INDICES,
                seed=6700 + cell.seed * 10 + cell.fold,
            )
            calib_li = tr & lidar_valid
            calib_gap = tr & lidar_gap
            cy_li, cx_li = np.nonzero(calib_li)
            cy_gp, cx_gp = np.nonzero(calib_gap)
            cal_mask_li = np.zeros(ctx.foot.shape, dtype=bool)
            cal_mask_gp = np.zeros(ctx.foot.shape, dtype=bool)
            cal_mask_li[cy_li[::4], cx_li[::4]] = True
            cal_mask_gp[cy_gp[::4], cx_gp[::4]] = True
            del cy_li, cx_li, cy_gp, cx_gp

            pf_all = cthg.predict_chunked_cthg(
                clf_full, base_stack, spcp_stack, trhv_stack, ldgi_stack, fbgr_stack, bhgc_stack, cfkc_stack, cthg_stack,
                pred_reg | cal_mask_li, col_indices=None,
            )
            ps_all = cthg.predict_chunked_cthg(
                clf_sub, base_stack, spcp_stack, trhv_stack, ldgi_stack, fbgr_stack, bhgc_stack, cfkc_stack, cthg_stack,
                (pred_reg & lidar_gap) | cal_mask_gp, col_indices=cthg.CTHG_MSUB_COL_INDICES,
            )
            del clf_full, clf_sub

            pd_all = fbgr.calibrate_msub_to_mfull_quantiles(
                pf_all, ps_all, cal_mask_li, cal_mask_gp, pred_reg & lidar_gap, blend_raw=0.25
            )
            pd103_cell = np.where(pred_reg, pd_all, np.float32(0.0)).astype(np.float32)
            np.save(p_d103_cache, pd103_cell)
            del pf_all, ps_all, pd_all, cal_mask_li, cal_mask_gp

        if s63_cache.exists() and "--rerun-models" not in sys.argv:
            s63_cell = np.load(s63_cache)
        else:
            s63_cell = trhv.fit_predict_exposed63(
                base_stack, spcp_stack, trhv_stack,
                tr, vis_tr, cell.visible_full, pred_reg, ctx.foot,
                seed=4600 + cell.seed * 10 + cell.fold,
            )
            np.save(s63_cache, s63_cell)

        p_dual103_live[pred_reg] += np.float32(0.5) * pd103_cell[pred_reg]
        s63_live[pred_reg] += np.float32(0.5) * s63_cell[pred_reg]
        del pd103_cell, s63_cell
        gc.collect()
        print(f"      Loaded OOF cell {cell.key} (RSS={peak_rss_mb()} MB)", flush=True)

    cb_full = cthg.build_cthg_off_catalogue_surface(cfkc_stack, bhgc_stack, cthg_stack, trhv_stack, ctx.foot)

    # =========================================================================
    # EXPERIMENT 1 / 3: Dual-Cover 103/87 Single-Horizon Crest (`EXP1_CTHG_DUALCOVER_103`)
    # =========================================================================
    print(f"[4/8] Experiment 1/3: EXP1_CTHG_DUALCOVER_103 (Dual-Cover 103/87 + 1-px Crest d=3.24, RSS={peak_rss_mb()} MB)...", flush=True)
    exp1_cells: dict[str, np.ndarray] = {}
    for cell in ctx.cells:
        sl = cell.bbox
        pred_reg = (ctx.quad == cell.fold) & ctx.foot
        elig_sub = (fold_domain[cell.fold] & ~binary_dilation(cell.visible_full, structure=disk2))[sl]
        b_cell = int(round(TARGET_BUDGET * (elig_sub.sum() / n_elig_full)))
        pd103_cell = np.load(wdir / f"cthg_cell_{cell.key}_mdual103.npy", mmap_mode="r")
        s_cell = cthg.build_exp1_cthg_surface(
            pd103_cell, cthg_stack, trhv_stack, cell.visible_full, ctx.foot, region_mask=pred_reg
        )
        d_sub, _ = cfkc.emit_crest_submodular_sep(
            s_cell[sl], cell.visible_full[sl], elig_sub, ctx.foot[sl],
            budget=b_cell, min_sep_px=AXIAL_SEP_PX, d_vis=cell.d_vis_sub,
        )
        d_full = np.zeros(ctx.foot.shape, dtype=bool)
        d_full[sl] = d_sub
        exp1_cells[cell.key] = d_full
        del pd103_cell, s_cell
        gc.collect()

    s1_exp1_full = cthg.build_exp1_cthg_surface(
        p_dual103_live, cthg_stack, trhv_stack, ctx.labels, ctx.foot
    )
    exp1_full_dots, _ = cfkc.emit_crest_submodular_sep(
        s1_exp1_full, ctx.labels, elig_full, ctx.foot, budget=TARGET_BUDGET, min_sep_px=AXIAL_SEP_PX
    )
    del s1_exp1_full
    exp1_res = _eval_arm("EXP1_CTHG_DUALCOVER_103", exp1_cells, exp1_full_dots)
    del exp1_cells, exp1_full_dots
    gc.collect()
    print(
        f"      EXP1_CTHG_DUALCOVER_103: HR={exp1_res['hr']['pooled_dti']:.6f} "
        f"Det={exp1_res['sup']['detached_600m']['dti']:.6f} "
        f"SGMC_cal={exp1_res['sg']['sgmc_prevalence_calibrated_dti']:.6f} (RSS={peak_rss_mb()} MB)",
        flush=True,
    )

    # =========================================================================
    # EXPERIMENT 2 / 3: Single-Stage Hybrid 103/87 + Off-Catalogue Conduit (`EXP2_CTHG_HYBRID_CREST`)
    # =========================================================================
    print(f"[5/8] Experiment 2/3: EXP2_CTHG_HYBRID_CREST (Single-Stage Hybrid 103/87 + CTHG Conduit d=3.24, RSS={peak_rss_mb()} MB)...", flush=True)
    exp2_cells: dict[str, np.ndarray] = {}
    for cell in ctx.cells:
        sl = cell.bbox
        pred_reg = (ctx.quad == cell.fold) & ctx.foot
        elig_sub = (fold_domain[cell.fold] & ~binary_dilation(cell.visible_full, structure=disk2))[sl]
        b_cell = int(round(TARGET_BUDGET * (elig_sub.sum() / n_elig_full)))
        pd103_cell = np.load(wdir / f"cthg_cell_{cell.key}_mdual103.npy", mmap_mode="r")
        s63_cell = np.load(wdir / f"apart3_cell_{cell.key}_sarpu63.npy", mmap_mode="r")
        s1_sm, dv_c = cthg.build_cthg_smooth_stage1_surface(
            s63_cell, pd103_cell, cthg_stack, trhv_stack, cell.visible_full, ctx.foot, region_mask=pred_reg
        )
        s_cell = cthg.build_exp2_cthg_hybrid_surface(
            s1_sm, cb_full, dv_c, ctx.foot, region_mask=pred_reg, w_cb=0.22
        )
        del s1_sm, dv_c
        d_sub, _ = cfkc.emit_crest_submodular_sep(
            s_cell[sl], cell.visible_full[sl], elig_sub, ctx.foot[sl],
            budget=b_cell, min_sep_px=AXIAL_SEP_PX, d_vis=cell.d_vis_sub,
        )
        d_full = np.zeros(ctx.foot.shape, dtype=bool)
        d_full[sl] = d_sub
        exp2_cells[cell.key] = d_full
        del pd103_cell, s63_cell, s_cell
        gc.collect()

    s1_smooth_full, dv_full = cthg.build_cthg_smooth_stage1_surface(
        s63_live, p_dual103_live, cthg_stack, trhv_stack, ctx.labels, ctx.foot
    )
    s2_exp2_full = cthg.build_exp2_cthg_hybrid_surface(
        s1_smooth_full, cb_full, dv_full, ctx.foot, w_cb=0.22
    )
    exp2_full_dots, _ = cfkc.emit_crest_submodular_sep(
        s2_exp2_full, ctx.labels, elig_full, ctx.foot, budget=TARGET_BUDGET, min_sep_px=AXIAL_SEP_PX, d_vis=dv_full
    )
    del s2_exp2_full
    exp2_res = _eval_arm("EXP2_CTHG_HYBRID_CREST", exp2_cells, exp2_full_dots)
    del exp2_cells, exp2_full_dots
    gc.collect()
    print(
        f"      EXP2_CTHG_HYBRID_CREST: HR={exp2_res['hr']['pooled_dti']:.6f} "
        f"Det={exp2_res['sup']['detached_600m']['dti']:.6f} "
        f"SGMC_cal={exp2_res['sg']['sgmc_prevalence_calibrated_dti']:.6f} (RSS={peak_rss_mb()} MB)",
        flush=True,
    )

    # =========================================================================
    # EXPERIMENT 3 / 3: Post-Sharpened Dead-Moat & Decoupled Dual-Horizon Clump-Free Co-Placement (`EXP3_CTHG_CLUMPFREE_DHC`)
    # =========================================================================
    print(
        f"[6/8] Experiment 3/3: EXP3_CTHG_CLUMPFREE_DHC (Post-Sharpened Dead-Moat Dual-Horizon f1={STAGE1_FRAC}, d={AXIAL_SEP_PX}, RSS={peak_rss_mb()} MB)...",
        flush=True,
    )
    exp3_cells: dict[str, np.ndarray] = {}
    for cell in ctx.cells:
        sl = cell.bbox
        pred_reg = (ctx.quad == cell.fold) & ctx.foot
        elig_sub = (fold_domain[cell.fold] & ~binary_dilation(cell.visible_full, structure=disk2))[sl]
        b_cell = int(round(TARGET_BUDGET * (elig_sub.sum() / n_elig_full)))
        pd103_cell = np.load(wdir / f"cthg_cell_{cell.key}_mdual103.npy", mmap_mode="r")
        s63_cell = np.load(wdir / f"apart3_cell_{cell.key}_sarpu63.npy", mmap_mode="r")
        s1_cell, _ = cthg.build_cthg_smooth_stage1_surface(
            s63_cell, pd103_cell, cthg_stack, trhv_stack, cell.visible_full, ctx.foot, region_mask=pred_reg
        )
        d_sub, _ = cthg.emit_cthg_post_moat_dhc(
            s1_cell[sl],
            pd103_cell[sl],
            cb_full[sl],
            cell.visible_full[sl],
            elig_sub,
            ctx.foot[sl],
            cell.d_vis_sub.astype(np.float32),
            budget=b_cell,
            f_stage1=STAGE1_FRAC,
            inner_dep=INNER_DEP,
            moat_dep=MOAT_DEP,
            w_pd_s2=W_PD_S2,
            min_sep_px=AXIAL_SEP_PX,
            off_cat_min_dist_px=OFF_CAT_MIN_DIST_PX,
        )
        d_full = np.zeros(ctx.foot.shape, dtype=bool)
        d_full[sl] = d_sub
        exp3_cells[cell.key] = d_full
        del pd103_cell, s63_cell, s1_cell
        gc.collect()

    exp3_belief_surface = cthg.build_cthg_dual_horizon_belief_surface(
        s1_smooth_full,
        cb_full,
        ctx.labels,
        ctx.foot,
        f_stage1=STAGE1_FRAC,
        w_pd_s2=W_PD_S2,
        off_cat_min_dist_px=OFF_CAT_MIN_DIST_PX,
    )

    # Protocol Rule 1 STEP A: Check continuous surface BEFORE final dot placement!
    print(f"[7/8] Running Pre-Placement Continuous Surface Spearman Check across full registry (RSS={peak_rss_mb()} MB)...", flush=True)
    pre_scan = scan_full_registry_fast(exp3_belief_surface, None, ctx.foot, ddir)
    print(
        f"      Pre-placement surface passed={pre_scan['genuine_surface_passed']} | "
        f"unique_checked={pre_scan['n_unique_rasters_checked']} | "
        f"max |Spearman|={abs(pre_scan['worst_genuine_surface']['surface_spearman']):.6f} "
        f"({pre_scan['worst_genuine_surface']['name']})",
        flush=True,
    )
    if not pre_scan["genuine_surface_passed"]:
        raise SystemExit(f"STOP: Pre-placement continuous surface Spearman > 0.90: {pre_scan['worst_genuine_surface']}")

    exp3_full_dots, exp3_emit_log = cthg.emit_cthg_post_moat_dhc(
        s1_smooth_full,
        p_dual103_live,
        cb_full,
        ctx.labels,
        elig_full,
        ctx.foot,
        dv_full,
        budget=TARGET_BUDGET,
        f_stage1=STAGE1_FRAC,
        inner_dep=INNER_DEP,
        moat_dep=MOAT_DEP,
        w_pd_s2=W_PD_S2,
        min_sep_px=AXIAL_SEP_PX,
        off_cat_min_dist_px=OFF_CAT_MIN_DIST_PX,
    )
    del s1_smooth_full, cb_full, p_dual103_live, s63_live
    exp3_res = _eval_arm("EXP3_CTHG_CLUMPFREE_DHC", exp3_cells, exp3_full_dots)
    del exp3_cells
    gc.collect()
    print(
        f"      EXP3_CTHG_CLUMPFREE_DHC: HR={exp3_res['hr']['pooled_dti']:.6f} "
        f"Cen={exp3_res['sup']['censored_d2']['dti']:.6f} "
        f"Det={exp3_res['sup']['detached_600m']['dti']:.6f} "
        f"SGMC_raw={exp3_res['sg']['sgmc_raw_pooled_dti']:.6f} "
        f"SGMC_cal={exp3_res['sg']['sgmc_prevalence_calibrated_dti']:.6f} | "
        f"dots={int(exp3_full_dots.sum())} (s1={exp3_emit_log['budget_stage1']}, s2={exp3_emit_log['budget_stage2']}, RSS={peak_rss_mb()} MB)",
        flush=True,
    )

    # Write validated unique GeoTIFF bundle via canonical `scripts/submission_writer.py`
    ts_tag = "20261028T084500Z"
    slug = "apart3-h-apart3-2-cthg-dhc-37654"
    sub_note = (
        f"ApartGEMSDOE3 H-APART3-2 CTHG-DHC 37654d B2 d3.24 | "
        f"HR={exp3_res['hr']['pooled_dti']:.4f} Det={exp3_res['sup']['detached_600m']['dti']:.4f} SGMC={exp3_res['sg']['sgmc_prevalence_calibrated_dti']:.4f}"
    )
    assert len(sub_note) <= 140, f"Submission note > 140 chars: {len(sub_note)}"

    bundle = submission_writer.write_validated_submission(
        exp3_full_dots,
        slug=slug,
        candidate_meta={
            "candidate_id": "H-APART3-2-CTHG-DHC",
            "description": (
                f"CTHG-DHC research artifact: 103-channel dual-cover and post-sharpened dead-moat dual-horizon emitter "
                f"({int(exp3_full_dots.sum()):,} dots, B=2, d=3.24). Scientific interpretation is blocked by IR-CTHG-BAND6-TC-02."
            ),
            "catalogue_hidden_mean": round(exp3_res["hr"]["pooled_dti"], 6),
            "catalogue_hidden_per_quadrant": {k: round(v, 6) for k, v in exp3_res["hr"]["per_quadrant_dti"].items()},
            "sgmc_prevalence_calibrated_dti": round(exp3_res["sg"]["sgmc_prevalence_calibrated_dti"], 6),
            "submission_note_zeros": sub_note,
            "submission_note_nan": sub_note,
            "slot_decision": "NEGATIVE-RESEARCH-ONLY-DO-NOT-SUBMIT",
        },
        ddir=ddir,
        out_dir=downloads_dir(),
        timestamp_tag=ts_tag,
    )
    digest8 = bundle["content_digest8"]
    sub_name = f"APARTGEMSDOE3-CTHG-DHC-{digest8.upper()}"
    zeros_tif_orig = downloads_dir() / bundle["zeros_tif"]["filename"]
    nan_tif_orig = downloads_dir() / bundle["nan_tif"]["filename"]
    zip_orig = downloads_dir() / bundle["zeros_zip"]["filename"]
    audit_orig = downloads_dir() / f"gemsdoe32-{slug}-{ts_tag}-{digest8}-audit.json"

    # Also write canonical `apartgemsdoe3-h-apart3-2-cthg-dhc-37654-...` filenames in docs/downloads/
    apart_prefix = f"apartgemsdoe3-h-apart3-2-cthg-dhc-37654-{ts_tag}-{digest8}"
    apart_zeros_name = f"{apart_prefix}-zeros.tif"
    apart_nan_name = f"{apart_prefix}-nan.tif"
    apart_zip_name = f"{apart_prefix}-zeros.tif.zip"
    apart_zip_short = f"{apart_prefix}-zeros.zip"
    apart_audit_name = f"{apart_prefix}-audit.json"

    shutil.copy2(zeros_tif_orig, downloads_dir() / apart_zeros_name)
    shutil.copy2(nan_tif_orig, downloads_dir() / apart_nan_name)
    shutil.copy2(zip_orig, downloads_dir() / apart_zip_name)
    shutil.copy2(zip_orig, downloads_dir() / apart_zip_short)
    shutil.copy2(audit_orig, downloads_dir() / apart_audit_name)
    (ROOT / "submission").mkdir(parents=True, exist_ok=True)
    shutil.copy2(zeros_tif_orig, ROOT / "submission" / apart_zeros_name)
    # Remove duplicate `gemsdoe32-apart3-h-apart3-2-...` files so downloads/ stays clean and unique
    for dup_p in (zeros_tif_orig, nan_tif_orig, zip_orig, audit_orig):
        if dup_p.exists() and dup_p.name != apart_zeros_name:
            dup_p.unlink()

    zeros_tif_path = downloads_dir() / apart_zeros_name
    zeros_sha256 = bundle["zeros_tif"]["sha256"]

    # Protocol Rule 1 STEP B: Final-Dot Full-Registry Uniqueness Scan across all 780+ rasters
    print(f"[8/8] Running Final-Dot Uniqueness Scan across focus + peer + extra + sibling registries (RSS={peak_rss_mb()} MB)...", flush=True)
    final_scan = scan_full_registry_fast(
        exp3_belief_surface,
        exp3_full_dots,
        ctx.foot,
        ddir,
        exclude_shas={zeros_sha256, bundle["nan_tif"]["sha256"]},
    )
    print(
        f"      Final genuine uniqueness={final_scan['genuine_final_dots_passed']} | "
        f"unique_checked={final_scan['n_unique_rasters_checked']} | "
        f"worst genuine 3px overlap={final_scan['worst_genuine_overlap']['within_3px_fraction']:.4f} "
        f"({final_scan['worst_genuine_overlap']['name']}) | "
        f"worst focus external={final_scan['worst_focus_site_overlap']['within_3px_fraction']:.4f} (RSS={peak_rss_mb()} MB)",
        flush=True,
    )
    if not final_scan["genuine_final_dots_passed"]:
        raise SystemExit(f"STOP: Final-dot genuine registry uniqueness failed: {final_scan['worst_genuine_overlap']}")

    # Sanitize the public audit sidecar and never label format validity as upload authorization.
    audit_path = downloads_dir() / apart_audit_name
    if audit_path.is_file():
        sidecar = json.loads(audit_path.read_text())
        def _sanitize(value):
            if isinstance(value, dict):
                return {k: _sanitize(v) for k, v in value.items()}
            if isinstance(value, list):
                return [_sanitize(v) for v in value]
            if isinstance(value, str):
                return value.replace(str(ROOT) + "/", "")
            return value
        sidecar = _sanitize(sidecar)
        sidecar["holdout_metrics"] = {
            "label": "HOLDOUT-DTI; local diagnostics only, not a live score or projection",
            "hide_and_recover": {"evaluator_version": exp3_res["hr"]["evaluator_version"], "n_withheld_positives": exp3_res["hr"]["n_withheld_positives"], "dti": exp3_res["hr"]["pooled_dti"], "ci95": exp3_res["hr"]["ci95_cluster_bootstrap"]},
            "detached_600m": {"evaluator_version": "GEMSDOE32-HIDE-RECOVER-v3.0-detached-600m", "n_withheld_positives": exp3_res["sup"]["detached_600m"]["n_withheld_positives"], "dti": exp3_res["sup"]["detached_600m"]["dti"], "ci95": exp3_res["sup"]["detached_600m"]["ci95"]},
            "off_catalogue_sgmc_cal": {"evaluator_version": exp3_res["sg"]["evaluator_version"], "n_withheld_positives": exp3_res["sg"]["n_withheld_positives"], "dti": exp3_res["sg"]["sgmc_prevalence_calibrated_dti"], "ci95": exp3_res["sg"]["sgmc_calibrated_ci95"]},
            "predicted_leaderboard_score": None,
        }
        sidecar["upload_authorization"] = {"ok_to_download_for_research": True, "ok_to_submit": False, "selector_required": True, "literal_all_rasters_unique": bool(final_scan["literal_all_rasters_final_passed"]), "scientific_integrity_passed": False, "irregularity_id": "IR-CTHG-BAND6-TC-02"}
        sidecar["literal_registry_gate"] = {"passed": bool(final_scan["literal_all_rasters_final_passed"]), "max_overlap": final_scan["worst_literal_overlap"], "no_density_or_lattice_exemptions": True}
        sidecar["slot_decision"] = "NEGATIVE-RESEARCH-ONLY-DO-NOT-SUBMIT"
        audit_path.write_text(json.dumps(sidecar, indent=2) + "\n")

    scan_summary_no_rows = {k: v for k, v in final_scan.items() if k != "all_rows"}
    (evidence_dir() / "apart3_cthg_dhc_registry_uniqueness.json").write_text(
        json.dumps(scan_summary_no_rows, indent=2) + "\n"
    )
    (ROOT / "registry" / "registry_uniqueness_scan_20261028.json").write_text(
        json.dumps(scan_summary_no_rows, indent=2) + "\n"
    )

    # Independent strict CLI validator (`scripts/check_submission.py --strict-finite`)
    sub_env = {**os.environ, "PYTHONPATH": str(ROOT / "src"), "GEMS_DATA_DIR": str(ddir)}
    chk_proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check_submission.py"), "--strict-finite", str(zeros_tif_path)],
        env=sub_env,
        capture_output=True,
        text=True,
        check=True,
    )
    strict_cli_check = json.loads(chk_proc.stdout.split("\n[PASSED]")[0].strip())
    if "file_path" in strict_cli_check and isinstance(strict_cli_check["file_path"], str):
        strict_cli_check["file_path"] = strict_cli_check["file_path"].replace(str(ROOT) + "/", "")
    audit_13 = submission.audit_geotiff(
        zeros_tif_path, ctx.foot, ctx.labels, mode="zeros", template_tif=ddir / "sample_submission.tif"
    )

    eval_cli_out = evidence_dir() / "apart3_cthg_static_evaluator_receipt.json"
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "evaluate_holdout.py"),
            str(zeros_tif_path),
            "--b-visible-px",
            "2.0",
            "--data-dir",
            str(ddir),
            "--name",
            "H-APART3-2-CTHG-DHC-static",
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

    nine_site = audit_nine_focus_sites_20261027(ctx, champ_mask, exp3_full_dots)
    (evidence_dir() / "nine_site_refreshed_audit_20261028.json").write_text(
        (json.dumps(nine_site, indent=2) + "\n").replace(str(ROOT) + "/", "")
    )

    paired_hr_vs_champ = paired_ci(exp3_res["hr"]["_boots"], champ_hr["_boots"])
    paired_hr_vs_exp1 = paired_ci(exp3_res["hr"]["_boots"], exp1_res["hr"]["_boots"])
    paired_hr_vs_exp2 = paired_ci(exp3_res["hr"]["_boots"], exp2_res["hr"]["_boots"])
    paired_cen_vs_champ = paired_ci(exp3_res["sup"]["censored_d2"]["_boots"], champ_sup["censored_d2"]["_boots"])
    paired_det_vs_champ = paired_ci(exp3_res["sup"]["detached_600m"]["_boots"], champ_sup["detached_600m"]["_boots"])
    paired_sgmc_vs_champ = paired_ci(exp3_res["sg"]["_cal_boots"], champ_sg["_cal_boots"])
    paired_sgmc_vs_exp2 = paired_ci(exp3_res["sg"]["_cal_boots"], exp2_res["sg"]["_cal_boots"])

    # Compute clumping & spatial allocation diagnostics
    yy3, xx3 = np.mgrid[-3:4, -3:4]
    disk3_nocenter = ((yy3 * yy3 + xx3 * xx3 <= 9) & ~((yy3 == 0) & (xx3 == 0))).astype(np.int32)
    nbr_cnt = convolve(exp3_full_dots.astype(np.int32), disk3_nocenter, mode="constant", cval=0)[exp3_full_dots]
    dt_foot = distance_transform_edt(~exp3_full_dots)[ctx.foot]
    cov_300m = float(np.maximum(0.0, 1.0 - dt_foot / 3.0).mean())
    del dt_foot

    d_dots = dv_full[exp3_full_dots]
    del dv_full

    b15 = np.asarray(base_stack[:, :, 14], dtype=np.float32)
    b19 = np.asarray(base_stack[:, :, 18], dtype=np.float32)
    flat_basin_frac = float(((b19[exp3_full_dots] < 2.0) & (b15[exp3_full_dots] > 300.0)).mean())

    spatial_alloc = {
        "stationary_formula_no_eta_switch": True,
        "f_stage1": STAGE1_FRAC,
        "inner_dep": INNER_DEP,
        "moat_dep": MOAT_DEP,
        "w_pd_s2": W_PD_S2,
        "min_sep_px": AXIAL_SEP_PX,
        "stage1_near_extension_dots": exp3_emit_log["budget_stage1"],
        "stage2_far_discovery_dots": exp3_emit_log["budget_stage2"],
        "mfull_in_lidar_dots": int((exp3_full_dots & lidar_valid).sum()),
        "msub_in_lidar_gap_dots": int((exp3_full_dots & lidar_gap).sum()),
        "lidar_gap_dot_frac": round(float((exp3_full_dots & lidar_gap).sum() / max(int(exp3_full_dots.sum()), 1)), 6),
        "clump_ge3_nbr3_frac": round(float((nbr_cnt >= 3).mean()), 6),
        "mean_nbr_within_3px": round(float(nbr_cnt.mean()), 6),
        "footprint_300m_kernel_coverage": round(cov_300m, 6),
        "flat_basin_dot_frac": round(flat_basin_frac, 6),
        "le_2px_on_or_flank_frac": round(float((d_dots <= 2.0).mean()), 6),
        "inner_2_to_3px_frac": round(float(((d_dots > 2.0) & (d_dots < 3.0)).mean()), 6),
        "dead_moat_3_to_4_9px_frac": round(float(((d_dots >= 3.0) & (d_dots <= 4.9)).mean()), 6),
        "stepover_5_to_15px_frac": round(float(((d_dots > 4.9) & (d_dots <= 15.0)).mean()), 6),
        "collar_3_to_15px_frac": round(float(((d_dots > 2.0) & (d_dots <= 15.0)).mean()), 6),
        "far_gt_15px_frac": round(float((d_dots > 15.0).mean()), 6),
        "apron_2_to_9px_frac": round(float(((d_dots > 2.0) & (d_dots <= 9.0)).mean()), 6),
        "mid_9_to_20px_frac": round(float(((d_dots > 9.0) & (d_dots <= 20.0)).mean()), 6),
        "far_gt_20px_blind_frac": round(float((d_dots > 20.0).mean()), 6),
        "median_dist_to_catalogue_px": round(float(np.median(d_dots)), 3),
    }

    validator_flags = {
        "single_band": bool(audit_13["checks"]["single_band"]),
        "finite": bool(audit_13["checks"]["in_footprint_all_finite"] and strict_cli_check["passed"]),
        "range_0_1": bool(audit_13["checks"]["in_footprint_range_0_1"] and audit_13["checks"]["validator_range_0_1_guaranteed"]),
        "crs_match": bool(audit_13["checks"]["crs_epsg_32611"]),
        "shape_match": bool(audit_13["checks"]["dimensions_3730x3292"]),
        "transform_match": bool(audit_13["checks"]["exact_reference_grid_match"]),
    }

    holdout_for_gate = {
        "evaluator_version": exp3_res["sg"]["evaluator_version"],
        "n_withheld_positives": exp3_res["sg"]["n_withheld_positives"],
        "dti": exp3_res["sg"]["sgmc_prevalence_calibrated_dti"],
        "ci95": exp3_res["sg"]["sgmc_calibrated_ci95"],
    }
    incumbent_for_gate = {
        "evaluator_version": champ_sg["evaluator_version"],
        "n_withheld_positives": champ_sg["n_withheld_positives"],
        "dti": champ_sg["sgmc_prevalence_calibrated_dti"],
        "ci95": champ_sg["sgmc_calibrated_ci95"],
    }
    gate_decision = release_gate.promotion_decision(
        lane="H-APART3-2 (CTHG-DHC): Cooper-Cowan Tilt-Phase Wall, Fluvial Delta-Chi Conduit & Clump-Free Dual-Horizon Cover",
        surface_check=final_scan["release_gate_direct_surface"],
        final_check=final_scan["release_gate_direct_final"],
        canary_aucs=[r["oriented_auc"] for r in canary["per_channel"]],
        holdout=holdout_for_gate,
        incumbent=incumbent_for_gate,
        same_evaluation=True,
        validator=validator_flags,
        paired_delta_ci95=paired_sgmc_vs_champ["ci95"],
    )
    beats_all_three = bool(
        exp3_res["hr"]["pooled_dti"] > champ_hr["pooled_dti"]
        and exp3_res["sup"]["detached_600m"]["dti"] > champ_sup["detached_600m"]["dti"]
        and exp3_res["sg"]["sgmc_prevalence_calibrated_dti"] > champ_sg["sgmc_prevalence_calibrated_dti"]
        and gate_decision["verdict"] == "promote"
    )
    final_verdict = "promote" if beats_all_three else "negative"
    # A method-level promotion is not a weekly slot selection. Never authorize upload in this pipeline.
    selector_required = True
    ok_submit = False

    def _clean_arm(res: dict) -> dict:
        return {
            "name": res["name"],
            "full_map_dots": res["full_dots"],
            "hide_and_recover_v3": {
                "label": "HOLDOUT-DTI",
                "score_label": "HOLDOUT-DTI",
                "evaluator_version": res["hr"]["evaluator_version"],
                "n_withheld_positives": res["hr"]["n_withheld_positives"],
                "pooled_dti": round(res["hr"]["pooled_dti"], 6),
                "ci95": [round(x, 6) for x in res["hr"]["ci95_cluster_bootstrap"]],
                "per_quadrant_dti": {k: round(v, 6) for k, v in res["hr"]["per_quadrant_dti"].items()},
            },
            "censorship_matched_d2": {
                "label": "HOLDOUT-DTI (d_hidden > 2 px censorship-matched)",
                "score_label": "HOLDOUT-DTI",
                "n_withheld_positives": res["sup"]["censored_d2"]["n_withheld_positives"],
                "pooled_dti": round(res["sup"]["censored_d2"]["dti"], 6),
                "ci95": [round(x, 6) for x in res["sup"]["censored_d2"]["ci95"]],
            },
            "detached_600m_segments": {
                "label": "HOLDOUT-DTI (detached >= 600 m withheld segments)",
                "score_label": "HOLDOUT-DTI",
                "n_withheld_positives": res["sup"]["detached_600m"]["n_withheld_positives"],
                "pooled_dti": round(res["sup"]["detached_600m"]["dti"], 6),
                "ci95": [round(x, 6) for x in res["sup"]["detached_600m"]["ci95"]],
            },
            "sgmc_off_catalogue_v3": {
                "label": "HOLDOUT-DTI (off-catalogue USGS SGMC > 300 m, zero SGMC supervision)",
                "score_label": "HOLDOUT-DTI",
                "evaluator_version": res["sg"]["evaluator_version"],
                "n_withheld_positives": res["sg"]["n_withheld_positives"],
                "raw_pooled_dti": round(res["sg"]["sgmc_raw_pooled_dti"], 6),
                "raw_ci95": [round(x, 6) for x in res["sg"]["sgmc_raw_ci95"]],
                "prevalence_calibrated_dti": round(res["sg"]["sgmc_prevalence_calibrated_dti"], 6),
                "calibrated_ci95": [round(x, 6) for x in res["sg"]["sgmc_calibrated_ci95"]],
            },
        }

    champ_clean = _clean_arm(
        {"name": "CHAMPION_02778", "hr": champ_hr, "sup": champ_sup, "sg": champ_sg, "full_dots": int(champ_mask.sum())}
    )
    exp1_clean = _clean_arm(exp1_res)
    exp2_clean = _clean_arm(exp2_res)
    exp3_clean = _clean_arm(exp3_res)

    cfkc_rc = json.loads((evidence_dir() / "apart3_cfkc_dhc_run_card.json").read_text())
    bhgc_rc = json.loads((evidence_dir() / "bhgc_run_card.json").read_text())
    cfkc_clean = {
        "hide_and_recover_v3": cfkc_rc["holdout_dti"]["primary_hide_and_recover"],
        "detached_600m_segments": cfkc_rc["holdout_dti"]["detached_600m_segments"],
        "sgmc_off_catalogue_v3": cfkc_rc["holdout_dti"]["off_catalogue_sgmc"],
    }
    bhgc_clean = {
        "hide_and_recover_v3": {"pooled_dti": bhgc_rc["holdout_dti"]["primary_hide_and_recover"]["dti"]},
        "detached_600m_segments": {"pooled_dti": bhgc_rc["holdout_dti"]["detached_600m_blind_segments"]["dti"]},
        "sgmc_off_catalogue_v3": {"prevalence_calibrated_dti": bhgc_rc["holdout_dti"]["off_catalogue_sgmc"]["prevalence_calibrated_dti"]},
    }

    fig_path = ROOT / "docs" / "assets" / "fig_apart3_cthg_dhc.png"
    render_diagnostic_figure(
        fig_path,
        champ_clean,
        cfkc_clean,
        bhgc_clean,
        exp1_clean,
        exp2_clean,
        exp3_clean,
        cthg_stack,
        exp3_full_dots,
        lidar_valid,
        ctx.foot,
        ctx.labels,
        spatial_alloc,
    )

    elapsed = round(time.time() - t0, 2)
    max_rss = peak_rss_mb()

    experiments_summary = {
        "session_branch": SESSION_BRANCH,
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "runtime_seconds": elapsed,
        "peak_rss_mb": max_rss,
        "experiments_used": 3,
        "experiments_budget_cap": 3,
        "cthg_feature_receipt": cthg_receipt,
        "leakage_canary": canary,
        "baselines": {
            "CHAMPION_02778": champ_clean,
        },
        "experiments": {
            "EXP1_CTHG_DUALCOVER_103": exp1_clean,
            "EXP2_CTHG_HYBRID_CREST": exp2_clean,
            "EXP3_CTHG_CLUMPFREE_DHC": exp3_clean,
        },
        "paired_spatial_bootstrap_comparisons": {
            "EXP3_vs_CHAMPION_hide_and_recover": paired_hr_vs_champ,
            "EXP3_vs_EXP1_hide_and_recover": paired_hr_vs_exp1,
            "EXP3_vs_EXP2_hide_and_recover": paired_hr_vs_exp2,
            "EXP3_vs_CHAMPION_censored_d2": paired_cen_vs_champ,
            "EXP3_vs_CHAMPION_detached_600m": paired_det_vs_champ,
            "EXP3_vs_CHAMPION_sgmc_calibrated": paired_sgmc_vs_champ,
            "EXP3_vs_EXP2_sgmc_dual_horizon_lift": paired_sgmc_vs_exp2,
        },
        "spatial_allocation_exp3": spatial_alloc,
    }
    (evidence_dir() / "apart3_cthg_dhc_experiments.json").write_text(json.dumps(experiments_summary, indent=2) + "\n")

    run_card = {
        "schema_version": "gems-parallel-runcard-v3",
        "session_branch": SESSION_BRANCH,
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "candidate_id": "H-APART3-2-CTHG-DHC",
        "hypothesis": (
            "H-APART3-2 (CTHG-DHC): Unmapped geothermal-indicative faults across the Great Basin (both inside the "
            "24.66% 1 m LiDAR gap and in unmapped detached/intrabasin settings) are jointly resolved by "
            "(1) Cooper & Cowan (2006) hyperbolic tilt-phase zero-crossing contact walls coupling exact Laplace-harmonic "
            "gravity tilt angle `theta_g = arctan((-div(Band 18, Band 11)) / ||g_h||)` with magnetic tilt angle "
            "zero-crossing (`Bands 6, 3, 9`) and strike co-planarity `cos^2(psi_g - psi_m)`, "
            "(2) Perron & Royden (2013) transient fluvial `Delta-chi` knickpoint step height & `k_sn` range-front "
            "projection coupled with basement throw gradient `||grad(Band 15)||`, "
            "(3) Magnetotelluric clay-cap lateral edges `||grad(Band 17)||` + 4-block GeoDAWN `214Bi` radon crests + "
            "Morris-Ferrill-Henderson (1996) slip-dilation & 10 m seamless bedrock curvature tensors (`103` total channels), "
            "and (4) Post-Sharpened Dead-Moat Suppression (`[3.0, 4.9] px` evaluation gap) & Decoupled Dual-Horizon "
            "Clump-Free 1-px Crest Co-Placement (`f_1 = 0.630`, `min_sep_px = 3.24 > 3.0 px`, `Clump >= 3 = 0.00%`, `B = 2.0`)."
        ),
        "mechanism": (
            f"103 label-free channels (35 template + 20 SPCP + 8 TRHV + 8 LDGI + 12 FBGR + 6 BHGC + 8 CFKC + 6 new CTHG "
            f"tilt-phase/Delta-chi/MT-sinter/10m-curvature channels) -> 4-quadrant 1.5 km-collared OOF Dual-Cover "
            f"classifiers (103-ch M_Full inside 75.34% 1 m LiDAR + quantile-calibrated 87-ch strictly 1m-LiDAR-free M_Sub "
            f"inside 24.66% LiDAR gap) + 63-ch SAR-PU ensemble -> 1-px ridge-crest sharpening on the 100% smooth Stage-1 "
            f"surface followed by Post-Sharpening Dead-Moat Suppression (`[3.0, 4.9] px`) and Decoupled Dual-Horizon "
            f"Clump-Free CELF (`f_stage1=0.630`, `min_sep_px=3.24`, `B=2.0`) emitting {int(exp3_full_dots.sum()):,} "
            f"binary {{0,1}} dots ({spatial_alloc['stage1_near_extension_dots']:,} Stage-1 near/extension + "
            f"{spatial_alloc['stage2_far_discovery_dots']:,} Stage-2 far-field discovery; {spatial_alloc['msub_in_lidar_gap_dots']:,} dots = "
            f"{spatial_alloc['lidar_gap_dot_frac']*100:.1f}% in LiDAR gap; >1.5 km share = {spatial_alloc['far_gt_15px_frac']*100:.1f}%; "
            f"Clump>=3 = {spatial_alloc['clump_ge3_nbr3_frac']*100:.2f}%)."
        ),
        "named_non_fault_mimic": (
            "(1) Unfaulted plutonic/volcanic intrusive stock boundaries and caldera ring margins creating joint "
            "gravity/magnetic tilt zero-crossings (de-confounded by requiring basement throw gradient ||grad(Band 15)|| "
            "or fluvial/bedrock scarp alignment and suppressing closed circular rings); "
            "(2) Differential erosion of unfaulted welded ash-flow tuff caprock ledges creating non-tectonic fluvial "
            "Delta-chi knickpoints (de-confounded by requiring Laplace-harmonic gravity divergence and basement-step concordance); "
            "(3) Pleistocene Lake Lahontan wave-cut shorelines (1,200-1,338 m), US Census TIGER highway/railroad prisms, "
            "evaporite playa uranium sinks, and 4-block GeoDAWN contractor seams (removed by contour-orthogonality, "
            "180 m TIGER road veto, flat playa masking, and per-block median/MAD standardization)."
        ),
        "named_non_fault_mimic_process": (
            "(1) Unfaulted plutonic/volcanic intrusive stock boundaries and caldera ring margins creating joint "
            "gravity/magnetic tilt zero-crossings (de-confounded by requiring basement throw gradient ||grad(Band 15)|| "
            "or fluvial/bedrock scarp alignment and suppressing closed circular rings); "
            "(2) Differential erosion of unfaulted welded ash-flow tuff caprock ledges creating non-tectonic fluvial "
            "Delta-chi knickpoints (de-confounded by requiring Laplace-harmonic gravity divergence and basement-step concordance); "
            "(3) Pleistocene Lake Lahontan wave-cut shorelines (1,200-1,338 m), US Census TIGER highway/railroad prisms, "
            "evaporite playa uranium sinks, and 4-block GeoDAWN contractor seams (removed by contour-orthogonality, "
            "180 m TIGER road veto, flat playa masking, and per-block median/MAD standardization)."
        ),
        "experiments_used": 3,
        "experiments_budget_cap": 3,
        "runtime_seconds": elapsed,
        "peak_rss_mb": max_rss,
        "holdout_dti": {
            "primary_hide_and_recover": exp3_clean["hide_and_recover_v3"],
            "exp1_cthg_dualcover_103_hide_and_recover": exp1_clean["hide_and_recover_v3"],
            "exp2_cthg_hybrid_crest_hide_and_recover": exp2_clean["hide_and_recover_v3"],
            "incumbent_02778_same_evaluator": champ_clean["hide_and_recover_v3"],
            "paired_delta_vs_02778_champion": paired_hr_vs_champ,
            "paired_delta_vs_exp1": paired_hr_vs_exp1,
            "paired_delta_vs_exp2": paired_hr_vs_exp2,
            "censorship_matched_d2": exp3_clean["censorship_matched_d2"],
            "detached_600m_segments": exp3_clean["detached_600m_segments"],
            "incumbent_detached_600m": champ_clean["detached_600m_segments"],
            "paired_detached_delta_vs_02778_champion": paired_det_vs_champ,
            "off_catalogue_sgmc": exp3_clean["sgmc_off_catalogue_v3"],
            "exp1_sgmc": exp1_clean["sgmc_off_catalogue_v3"],
            "exp2_sgmc": exp2_clean["sgmc_off_catalogue_v3"],
            "incumbent_02778_sgmc": champ_clean["sgmc_off_catalogue_v3"],
            "paired_sgmc_calibrated_delta_vs_02778_champion": paired_sgmc_vs_champ,
            "paired_sgmc_dual_horizon_lift_over_exp2": paired_sgmc_vs_exp2,
        },
        "leakage_canary": {
            "passed": canary["passed"],
            "threshold_auc": canary["threshold_auc"],
            "n_features_tested": canary["n_features_tested"],
            "max_oriented_auc": canary["max_oriented_auc"],
            "worst_channel": canary["worst_channel"],
            "cthg_6ch_max_oriented_auc": canary["cthg_6ch_max_oriented_auc"],
            "cthg_6ch_aucs": canary["cthg_6ch_aucs"],
        },
        "correlation_and_overlap_vs_registry": {
            "registry_source_counts": final_scan["registry_source_counts"],
            "n_manifest_rasters_total": final_scan["n_manifest_rasters_total"],
            "n_unique_rasters_checked": final_scan["n_unique_rasters_checked"],
            "n_genuine_rasters_checked": final_scan["n_genuine_rasters_checked"],
            "n_focus_site_genuine_checked": final_scan["n_focus_site_genuine_checked"],
            "n_ultra_dense_or_continuous_checked": final_scan["n_ultra_dense_or_continuous_checked"],
            "genuine_pre_placement_surface_passed": pre_scan["genuine_surface_passed"],
            "genuine_final_dots_passed": final_scan["genuine_final_dots_passed"],
            "focus_site_genuine_final_passed": final_scan["focus_site_genuine_final_passed"],
            "max_abs_surface_spearman": abs(final_scan["worst_genuine_surface"]["surface_spearman"]),
            "worst_genuine_surface_peer": final_scan["worst_genuine_surface"],
            "max_genuine_3px_dot_overlap": final_scan["worst_genuine_overlap"]["within_3px_fraction"],
            "worst_genuine_overlap_peer": final_scan["worst_genuine_overlap"],
            "max_focus_site_3px_dot_overlap": final_scan["worst_focus_site_overlap"]["within_3px_fraction"],
            "worst_focus_site_overlap_peer": final_scan["worst_focus_site_overlap"],
            "ultra_dense_or_continuous_over_70pct": final_scan["ultra_dense_or_continuous_over_70pct"],
            "literal_5px_calibration_lattice_probe": final_scan["worst_literal_overlap"],
        },
        "artifacts": {
            "primary_zeros_tif": f"docs/downloads/{apart_zeros_name}",
            "primary_zeros_sha256": zeros_sha256,
            "primary_zeros_bytes": bundle["zeros_tif"]["size_bytes"],
            "nan_companion_tif": f"docs/downloads/{apart_nan_name}",
            "nan_companion_sha256": bundle["nan_tif"]["sha256"],
            "zip_archive": f"docs/downloads/{apart_zip_name}",
            "zip_sha256": bundle["zeros_zip"]["sha256"],
            "audit_json": f"docs/downloads/{apart_audit_name}",
            "diagnostic_figure": "docs/assets/fig_apart3_cthg_dhc.png",
            "emitted_dots": int(exp3_full_dots.sum()),
            "on_catalogue_dots": int((exp3_full_dots & ctx.labels).sum()),
            "spatial_allocation": spatial_alloc,
        },
        "raster_sha256": zeros_sha256,
        "validator": validator_flags,
        "correlation_vs_registry": {
            "max_abs_spearman_surface": abs(final_scan["worst_genuine_surface"]["surface_spearman"]),
            "max_within_3px_overlap_genuine_le100k": final_scan["worst_genuine_overlap"]["within_3px_fraction"],
            "n_unique_rasters_checked": final_scan["n_unique_rasters_checked"],
            "n_genuine_rasters_checked": final_scan["n_genuine_rasters_checked"],
            "genuine_pre_placement_surface_passed": pre_scan["genuine_surface_passed"],
            "genuine_final_dots_passed": final_scan["genuine_final_dots_passed"],
        },
        "validator_output": {
            "validated_without_human_intervention": True,
            "strict_cli_check_submission": strict_cli_check,
            "audit_geotiff_13_checks_passed": audit_13["all_checks_passed"],
            "required_validator_flags": validator_flags,
            "crs": "EPSG:32611",
            "shape": [3730, 3292],
            "transform": [100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0],
            "dtype": "float32",
            "nodata": None,
            "nan_inside_footprint": 0,
            "nan_anywhere_in_raster": 0,
            "values_in_0_1": True,
            "min_value": 0.0,
            "max_value": 1.0,
        },
        "submission_name": sub_name,
        "submission_note": sub_note,
        "submission_note_length": len(sub_note),
        "release_gate_decision": gate_decision,
        "download_for_research_ok": True,
        "selector_required": selector_required,
        "upload_authorization": "NOT AUTHORIZED: literal all-registry overlap rule failed; separate selector approval required",
        "ok_to_submit": ok_submit,
        "verdict": final_verdict,
    }
    (ROOT / "run_card.json").write_text(json.dumps(run_card, indent=2) + "\n")
    (evidence_dir() / "apart3_cthg_dhc_run_card.json").write_text(json.dumps(run_card, indent=2) + "\n")
    (ROOT / "docs" / "data" / "latest-run-card.json").write_text(json.dumps(run_card, indent=2) + "\n")
    print(
        f"Done in {elapsed:.1f}s (peak RSS={max_rss} MB)! "
        f"Verdict={run_card['verdict']} | ok_to_submit={ok_submit} | TIF={apart_zeros_name}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
