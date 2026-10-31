#!/usr/bin/env python3
"""Compute the 2026-10-31 gate summary for the H-S1 and H-M1 candidates from saved artifacts.

Reads only files written by the experiment drivers and the registry scan:
  evidence/<ID>_run_card.json            (holdout, canaries, controls, file and hash)
  evidence/<ID>_registry_scan.json       (full-registry surface and final-dot comparison)
  docs/downloads/<zeros>.tif             (re-validated here with the shared strict validator)

Writes:
  evidence/candidates_20261031_summary.json   (gate table; every verdict fail-closed)
and updates each run card's `verdict` / `gates` / `ok_to_submit` fields.
Nothing here authorizes a submission. The weekly-slot selector is separate and no lane is assigned.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gemsdoe32.submission import validate_submission_geotiff  # noqa: E402

CHAMPION_FILE = "docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif"
CANARY_MAX = 0.90
DENSE_COVERAGE = 0.70  # rasters whose 3-px dilation covers >= 70 % of the footprint are space-filling


def _nonfinite_or_range_ok(path: Path, template: Path) -> dict:
    rep = validate_submission_geotiff(path, template, strict_whole_array_finite=True).to_dict()
    return {"passed": bool(rep.get("passed")), "detail": rep}


def _note_dot_count(note: str):
    import re
    m = re.search(r"(\d+) dots", note)
    return int(m.group(1)) if m else None


def summarize(card_id: str, card_path: Path, scan_path: Path, template: Path) -> dict:
    card = json.loads(card_path.read_text())
    scan = json.loads(scan_path.read_text())
    hold = card["holdout_candidate"]
    hr = hold["hide_and_recover"]
    sg = hold["sgmc_off_catalogue"]
    champ = card.get("holdout_champion_GEMSDOE32") or {}
    if not champ:
        # Card written before the champion comparison existed: evaluate the champion with the shared evaluator.
        import importlib.util
        spec = importlib.util.spec_from_file_location("evaluate_holdout", ROOT / "scripts" / "evaluate_holdout.py")
        ev = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(ev)
        champ = ev.evaluate_path(ROOT / CHAMPION_FILE, b_visible_px=0.0, name="GEMSDOE32-champion")
        card["holdout_champion_GEMSDOE32"] = champ
    champ_hr = champ.get("hide_and_recover", {})
    champ_sg = champ.get("sgmc_off_catalogue", {})
    final = scan["final_dots"]
    surf = scan.get("surface", {})
    comps = final["comparisons"]
    literal_dups = [r for r in comps if r.get("literal_duplicate")]
    dense_dups = [r for r in literal_dups if (r.get("footprint_coverage_3px") or 0) >= DENSE_COVERAGE]
    sparse_dups = [r for r in literal_dups if (r.get("footprint_coverage_3px") or 0) < DENSE_COVERAGE]
    sparse_measurable = [r for r in comps if r.get("measurable") and (r.get("footprint_coverage_3px") or 1) < DENSE_COVERAGE]
    max_sparse_overlap = max((r["within_3px_fraction"] for r in sparse_measurable), default=None)
    fmt = _nonfinite_or_range_ok(ROOT / card["candidate_file"], template)

    gates = {
        "G1_format_strict_finite_0_1_crs_shape_transform": {"passed": fmt["passed"]},
        "G2_single_feature_leakage_canary_max_auc_le_0.90": {
            "passed": bool(max(card["single_feature_canary_auc_holdout_seed20"].values()) <= CANARY_MAX),
            "max_auc": max(card["single_feature_canary_auc_holdout_seed20"].values()),
        },
        "G3_holdout_HIDE_RECOVER_beats_GEMSDOE32_incumbent": {
            "passed": bool(hr and champ_hr and hr["pooled_dti"] > champ_hr["pooled_dti"]
                           and hr["ci95_cluster_bootstrap"][0] > champ_hr["ci95_cluster_bootstrap"][1]),
            "note": "Non-overlapping 95% CIs. A paired CI was not computed, so the repo's paired-delta requirement is not met.",
            "candidate": [hr["pooled_dti"], hr["ci95_cluster_bootstrap"]],
            "champion": [champ_hr.get("pooled_dti"), champ_hr.get("ci95_cluster_bootstrap")],
        },
        "G4_SGMC_calibrated_no_regression_vs_GEMSDOE32": {
            "passed": bool(sg and champ_sg and sg["sgmc_prevalence_calibrated_dti"] >= champ_sg["sgmc_prevalence_calibrated_dti"]),
            "candidate": [sg["sgmc_prevalence_calibrated_dti"], sg["sgmc_calibrated_ci95"]],
            "champion": [champ_sg.get("sgmc_prevalence_calibrated_dti"), champ_sg.get("sgmc_calibrated_ci95")],
        },
        "G5_surface_registry_literal_abs_spearman_le_0.90": {
            "passed": bool(surf.get("literal_rule_passed", surf.get("passed"))),
            "worst_abs_spearman": surf.get("worst_abs_spearman"),
            "registry_rasters": surf.get("registry_rasters"),
        },
        "G6_final_dots_registry_literal_within_3px_le_0.70": {
            "passed": bool(final.get("literal_rule_passed")),
            "literal_duplicate_rasters": len(literal_dups),
            "of_which_space_filling_or_dense_coverage_ge_0.70": len(dense_dups),
            "of_which_sparse_coverage_lt_0.70": len(sparse_dups),
            "max_within_3px_among_sparse_rasters": max_sparse_overlap,
            "registry_rasters_compared": final.get("registry_rasters"),
            "unique_masks_or_surfaces": final.get("unique_pixel_masks_or_surfaces"),
            "literal_duplicates": [
                {"repo": r["repo"], "path": r["path"], "within_3px": r["within_3px_fraction"],
                 "coverage_3px": r["footprint_coverage_3px"], "abs_spearman": abs(r["spearman"] or 0.0)}
                for r in literal_dups
            ],
        },
        "G9_submission_note_states_actual_dot_count": {
            "passed": _note_dot_count(card["submission_note"]) == card["dots_after_label_mask"],
            "note_says": _note_dot_count(card["submission_note"]),
            "raster_dots": card["dots_after_label_mask"],
        },
        "G7_method_lane_assigned": {"passed": False, "note": "No lane paragraph in the prompt or checkout."},
        "G8_selector_authorization_weekly_slot": {"passed": False, "note": "Separate selector step; none recorded."},
    }
    passed_all = all(g["passed"] for g in gates.values())
    verdict = "negative" if not passed_all else "promote_pending_selector"
    blockers = [k for k, g in gates.items() if not g["passed"]]
    out = {
        "candidate_id": card_id,
        "file": card["candidate_file"],
        "sha256": card["candidate_sha256"],
        "submission_name": card["submission_name"],
        "submission_note": card["submission_note"],
        "note_chars": len(card["submission_note"]),
        "dots": card["dots_after_label_mask"],
        "holdout_dti_hide_recover": {"value": hr["pooled_dti"], "ci95": hr["ci95_cluster_bootstrap"],
                                     "evaluator": hr["evaluator_version"], "withheld_positives": hr["n_withheld_positives"],
                                     "label": "HOLDOUT-DTI"},
        "sgmc_calibrated_dti": {"value": sg["sgmc_prevalence_calibrated_dti"], "ci95": sg["sgmc_calibrated_ci95"],
                                "evaluator": sg["evaluator_version"], "label": "HOLDOUT-DTI"},
        "live_score_estimate": "NOT ESTIMABLE (no calibrated mapping; no organizer receipt)",
        "unique_literal_rule": bool(final.get("literal_rule_passed")) and bool(surf.get("literal_rule_passed", surf.get("passed"))),
        "gates": gates,
        "blocking_gates": blockers,
        "verdict": verdict,
        "ok_to_submit": False,
        "ok_to_download_for_research_only": True,
    }
    # Update the run card in place so the card and the summary agree.
    card["gates"] = {k: {"passed": v["passed"]} for k, v in gates.items()}
    card["blocking_gates"] = blockers
    card["validator_output"] = {"tool": "gemsdoe32.submission.validate_submission_geotiff(strict_whole_array_finite=True)",
                                "passed": fmt["passed"], "detail": fmt["detail"]}
    card["verdict"] = verdict
    card["ok_to_submit"] = False
    card["registry_scan"] = str(scan_path.relative_to(ROOT))
    card_path.write_text(json.dumps(card, indent=2, default=float) + "\n")
    return out


H1_ID = "H1-LIDAR-SCARP-DEM-CHI"
H1_CARD = "evidence/H1-LIDAR-SCARP-DEM-CHI_run_card.json"
H1_RECHECK = "evidence/H1-LIDAR-SCARP-DEM-CHI_holdout_recheck_20261031.json"
H1_SCAN = "evidence/H1-LIDAR-SCARP-DEM-CHI_registry_scan_20261031.json"


def summarize_h1(template: Path) -> dict:
    """H1 comes from another session's run card (branch arena/d20ee5aa). Its card is read, not written.

    The holdout is re-run here with the shared evaluator, and the full-registry scan is run here too.
    """
    card = json.loads((ROOT / H1_CARD).read_text())
    rc = json.loads((ROOT / H1_RECHECK).read_text())
    scan = json.loads((ROOT / H1_SCAN).read_text())
    path = ROOT / card["artifacts"]["primary_zeros_tif"]
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    if sha != card["raster_sha256"]:
        raise ValueError("H1 raster hash does not match its run card")
    fmt = _nonfinite_or_range_ok(path, template)
    hr = rc["hide_and_recover"]
    sg = rc["sgmc_off_catalogue"]
    # GEMSDOE32 incumbent, read from the evaluator output saved in the H-S1 run card (same evaluator versions).
    inc = json.loads((ROOT / "evidence/H-S1-SPECTRAL-ROLLOFF_run_card.json").read_text())["holdout_champion_GEMSDOE32"]
    champ_hr = [inc["hide_and_recover"]["pooled_dti"], inc["hide_and_recover"]["ci95_cluster_bootstrap"]]
    champ_sg = [inc["sgmc_off_catalogue"]["sgmc_prevalence_calibrated_dti"], inc["sgmc_off_catalogue"]["sgmc_calibrated_ci95"]]
    final = scan["final_dots"]
    dots = int(scan["candidate_dots"])
    comps = final["comparisons"]
    literal_dups = [r for r in comps if r.get("literal_duplicate")]
    sparse_dups = [r for r in literal_dups if (r.get("footprint_coverage_3px") or 0) < DENSE_COVERAGE]
    gates = {
        "G1_format_strict_finite_0_1_crs_shape_transform": {"passed": fmt["passed"]},
        "G2_single_feature_leakage_canary_max_auc_le_0.90": {
            "passed": False, "note": "Not computed by the H1 run card (feature_canaries False). Not run here."},
        "G3_holdout_HIDE_RECOVER_beats_GEMSDOE32_incumbent": {
            "passed": bool(hr["ci95_cluster_bootstrap"][0] > champ_hr[1][1]),
            "note": "Recheck CI lower bound is below the incumbent's CI upper bound, so the intervals overlap. Paired CI not computed.",
            "candidate": [hr["pooled_dti"], hr["ci95_cluster_bootstrap"]], "champion": champ_hr},
        "G4_SGMC_calibrated_no_regression_vs_GEMSDOE32": {
            "passed": bool(sg["sgmc_prevalence_calibrated_dti"] >= champ_sg[0]),
            "note": "Point estimate higher; calibrated CIs overlap by about 0.0003. Not a demonstrated gain.",
            "candidate": [sg["sgmc_prevalence_calibrated_dti"], sg["sgmc_calibrated_ci95"]], "champion": champ_sg},
        "G5_surface_registry_literal_abs_spearman_le_0.90": {
            "passed": False, "note": "No continuous surface file exists for H1. The surface-before-placement stage was not run."},
        "G6_final_dots_registry_literal_within_3px_le_0.70": {
            "passed": bool(final.get("literal_rule_passed")),
            "literal_duplicate_rasters": len(literal_dups),
            "of_which_space_filling_or_dense_coverage_ge_0.70": len(literal_dups) - len(sparse_dups),
            "of_which_sparse_coverage_lt_0.70": len(sparse_dups),
            "registry_rasters_compared": final.get("registry_rasters"),
            "unique_masks_or_surfaces": final.get("unique_pixel_masks_or_surfaces"),
            "literal_duplicates": [
                {"repo": r["repo"], "path": r["path"], "within_3px": r["within_3px_fraction"],
                 "coverage_3px": r["footprint_coverage_3px"], "abs_spearman": abs(r["spearman"] or 0.0)}
                for r in literal_dups],
        },
        "G9_submission_note_states_actual_dot_count": {
            "passed": _note_dot_count(card["submission_note"]) == dots,
            "note_says": _note_dot_count(card["submission_note"]), "raster_dots": dots},
        "G7_method_lane_assigned": {"passed": False, "note": "Lane H1 is named in its own card, but the 2026-10-31 checkout has no lane assignment for this session. Not accepted here."},
        "G8_selector_authorization_weekly_slot": {"passed": False, "note": "Separate selector step; none recorded (slot_authorized False in its card)."},
    }
    blockers = [k for k, g in gates.items() if not g["passed"]]
    return {
        "candidate_id": H1_ID,
        "source_card": H1_CARD,
        "source_note": "Created on branch arena/d20ee5aa by another session; verified here.",
        "file": card["artifacts"]["primary_zeros_tif"],
        "sha256": sha,
        "submission_name": card["submission_name"],
        "submission_note": card["submission_note"],
        "note_chars": len(card["submission_note"]),
        "dots": dots,
        "holdout_dti_hide_recover": {"value": hr["pooled_dti"], "ci95": hr["ci95_cluster_bootstrap"],
                                     "evaluator": hr["evaluator_version"], "withheld_positives": hr["n_withheld_positives"],
                                     "label": "HOLDOUT-DTI"},
        "sgmc_calibrated_dti": {"value": sg["sgmc_prevalence_calibrated_dti"], "ci95": sg["sgmc_calibrated_ci95"],
                                "evaluator": sg["evaluator_version"], "label": "HOLDOUT-DTI"},
        "live_score_estimate": "NOT ESTIMABLE (no calibrated mapping; no organizer receipt)",
        "unique_literal_rule": bool(final.get("literal_rule_passed")),
        "gates": gates,
        "blocking_gates": blockers,
        "verdict": "negative",
        "ok_to_submit": False,
        "ok_to_download_for_research_only": True,
    }


def main() -> int:
    template = ROOT / ".cache" / "gems_data" / "sample_submission.tif"
    results = []
    for cid, card_name, scan_name in (
        ("H-S1-SPECTRAL-ROLLOFF", "H-S1-SPECTRAL-ROLLOFF_run_card.json", "H-S1-SPECTRAL-ROLLOFF_registry_scan.json"),
        ("H-M1-CROSSGRAD-MG", "H-M1-CROSSGRAD-MG_run_card.json", "H-M1-CROSSGRAD-MG_registry_scan.json"),
    ):
        results.append(summarize(cid, ROOT / "evidence" / card_name, ROOT / "evidence" / scan_name, template))
    results.append(summarize_h1(template))
    summary = {
        "date_utc": "2026-10-31",
        "champion_reference": {"file": CHAMPION_FILE, "owner_reported_score": 0.2778,
                               "score_label": "OWNER-REPORT"},
        "gate_rules": "Fail-closed. A candidate is cleared only if every gate passes AND an owner-assigned lane and selector approval exist.",
        "candidates": results,
        "any_file_ok_to_submit": False,
    }
    (ROOT / "evidence" / "candidates_20261031_summary.json").write_text(json.dumps(summary, indent=2, default=float) + "\n")
    for r in results:
        print(r["candidate_id"], r["verdict"], "blocking:", r["blocking_gates"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
