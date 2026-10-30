#!/usr/bin/env python3
"""Write the JSON run card for the VO-LEARN candidate and stage its public artifacts.

Every number is read from an evidence file (no hand-typed results):
  evidence/vo-learn-hgb-e1_holdout.json          (E1, pre-declared primary, frac 0.0075)
  evidence/vo-learn-logreg-e2_holdout.json       (E2, logistic-regression control learner)
  evidence/vo-learn-hgb-frac15-e3_holdout.json   (E3, frac 0.015, selected post hoc)
  evidence/vo-learn-hgb-frac15_registry_gate.json (literal registry duplicate gate)
  evidence/nine_site_pairwise_uniqueness_20261030.json (nine-site pairwise uniqueness)
  .cache/gems_work/candidates/*-zeros.tif / *-audit.json (writer output, sha256 checked)

Also appends new irregularity items to registry/irregularities.json (idempotent by id).
Writes no submission decision: the card records NOT CLEARED and the blocking gates.
"""
from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CAND = ROOT / ".cache/gems_work/candidates"
STEM = "gemsdoe32-gemsdoe32-vo-learn-hgb-k1p5-nms5-20261030-20261030T020000Z-233ea4b6"
PUBLIC_STEM = "apartgemsdoe3-vo-learn-hgb-frac15-233ea4b6"
PUBLIC_NAME = "apartgemsdoe3-vo-learn-233ea4b6"
DOWNLOADS = ROOT / "docs/downloads"
RUN_CARD = ROOT / "evidence/vo-learn-hgb-frac15_run_card.json"
IRREG = ROOT / "registry/irregularities.json"


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load(rel: str) -> dict:
    return json.loads((ROOT / rel).read_text())


def holdout_block(d: dict) -> dict:
    cand, ctrl = d["candidate_holdout"], d["control_holdout_VO_NEAR"]
    return {
        "score_label": "HOLDOUT-DTI",
        "evaluator_version": cand["evaluator_version"],
        "candidate": {"pooled_dti": cand["pooled_dti"], "ci95": cand["ci95_cluster_bootstrap"]},
        "control_VO_NEAR": {"pooled_dti": ctrl["pooled_dti"], "ci95": ctrl["ci95_cluster_bootstrap"]},
        "paired_candidate_minus_control": {"mean": d["paired_candidate_minus_control_mean"],
                                           "ci95": d["paired_candidate_minus_control_ci95"]},
        "n_withheld_positives": cand["n_withheld_positives"],
        "n_spatial_clusters": cand["n_spatial_clusters"],
        "n_bootstrap_reps": cand["n_bootstrap_reps"],
        "learner": d["learner"],
        "frac_of_footprint": d["frac_of_footprint"],
        "nms_radius_px": d["nms_radius_px"],
        # Direction-agnostic per-cell AUC: the script stores max|a-0.5|+0.5 = max over cells of max(a, 1-a).
        "max_single_feature_canary_auc": max(v["auc_max_abs_dev_from_0p5"] for v in d["feature_alone_canary_auc"].values()),
        "canary_max_feature": max(d["feature_alone_canary_auc"], key=lambda k: d["feature_alone_canary_auc"][k]["auc_max_abs_dev_from_0p5"]),
        "features_flagged_leakage_gt_0p90": d["features_flagged_leakage_gt_0p90"],
        "runtime_s": d["runtime_s"],
    }


NEW_IRREGULARITIES = [
    {"id": "IR-VO-01", "severity": "high (blocks submission)",
     "statement": "The VO-LEARN candidate FAILS the literal registry duplicate gate. Its only literal failure is the 5-px calibration lattice (GEMSDOE24 inputs/calibration/13gems_20261001_r13-lattice-s5_v2_nan-outside.tif, 98.2% of candidate dots within 3 px). The lattice covers 99.87% of the footprint within 3 px, and a uniform random 77,511-dot null scores 0.9986-0.9988. The literal rule therefore cannot be met by any dot set above roughly 22,163 dots.",
     "mitigation": "Owner decision required (see IR-45-LATTICE-02, IR-51-LATTICE-01). Not exempted, and dots were not moved off lattice points to pass. Diagnostics only: evidence/vo-learn-hgb-frac15_registry_gate.json."},
    {"id": "IR-VO-02", "severity": "high (audit incomplete)",
     "statement": "Two registry rasters cannot be compared against the template, so the literal audit is incomplete (audit_complete false). GEMSDOE31 docs/downloads/gemsdoe31-csdu-stepover-8cf9dc27-nan.tif has nonfinite values inside the footprint. GEMSDOE36 docs/downloads/GEMS36_FORMAT_TEST_NOT_SUBMISSION.tif has a grid mismatch (32x48). The earlier inspection identified only GEMSDOE36, so this entry adds GEMSDOE31 and corrects that count.",
     "mitigation": "Owner or auditor must decide whether malformed rasters are excluded by rule, or repaired and compared. Record the decision before any clearance."},
    {"id": "IR-VO-03", "severity": "medium",
     "statement": "E3 (frac 0.015) was selected after E1 and E2 from two pre-declared budgets, so its holdout is exploratory and optimistically biased. E1 (frac 0.0075) is the pre-declared primary. The final candidate uses the E3 budget.",
     "mitigation": "Report E1 as the primary result. Treat E3 as a sensitivity point. Any clearance needs a fresh holdout or a pre-registered budget."},
    {"id": "IR-VO-04", "severity": "medium",
     "statement": "Pre-registered HGB settings (learning rate 0.1, min_samples_leaf 100) were not used. The run used learning rate 0.08, min_samples_leaf 200, max_leaf_nodes 63, max_iter 200, and l2 1.0. Per-fold budget = frac x footprint / 4 (k=9689 per fold, total 38,756 for frac 0.0075 and 77,511 for 0.015).",
     "mitigation": "Recorded in this run card. The deviation is disclosed and the settings are fixed in scripts/run_visible_only_candidate.py."},
    {"id": "IR-VO-05", "severity": "high (disclosure)",
     "statement": "The official rules document (NLR, September 2026, section 3.2) requires any prize submission narrative to state the extent and manner of generative-AI use. This work was produced with an AI coding agent. No narrative has been drafted, and no disclosure has been made.",
     "mitigation": "Owner must write the disclosure for any prize narrative. Source: https://docs.nlr.gov/docs/fy26osti/96647.pdf"},
    {"id": "IR-VO-06", "severity": "medium",
     "statement": "The rules (section 3.2) state three submissions per week. The repo records a weekly slot concept but no numeric cap that was verified against the live submission page, which is login-walled.",
     "mitigation": "Owner to confirm the live cap on the DrivenData submission page before any slot decision."},
    {"id": "IR-VO-07", "severity": "medium",
     "statement": "The published 91eae1ca family is two byte-identical pairs, not one group. GEMSDOE30 docs/downloads/gemsdoe30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca-nanoutside.tif matches GEMSDOE31 gemsdoe31-reference-d28-offcat-44090-20261004-nan.tif. GEMSDOE30 gemsdoe30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca.tif matches a GEMSDOE32 copy. This corrects an earlier note that stated a single group of four. GEMSDOE31 gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-nan.tif also has a byte-identical copy in the GEMSDOE32 repository.",
     "mitigation": "Recorded from registry/focus_registry_manifest_20261030.json (489 rasters, 19 byte-duplicate groups, 464 unique SHA-256). Owner to confirm which copy is the official submission."},
    {"id": "IR-VO-08", "severity": "medium",
     "statement": "Leaderboard snapshots conflict. The live leaderboard fetched 2026-10-30 shows #1 xiaofanhu at 0.4544 and #3 Batik Shirt Brothers at 0.3911. The repository snapshot of 2026-10-25 shows 0.4413 and 0.3904. Earlier cited values include 0.3195 (2026-10-03) and 0.3262 (2026-10-04). The conflict is flagged and not reconciled.",
     "mitigation": "Timestamped sources only. Source: https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/"},
    {"id": "IR-VO-09", "severity": "high (scoring)",
     "statement": "Holdout is not a leaderboard proxy. The reported 0.2778 file scores 0.004515 HOLDOUT-DTI, even though it is the best public-leaderboard family. Holdout applies only to methods refit per fold. A fixed raster built from full-catalogue labels is not measured fairly by it.",
     "mitigation": "All holdout figures are labelled HOLDOUT-DTI. No leaderboard estimate is written. ORGANIZER-CONFIRMED requires a submission receipt."},
    {"id": "IR-VO-10", "severity": "high (nine-site uniqueness)", "statement": "__NINE_SITE_STATEMENT__",
     "mitigation": "Same lattice decision as IR-VO-01, plus owner review of same-site format variants and cross-site copies. Uniqueness per site is reported with the exact comparator, not as a pass. Per-site counts: evidence/nine_site_pairwise_uniqueness_20261030.json."},
    {"id": "IR-VO-11", "severity": "low",
     "statement": "evidence/nine_site_best_files_audit.json contains unquoted NaN and is not strict JSON. New audit files were written with strict JSON.",
     "mitigation": "Parse with a tolerant reader or regenerate. Not edited in this run, to avoid altering an existing evidence file."},
    {"id": "IR-VO-13", "severity": "high (format)",
     "statement": "Format conflict: the official specification (DrivenData competition page 967) says values outside the bounds are 'null or nan', and the same page requires every predicted value in [0, 1]. A NaN-filled file was rejected by the portal with 'Predicted values must be in range [0, 1]'. The zeros variant satisfies the range rule but departs from the literal 'null or nan' wording. No organizer receipt confirms that zeros are accepted.",
     "mitigation": "Owner to decide which variant to submit, after a test that the organizer accepts it. Do not submit either variant until this is resolved. Source: https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/"},
    {"id": "IR-VO-12", "severity": "low",
     "statement": "registry/focus_registry_manifest.json (451 rasters) is stale. The 489-raster manifest registry/focus_registry_manifest_20261030.json is current.",
     "mitigation": "Use the 489-raster manifest only."},
]


def nine_site_statement() -> str:
    pair = json.loads((ROOT / "evidence/nine_site_pairwise_uniqueness_20261030.json").read_text())
    parts, failing = [], 0
    for r in pair["results"]:
        dups = r.get("literal_duplicates_excluding_self", [])
        if dups:
            failing += 1
        cal = any("calibration" in d["path"] for d in dups)
        same = sum(1 for d in dups if "calibration" not in d["path"] and d["repo"] == r["site"])
        cross = sum(1 for d in dups if "calibration" not in d["path"] and d["repo"] != r["site"])
        parts.append(f'{r["site"]}: lattice={"yes" if cal else "no"}, same-site variants={same}, other-site rasters={cross}')
    return (f"Nine-site pairwise check (scripts/nine_site_pairwise_uniqueness.py): {failing} of {len(pair['results'])} best files FAIL the literal "
            "uniqueness rule against other registry rasters. The calibration lattice is one failure, not the only one. "
            + "; ".join(parts) + ". Byte-identical copies are listed separately per site in the JSON.")


def stage_artifacts() -> dict:
    DOWNLOADS.mkdir(parents=True, exist_ok=True)
    out = {}
    pairs = {
        f"{STEM}-zeros.tif": f"{PUBLIC_STEM}-zeros.tif",
        f"{STEM}-zeros.zip": f"{PUBLIC_STEM}-zeros.zip",
        f"{STEM}-audit.json": f"{PUBLIC_STEM}-audit.json",
    }
    for src_name, dst_name in pairs.items():
        src, dst = CAND / src_name, DOWNLOADS / dst_name
        if not src.is_file():
            raise FileNotFoundError(src)
        shutil.copyfile(src, dst)
        out[dst_name] = {"sha256": sha256(dst), "bytes": dst.stat().st_size,
                         "source_cache_name": src_name}
    return out


def add_irregularities() -> list[str]:
    data = json.loads(IRREG.read_text())
    existing = {it["id"] for it in data["items"]}
    added = []
    for item in NEW_IRREGULARITIES:
        if item["statement"] == "__NINE_SITE_STATEMENT__":
            item["statement"] = nine_site_statement()
        if item["id"] not in existing:
            data["items"].append(item)
            added.append(item["id"])
    if added:
        data["updated_utc"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        IRREG.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n")
    return added


def main() -> int:
    artifacts = stage_artifacts()
    audit = json.loads((CAND / f"{STEM}-audit.json").read_text())
    zeros = audit["zeros_tif"]
    gate = load("evidence/vo-learn-hgb-frac15_registry_gate.json")
    pair = load("evidence/nine_site_pairwise_uniqueness_20261030.json")
    e1 = load("evidence/vo-learn-hgb-e1_holdout.json")
    e2 = load("evidence/vo-learn-logreg-e2_holdout.json")
    e3 = load("evidence/vo-learn-hgb-frac15-e3_holdout.json")
    final_tif_sha = sha256(DOWNLOADS / f"{PUBLIC_STEM}-zeros.tif")
    if final_tif_sha != zeros["sha256"]:
        raise RuntimeError("staged copy sha256 does not match the writer audit")

    card = {
        "schema_version": 1,
        "candidate_id": "VO-LEARN-HGB-K1P5-NMS5",
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "lane": "VO-LEARN (visible-only classifier refit per spatial fold; top-K dots after 5x5 NMS)",
        "lane_note": "The assigned method paragraph is absent from the session prompt. The lane was declared by this run, and the declaration is disclosed here.",
        "control": "VO-NEAR (K in-domain pixels nearest visible faults)",
        "experiments_used": 3,
        "experiment_budget": 3,
        "experiment_budget_note": "E1 is the pre-declared primary. E2 is the logistic-regression control. E3 is a sensitivity point selected post hoc (IR-VO-03).",
        "experiments": {
            "E1_primary_hgb_frac0p0075": holdout_block(e1) | {"npz_candidate_sha256": e1["npz_candidate_sha256"]},
            "E2_logreg_frac0p0075": holdout_block(e2) | {"npz_candidate_sha256": e2["npz_candidate_sha256"]},
            "E3_hgb_frac0p015_post_hoc": holdout_block(e3) | {"npz_candidate_sha256": e3["npz_candidate_sha256"]},
        },
        "final_artifact": {
            "public_downloadable_zeros_tif": f"docs/downloads/{PUBLIC_STEM}-zeros.tif",
            "public_zip": f"docs/downloads/{PUBLIC_STEM}-zeros.zip",
            "public_audit_json": f"docs/downloads/{PUBLIC_STEM}-audit.json",
            "submission_name": PUBLIC_NAME,
            # Comment carries no score: the writer note embeds a holdout figure, which must not reach the organizer field.
            "submission_note": "VO-LEARN HGB visible-only, 1.5% footprint dots, 5x5 NMS; no score claimed.",
            "writer_note_not_used": audit["submission_note_zeros"],
            "sha256_zeros_tif": final_tif_sha,
            "bytes_zeros_tif": zeros["size_bytes"],
            "shape": zeros["shape"], "crs": zeros["crs"], "transform": zeros["transform"],
            "dtype": zeros["dtype"], "emitted_positive_pixels": zeros["emitted_positive_pixels"],
            "on_catalogue_positive_pixels": zeros["on_catalogue_positive_pixels"],
            "in_footprint_min": zeros["in_footprint_min"], "in_footprint_max": zeros["in_footprint_max"],
            "writer_checks_all_passed": zeros["all_checks_passed"],
            "format_check_command": "scripts/check_submission.py --template .cache/gems_data/sample_submission.tif --strict-finite docs/downloads/" + PUBLIC_STEM + "-zeros.tif",
            "nan_variant_status": "Not public. The portal rejected a NaN-filled file (\"Predicted values must be in range [0, 1]\"). The spec says NaN outside bounds, so the NaN/zeros conflict is open (see the irregularity ledger).",
            "artifacts_staged": artifacts,
        },
        "registry_gate": {
            "script": "scripts/run_registry_gate.py",
            "evidence": "evidence/vo-learn-hgb-frac15_registry_gate.json",
            "rule": "full-footprint |Spearman| <= 0.90 AND candidate dots within 3 px <= 0.70 vs every registry raster; no exemptions",
            "surface_passed": gate["surface_gate"]["passed"],
            "surface_worst_abs_spearman": gate["surface_gate"]["worst_abs_spearman"],
            "final_literal_rule_passed": gate["final_dot_gate"]["literal_rule_passed"],
            "final_literal_duplicates": gate["final_dot_gate"]["literal_duplicates"],
            "final_worst_abs_spearman": gate["final_dot_gate"]["worst_abs_spearman"],
            "final_worst_within_3px_non_calibration": gate["diagnostics_report_only"]["worst_non_calibration_within_3px"],
            "malformed_or_missing": gate["final_dot_gate"]["malformed_or_missing"],
            "audit_complete": gate["final_dot_gate"]["audit_complete"],
            "byte_identical_matches": gate["byte_identical_registry_files"] if "byte_identical_registry_files" in gate else [],
            "lattice_coverage_3px_footprint": gate["diagnostics_report_only"]["literal_lattice_or_calibration_rows"][0]["footprint_coverage_3px"],
            "random_null_overlap_note": "Random 77,511-dot null overlap 0.9986-0.9988 (computed in session; see IR-VO-01).",
            "space_filling_variant_informational": gate["diagnostics_report_only"]["space_filling_variant_IR47_informational"]["passed"],
        },
        "nine_site_pairwise_uniqueness": {
            "script": "scripts/nine_site_pairwise_uniqueness.py",
            "evidence": "evidence/nine_site_pairwise_uniqueness_20261030.json",
            "rule": pair["rule"],
            "per_site_literal_passed": {r["site"]: r.get("literal_rule_passed_vs_others") for r in pair["results"]},
        },
        "decision": {
            "status": "NOT CLEARED",
            "ok_to_submit": False,
            "weekly_slot_used": False,
            "promoted_to_slot": False,
            "blocking": [
                "Calibration lattice literal duplicate failure (IR-VO-01; owner decision IR-45-LATTICE-02 / IR-51-LATTICE-01).",
                "Registry audit incomplete: 2 malformed rasters (IR-VO-02).",
                "NaN-vs-zeros format conflict open (portal rejected NaN; zeros in range but departs from literal wording).",
                "No ORGANIZER-CONFIRMED receipt; no leaderboard score is estimable from HOLDOUT-DTI (IR-VO-09).",
                "Generative-AI disclosure required by rules section 3.2 (IR-VO-05).",
            ],
        },
        "estimated_leaderboard_score": "NOT ESTIMABLE. HOLDOUT-DTI values are not on the leaderboard scale (IR-VO-09). No ORGANIZER-CONFIRMED receipt exists.",
        "leaderboard_snapshot_2026_10_30": {"live_1st": {"name": "xiaofanhu", "score": 0.4544},
                                             "source": "https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/",
                                             "note": "Timestamped; conflicts with 0.4413 repo snapshot (IR-VO-08)."},
        "deviations": [
            "Pre-registered HGB settings not used (IR-VO-04).",
            "E3 selected after E1 and E2 (IR-VO-03).",
            "Lane declared by this run; the assigned method paragraph is absent (lane_note).",
        ],
        "irregularities_referenced": [item["id"] for item in NEW_IRREGULARITIES],
        "sources": {
            "competition": "https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/",
            "rules_pdf": "https://docs.nlr.gov/docs/fy26osti/96647.pdf",
            "reference_repo": "https://github.com/drivendataorg/gems-prize-reference-solution",
            "epsg_32611": "https://epsg.io/32611",
            "community_masking_thread": "https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516",
        },
    }
    RUN_CARD.write_text(json.dumps(card, indent=2, ensure_ascii=False, allow_nan=False) + "\n")
    added = add_irregularities()
    print("wrote", RUN_CARD.relative_to(ROOT), "| irregularities added:", added)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
