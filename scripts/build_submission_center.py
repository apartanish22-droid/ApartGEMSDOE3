#!/usr/bin/env python3
"""Build the Submission Center page (docs/submit.html) and its machine-readable twin.

Every number on the page is read from an evidence file. The page is fail-closed:
it states NOT CLEARED and links the downloadable file only as a research artifact.
Run after scripts/build_review_site.py (build_site.py calls both).
"""
from __future__ import annotations

import html
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"

RUN_CARD = ROOT / "evidence/vo-learn-hgb-frac15_run_card.json"
PAIRWISE = ROOT / "evidence/nine_site_pairwise_uniqueness_20261030.json"
FIXED = ROOT / "evidence/nine_site_fixed_file_audit_20261030.json"
IRREG = ROOT / "registry/irregularities.json"

PUBLIC_STEM = "apartgemsdoe3-vo-learn-hgb-frac15-233ea4b6"
RULES_PDF = "https://docs.nlr.gov/docs/fy26osti/96647.pdf"
COMPETITION = "https://www.drivendata.org/competitions/306/competition-doe-gems/"
PAGE_967 = "https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/"
LEADERBOARD = "https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/"
REF_REPO = "https://github.com/drivendataorg/gems-prize-reference-solution"
MASKING = "https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516"
EPSG = "https://epsg.io/32611"
GEODAWN_DOI = "https://doi.org/10.5066/P93LGLVQ"
TVERSKY = "https://en.wikipedia.org/wiki/Tversky_index"
INGENIOUS = "https://gbcge.org/ingenious/"
USGS_GEODAWN = "https://www.usgs.gov/"


def esc(v: object) -> str:
    return html.escape("" if v is None else str(v), quote=True)


def load(path: Path) -> dict:
    # The nine-site best-files audit contains unquoted NaN; accept it, but never write it back.
    return json.loads(path.read_text(), parse_constant=lambda c: None)


def is_calibration(path: str) -> bool:
    return "calibration" in path


def site_rows(pairwise: dict, fixed: dict) -> list[dict]:
    fixed_by_site = {r["site"]: r for r in fixed["rows"]}
    rows = []
    for r in pairwise["results"]:
        site = r["site"]
        fx = fixed_by_site.get(site, {})
        hold = fx.get("holdout_hide_recover", {})
        dups = r.get("literal_duplicates_excluding_self", [])
        non_cal = [d for d in dups if not is_calibration(d["path"])]
        same_site = [d for d in non_cal if d["repo"] == site]
        cross_site = [d for d in non_cal if d["repo"] != site]
        byte_dups = r.get("byte_identical_other_registry_files", [])
        rows.append({
            "site": site,
            "best_file": Path(r["file"]).name,
            "stated_OWNER_REPORT": r.get("stated_score_OWNER_REPORT"),
            "byte_identical_other_registry_files": byte_dups,
            "literal_failures_total": len(dups),
            "literal_failures_non_calibration": [f"{d['repo']}:{d['path']}" for d in non_cal],
            "literal_failures_same_site_variants": len(same_site),
            "literal_failures_cross_site_rasters": len(cross_site),
            "calibration_lattice_failure": any(is_calibration(d["path"]) for d in dups),
            "worst_within_3px": r.get("worst_within_3px"),
            "holdout_fixed_file_DIAGNOSTIC": {
                "label": "HOLDOUT-DTI (diagnostic; fixed raster, not a leaderboard proxy)",
                "evaluator": hold.get("evaluator_version"),
                "pooled_dti": hold.get("pooled_dti"),
                "ci95": hold.get("ci95"),
                "n_withheld_positives": hold.get("n_withheld_positives"),
            },
            "malformed_or_missing_in_comparison": r.get("malformed_or_missing_in_comparison"),
        })
    return rows


def rows_fixed_0278(rows: list[dict]) -> float | None:
    for r in rows:
        if r["site"] == "GEMSDOE32":
            return r["holdout_fixed_file_DIAGNOSTIC"].get("pooled_dti")
    return None


def fmt(x: float | None, nd: int = 4) -> str:
    return "—" if x is None else f"{x:.{nd}f}"


def ci(c: list | None) -> str:
    return "—" if not c or len(c) != 2 else f"[{c[0]:.4f}, {c[1]:.4f}]"


def site_table(rows: list[dict]) -> str:
    out = ['<div class="scroll"><table><thead><tr><th>Site</th><th>Best file</th>'
           '<th>Score (OWNER-REPORT, unverified)</th><th>Holdout diagnostic (HOLDOUT-DTI, fixed raster)</th>'
           '<th>Byte-identical copies elsewhere</th><th>Literal uniqueness vs other registry rasters</th></tr></thead><tbody>']
    for r in rows:
        h = r["holdout_fixed_file_DIAGNOSTIC"]
        if r["literal_failures_total"]:
            parts = []
            if r["calibration_lattice_failure"]:
                parts.append("calibration lattice")
            if r["literal_failures_same_site_variants"]:
                parts.append(f'{r["literal_failures_same_site_variants"]} same-site variant(s)')
            if r["literal_failures_cross_site_rasters"]:
                parts.append(f'{r["literal_failures_cross_site_rasters"]} other-site raster(s)')
            uniq = "<b>FAIL</b>: " + ", ".join(parts)
        else:
            uniq = "PASS"
        bytes_ = "; ".join(esc(x) for x in r["byte_identical_other_registry_files"]) or "none"
        out.append(
            f'<tr><td><b>{esc(r["site"])}</b></td><td><code>{esc(r["best_file"])}</code></td>'
            f'<td>{fmt(r["stated_OWNER_REPORT"])} <span class="muted">OWNER-REPORT · not an organizer receipt</span></td>'
            f'<td>{fmt(h.get("pooled_dti"), 4)} <span class="muted">CI95 {ci(h.get("ci95"))}, n={esc(h.get("n_withheld_positives"))}</span></td>'
            f'<td class="small">{bytes_}</td><td>{uniq}</td></tr>'
        )
    out.append("</tbody></table></div>")
    return "".join(out)


def experiments_table(card: dict) -> str:
    rows = []
    for key, e in card["experiments"].items():
        c, k = e["candidate"], e["control_VO_NEAR"]
        rows.append(
            f'<tr><td><code>{esc(key)}</code></td><td>{esc(e["learner"])}</td>'
            f'<td>{esc(e["frac_of_footprint"])}</td>'
            f'<td>{fmt(c["pooled_dti"])} <span class="muted">CI95 {ci(c["ci95"])}</span></td>'
            f'<td>{fmt(k["pooled_dti"])} <span class="muted">CI95 {ci(k["ci95"])}</span></td>'
            f'<td>{fmt(e["paired_candidate_minus_control"]["mean"])} <span class="muted">CI95 {ci(e["paired_candidate_minus_control"]["ci95"])}</span></td>'
            f'<td>{fmt(e["max_single_feature_canary_auc"], 3)}</td></tr>'
        )
    return ('<div class="scroll"><table><thead><tr><th>Experiment</th><th>Learner</th><th>Budget (frac)</th>'
            '<th>Candidate HOLDOUT-DTI</th><th>Control VO-NEAR HOLDOUT-DTI</th><th>Paired difference</th>'
            '<th>Canary max AUC</th></tr></thead><tbody>' + "".join(rows) + "</tbody></table></div>")


def leaderboard_table() -> str:
    items = [
        ("2026-10-03", "DARD", "0.3195", "registry/sources.json (earlier snapshot)"),
        ("2026-10-04", "nchuzhoy", "0.3262", "registry/sources.json (earlier snapshot)"),
        ("2026-10-25", "xiaofanhu", "0.4413", "repository snapshot (cited in session prompt)"),
        ("2026-10-30", "xiaofanhu", "0.4544", f'<a href="{LEADERBOARD}">live leaderboard fetch</a>'),
    ]
    body = "".join(f"<tr><td>{esc(d)}</td><td>{esc(n)}</td><td>{esc(s)}</td><td>{src}</td></tr>" for d, n, s, src in items)
    return ('<div class="scroll"><table><thead><tr><th>Date</th><th>#1 (name)</th><th>Score</th><th>Source</th></tr></thead>'
            f'<tbody>{body}</tbody></table></div><p class="muted">Conflicting snapshots are flagged, not reconciled (IR-VO-08). '
            'The public leaderboard may differ from the private scores that decide prizes (rules, section 3.2).</p>')


HYPOTHESES = [
    {
        "rank": 1, "id": "S-RING-VOLEARN",
        "title": "Catalogue-ring-aware VO-LEARN (distance-to-visible-catalogue weighting, fold-local)",
        "idea": "Within each fold, weight the classifier's candidate dots by their distance to visible catalogue traces (2-3 px ring), so the top-K budget favours the ring where the holdout and the fixed-file results both concentrate.",
        "gain_basis": "Highest expected gain of the four, on indirect evidence. The registry records a 2-px catalogue-flank removal (H33-2, live +0.004870) in the 0.2778 family. On the fixed-file holdout, sites 24, 25, 27 and 30 score 0.093-0.097 against 0.0045 for the 0.2778 file. The hypothesis that the holdout rewards catalogue-adjacent dots is not verified. Expected gain is unmeasured.",
        "cost": "Very low: one distance transform per fold; estimated about 5 minutes of compute.",
        "risk": "Metric-fitting risk: the ring may score on the holdout without helping the leaderboard, which masks known faults (community thread). Must be tested against E3 paired difference.",
        "validation": "One spatially blocked holdout run (not yet authorised). Pass if the paired difference against VO-NEAR exceeds the E3 paired difference (see the experiments table) with a CI that excludes zero.",
    },
    {
        "rank": 2, "id": "S-PERFOLD-QUANTILE",
        "title": "Per-fold quantile budget instead of one global top-K",
        "idea": "Replace the single global top-K with equal dots per fold cell, which reduces concentration in the highest-prevalence cells.",
        "gain_basis": "Medium-low: the per-cell results in E1 show uneven contributions; a balanced budget may reduce variance. Gain unmeasured.",
        "cost": "Low: a change to the selection step only.",
        "risk": "May lower the pooled score if the strongest cells carry real signal.",
        "validation": "Holdout run with the same frac and NMS radius; compare pooled DTI and paired CI.",
    },
    {
        "rank": 3, "id": "S-HGB-LOGREG-RANKAVG",
        "title": "Rank-average ensemble of the HGB and logistic-regression learners",
        "idea": "Average within-fold ranks of the two learners before top-K selection.",
        "gain_basis": "Low-medium: E2 (logreg, 0.0446) was below E1 (HGB, 0.0608) at the same budget, so an ensemble may not beat HGB alone. Gain unmeasured.",
        "cost": "Low: estimated about 2x the E1 runtime (E1 took 313 s).",
        "risk": "Two learners double the surface for leakage review.",
        "validation": "Holdout run; leakage canary must stay at or below 0.90 AUC for each feature.",
    },
    {
        "rank": 4, "id": "S-SCARP-GATED-VOLEARN",
        "title": "Scarp-coherence gate on VO-LEARN candidates (existing LiDAR channels)",
        "idea": "Keep only candidate dots where the 1 m LiDAR scarp channels (existing in the stack) show coherent step structure.",
        "gain_basis": "Low-medium on the 68-75% 3DEP coverage only (the registry notes 68-75% 3DEP coverage); the rest of the footprint would be unaffected or zeroed, which could cost real recall.",
        "cost": "Medium: coverage-aware gating and a validity mask.",
        "risk": "Coverage gaps can create artificial spatial structure, which the blocked holdout must catch.",
        "validation": "Holdout run restricted to the 3DEP-covered domain, reported separately.",
    },
]


def hypotheses_table() -> str:
    cards = []
    for h in HYPOTHESES:
        cards.append(
            f'<div class="card"><h3>#{h["rank"]} · {esc(h["title"])}</h3>'
            f'<p><span class="tag">proposal · not run · no slot</span> <code>{esc(h["id"])}</code></p>'
            f'<p><b>Idea.</b> {esc(h["idea"])}</p>'
            f'<p><b>Expected gain (unmeasured).</b> {esc(h["gain_basis"])}</p>'
            f'<p><b>Cost.</b> {esc(h["cost"])}</p>'
            f'<p><b>Risk.</b> {esc(h["risk"])}</p>'
            f'<p><b>Validation before any slot.</b> {esc(h["validation"])}</p></div>'
        )
    return "".join(cards)


def steps() -> str:
    items = [
        f'Read the rules and the scoring page: <a href="{RULES_PDF}">NLR official rules (Sept 2026)</a> and <a href="{PAGE_967}">DrivenData competition page 967</a>.',
        "Confirm that a single-band float32 GeoTIFF in EPSG:32611, 100 m, on the reference grid, has every predicted value in [0, 1]. Run scripts/check_submission.py --strict-finite on the exact file.",
        "Confirm the file's SHA-256 matches the run card before uploading.",
        "Check the live weekly limit on the DrivenData submission page (login-walled). The rules state three per week; the repository does not record a verified number (IR-VO-06).",
        "Write the narrative disclosure of generative-AI use required by rules section 3.2 (IR-VO-05).",
        "Submit only after every gate on this page passes and the owner clears the candidate. Use a short unique name and a comment that does not present a holdout figure as a score.",
        "Record the organizer receipt. Only then may the score be labelled ORGANIZER-CONFIRMED.",
    ]
    return "<ol>" + "".join(f"<li>{x}</li>" for x in items) + "</ol>"


def irregularity_list(card_ids: list[str], registry: dict) -> str:
    by_id = {it["id"]: it for it in registry["items"]}
    rows = []
    for iid in card_ids:
        it = by_id.get(iid)
        if it:
            rows.append(f'<li><b>{esc(iid)}</b> · severity: {esc(it["severity"])}. {esc(it["statement"])} <span class="muted">Mitigation: {esc(it["mitigation"])}</span></li>')
    return "<ul>" + "".join(rows) + "</ul>"


def sources_table() -> str:
    items = [
        (COMPETITION, "Competition page (login-walled data; public text)", "fetched 2026-10-30"),
        (PAGE_967, "Scoring and submission format: distance-weighted Tversky, alpha 0.2, beta 0.8, 300 m kernel; single-band float32 GeoTIFF in [0, 1], EPSG:32611, 100 m", "fetched 2026-10-30"),
        (LEADERBOARD, "Live leaderboard: #1 0.4544 (xiaofanhu)", "fetched 2026-10-30"),
        (RULES_PDF, "Official rules: one GeoTIFF, one raster layer, 100 m, whole GeoDAWN study area; three submissions per week; generative-AI narrative disclosure", "fetched 2026-10-30 (pages 1-3 of 7 read)"),
        (REF_REPO, "Reference solution by Prof. John Lipor; baseline notebook and environment files", "fetched 2026-10-30"),
        (MASKING, "Staff post: known USGS/INGENIOUS faults are masked during evaluation, including final re-evaluation", "fetched 2026-10-30"),
        (EPSG, "EPSG:32611 = WGS 84 / UTM zone 11N; central meridian -117, scale 0.9996, false easting 500000", "fetched 2026-10-30"),
        (GEODAWN_DOI, "GeoDAWN dataset DOI as cited in the rules PDF footnote", "DOI cited in rules; not re-fetched"),
        (TVERSKY, "Tversky index definition", "not re-fetched this session"),
        (INGENIOUS, "INGENIOUS project, cited in the scoring thread", "not re-fetched this session"),
    ]
    body = "".join(f'<tr><td><a href="{esc(u)}">{esc(u)}</a></td><td>{esc(d)}</td><td>{esc(s)}</td></tr>' for u, d, s in items)
    return ('<div class="scroll"><table><thead><tr><th>Link</th><th>What was checked</th><th>Status</th></tr></thead>'
            f'<tbody>{body}</tbody></table></div>')


def build(card: dict, rows: list[dict], registry: dict) -> str:
    cand = card["final_artifact"]
    gate = card["registry_gate"]
    blocking = "".join(f"<li>{esc(b)}</li>" for b in card["decision"]["blocking"])
    dl = f'downloads/{PUBLIC_STEM}-zeros.tif'
    zip_ = f'downloads/{PUBLIC_STEM}-zeros.zip'
    audit = f'downloads/{PUBLIC_STEM}-audit.json'
    gate_line = (
        f'surface |Spearman| worst {fmt(gate["surface_worst_abs_spearman"], 3)} (pass ≤ 0.90); '
        f'final worst |Spearman| {fmt(gate["final_worst_abs_spearman"], 3)}; '
        f'non-calibration within-3 px worst {fmt(gate["final_worst_within_3px_non_calibration"]["within_3px_fraction"], 3)} (pass ≤ 0.70); '
        f'<b>calibration lattice within-3 px {fmt(gate["final_literal_duplicates"][0]["within_3px_fraction"], 3)} (FAIL)</b>; '
        f'malformed or missing registry rasters: {gate["malformed_or_missing"]}; audit complete: {str(gate["audit_complete"]).lower()}.'
    )
    e1 = card["experiments"]["E1_primary_hgb_frac0p0075"]
    e3_hold = fmt(card["experiments"]["E3_hgb_frac0p015_post_hoc"]["candidate"]["pooled_dti"])
    file_hold = fmt(rows_fixed_0278(rows))
    body = f'''
<section class="alert"><strong>NOT CLEARED — DO NOT SUBMIT.</strong> The VO-LEARN candidate is format-valid, but it fails the literal registry duplicate gate on the calibration lattice, and the registry audit is incomplete. No weekly slot was used. There is no file currently OK to submit.
<ul>{blocking}</ul></section>

<section><h2>Decision at a glance</h2>
<p><b>Candidate:</b> <code>{esc(card["candidate_id"])}</code> · lane: {esc(card["lane"])} · control: {esc(card["control"])}.</p>
<p><b>Estimated leaderboard score:</b> {esc(card["estimated_leaderboard_score"])}</p>
<p><b>Experiments:</b> {card["experiments_used"]} of {card["experiment_budget"]} used. E1 is the pre-declared primary. E3 is post hoc (IR-VO-03).</p>
<p class="muted">Labels: HOLDOUT-DTI = spatially blocked hide-and-recover evaluation (evaluator {esc(e1["evaluator_version"])}). ORGANIZER-CONFIRMED = score from a submission-page receipt; none exists. OWNER-REPORT = repository-recorded owner claim, unverified.</p></section>

<section><h2>Executive summary by site</h2>
<p>Scores for the nine sites are <b>OWNER-REPORT</b> values recorded in the repository and are not verified. Holdout values are <b>HOLDOUT-DTI diagnostics on fixed rasters</b>: a fixed raster built from full-catalogue labels is not what the hide-and-recover holdout was designed to score, so these values are not leaderboard estimates. Uniqueness is the literal rule (full-footprint |Spearman| ≤ 0.90 and ≤ 70% of dots within 3 px) against every other registry raster, excluding the file's own bytes.</p>
{site_table(rows)}
<p class="small muted">The GEMSDOE30 best file is byte-identical to a copy stored in the GEMSDOE32 repository. That copy is outside the nine-site cohort, so the cross-site duplicate check above does not cover it (IR-VO-07). Full detail: <a href="evidence/nine_site_pairwise_uniqueness_20261030.json">pairwise uniqueness JSON</a> · <a href="evidence/nine_site_fixed_file_audit_20261030.json">fixed-file audit JSON</a>.</p>
</section>

<section><h2>Why 0.2778 scored highest, and whether it can be beaten</h2>
<p>The 0.2778 file (GEMSDOE32 <code>h33-h33-2-b2</code>) is built on a 0.2708 base by removing every dot within 2 px of the published catalogue. The registry records this as hypothesis H33-2, with a live-mirror gain of +0.004870 in 4 of 4 folds. Its score therefore reflects removal of catalogue-adjacent mass as well as detection; the owner-reported figures are not verified. The repository's own explanation is in <a href="knowledge/03_why_02778_and_the_anatomy_of_the_family.md">knowledge/03</a>.</p>
<p><b>Can it be beaten?</b> This session has not shown that. The candidate's HOLDOUT-DTI at E3 is {e3_hold} and is not on the leaderboard scale. The 0.2778 file scores {file_hold} on the same holdout. The two measures cannot be compared, so no leaderboard claim is made (IR-VO-09).</p></section>

<section><h2>Candidate: VO-LEARN, visible-only</h2>
<p>A classifier is refit on visible catalogue traces only, for each spatial fold. It ranks withheld pixels, and the top-K dots after 5 × 5 non-maximum suppression are emitted. The final refit uses all labels, and the dots on catalogue traces are masked to zero.</p>
{experiments_table(card)}
<p class="small muted">Canary: the highest single-feature AUC is {fmt(e1["max_single_feature_canary_auc"], 3)} (threshold 0.90); no feature is flagged for leakage. Paired difference = candidate minus VO-NEAR control (the K in-domain pixels nearest visible faults).</p>
<h3>Registry duplicate gate</h3>
<p>{gate_line}</p>
<p class="small muted">Gate script: <code>scripts/run_registry_gate.py</code> · evidence <a href="evidence/vo-learn-hgb-frac15_registry_gate.json">registry gate JSON</a>. The lattice covers 99.87% of the footprint within 3 px, and a uniform random dot set of the same size scores 0.9986-0.9988. The literal rule therefore cannot pass for any dot set above roughly 22,163 dots (IR-VO-01).</p>
</section>

<section><h2>Candidate file (audit copy, not cleared)</h2>
<div class="card">
<p><span class="tag tag-red">NOT CLEARED</span> This file is format-valid and in range. It must not be uploaded until the owner clears the calibration-lattice decision and the registry audit is complete. Per README rule 7, no download or submit call to action is shown for a candidate that has not passed every gate; the links below are audit copies only.</p>
<p>Audit copies: <a href="{dl}">GeoTIFF (zeros variant)</a> · <a href="{zip_}">ZIP</a> · <a href="{audit}">writer audit JSON</a></p>
<ul class="small">
<li>Name: <code>{esc(PUBLIC_STEM)}-zeros.tif</code> · proposed submission name: <code>{esc(cand["submission_name"])}</code></li>
<li>Comment (repository convention: 140 characters maximum): <code>{esc(cand["submission_note"])}</code> — the comment must not present the holdout figure as a score.</li>
<li>SHA-256: <code>{esc(cand["sha256_zeros_tif"])}</code> · {cand["bytes_zeros_tif"]:,} bytes</li>
<li>Grid: EPSG:32611, 100 m, {cand["shape"][1]} × {cand["shape"][0]}, float32, single band · positive pixels {cand["emitted_positive_pixels"]:,} · on-catalogue positives {cand["on_catalogue_positive_pixels"]}</li>
<li>Values in footprint: min {cand["in_footprint_min"]}, max {cand["in_footprint_max"]} · writer checks passed: {str(cand["writer_checks_all_passed"]).lower()}</li>
<li>Open issue: the official spec says NaN outside the bounds, but the portal rejected a NaN-filled file (“Predicted values must be in range [0, 1]”). The zeros variant is in range, but it departs from the literal wording (IR-VO-13). Acceptance is unconfirmed.</li>
</ul>
<p class="small muted">Format check: <code>{esc(cand["format_check_command"])}</code></p>
</div></section>

<section><h2>Leaderboard conflict (flagged, not resolved)</h2>{leaderboard_table()}</section>

<section><h2>Ranked new hypotheses</h2>
<p>These are <b>proposals only</b>. None has been run, and none has an estimated score. The ranking follows the strength of the measured evidence behind each idea and its cost. The top proposal must be validated on a spatially blocked holdout before any slot is used. No slot is authorised for this session.</p>
<div class="grid">{hypotheses_table()}</div></section>

<section><h2>Submission steps</h2>{steps()}</section>

<section><h2>Irregularities for owner review</h2>{irregularity_list(card["irregularities_referenced"], registry)}
<p class="muted">Full ledger: <a href="registry/irregularities.json">registry/irregularities.json</a> · run card: <a href="evidence/vo-learn-hgb-frac15_run_card.json">evidence/vo-learn-hgb-frac15_run_card.json</a></p></section>

<section><h2>Sources and verification</h2>{sources_table()}
<p class="muted">Every claim on this page traces to a file in the repository or to a link above. Items marked “not re-fetched this session” have not been verified in this session.</p></section>
'''
    return body


def page(body: str, generated: str) -> str:
    css = (":root{color-scheme:dark;--bg:#0b1220;--panel:#142238;--line:#30415c;--text:#e8edf7;--muted:#a8b7cc;"
           "--link:#8bd7fa;--alert:#4b2025;--ok:#1f4d3a}*{box-sizing:border-box}body{margin:0;background:var(--bg);"
           "color:var(--text);font:16px/1.6 system-ui,sans-serif}header{background:#111f35;border-bottom:1px solid var(--line)}"
           ".wrap{max-width:1120px;margin:auto;padding:20px}.brand{color:#8bd7fa;letter-spacing:.12em;font-size:.82rem}"
           "h1{margin:.15em 0;font-size:2rem}h2{margin-top:0}h3{margin:.3em 0}nav{display:flex;flex-wrap:wrap;gap:8px 18px;margin-top:14px}"
           "a{color:var(--link)}nav a{text-decoration:none}main section{background:var(--panel);border:1px solid var(--line);"
           "border-radius:12px;margin:18px 0;padding:22px}.alert{padding:16px;background:var(--alert);border:1px solid #e47b82;border-radius:8px}"
           ".card{background:#0f1b2e;border:1px solid var(--line);border-radius:10px;padding:16px;margin:10px 0}"
           ".grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:12px}"
           ".tag{display:inline-block;padding:2px 8px;border-radius:999px;background:#25344f;color:#cfe6ff;font-size:.85rem}"
           ".tag-red{background:#6b2a30;color:#ffd7da}.muted{color:var(--muted)}.small{font-size:.9rem}"
           ".scroll{overflow:auto}table{border-collapse:collapse;width:100%;min-width:720px}"
           "th,td{text-align:left;vertical-align:top;padding:10px;border-bottom:1px solid var(--line)}"
           "code{overflow-wrap:anywhere;color:#fff}li{margin:.4em 0}")
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>Submission Center · ApartGEMSDOE3</title><style>' + css + '</style></head><body>'
            '<header><div class="wrap"><div class="brand">APARTGEMSDOE3 · SUBMISSION CENTER · NOT CLEARED</div>'
            '<h1>Submission Center</h1><nav aria-label="Main navigation">'
            '<a href="index.html">Overview</a><a href="submit.html">Submission Center</a>'
            '<a href="executive-summary.html">Executive summary</a><a href="release-status.html">Release status</a>'
            '<a href="submissions.html">How to submit</a><a href="sources.html">Sources</a></nav></div></header>'
            '<main class="wrap">' + body + '</main>'
            f'<footer class="wrap small muted">Generated {esc(generated)} from evidence files. DO NOT SUBMIT.</footer>'
            '</body></html>\n')


def main() -> int:
    card = load(RUN_CARD)
    pairwise = load(PAIRWISE)
    fixed = load(FIXED)
    registry = load(IRREG)
    rows = site_rows(pairwise, fixed)
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    body = build(card, rows, registry)
    (DOCS / "submit.html").write_text(page(body, generated), encoding="utf-8")
    machine = {
        "schema_version": 1,
        "generated_utc": generated,
        "decision": card["decision"],
        "candidate_id": card["candidate_id"],
        "estimated_leaderboard_score": card["estimated_leaderboard_score"],
        "nine_site": rows,
        "run_card": "evidence/vo-learn-hgb-frac15_run_card.json",
    }
    (DOCS / "data").mkdir(parents=True, exist_ok=True)
    (DOCS / "data" / "submission_center.json").write_text(
        json.dumps(machine, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    print("wrote docs/submit.html and docs/data/submission_center.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
