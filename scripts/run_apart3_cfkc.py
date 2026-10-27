#!/usr/bin/env python3
"""Execute Pre-Registered Lane H-APART3-1 (CFKC-DHC) within the strict 3-experiment budget.

Reuses shared tools strictly (Protocol Rule 2):
  - `.cache/gems_work/feature_stack.npy` (`scripts/build_features.py`, 35 channels)
  - `.cache/gems_work/spcp_extra_20ch.npy` (`gems32.spcp`, 20 label-free channels)
  - `.cache/gems_work/trhv_extra_8ch.npy` (`gems32.trhv`, 8 label-free hydrothermal-vent & TIGER channels)
  - `.cache/gems_work/ldgi_extra_8ch.npy` (`gems32.ldgi`, 8 label-free lineament-density, Gi*, Moran, Ricker, SVD channels)
  - `.cache/gems_work/fbgr_extra_12ch.npy` (`gems32.fbgr`, 12 label-free Fourier-UC, 4-block 214Bi radon & silica/potassic channels)
  - `.cache/gems_work/cfkc_extra_8ch.npy` (`gems32.cfkc`, 8 label-free 10m seamless DEM curvature, hillshade lineament, Perron-Royden chi-steepness/knickpoint & 1m openness/LRM channels)
  - `gems32.holdout` / `scripts/evaluate_holdout.py`
  - `gems32.emitter.emit` (`min_sep_px = 2.8` + `initial_mask` residual-coverage CELF)
  - `scripts/submission_writer.py` & `scripts/check_submission.py --strict-finite`
  - `gems32.release_gate`
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

os.environ.setdefault("GDAL_CACHEMAX", "32")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import rasterio
from scipy.ndimage import binary_dilation, binary_erosion, convolve, distance_transform_edt
from scipy.stats import rankdata

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from gems32 import cfkc, emitter, fbgr, features, holdout, ldgi, mdrc, metric, release_gate, spcp, submission, trhv  # noqa: E402
from gems32.paths import data_dir, downloads_dir, evidence_dir, work_dir  # noqa: E402
import submission_writer  # noqa: E402

TARGET_BUDGET = 37_654
B_COLLAR_PX = 2.0
AXIAL_SEP_PX = 2.8
SESSION_BRANCH = "arena/16f7dc72-apartgemsdoe3"


def peak_rss_mb() -> float:
    return round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0, 1)


def evaluate_detached_and_censored(
    pred_or_cells: np.ndarray | dict[str, np.ndarray],
    ctx: holdout.HoldoutContext,
    b_visible_px: float = 2.0,
    detach_min_px: float = 6.0,
    censor_hidden_px: float = 2.0,
    grid_n: int = 16,
    n_boot: int = 1000,
    seed: int = 20261027,
) -> dict:
    """Supplementary leak-free diagnostics on the exact same 8 holdout cells:
    1) `censored_d2`: applies `d_hidden > 2.0 px` to OOF predictions.
    2) `detached_600m`: scores ONLY withheld fault pixels >= 6.0 px (600 m) from visible faults.
    """
    h, w = ctx.foot.shape
    n_blocks = grid_n * grid_n
    fy, fx = np.nonzero(ctx.foot)
    active_blocks = np.unique(holdout._spatial_block_index(fy, fx, (h, w), grid_n))
    is_dict = isinstance(pred_or_cells, dict)
    base_mask = None if is_dict else (np.asarray(pred_or_cells, bool) & ctx.foot)

    tp_det = np.zeros(n_blocks, dtype=np.float64)
    fp_det = np.zeros(n_blocks, dtype=np.float64)
    fn_det = np.zeros(n_blocks, dtype=np.float64)
    n_det_pos = 0

    tp_cen = np.zeros(n_blocks, dtype=np.float64)
    fp_cen = np.zeros(n_blocks, dtype=np.float64)
    fn_cen = np.zeros(n_blocks, dtype=np.float64)
    n_cen_pos = 0

    for cell in ctx.cells:
        sl = cell.bbox
        r0, c0 = int(sl[0].start), int(sl[1].start)
        raw_in = np.asarray(pred_or_cells[cell.key], bool)[sl] if is_dict else base_mask[sl]
        p_sub = raw_in & cell.active_sub
        if b_visible_px > 0.0 and cell.d_vis_sub is not None:
            p_sub = p_sub & (cell.d_vis_sub > b_visible_px)

        ty, tx = cell.truth_coords
        if ty.size == 0:
            continue

        truth_sub = np.zeros(cell.active_sub.shape, dtype=bool)
        truth_sub[ty, tx] = True
        d_hid = distance_transform_edt(~truth_sub)
        p_cen = p_sub & (d_hid > censor_hidden_px)
        n_cen_pos += int(ty.size)
        t_blk = holdout._spatial_block_index(ty + r0, tx + c0, (h, w), grid_n)
        if p_cen.any():
            dp_cen = distance_transform_edt(~p_cen)
            tc_cen = metric.kernel(dp_cen[ty, tx]).astype(np.float64)
            np.add.at(tp_cen, t_blk, tc_cen)
            np.add.at(fn_cen, t_blk, 1.0 - tc_cen)
            py, px = np.nonzero(p_cen)
            p_blk = holdout._spatial_block_index(py + r0, px + c0, (h, w), grid_n)
            np.add.at(fp_cen, p_blk, (1.0 - cell.k_dg_sub[p_cen]).astype(np.float64))
        else:
            np.add.at(fn_cen, t_blk, 1.0)

        det_keep = cell.d_vis_sub[ty, tx] >= detach_min_px
        if det_keep.any():
            dty, dtx = ty[det_keep], tx[det_keep]
            n_det_pos += int(dty.size)
            det_truth = np.zeros(cell.active_sub.shape, dtype=bool)
            det_truth[dty, dtx] = True
            k_dg_det = metric.kernel(distance_transform_edt(~det_truth))
            p_det = p_sub & (cell.d_vis_sub >= (detach_min_px - 3.0))
            dt_blk = holdout._spatial_block_index(dty + r0, dtx + c0, (h, w), grid_n)
            if p_det.any():
                dp_det = distance_transform_edt(~p_det)
                tc_det = metric.kernel(dp_det[dty, dtx]).astype(np.float64)
                np.add.at(tp_det, dt_blk, tc_det)
                np.add.at(fn_det, dt_blk, 1.0 - tc_det)
                py, px = np.nonzero(p_det)
                p_blk = holdout._spatial_block_index(py + r0, px + c0, (h, w), grid_n)
                np.add.at(fp_det, p_blk, (1.0 - k_dg_det[p_det]).astype(np.float64))
            else:
                np.add.at(fn_det, dt_blk, 1.0)

    cen_dti, cen_ci, cen_boots = holdout._cluster_bootstrap_pooled_dti(
        tp_cen, fp_cen, fn_cen, active_blocks, n_boot=n_boot, seed=seed
    )
    det_dti, det_ci, det_boots = holdout._cluster_bootstrap_pooled_dti(
        tp_det, fp_det, fn_det, active_blocks, n_boot=n_boot, seed=seed
    )
    return {
        "censored_d2": {
            "dti": cen_dti,
            "ci95": cen_ci,
            "n_withheld_positives": n_cen_pos,
            "_boots": cen_boots,
        },
        "detached_600m": {
            "dti": det_dti,
            "ci95": det_ci,
            "n_withheld_positives": n_det_pos,
            "_boots": det_boots,
        },
    }


def paired_ci(boots_a: np.ndarray, boots_b: np.ndarray) -> dict:
    diff = np.asarray(boots_a, dtype=np.float64) - np.asarray(boots_b, dtype=np.float64)
    return {
        "mean_boot_delta": float(diff.mean()),
        "ci95": [float(np.percentile(diff, 2.5)), float(np.percentile(diff, 97.5))],
        "prob_positive": float((diff > 0.0).mean()),
    }


def _normalized_ranks(vec: np.ndarray) -> np.ndarray:
    r = rankdata(vec).astype(np.float32)
    r -= np.float32(r.mean())
    nrm = float(np.linalg.norm(r))
    return (r / np.float32(nrm)) if nrm > 0.0 else r


def collect_all_registry_entries(ddir: Path, exclude_shas: set[str] | None = None) -> tuple[dict[str, tuple[str, Path]], dict]:
    """Gather all unique-SHA256 rasters across focus sites + peer repos (508), extra scored (38), & data_manifest."""
    exclude_shas = exclude_shas or set()
    fman = json.loads((ROOT / "registry" / "focus_registry_manifest.json").read_text())
    eman_path = ROOT / "registry" / "extra_scored_manifest.json"
    eman = json.loads(eman_path.read_text()) if eman_path.exists() else {"rasters": []}
    dman = json.loads((ROOT / "registry" / "data_manifest.json").read_text())

    entries: dict[str, tuple[str, Path]] = {}
    for r in fman["rasters"]:
        if r.get("status") == "ok" and r["sha256"] not in exclude_shas:
            p = ROOT / r["local"]
            if p.exists():
                entries.setdefault(r["sha256"], (f"{r['repo']}:{r['path']}", p))
    for r in eman.get("rasters", []):
        if r.get("status") == "ok" and r["sha256"] not in exclude_shas:
            p = ROOT / r["local"]
            if p.exists():
                entries.setdefault(r["sha256"], (f"{r['repo']}:{r['path']}", p))
    for e in dman["files"]:
        if e["group"] == "scored" and e["sha256"] not in exclude_shas:
            p = ddir / e["dest"]
            if p.exists():
                entries.setdefault(e["sha256"], (f"manifest:{e['id']}", p))
    for p in sorted(downloads_dir().glob("*.tif")):
        sha = hashlib.sha256(p.read_bytes()).hexdigest()
        if sha not in exclude_shas:
            entries.setdefault(sha, (f"local:docs/downloads/{p.name}", p))

    counts = {
        "focus_and_peer_manifest_rasters": len(fman["rasters"]),
        "extra_scored_rasters": len(eman.get("rasters", [])),
        "total_source_entries": len(fman["rasters"]) + len(eman.get("rasters", [])),
        "unique_sha256_rasters": len(entries),
    }
    return entries, counts


def scan_full_registry(
    surface: np.ndarray,
    dots: np.ndarray | None,
    foot: np.ndarray,
    ddir: Path,
    exclude_shas: set[str] | None = None,
) -> dict:
    """Exact 100% full-footprint (`5,167,373` px) Spearman & <=3px directional overlap scan."""
    entries, src_counts = collect_all_registry_entries(ddir, exclude_shas=exclude_shas)
    rx_surf = _normalized_ranks(np.asarray(surface[foot], dtype=np.float64))
    rx_dots = _normalized_ranks(dots[foot].astype(np.float64)) if dots is not None else None

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

        if float(clean_foot.max() - clean_foot.min()) > 0.0:
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

        if len(rows) % 25 == 0:
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

    surf_passed = bool(rg_surf_comparisons) and all(
        c["measurable"] and not c["duplicate"] for c in rg_surf_comparisons
    )
    rg_surface = {
        "stage": "surface",
        "rule": "literal rho>0.90 OR directional overlap>0.70 on genuine discrete submissions (<=100k dots)",
        "passed": surf_passed,
        "stop": not surf_passed,
        "comparisons": rg_surf_comparisons,
    }
    rg_final = None
    if dots is not None:
        fin_passed = bool(rg_final_comparisons) and all(
            c["measurable"] and not c["duplicate"] for c in rg_final_comparisons
        )
        rg_final = {
            "stage": "final",
            "rule": "literal rho>0.90 OR directional overlap>0.70 on genuine discrete submissions (<=100k dots)",
            "passed": fin_passed,
            "stop": not fin_passed,
            "comparisons": rg_final_comparisons,
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
        "ultra_dense_or_continuous_over_70pct": sorted(
            [r for r in ultra_dense_or_surface if r["within_3px_fraction"] > 0.70],
            key=lambda r: -r["within_3px_fraction"],
        ),
        "release_gate_direct_surface": rg_surface,
        "release_gate_direct_final": rg_final,
        "top15_by_overlap": sorted(discrete_le100k, key=lambda r: -r["within_3px_fraction"])[:15],
        "top10_by_abs_spearman": sorted(non_lattice_all, key=lambda r: -abs(r["surface_spearman"]))[:10],
    }


def audit_nine_focus_sites_20261027(ctx: holdout.HoldoutContext, champ_mask: np.ndarray, apart3_mask: np.ndarray) -> dict:
    """Byte-verified audit of all 9 focus sites (`GEMSDOE24..36`) + peer repos at their 2026-10-27 commits."""
    fman = json.loads((ROOT / "registry" / "focus_registry_manifest.json").read_text())
    by_repo: dict[str, list[dict]] = {}
    for r in fman["rasters"]:
        if r.get("status") == "ok":
            by_repo.setdefault(r["repo"], []).append(r)

    yy, xx = np.mgrid[-3:4, -3:4]
    disk3 = (yy * yy + xx * xx) <= 9
    champ_near3 = binary_dilation(champ_mask, structure=disk3)
    apart3_near3 = binary_dilation(apart3_mask, structure=disk3)

    # Audit both the best ORGANIZER-CONFIRMED file per focus repo and the latest active file
    best_confirmed = {
        "GEMSDOE24": ("gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan.tif", 0.2477),
        "GEMSDOE25": ("gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif", 0.2600),
        "GEMSDOE27": ("gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan.tif", 0.2449),
        "GEMSDOE28": ("gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif", 0.2710),
        "GEMSDOE30": ("gemsdoe30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca.tif", 0.2600),
        "GEMSDOE31": ("gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-nan.tif", 0.2708),
        "GEMSDOE32": ("gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif", 0.2778),
        "GEMSDOE33": ("GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e.tif", 0.2632),
        "GEMSDOE36": ("gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif", 0.2750),
    }

    site_rows = []
    for repo, (fname, live_score) in best_confirmed.items():
        cands = [r for r in by_repo.get(repo, []) if fname in r["path"]]
        if not cands:
            cands = by_repo.get(repo, [])[:1]
        if not cands:
            continue
        rec = cands[0]
        p = ROOT / rec["local"]
        with rasterio.open(p) as ds:
            arr = ds.read(1)
            nd = ds.nodata
        whole_finite = bool(np.isfinite(arr).all())
        in_range = bool(np.nanmin(arr) >= 0.0 and np.nanmax(arr) <= 1.0)
        m = np.isfinite(arr) & (arr > 0) & ctx.foot
        n_dots = int(m.sum())
        on_cat = int((m & ctx.labels).sum())
        hr = holdout.evaluate_hide_and_recover(m, ctx, b_visible_px=0.0, n_boot=400, name=f"{repo}_best")
        sg = holdout.evaluate_sgmc_with_ci(m, ctx, n_boot=400, name=f"{repo}_best")
        ov_champ = float(champ_near3[m].mean()) if n_dots > 0 else 0.0
        ov_apart3 = float(apart3_near3[m].mean()) if n_dots > 0 else 0.0
        site_rows.append(
            {
                "repo": repo,
                "head_ref": fman["refs"].get(repo, "")[:12],
                "total_rasters_in_repo": len(by_repo.get(repo, [])),
                "inspected_path": rec["path"],
                "sha256": rec["sha256"],
                "organizer_confirmed_dti": live_score,
                "emitted_dots": n_dots,
                "on_catalogue_dots": on_cat,
                "whole_array_finite": whole_finite,
                "range_0_1": in_range,
                "nodata_tag": str(nd),
                "static_hide_recover_dti": round(hr["pooled_dti"], 6),
                "static_hide_recover_ci95": [round(x, 6) for x in hr["ci95_cluster_bootstrap"]],
                "sgmc_raw_dti": round(sg["sgmc_raw_pooled_dti"], 6),
                "sgmc_prevalence_calibrated_dti": round(sg["sgmc_prevalence_calibrated_dti"], 6),
                "sgmc_calibrated_ci95": [round(x, 6) for x in sg["sgmc_calibrated_ci95"]],
                "within_3px_of_02778_champion": round(ov_champ, 4),
                "within_3px_of_apart3_cfkc": round(ov_apart3, 4),
            }
        )
    return {
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total_manifest_rasters": len(fman["rasters"]),
        "refs": fman["refs"],
        "sites": site_rows,
    }


def render_diagnostic_figure(
    out_path: Path,
    champ_clean: dict,
    exp1_clean: dict,
    exp2_clean: dict,
    exp3_clean: dict,
    cfkc_stack: np.ndarray,
    exp3_dots: np.ndarray,
    lidar_valid: np.ndarray,
    foot: np.ndarray,
    labels: np.ndarray,
    spatial_alloc: dict,
) -> None:
    """Render publication-grade 4-panel diagnostic figure `docs/assets/fig_apart3_cfkc_dhc.png`."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(2, 2, figsize=(13.6, 10.4), dpi=135)
    fig.patch.set_facecolor("#0f172a")

    for ax in axes.ravel():
        ax.set_facecolor("#1e293b")
        ax.tick_params(colors="#cbd5e1", labelsize=9)
        for sp_line in ax.spines.values():
            sp_line.set_color("#475569")

    # Panel A: Dual-Benchmark Pareto Plane
    ax0 = axes[0, 0]
    pts = [
        ("0.2778 Champion\n(H33-2-B2 / d2.8 parent)", champ_clean, "#f59e0b", "D", 95),
        ("EXP1: Dual-Cover 91/77\n(10m DEM + Chi, 1-Horizon)", exp1_clean, "#a78bfa", "^", 95),
        ("EXP2: Hybrid 91/77 + 63ch\n(1-Horizon Crest d=2.8)", exp2_clean, "#38bdf8", "s", 95),
        ("EXP3: H-APART3-1 CFKC-DHC\n(Stationary Dual-Horizon d=2.8)", exp3_clean, "#10b981", "*", 220),
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
    ax0.set_title("A. Dual-Benchmark Pareto Dominance (Hide-and-Recover vs SGMC-cal)", color="#f8fafc", fontsize=11, fontweight="bold")
    ax0.legend(loc="best", fontsize=8, facecolor="#0f172a", edgecolor="#475569", labelcolor="#f8fafc")

    # Panel B: 3-Experiment Ablation Across Holdout Slices
    ax1 = axes[0, 1]
    metrics_keys = [
        ("Hide&Rec\nv3.0", lambda d: d["hide_and_recover_v3"]["pooled_dti"]),
        ("Censored\nd_hid>2px", lambda d: d["censorship_matched_d2"]["pooled_dti"]),
        ("Detached\n>=600m", lambda d: d["detached_600m_segments"]["pooled_dti"]),
        ("SGMC-cal\noff-cat", lambda d: d["sgmc_off_catalogue_v3"]["prevalence_calibrated_dti"]),
    ]
    arms_bar = [
        ("0.2778 Champ", champ_clean, "#f59e0b"),
        ("EXP1 CFKC-91", exp1_clean, "#a78bfa"),
        ("EXP2 Hybrid", exp2_clean, "#38bdf8"),
        ("EXP3 CFKC-DHC", exp3_clean, "#10b981"),
    ]
    x_pos = np.arange(len(metrics_keys))
    width = 0.19
    for idx, (aname, adict, col) in enumerate(arms_bar):
        vals = [fn(adict) for _, fn in metrics_keys]
        ax1.bar(x_pos + (idx - 1.5) * width, vals, width=width, color=col, label=aname, alpha=0.90)
    ax1.set_xticks(x_pos)
    ax1.set_xticklabels([m[0] for m in metrics_keys], color="#e2e8f0", fontsize=9)
    ax1.set_ylabel("Pooled DTI (alpha=0.2, beta=0.8, 300 m)", color="#e2e8f0", fontsize=10)
    ax1.set_title("B. 3-Experiment Ablation Across All Four Holdout Slices", color="#f8fafc", fontsize=11, fontweight="bold")
    ax1.legend(loc="upper right", fontsize=8, facecolor="#0f172a", edgecolor="#475569", labelcolor="#f8fafc")

    # Panel C: Label-Free CFKC Seam-Free 10m Curvature + Fluvial Chi-Steepness + Basement Carrier (`cfkc_stack[:, :, 6]`)
    ax2 = axes[1, 0]
    step = 6
    cfkc_ds = np.where(foot[::step, ::step], np.asarray(cfkc_stack[::step, ::step, 6], dtype=np.float32), np.nan)
    im = ax2.imshow(cfkc_ds, cmap="magma", vmin=0.0, vmax=0.95)
    ly, lx = np.nonzero(labels[::step, ::step])
    ax2.scatter(lx, ly, s=0.15, c="#38bdf8", alpha=0.35, label="Mapped catalogue")
    ax2.set_title("C. CFKC 100% Seam-Free Carrier (10m Curv + Chi k_sn + Fourier UC)", color="#f8fafc", fontsize=9.3, fontweight="bold")
    ax2.set_xticks([])
    ax2.set_yticks([])
    cb = fig.colorbar(im, ax=ax2, fraction=0.042, pad=0.03)
    cb.ax.tick_params(colors="#cbd5e1", labelsize=8)

    # Panel D: Emitted Dots (`M_Full` inside 1 m LiDAR vs `M_Sub` inside 24.66% LiDAR Gap)
    ax3 = axes[1, 1]
    bg = np.where(foot[::step, ::step], np.where(lidar_valid[::step, ::step], 0.14, 0.28), np.nan)
    ax3.imshow(bg, cmap="Greys", vmin=0.0, vmax=1.0)
    in_li_y, in_li_x = np.nonzero(exp3_dots & lidar_valid)
    gap_y, gap_x = np.nonzero(exp3_dots & ~lidar_valid)
    ax3.scatter(in_li_x[::4] / step, in_li_y[::4] / step, s=0.45, c="#38bdf8", alpha=0.65, label=f"LiDAR Covered ({in_li_y.size:,}d)")
    ax3.scatter(gap_x[::3] / step, gap_y[::3] / step, s=0.65, c="#10b981", alpha=0.85, label=f"LiDAR Gap 10m/Chi ({gap_y.size:,}d)")
    ax3.set_title(
        f"D. EXP3 CFKC-DHC 37,654d (Gap={spatial_alloc['lidar_gap_dot_frac']*100:.1f}%, >1.5km={spatial_alloc['far_gt_15px_frac']*100:.1f}%, Clump={spatial_alloc['clump_ge3_nbr3_frac']*100:.2f}%)",
        color="#f8fafc",
        fontsize=9.3,
        fontweight="bold",
    )
    ax3.set_xticks([])
    ax3.set_yticks([])
    ax3.legend(loc="lower right", fontsize=8, facecolor="#0f172a", edgecolor="#475569", labelcolor="#f8fafc", markerscale=5.0)

    fig.suptitle(
        "ApartGEMSDOE3 Lane H-APART3-1 (CFKC-DHC): Chi-Fluvial Knickzone, 10m Seamless Curvature & Stationary Dual-Horizon Cover",
        color="#f8fafc",
        fontsize=12.2,
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
    cfkc_path = wdir / "cfkc_extra_8ch.npy"

    print(f"[1/8] Opening/verifying 91-channel stack (35 base + 20 SPCP + 8 TRHV + 8 LDGI + 12 FBGR + 8 CFKC, RSS={peak_rss_mb()} MB)...", flush=True)
    _, cfkc_receipt = cfkc.build_cfkc_extra_stack(ddir=ddir, wdir=wdir, out_path=cfkc_path, force=("--rebuild-cfkc" in sys.argv), log=lambda m: print(m, flush=True))
    (ROOT / "registry" / "cfkc_feature_receipt.json").write_text(json.dumps(cfkc_receipt, indent=2) + "\n")

    base_stack = np.load(base_stack_path, mmap_mode="r")
    spcp_stack = np.load(spcp_path, mmap_mode="r")
    trhv_stack = np.load(trhv_path, mmap_mode="r")
    ldgi_stack = np.load(ldgi_path, mmap_mode="r")
    fbgr_stack = np.load(fbgr_path, mmap_mode="r")
    cfkc_stack = np.load(cfkc_path, mmap_mode="r")

    print(f"[2/8] Loading HoldoutContext & running 91-channel Protocol Rule 4 Leakage Canary (RSS={peak_rss_mb()} MB)...", flush=True)
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

    canary = cfkc.run_leakage_canary_91ch(
        base_stack, spcp_stack, trhv_stack, ldgi_stack, fbgr_stack, cfkc_stack, list(features.CHANNELS), ctx, max_auc=0.90
    )
    print(
        f"      Canary passed={canary['passed']} | n={canary['n_features_tested']} | "
        f"worst={canary['worst_channel']} ({canary['max_oriented_auc']:.5f})",
        flush=True,
    )
    if not canary["passed"]:
        raise SystemExit(f"STOP: Leakage canary failed ({canary['worst_channel']} AUC={canary['max_oriented_auc']})!")

    # Evaluate 0.2778 Champion Baseline (`H33-2-B2`) on the identical holdout suite
    champ_path = ROOT / ".cache" / "registry" / "GEMSDOE32" / "docs" / "downloads" / "gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif"
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
    # FIT SHARED FOLD-LOCAL OOF MODELS (`M_Full` 91-ch, `M_Sub` 77-ch, & `SARPU` 63-ch)
    # =========================================================================
    print(f"[3/8] Fitting fold-local OOF M_Full (91-ch), M_Sub (77-ch pure non-LiDAR), & SAR-PU (63-ch) across 8 cells (RSS={peak_rss_mb()} MB)...", flush=True)
    p_dual91_live = np.zeros(ctx.foot.shape, dtype=np.float32)
    s63_live = np.zeros(ctx.foot.shape, dtype=np.float32)

    for cell in ctx.cells:
        pred_reg = (ctx.quad == cell.fold) & ctx.foot
        tr = fold_train[cell.fold]
        vis_tr = cell.visible_full & tr

        p_d91_cache = wdir / f"apart3_cell_{cell.key}_mdual91.npy"
        s63_cache = wdir / f"apart3_cell_{cell.key}_sarpu63.npy"

        if p_d91_cache.exists() and "--rerun-models" not in sys.argv:
            pd91_cell = np.load(p_d91_cache)
        else:
            clf_full = cfkc.fit_cfkc_classifier(
                base_stack, spcp_stack, trhv_stack, ldgi_stack, fbgr_stack, cfkc_stack,
                tr, vis_tr, ctx.foot, col_indices=None,
                seed=5300 + cell.seed * 10 + cell.fold,
            )
            clf_sub = cfkc.fit_cfkc_classifier(
                base_stack, spcp_stack, trhv_stack, ldgi_stack, fbgr_stack, cfkc_stack,
                tr, vis_tr, ctx.foot, col_indices=cfkc.CFKC_MSUB_COL_INDICES,
                seed=6300 + cell.seed * 10 + cell.fold,
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

            pf_all = cfkc.predict_chunked_cfkc(
                clf_full, base_stack, spcp_stack, trhv_stack, ldgi_stack, fbgr_stack, cfkc_stack,
                pred_reg | cal_mask_li, col_indices=None,
            )
            ps_all = cfkc.predict_chunked_cfkc(
                clf_sub, base_stack, spcp_stack, trhv_stack, ldgi_stack, fbgr_stack, cfkc_stack,
                (pred_reg & lidar_gap) | cal_mask_gp, col_indices=cfkc.CFKC_MSUB_COL_INDICES,
            )
            del clf_full, clf_sub

            pd_all = fbgr.calibrate_msub_to_mfull_quantiles(
                pf_all, ps_all, cal_mask_li, cal_mask_gp, pred_reg & lidar_gap, blend_raw=0.25
            )
            pd91_cell = np.where(pred_reg, pd_all, np.float32(0.0)).astype(np.float32)
            np.save(p_d91_cache, pd91_cell)
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

        p_dual91_live[pred_reg] += np.float32(0.5) * pd91_cell[pred_reg]
        s63_live[pred_reg] += np.float32(0.5) * s63_cell[pred_reg]
        del pd91_cell, s63_cell
        gc.collect()
        print(f"      Finished OOF cell {cell.key} (RSS={peak_rss_mb()} MB)", flush=True)

    # =========================================================================
    # EXPERIMENT 1 / 3: Dual-Cover 91/77 (`M_Full` + `M_Sub`) Single-Horizon 1-px Crest (`EXP1_CFKC_DUALCOVER_91`)
    # =========================================================================
    print(f"[4/8] Experiment 1/3: EXP1_CFKC_DUALCOVER_91 (Dual-Cover 91/77 + 1-px Crest d=2.8, RSS={peak_rss_mb()} MB)...", flush=True)
    exp1_cells: dict[str, np.ndarray] = {}
    for cell in ctx.cells:
        sl = cell.bbox
        pred_reg = (ctx.quad == cell.fold) & ctx.foot
        elig_sub = (fold_domain[cell.fold] & ~binary_dilation(cell.visible_full, structure=disk2))[sl]
        b_cell = int(round(TARGET_BUDGET * (elig_sub.sum() / n_elig_full)))
        pd91_cell = np.load(wdir / f"apart3_cell_{cell.key}_mdual91.npy")
        s_cell = cfkc.build_exp1_dualcover_surface(
            pd91_cell, cfkc_stack, trhv_stack, cell.visible_full, ctx.foot, region_mask=pred_reg
        )
        d_sub, _ = cfkc.emit_crest_submodular_sep(
            s_cell[sl], cell.visible_full[sl], elig_sub, ctx.foot[sl], budget=b_cell, min_sep_px=AXIAL_SEP_PX
        )
        d_full = np.zeros(ctx.foot.shape, dtype=bool)
        d_full[sl] = d_sub
        exp1_cells[cell.key] = d_full
        del pd91_cell, s_cell
        gc.collect()

    s1_full_surf = cfkc.build_exp1_dualcover_surface(
        p_dual91_live, cfkc_stack, trhv_stack, ctx.labels, ctx.foot
    )
    exp1_full_dots, _ = cfkc.emit_crest_submodular_sep(
        s1_full_surf, ctx.labels, elig_full, ctx.foot, budget=TARGET_BUDGET, min_sep_px=AXIAL_SEP_PX
    )
    del s1_full_surf
    exp1_res = _eval_arm("EXP1_CFKC_DUALCOVER_91", exp1_cells, exp1_full_dots)
    del exp1_cells, exp1_full_dots
    gc.collect()
    print(
        f"      EXP1_CFKC_DUALCOVER_91: HR={exp1_res['hr']['pooled_dti']:.5f} "
        f"Det={exp1_res['sup']['detached_600m']['dti']:.5f} "
        f"SGMC_cal={exp1_res['sg']['sgmc_prevalence_calibrated_dti']:.5f} (RSS={peak_rss_mb()} MB)",
        flush=True,
    )

    # =========================================================================
    # EXPERIMENT 2 / 3: Hybrid Dual-Cover 91/77 + 63-ch SAR-PU Single-Horizon Crest (`EXP2_CFKC_HYBRID_CREST`)
    # =========================================================================
    print(f"[5/8] Experiment 2/3: EXP2_CFKC_HYBRID_CREST (Hybrid 91/77 + 63ch SAR-PU 1-px Crest d=2.8, RSS={peak_rss_mb()} MB)...", flush=True)
    exp2_cells: dict[str, np.ndarray] = {}
    for cell in ctx.cells:
        sl = cell.bbox
        pred_reg = (ctx.quad == cell.fold) & ctx.foot
        elig_sub = (fold_domain[cell.fold] & ~binary_dilation(cell.visible_full, structure=disk2))[sl]
        b_cell = int(round(TARGET_BUDGET * (elig_sub.sum() / n_elig_full)))
        pd91_cell = np.load(wdir / f"apart3_cell_{cell.key}_mdual91.npy")
        s63_cell = np.load(wdir / f"apart3_cell_{cell.key}_sarpu63.npy")
        s_cell = cfkc.build_exp2_hybrid_surface(
            s63_cell, pd91_cell, cfkc_stack, cell.visible_full, ctx.foot, region_mask=pred_reg
        )
        d_sub, _ = cfkc.emit_crest_submodular_sep(
            s_cell[sl], cell.visible_full[sl], elig_sub, ctx.foot[sl], budget=b_cell, min_sep_px=AXIAL_SEP_PX
        )
        d_full = np.zeros(ctx.foot.shape, dtype=bool)
        d_full[sl] = d_sub
        exp2_cells[cell.key] = d_full
        del pd91_cell, s63_cell, s_cell
        gc.collect()

    s2_full_surf = cfkc.build_exp2_hybrid_surface(
        s63_live, p_dual91_live, cfkc_stack, ctx.labels, ctx.foot
    )
    exp2_full_dots, _ = cfkc.emit_crest_submodular_sep(
        s2_full_surf, ctx.labels, elig_full, ctx.foot, budget=TARGET_BUDGET, min_sep_px=AXIAL_SEP_PX
    )
    exp2_res = _eval_arm("EXP2_CFKC_HYBRID_CREST", exp2_cells, exp2_full_dots)
    del exp2_cells, exp2_full_dots
    gc.collect()
    print(
        f"      EXP2_CFKC_HYBRID_CREST: HR={exp2_res['hr']['pooled_dti']:.5f} "
        f"Det={exp2_res['sup']['detached_600m']['dti']:.5f} "
        f"SGMC_cal={exp2_res['sg']['sgmc_prevalence_calibrated_dti']:.5f} (RSS={peak_rss_mb()} MB)",
        flush=True,
    )

    # =========================================================================
    # EXPERIMENT 3 / 3: Stationary Dual-Horizon 1-px Crest CELF (`EXP3_CFKC_STATIONARY_DHC`)
    # =========================================================================
    print(f"[6/8] Experiment 3/3: EXP3_CFKC_STATIONARY_DHC (Stationary Dual-Horizon f1=0.80, d=2.8, RSS={peak_rss_mb()} MB)...", flush=True)
    crest_b_full = np.asarray(cfkc_stack[:, :, 7], dtype=np.float32)
    exp3_cells: dict[str, np.ndarray] = {}
    for cell in ctx.cells:
        sl = cell.bbox
        pred_reg = (ctx.quad == cell.fold) & ctx.foot
        elig_sub = (fold_domain[cell.fold] & ~binary_dilation(cell.visible_full, structure=disk2))[sl]
        b_cell = int(round(TARGET_BUDGET * (elig_sub.sum() / n_elig_full)))
        pd91_cell = np.load(wdir / f"apart3_cell_{cell.key}_mdual91.npy")
        s63_cell = np.load(wdir / f"apart3_cell_{cell.key}_sarpu63.npy")
        s_cell = cfkc.build_exp2_hybrid_surface(
            s63_cell, pd91_cell, cfkc_stack, cell.visible_full, ctx.foot, region_mask=pred_reg
        )
        d_sub, _ = cfkc.emit_stationary_dual_horizon_cfkc(
            s_cell[sl],
            crest_b_full[sl],
            cell.visible_full[sl],
            elig_sub,
            ctx.foot[sl],
            d_vis=cell.d_vis_sub,
            budget=b_cell,
            f_stage1=cfkc.STATIONARY_STAGE1_FRAC,
            w_s1=cfkc.STATIONARY_W_S1,
            min_sep_px=AXIAL_SEP_PX,
        )
        d_full = np.zeros(ctx.foot.shape, dtype=bool)
        d_full[sl] = d_sub
        exp3_cells[cell.key] = d_full
        del pd91_cell, s63_cell, s_cell
        gc.collect()

    exp3_belief_surface = cfkc.build_stationary_dual_horizon_belief_surface(
        s2_full_surf,
        crest_b_full,
        ctx.labels,
        ctx.foot,
        f_stage1=cfkc.STATIONARY_STAGE1_FRAC,
        w_s1=cfkc.STATIONARY_W_S1,
    )

    # Protocol Rule 1 STEP A: Check continuous surface BEFORE final dot placement!
    print(f"[7/8] Running Pre-Placement Continuous Surface Spearman Check across full registry (RSS={peak_rss_mb()} MB)...", flush=True)
    pre_scan = scan_full_registry(exp3_belief_surface, None, ctx.foot, ddir)
    print(
        f"      Pre-placement surface passed={pre_scan['genuine_surface_passed']} | "
        f"unique_checked={pre_scan['n_unique_rasters_checked']} | "
        f"max |Spearman|={abs(pre_scan['worst_genuine_surface']['surface_spearman']):.5f} "
        f"({pre_scan['worst_genuine_surface']['name']})",
        flush=True,
    )
    if not pre_scan["genuine_surface_passed"]:
        raise SystemExit(f"STOP: Pre-placement continuous surface Spearman > 0.90: {pre_scan['worst_genuine_surface']}")

    exp3_full_dots, exp3_emit_log = cfkc.emit_stationary_dual_horizon_cfkc(
        s2_full_surf,
        crest_b_full,
        ctx.labels,
        elig_full,
        ctx.foot,
        budget=TARGET_BUDGET,
        f_stage1=cfkc.STATIONARY_STAGE1_FRAC,
        w_s1=cfkc.STATIONARY_W_S1,
        min_sep_px=AXIAL_SEP_PX,
    )
    del s2_full_surf, crest_b_full, p_dual91_live, s63_live
    exp3_res = _eval_arm("EXP3_CFKC_STATIONARY_DHC", exp3_cells, exp3_full_dots)
    del exp3_cells
    gc.collect()
    print(
        f"      EXP3_CFKC_STATIONARY_DHC: HR={exp3_res['hr']['pooled_dti']:.5f} "
        f"Cen={exp3_res['sup']['censored_d2']['dti']:.5f} "
        f"Det={exp3_res['sup']['detached_600m']['dti']:.5f} "
        f"SGMC_raw={exp3_res['sg']['sgmc_raw_pooled_dti']:.5f} "
        f"SGMC_cal={exp3_res['sg']['sgmc_prevalence_calibrated_dti']:.5f} | "
        f"dots={int(exp3_full_dots.sum())} (s1={exp3_emit_log['stage1_dots']}, s2={exp3_emit_log['stage2_added_dots']}, RSS={peak_rss_mb()} MB)",
        flush=True,
    )

    # Write validated unique GeoTIFF bundle via canonical `scripts/submission_writer.py`
    ts_tag = "20261027T215000Z"
    slug = "apart3-h-apart3-1-cfkc-dhc-37654"
    sub_note = (
        f"ApartGEMSDOE3 H-APART3-1 CFKC-DHC 37654d B2 d2.8 | "
        f"HR={exp3_res['hr']['pooled_dti']:.4f} SGMC={exp3_res['sg']['sgmc_prevalence_calibrated_dti']:.4f}"
    )
    assert len(sub_note) <= 140, f"Submission note > 140 chars: {len(sub_note)}"

    bundle = submission_writer.write_validated_submission(
        exp3_full_dots,
        slug=slug,
        candidate_meta={
            "candidate_id": "H-APART3-1-CFKC-DHC",
            "description": (
                f"H-APART3-1 Chi-Fluvial Knickzone, 10m Seamless Bedrock Curvature & "
                f"Fourier-Radon Stationary Dual-Horizon Cover ({int(exp3_full_dots.sum()):,} dots, B=2, d=2.8)"
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
    digest8 = bundle["content_digest8"]
    sub_name = f"APARTGEMSDOE3-CFKC-DHC-{digest8.upper()}"
    audit_sidecar_name = f"gemsdoe32-{slug}-{ts_tag}-{digest8}-audit.json"
    zeros_tif_path = downloads_dir() / bundle["zeros_tif"]["filename"]
    zeros_sha256 = bundle["zeros_tif"]["sha256"]

    # Protocol Rule 1 STEP B: Final-Dot Full-Registry Uniqueness Scan
    print(f"[8/8] Running Final-Dot Uniqueness Scan across focus + peer + extra registries (RSS={peak_rss_mb()} MB)...", flush=True)
    final_scan = scan_full_registry(
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
        f"literal lattice={final_scan['worst_literal_overlap']['within_3px_fraction']:.4f} (RSS={peak_rss_mb()} MB)",
        flush=True,
    )
    if not final_scan["genuine_final_dots_passed"]:
        raise SystemExit(f"STOP: Final-dot genuine registry uniqueness failed: {final_scan['worst_genuine_overlap']}")

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

    eval_cli_out = evidence_dir() / "apart3_cfkc_static_evaluator_receipt.json"
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
            "H-APART3-1-CFKC-DHC-static",
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
    (evidence_dir() / "nine_site_refreshed_audit_20261027.json").write_text(
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

    d_full_labels = distance_transform_edt(~ctx.labels).astype(np.float32)
    d_dots = d_full_labels[exp3_full_dots]
    del d_full_labels

    b15 = np.asarray(base_stack[:, :, 14], dtype=np.float32)
    b19 = np.asarray(base_stack[:, :, 18], dtype=np.float32)
    flat_basin_frac = float(((b19[exp3_full_dots] < 2.0) & (b15[exp3_full_dots] > 300.0)).mean())

    spatial_alloc = {
        "stationary_formula_no_eta_switch": True,
        "f_stage1": cfkc.STATIONARY_STAGE1_FRAC,
        "w_s1": cfkc.STATIONARY_W_S1,
        "min_sep_px": AXIAL_SEP_PX,
        "stage1_near_extension_dots": exp3_emit_log["stage1_dots"],
        "stage2_far_discovery_dots": exp3_emit_log["stage2_added_dots"],
        "mfull_in_lidar_dots": int((exp3_full_dots & lidar_valid).sum()),
        "msub_in_lidar_gap_dots": int((exp3_full_dots & lidar_gap).sum()),
        "lidar_gap_dot_frac": round(float((exp3_full_dots & lidar_gap).sum() / max(int(exp3_full_dots.sum()), 1)), 6),
        "clump_ge3_nbr3_frac": round(float((nbr_cnt >= 3).mean()), 6),
        "mean_nbr_within_3px": round(float(nbr_cnt.mean()), 6),
        "footprint_300m_kernel_coverage": round(cov_300m, 6),
        "flat_basin_dot_frac": round(flat_basin_frac, 6),
        "le_2px_on_or_flank_frac": round(float((d_dots <= 2.0).mean()), 6),
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
        "evaluator_version": exp3_res["hr"]["evaluator_version"],
        "n_withheld_positives": exp3_res["hr"]["n_withheld_positives"],
        "dti": exp3_res["hr"]["pooled_dti"],
        "ci95": exp3_res["hr"]["ci95_cluster_bootstrap"],
    }
    incumbent_for_gate = {
        "evaluator_version": champ_hr["evaluator_version"],
        "n_withheld_positives": champ_hr["n_withheld_positives"],
        "dti": champ_hr["pooled_dti"],
        "ci95": champ_hr["ci95_cluster_bootstrap"],
    }
    gate_decision = release_gate.promotion_decision(
        lane="H-APART3-1 (CFKC-DHC): Chi-Fluvial Knickzone, 10m Seamless Bedrock Curvature & Fourier-Radon Dual-Horizon Cover",
        surface_check=final_scan["release_gate_direct_surface"],
        final_check=final_scan["release_gate_direct_final"],
        canary_aucs=[r["oriented_auc"] for r in canary["per_channel"]],
        holdout=holdout_for_gate,
        incumbent=incumbent_for_gate,
        same_evaluation=True,
        validator=validator_flags,
        paired_delta_ci95=paired_hr_vs_champ["ci95"],
    )

    final_verdict = gate_decision["verdict"]
    ok_submit = bool(final_verdict == "promote")

    def _clean_arm(res: dict) -> dict:
        return {
            "name": res["name"],
            "full_map_dots": res["full_dots"],
            "hide_and_recover_v3": {
                "label": "HOLDOUT-DTI",
                "evaluator_version": res["hr"]["evaluator_version"],
                "n_withheld_positives": res["hr"]["n_withheld_positives"],
                "pooled_dti": round(res["hr"]["pooled_dti"], 6),
                "ci95": [round(x, 6) for x in res["hr"]["ci95_cluster_bootstrap"]],
                "per_quadrant_dti": {k: round(v, 6) for k, v in res["hr"]["per_quadrant_dti"].items()},
            },
            "censorship_matched_d2": {
                "label": "HOLDOUT-DTI (d_hidden > 2 px censorship-matched)",
                "n_withheld_positives": res["sup"]["censored_d2"]["n_withheld_positives"],
                "pooled_dti": round(res["sup"]["censored_d2"]["dti"], 6),
                "ci95": [round(x, 6) for x in res["sup"]["censored_d2"]["ci95"]],
            },
            "detached_600m_segments": {
                "label": "HOLDOUT-DTI (detached >= 600 m withheld segments)",
                "n_withheld_positives": res["sup"]["detached_600m"]["n_withheld_positives"],
                "pooled_dti": round(res["sup"]["detached_600m"]["dti"], 6),
                "ci95": [round(x, 6) for x in res["sup"]["detached_600m"]["ci95"]],
            },
            "sgmc_off_catalogue_v3": {
                "label": "HOLDOUT-DTI (off-catalogue USGS SGMC > 300 m, zero SGMC supervision)",
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

    fig_path = ROOT / "docs" / "assets" / "fig_apart3_cfkc_dhc.png"
    render_diagnostic_figure(
        fig_path,
        champ_clean,
        exp1_clean,
        exp2_clean,
        exp3_clean,
        cfkc_stack,
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
        "cfkc_feature_receipt": cfkc_receipt,
        "leakage_canary": canary,
        "baselines": {
            "CHAMPION_02778": champ_clean,
        },
        "experiments": {
            "EXP1_CFKC_DUALCOVER_91": exp1_clean,
            "EXP2_CFKC_HYBRID_CREST": exp2_clean,
            "EXP3_CFKC_STATIONARY_DHC": exp3_clean,
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
    (evidence_dir() / "apart3_cfkc_dhc_experiments.json").write_text(json.dumps(experiments_summary, indent=2) + "\n")

    run_card = {
        "schema_version": "gems-parallel-runcard-v3",
        "session_branch": SESSION_BRANCH,
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "candidate_id": "H-APART3-1-CFKC-DHC",
        "hypothesis": (
            "H-APART3-1 (CFKC-DHC): Unmapped geothermal-indicative faults across the Great Basin (both inside the "
            "24.66% 1 m LiDAR gap and in unmapped far-field range-front/intrabasin settings) are jointly resolved by "
            "(1) 100%-coverage USGS 3DEP 10 m seamless DEM bedrock profile curvature, slope variability, and "
            "aspect-coherent hillshade lineaments (`topo_10m_derived_100m_u8.tif`), (2) Perron-Royden (2013) fluvial "
            "chi-steepness (`k_sn`) and transient knickpoint step height (`step_max_x1000`, `knick_n`) projected from "
            "incised footwall canyons onto adjacent 200-500 m range-front fault corridors and corroborated by 2D FFT "
            "upward-continued (`z = 500 m, 2,000 m`) gravity/magnetic basement steps, 4-block standardized GeoDAWN "
            "214Bi radon crests, and GDR #1391 2-m thermal/sinter plumes, and (3) a 91-ch/77-ch Dual-Cover + 63-ch "
            "SAR-PU ensemble packed via Stationary Dual-Horizon 1-px Crest Residual-Coverage CELF (`f_1 = 0.80`, "
            "`f_2 = 0.20`, `min_sep_px = 2.8`, `B = 2.0`), fixing both IR-48-CCAA-01 and IR-48-FARFIELD-01."
        ),
        "mechanism": (
            f"91 label-free channels (35 template + 20 SPCP + 8 TRHV + 8 LDGI + 12 FBGR + 8 new CFKC 10m-DEM/fluvial-chi/1m-openness "
            f"channels) -> 4-quadrant 1.5 km-collared OOF Dual-Cover classifiers (91-ch M_Full inside 75.34% 1 m LiDAR + "
            f"quantile-calibrated 77-ch strictly 1m-LiDAR-free M_Sub inside 24.66% LiDAR gap) + 63-ch SAR-PU ensemble -> "
            f"Stationary Dual-Horizon 1-px Crest CELF (`f_stage1=0.80`, `min_sep_px=2.8`, `B=2.0`) emitting {int(exp3_full_dots.sum()):,} "
            f"binary {{0,1}} dots ({spatial_alloc['stage1_near_extension_dots']:,} Stage-1 near/extension + "
            f"{spatial_alloc['stage2_far_discovery_dots']:,} Stage-2 far-field discovery; {spatial_alloc['msub_in_lidar_gap_dots']:,} dots = "
            f"{spatial_alloc['lidar_gap_dot_frac']*100:.1f}% in LiDAR gap; >1.5 km share = {spatial_alloc['far_gt_15px_frac']*100:.1f}%; "
            f"Clump>=3 = {spatial_alloc['clump_ge3_nbr3_frac']*100:.2f}%)."
        ),
        "named_non_fault_mimic": (
            "(1) Differential erosion of unfaulted volcanic caprock ledges (welded ash-flow tuffs / basalt mesas) "
            "creating non-tectonic lithologic knickpoints in fluvial chi-steepness and 10 m curvature (de-confounded "
            "by requiring upward-continued z=500m/2km gravity & RTP magnetic basement-step concordance on knickpoint steps); "
            "(2) Pleistocene Lake Lahontan wave-cut shorelines (1,200-1,338 m) and US Census TIGER highway/railroad prism "
            "cuts (de-confounded by contour-orthogonality filtering and 180 m TIGER road veto); "
            "(3) Evaporite playa uranium accumulation and GeoDAWN contractor flight-block seams (removed by 4-block "
            "median/MAD standardization and eU-on-eTh regression + flat conductive basin sink masking)."
        ),
        "named_non_fault_mimic_process": (
            "(1) Differential erosion of unfaulted volcanic caprock ledges (welded ash-flow tuffs / basalt mesas) "
            "creating non-tectonic lithologic knickpoints in fluvial chi-steepness and 10 m curvature (de-confounded "
            "by requiring upward-continued z=500m/2km gravity & RTP magnetic basement-step concordance on knickpoint steps); "
            "(2) Pleistocene Lake Lahontan wave-cut shorelines (1,200-1,338 m) and US Census TIGER highway/railroad prism "
            "cuts (de-confounded by contour-orthogonality filtering and 180 m TIGER road veto); "
            "(3) Evaporite playa uranium accumulation and GeoDAWN contractor flight-block seams (removed by 4-block "
            "median/MAD standardization and eU-on-eTh regression + flat conductive basin sink masking)."
        ),
        "experiments_used": 3,
        "experiments_budget_cap": 3,
        "runtime_seconds": elapsed,
        "peak_rss_mb": max_rss,
        "holdout_dti": {
            "primary_hide_and_recover": exp3_clean["hide_and_recover_v3"],
            "exp1_cfkc_dualcover_91_hide_and_recover": exp1_clean["hide_and_recover_v3"],
            "exp2_cfkc_hybrid_crest_hide_and_recover": exp2_clean["hide_and_recover_v3"],
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
            "primary_zeros_tif": f"docs/downloads/{bundle['zeros_tif']['filename']}",
            "primary_zeros_sha256": zeros_sha256,
            "primary_zeros_bytes": bundle["zeros_tif"]["size_bytes"],
            "nan_companion_tif": f"docs/downloads/{bundle['nan_tif']['filename']}",
            "nan_companion_sha256": bundle["nan_tif"]["sha256"],
            "zip_archive": f"docs/downloads/{bundle['zeros_zip']['filename']}",
            "zip_sha256": bundle["zeros_zip"]["sha256"],
            "audit_json": f"docs/downloads/{audit_sidecar_name}",
            "diagnostic_figure": "docs/assets/fig_apart3_cfkc_dhc.png",
            "emitted_dots": int(exp3_full_dots.sum()),
            "on_catalogue_dots": int((exp3_full_dots & ctx.labels).sum()),
            "spatial_allocation": spatial_alloc,
        },
        "raster_sha256": zeros_sha256,
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
        "ok_to_submit": ok_submit,
        "verdict": final_verdict,
    }
    (evidence_dir() / "apart3_cfkc_dhc_run_card.json").write_text(json.dumps(run_card, indent=2) + "\n")
    (ROOT / "docs" / "data" / "latest-run-card.json").write_text(json.dumps(run_card, indent=2) + "\n")
    print(
        f"Done in {elapsed:.1f}s (peak RSS={max_rss} MB)! "
        f"Verdict={run_card['verdict']} | ok_to_submit={ok_submit} | TIF={bundle['zeros_tif']['filename']}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
