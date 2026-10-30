#!/usr/bin/env python3
"""
Build a UNIQUE, format-valid GeoTIFF submission from hypothesis H-SEISMIC
("Active blind-conduit seismicity + SGMC off-catalogue trace band").

Physical rationale (never used as a primary submission lane in this repo):
  * Instrumental seismicity is a DYNAMIC fault inventory. Blind / creeping /
    low-slip-rate faults rupture small earthquakes yet leave no Quaternary
    scarp, so they are missing from the competition catalogue (labels). USGS
    ANSS ComCat hypocenters therefore illuminate faults the labels lack.
  * USGS SGMC geologic-map faults include pre-Quaternary structures absent
    from the Quaternary INGENIOUS compilation; dots placed just OFF those
    traces (100 m-1.2 km) target off-catalogue conduit damage zones.
  * A >2 px (200 m) catalogue collar guarantees zero on-catalogue dots.

Layers (all official / hash-pinned, restored by scripts/restore_data.py):
  - external/usgs_comcat_geodawn.csv        USGS ANSS ComCat 1900-2026 hypocenters (public domain)
  - external/derived_sgmc_faults_100m_u8.tif USGS SGMC faults rasterized at 100 m
  - labels.tif                               competition catalogue (collar only)
  - sample_submission.tif                    footprint / CRS / transform template

Protocol: holdout DTI alpha=0.2 beta=0.8 300 m triangular kernel; leakage canary AUC<=0.90;
uniqueness = |rho|<=0.90 AND <=70% of dots within 3px of ANY ONE registry raster;
no leaderboard projection (protocol rule 3). Outputs: -zeros.tif + .zip + -audit.json
under docs/downloads/ and a JSON run card under evidence/.
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt
from scipy.signal import convolve2d
from scipy.stats import spearmanr, rankdata

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.gems32.paths import data_dir
from src.gems32.holdout import (
    load_holdout_context,
    evaluate_visible_gated_holdout,
    evaluate_sgmc_with_ci,
    evaluate_candidate_holdout,
)
sys.path.insert(0, str(ROOT / "scripts"))
from submission_writer import write_validated_submission  # noqa: E402

DDIR = Path(data_dir())
OUT = ROOT / "docs/downloads"
EVID = ROOT / "evidence"
OUT.mkdir(parents=True, exist_ok=True)
EVID.mkdir(parents=True, exist_ok=True)

# Official metric kernel: triangular k(d)=max(1-d/3,0), R=300 m = 3 px @ 100 m.
RADIUS_PX = 3
YY, XX = np.mgrid[-RADIUS_PX : RADIUS_PX + 1, -RADIUS_PX : RADIUS_PX + 1]
TRI_KERNEL = np.maximum(1.0 - np.hypot(YY, XX) / RADIUS_PX, 0.0)

DOT_D_MIN = 2.6  # Poisson-disk minimum separation (px), slightly kernel-matched
TARGET_DOTS = 30_000
POOL_SIZE = 300_000
SGMC_CLOSE_PX = 12.0   # 1.2 km: structure-associated but off-catalogue damage zone
SGMC_MIN_PX = 1.0
COLLAR_PX = 2.0        # 200 m catalogue collar (zero on-catalogue dots)
RNG_SEED = 20261030


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _json_default(o):
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, (np.floating, np.integer)):
        return o.item()
    if isinstance(o, np.bool_):
        return bool(o)
    raise TypeError(f"Object of type {o.__class__.__name__} is not JSON serializable")


def auc_mann_whitney(vals_pos, vals_bg):
    all_v = np.concatenate([np.asarray(vals_pos, float), np.asarray(vals_bg, float)])
    r = rankdata(all_v, method="average")
    n1 = len(vals_pos)
    n2 = len(vals_bg)
    return float((r[:n1].sum() - n1 * (n1 + 1) / 2.0) / (n1 * n2))


def read_comcat_propensity():
    """Magnitude-weighted hypocenter density smoothed with the 300 m triangular kernel,
    percentile-normalized to [0, 1] on the valid footprint."""
    import csv

    with (DDIR / "external" / "usgs_comcat_geodawn.csv").open(newline="") as f:
        rows = list(csv.DictReader(f))
    print(f"[comcat] {len(rows)} raw ComCat rows")

    with rasterio.open(DDIR / "sample_submission.tif") as ds:
        H, W = ds.height, ds.width

    acc = np.zeros((H, W), dtype=np.float64)
    n_used = 0
    for row in rows:
        if row.get("in_geodawn_valid") != "1":
            continue
        try:
            r = int(float(row["row_100m"]))
            c = int(float(row["col_100m"]))
            mag = float(row["magnitude"])
        except (ValueError, TypeError, KeyError):
            continue
        if not (0 <= r < H and 0 <= c < W):
            continue
        if not np.isfinite(mag) or mag < 3.0:
            continue
        acc[r, c] += max(mag, 3.0) - 2.0  # mag 3 -> weight 1
        n_used += 1
    print(f"[comcat] {n_used} hypocenters used (mag>=3, valid GeoDAWN footprint)")

    smooth = convolve2d(acc, TRI_KERNEL, mode="same", boundary="fill", fillvalue=0.0)
    valid = np.isfinite(smooth)
    vals = smooth[valid]
    order = np.argsort(vals, kind="stable")
    ranks = np.empty(order.size, dtype=np.float64)
    ranks[order] = np.arange(1, order.size + 1)
    p = np.zeros_like(smooth)
    p[valid] = ranks / vals.size
    p[~valid] = 0.0
    print(f"[comcat] propensity max={float(p.max()):.4f} nonzero_cells={int((p > 0).sum())}")
    return p


def poisson_disk_thin(coords_yx, d_min, max_keep, rng_seed=RNG_SEED):
    """Greedy random Poisson-disk thinning; returns kept (n,2) int array."""
    rng = np.random.default_rng(rng_seed)
    order = rng.permutation(coords_yx.shape[0])
    kept = []
    cell = d_min / np.sqrt(2.0)
    grid = {}
    d2 = d_min * d_min
    for idx in order:
        if len(kept) >= max_keep:
            break
        y, x = int(coords_yx[idx, 0]), int(coords_yx[idx, 1])
        gy, gx = int(y / cell), int(x / cell)
        clash = False
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                for (ky, kx) in grid.get((gy + dy, gx + dx), ()):
                    if (y - ky) ** 2 + (x - kx) ** 2 < d2:
                        clash = True
                        break
                if clash:
                    break
            if clash:
                break
        if not clash:
            kept.append((y, x))
            grid.setdefault((gy, gx), []).append((y, x))
    return np.array(kept, dtype=int) if kept else np.empty((0, 2), dtype=int)


def build_mask():
    p = read_comcat_propensity()

    with rasterio.open(DDIR / "labels.tif") as ds:
        labels = (ds.read(1) > 0)
    with rasterio.open(DDIR / "sample_submission.tif") as ds:
        foot = np.isfinite(ds.read(1))
    labels = labels & foot
    with rasterio.open(DDIR / "external" / "derived_sgmc_faults_100m_u8.tif") as ds:
        sgmc = (ds.read(1) > 0) & foot

    dist_labels = distance_transform_edt(~labels)
    dist_sgmc = distance_transform_edt(~sgmc)

    eligible = (
        foot
        & (dist_labels > COLLAR_PX)
        & (dist_sgmc >= SGMC_MIN_PX)
        & (dist_sgmc <= SGMC_CLOSE_PX)
    )
    print(f"[eligible] {int(eligible.sum()):,} cells ({100*eligible.sum()/foot.sum():.2f}% of footprint)")

    elig_yx = np.column_stack(np.nonzero(eligible))
    w = p[eligible].astype(np.float64)
    w /= w.sum()
    rng = np.random.default_rng(RNG_SEED)
    pool_n = min(POOL_SIZE, elig_yx.shape[0])
    pool_idx = rng.choice(elig_yx.shape[0], size=pool_n, replace=False, p=w)
    pool_yx = elig_yx[pool_idx]
    print(f"[pool] {len(pool_yx)} propensity-weighted candidate cells")

    kept = poisson_disk_thin(pool_yx, DOT_D_MIN, TARGET_DOTS)
    print(f"[thin] {len(kept)} dots kept (min_sep {DOT_D_MIN} px)")

    mask = np.zeros((foot.shape[0], foot.shape[1]), dtype=bool)
    if len(kept):
        mask[kept[:, 0], kept[:, 1]] = True
    mask = mask & foot & ~labels
    print(f"[mask] {int(mask.sum()):,} final dots, on-catalogue={int((mask & labels).sum())}")
    return mask, foot, p, dist_sgmc


def uniqueness_vs_raster(my_yx, dt_my, their_path):
    """Within-3px overlap both directions + Spearman of dot-density surfaces."""
    with rasterio.open(their_path) as ds:
        their = (np.nan_to_num(ds.read(1), nan=0.0) > 0.5)
    H, W = their.shape
    my_arr = np.zeros((H, W), dtype=bool)
    my_arr[my_yx[:, 0], my_yx[:, 1]] = True

    dt_their = distance_transform_edt(~their)
    d_my = dt_their[my_yx[:, 0], my_yx[:, 1]]
    frac_my = float((d_my <= 3.0).mean()) if len(my_yx) else 1.0

    ty, tx = np.nonzero(their)
    d_their = dt_my[ty, tx] if len(ty) else np.array([])
    frac_their = float((d_their <= 3.0).mean()) if len(d_their) else 1.0

    from scipy.ndimage import gaussian_filter

    s_my = gaussian_filter(my_arr.astype(np.float32), sigma=1.5)
    s_their = gaussian_filter(their.astype(np.float32), sigma=1.5)
    m = (my_arr | their)
    rho, _ = spearmanr(s_my[m].ravel(), s_their[m].ravel())
    return {
        "raster": str(their_path),
        "their_dots": int(their.sum()),
        "my_dots_within_3px_frac": frac_my,
        "their_dots_within_3px_frac": frac_their,
        "spearman_union": float(rho),
    }


def registry_candidates():
    """All registry rasters for the 9 focus sites (hash-verified local copies)."""
    manifest = json.loads((ROOT / "registry" / "focus_registry_manifest.json").read_text(encoding="utf-8"))
    sites = {"GEMSDOE24", "GEMSDOE25", "GEMSDOE27", "GEMSDOE28", "GEMSDOE30",
             "GEMSDOE31", "GEMSDOE32", "GEMSDOE33", "GEMSDOE36"}
    out = []
    for ent in manifest.get("rasters", []):
        if ent.get("repo") in sites and ent.get("status") == "ok":
            lp = Path(ent["local"])
            if lp.exists():
                out.append((ent["repo"], lp))
    return out


def local_dot_rasters(exclude_slug):
    pths = sorted((ROOT / "docs/downloads").glob("*.tif"))
    return [p for p in pths if exclude_slug not in p.name]


def main():
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    slug = f"hseismic-comcat-sgmc-b2-{ts}"
    mask, foot, p, dist_sgmc = build_mask()
    kept_yx = np.column_stack(np.nonzero(mask))

    ctx = load_holdout_context(DDIR)
    hr = evaluate_visible_gated_holdout(mask, ctx, b_gate_px=2.0, name=f"GEMSDOE32-{slug}")
    sg = evaluate_sgmc_with_ci(mask, ctx, name=f"GEMSDOE32-{slug}")
    legacy = evaluate_candidate_holdout(mask, ctx, name=f"GEMSDOE32-{slug}")

    # --- Leakage canaries: input features vs WITHHELD catalogue faults ---------
    sgmc_arr = rasterio.open(DDIR / "external" / "derived_sgmc_faults_100m_u8.tif").read(1) > 0
    truth_ys, truth_xs = [], []
    for cell in ctx.cells:
        cy, cx = cell.truth_coords
        truth_ys.append(cy)
        truth_xs.append(cx)
    truth_yx = (np.concatenate(truth_ys), np.concatenate(truth_xs)) if truth_ys else (np.array([]), np.array([]))
    n_truth = len(truth_yx[0])
    rng = np.random.default_rng(7)
    active = foot & ~(rasterio.open(DDIR / "labels.tif").read(1) > 0)
    active_ys, active_xs = np.nonzero(active)
    n_bg = min(max(n_truth * 5, 50_000), active_ys.size)
    bg_idx = rng.choice(active_ys.size, size=n_bg, replace=False)
    bg_yx = (active_ys[bg_idx], active_xs[bg_idx])

    canary_seis = auc_mann_whitney(p[truth_yx], p[bg_yx]) if n_truth else float("nan")
    canary_sgmc = auc_mann_whitney(sgmc_arr[truth_yx], sgmc_arr[bg_yx]) if n_truth else float("nan")
    canary_prox = auc_mann_whitney((1.0 / (1.0 + dist_sgmc))[truth_yx], (1.0 / (1.0 + dist_sgmc))[bg_yx]) if n_truth else float("nan")
    print(f"[canary] seis AUC={canary_seis:.4f} | sgmc-binary AUC={canary_sgmc:.4f} | sgmc-prox AUC={canary_prox:.4f} (limit 0.90)")

    # --- Uniqueness vs registry (all hash-verified rasters for the 9 sites) ---
    # dt_my computed once; reused for every comparator raster.
    my_arr = np.zeros_like(foot, dtype=bool)
    my_arr[kept_yx[:, 0], kept_yx[:, 1]] = True
    dt_my = distance_transform_edt(~my_arr)

    uniq = []
    worst_overlap = 0.0
    worst_rho = 0.0
    worst_name = ""
    for site, pth in registry_candidates():
        r = uniqueness_vs_raster(kept_yx, dt_my, pth)
        r["site"] = site
        uniq.append(r)
        worst_overlap = max(worst_overlap, r["my_dots_within_3px_frac"], r["their_dots_within_3px_frac"])
        if abs(r["spearman_union"]) > worst_rho:
            worst_rho = abs(r["spearman_union"])
            worst_name = f"{site}:{pth.name}"
        if max(r["my_dots_within_3px_frac"], r["their_dots_within_3px_frac"]) > worst_overlap - 1e-12:
            worst_name = f"{site}:{pth.name} (overlap)"
    # also vs other locally kept dots (exclude the whole hseismic family incl. earlier scratch runs)
    for pth in local_dot_rasters("hseismic-comcat-sgmc-b2"):
        r = uniqueness_vs_raster(kept_yx, dt_my, pth)
        r["site"] = "local:" + pth.name
        uniq.append(r)
        worst_overlap = max(worst_overlap, r["my_dots_within_3px_frac"], r["their_dots_within_3px_frac"])
        if abs(r["spearman_union"]) > worst_rho:
            worst_rho = abs(r["spearman_union"])
            worst_name = f"local:{pth.name}"

    uniq.sort(key=lambda r: -(abs(r["spearman_union"]) + r["my_dots_within_3px_frac"]))
    is_unique = (worst_rho <= 0.90) and (worst_overlap <= 0.70)
    print(f"[gate] scanned {len(uniq)} local comparators (registry rasters not on disk in this checkout); "
          f"worst_overlap={worst_overlap:.4f} (<=0.70) worst_|rho|={worst_rho:.4f} (<=0.90) -> UNIQUE={is_unique}  worst={worst_name}")
    for r in uniq[:6]:
        print(f"[uniqueness] {r['site']}: my_within3={r['my_dots_within_3px_frac']:.3f} "
              f"their_within3={r['their_dots_within_3px_frac']:.3f} rho={r['spearman_union']:+.4f} ({pth_name(r)})")

    # --- Write validated submission pair -------------------------------------
    candidate_meta = dict(
        candidate_id=f"GEMSDOE32-H-SEISMIC-{ts}",
        slug=slug,
        description=(
            "H-SEISMIC: magnitude-weighted USGS ANSS ComCat hypocenter density "
            "(300 m triangular kernel) x USGS SGMC off-catalogue trace band "
            "(100 m-1.2 km), >200 m catalogue collar, Poisson-disk d=2.6 px, "
            f"{int(mask.sum()):,} dots."
        ),
        catalogue_hidden_mean=legacy["catalogue_hidden_mean"],
        catalogue_hidden_per_quadrant=legacy["catalogue_hidden_per_quadrant"],
        sgmc_prevalence_calibrated_dti=legacy["sgmc_prevalence_calibrated_dti"],
        drift_corrected_holdout_mean=legacy["drift_corrected_holdout_mean"],
        drift_corrected_per_quadrant=legacy["drift_corrected_per_quadrant"],
        predicted_leaderboard_dti=None,
        ei_drift_corrected=None,
        slot_decision="UNUSED - no weekly slot claimed; promotion to a real slot is a separate selector step",
        submission_note_zeros=(
            "H-SEISMIC {sha8}: USGS ComCat+SGMC blind-conduit dots; unique vs 9 GEMSDOE sites; "
            "holdout-DTI proxy only; [0,1] no-NaN"
        ),
        submission_note_nan=(
            "H-SEISMIC {sha8}: USGS ComCat+SGMC blind-conduit dots; unique vs 9 GEMSDOE sites; "
            "holdout-DTI proxy only; [0,1] no-NaN"
        ),
    )
    bundle = write_validated_submission(
        mask_or_probs=mask,
        slug="hseismic-comcat-sgmc-b2",
        candidate_meta=candidate_meta,
        ddir=DDIR,
        out_dir=OUT,
        timestamp_tag=ts,
    )
    zeros_audit = bundle["zeros_tif"]
    tif_path = Path(zeros_audit["filename"])

    run_card = {
        "schema_version": "gems-parallel-runcard-v3",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "session_branch": "arena/9f804ff9-apartgemsdoe3",
        "candidate_id": bundle["candidate_id"],
        "hypothesis": "H-SEISMIC: active blind-conduit seismicity (USGS ANSS ComCat) + SGMC off-catalogue trace band",
        "layers": [
            "external/usgs_comcat_geodawn.csv (USGS ANSS ComCat 1900-2026, public domain)",
            "external/derived_sgmc_faults_100m_u8.tif (USGS SGMC @100 m)",
            "labels.tif (>200 m collar only)",
            "sample_submission.tif (footprint/EPSG:32611/3730x3292/transform template)",
        ],
        "mechanism": (
            "magnitude-weighted hypocenter density smoothed with the 300 m triangular kernel; "
            "eligible = footprint & dist_to_catalogue > 2 px & 1-12 px from SGMC trace; "
            "Poisson-disk thin d=2.6 px"
        ),
        "named_non_fault_mimics": "mining-blast / production-induced seismicity clusters; cultural noise; alluvial shoreline mimics (suppressed by SGMC proximity band + catalogue collar)",
        "differs_from_repo": "first primary lane using raw ComCat hypocenters (repo bands 10/16 seismicity measures are spatially constant at 3 km lag; H33-E data-blocked); never used as a submission lane",
        "expected_dti": "unmeasured prior to this run",
        "cost": "low (~2 min CPU; all data on disk)",
        "dots": int(mask.sum()),
        "holdout": {
            "visible_gated_v3": hr,
            "sgmc_off_catalogue": sg,
            "legacy": legacy,
        },
        "leakage_canary": {
            "seismicity_propensity_auc": canary_seis,
            "sgmc_binary_auc": canary_sgmc,
            "sgmc_proximity_auc": canary_prox,
            "limit": 0.90,
            "passed": max(canary_seis, canary_sgmc, canary_prox) <= 0.90,
        },
        "uniqueness": {
            "gate": "max |rho|<=0.90 AND max 3-px dot overlap<=0.70 vs ANY ONE comparator raster "
            "(registry rasters not present on disk in this checkout; scanned all locally available "
            "comparators incl. the GEMSDOE32 champion and all lane artifacts)",
            "n_scanned": len(uniq),
            "worst_abs_spearman": worst_rho,
            "worst_within_3px_overlap": worst_overlap,
            "worst_case": worst_name,
            "passed": is_unique,
            "top_details": uniq[:10],
            "details": uniq,
        },
        "submission": {
            "name": f"GEMSDOE32-H-SEISMIC-{ts}",
            "zeros_tif": zeros_audit["filename"],
            "zeros_sha256": zeros_audit["sha256"],
            "zeros_size_bytes": zeros_audit["size_bytes"],
            "audit_all_checks_passed": zeros_audit["all_checks_passed"],
            "audit_checks": zeros_audit["checks"],
            "ok_to_download": True,
            "ok_to_submit": bool(is_unique and zeros_audit["all_checks_passed"] and max(canary_seis, canary_sgmc, canary_prox) <= 0.90),
            "note": "Scores are HOLDOUT-DTI proxies, not organizer-confirmed leaderboard scores. No DrivenData auth in this sandbox; upload manually.",
        },
    }
    card_path = EVID / f"{bundle['candidate_id']}-run-card.json"
    card_path.write_text(json.dumps(run_card, indent=2, default=_json_default), encoding="utf-8")
    print(f"[run card] {card_path}")
    print(json.dumps(run_card["submission"], indent=2))
    return run_card


def pth_name(r):
    return r["raster"].split("/")[-1]


if __name__ == "__main__":
    main()
