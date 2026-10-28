#!/usr/bin/env python3
"""Build the evidence-first CTHG executive portal from the current run-card and audits."""
from __future__ import annotations

import html
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


def load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def esc(value: object) -> str:
    return html.escape(str(value))


def main() -> None:
    raise SystemExit("Historical portal builder disabled: it can publish an unsafe release claim. Use scripts/build_review_site.py.")
    card = load("run_card.json")
    audit = load("evidence/nine_site_best_files_audit.json")
    nine_run = load("evidence/nine_site_refreshed_audit_20261028.json")
    experiments = load("evidence/apart3_cthg_dhc_experiments.json")
    (DOCS / "research").mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / "knowledge" / "03_why_02778_and_the_anatomy_of_the_family.md",
                 DOCS / "research" / "why-02778-reported-score.md")
    reg = card["correlation_and_overlap_vs_registry"]
    hr = card["holdout_dti"]["primary_hide_and_recover"]
    det = card["holdout_dti"]["detached_600m_segments"]
    sg = card["holdout_dti"]["off_catalogue_sgmc"]
    val = card["validator"]
    f = card["artifacts"]["primary_zeros_tif"]
    f_rel = str(Path(f).relative_to("docs"))
    zip_name = card["artifacts"]["zip_archive"]
    zip_rel = str(Path(zip_name).relative_to("docs"))
    sub_name = card["submission_name"]
    note = card["submission_note"]
    pairwise = audit["pairwise"]
    site_meta = {s["site"]: s for s in audit["sites"]}
    run_meta = {s["repo"]: s for s in nine_run["sites"]}

    focus_rows: list[str] = []
    for site in ["GEMSDOE24", "GEMSDOE25", "GEMSDOE27", "GEMSDOE28", "GEMSDOE30", "GEMSDOE31", "GEMSDOE32", "GEMSDOE33", "GEMSDOE36"]:
        rec = site_meta[site]
        rr = run_meta[site]
        comparisons = [p for p in pairwise if site in (p["a"], p["b"])]
        max_ov = max(max(p["a_dots_within_3px_of_b"] or 0.0, p["b_dots_within_3px_of_a"] or 0.0) for p in comparisons)
        max_rho = max(abs(p["spearman_footprint"]) for p in comparisons)
        duplicate = max_ov > 0.70 or max_rho > 0.90
        manifest = next((x for x in load("registry/focus_registry_manifest.json")["rasters"]
                         if x["repo"] == site and x["path"] == rec["file"] and x["sha256"] == rec["sha256"]), None)
        if manifest:
            href = f"https://github.com/buffedlizard55-lab/{site}/raw/{manifest['ref']}/{rec['file']}"
        else:
            href = f"https://github.com/buffedlizard55-lab/{site}"
        owner_score = rec["published_score_OWNER_REPORT"]
        focus_rows.append(f"""
        <tr>
          <td><a href="https://github.com/buffedlizard55-lab/{site}" target="_blank" rel="noopener"><b>{site}</b></a></td>
          <td><a href="{esc(href)}" target="_blank" rel="noopener"><code>{esc(Path(rec['file']).name)}</code></a><br><small>SHA-256 <code>{rec['sha256'][:12]}…</code>; {rec['positive_dots']:,} positive pixels</small></td>
          <td><b>{owner_score:.4f}</b><br><small>OWNER-REPORT; not receipt-verified</small></td>
          <td><b>Not defensibly estimable</b><br><small>HOLDOUT-DTI is not a leaderboard projection; no receipt-linked calibration set</small></td>
          <td><b class="bad">DUPLICATE</b><br><small>pairwise max overlap {max_ov:.1%}; max |ρ| {max_rho:.3f}</small></td>
        </tr>""")

    validator_items = [
        ("Single-band GeoTIFF", val["single_band"]),
        ("All values finite; no NaN in footprint", val["finite"]),
        ("Values in [0, 1]", val["range_0_1"]),
        ("CRS matches reference EPSG:32611", val["crs_match"]),
        ("3730 × 3292 shape matches", val["shape_match"]),
        ("Affine transform matches", val["transform_match"]),
    ]
    checks_html = "".join(f'<li><span>{esc(label)}</span><b class="{"ok" if passed else "bad"}">{"PASS" if passed else "FAIL"}</b></li>' for label, passed in validator_items)

    arms = [("0.2778 reference diagnostic", experiments["baselines"]["CHAMPION_02778"])] + list(experiments["experiments"].items())
    arm_rows = []
    for title, arm in arms:
        h = arm["hide_and_recover_v3"]
        d = arm["detached_600m_segments"]
        s = arm["sgmc_off_catalogue_v3"]
        arm_rows.append(f'''<tr><td><b>{esc(title)}</b></td>
          <td><b>{h["pooled_dti"]:.6f}</b><small><br>HOLDOUT-DTI · {esc(h.get("evaluator_version", "GEMSDOE32-HIDE-RECOVER-v3.0"))}; n={h["n_withheld_positives"]:,}; 95% CI [{h["ci95"][0]:.6f}, {h["ci95"][1]:.6f}]</small></td>
          <td><b>{d["pooled_dti"]:.6f}</b><small><br>HOLDOUT-DTI · detached-600m; n={d["n_withheld_positives"]:,}; 95% CI [{d["ci95"][0]:.6f}, {d["ci95"][1]:.6f}]</small></td>
          <td><b>{s["prevalence_calibrated_dti"]:.6f}</b><small><br>HOLDOUT-DTI · {esc(s.get("evaluator_version", "GEMSDOE32-SGMC-CAL-v3.0"))}; n={s["n_withheld_positives"]:,}; 95% CI [{s["calibrated_ci95"][0]:.6f}, {s["calibrated_ci95"][1]:.6f}]</small></td></tr>''')

    download = f"""<div class="hero">
      <div class="status negative">NO FILE AUTHORIZED · DO NOT SUBMIT ({esc(card['verdict'].upper())})</div>
      <h1>CTHG-DHC: a new, automatically validated GeoTIFF</h1>
      <p class="lead">Download is available for research and review. It is <strong>not authorized for a competition slot</strong>: literal all-registry uniqueness fails, and the separate weekly selector has not approved it.</p>
      <div class="buttons"><a class="button primary" href="{esc(f_rel)}" download>Download research GeoTIFF (.tif)</a><a class="button" href="{esc(zip_rel)}" download>Download single-TIFF ZIP</a><a class="button" href="research/h-apart3-2-cthg-dhc-preregistration-20261028.md">Read preregistration</a></div>
      <div class="grid">
        <div><label>File</label><code>{esc(Path(f).name)}</code></div>
        <div><label>SHA-256</label><code>{esc(card['raster_sha256'])}</code></div>
        <div><label>Submission name (for selector, not authorization)</label><code>{esc(sub_name)}</code></div>
        <div><label>Suggested note ({len(note)}/140 chars)</label><code>{esc(note)}</code></div>
      </div>
      <p class="reason"><b>Stop reason:</b> candidate dots overlap an existing registered 5-pixel calibration lattice at <b>{card['correlation_and_overlap_vs_registry']['literal_5px_calibration_lattice_probe']['within_3px_fraction']:.2%}</b>, and exceed the 70% limit against dense registered rasters. The protocol says no density or lattice exemptions. The source itself is explicitly a calibration raster, but the current rules say “any registry raster”; therefore we fail closed instead of calling this unique. A second critical issue is <code>IR-CTHG-BAND6-TC-02</code>: CTHG labels Band 6 (<code>tc</code>) as magnetic tilt, while the repository’s prior forensic record identifies it as airborne radiometric Total Count. The claimed physical tilt mechanism is unverified. The artifact is not scientifically promoted.</p>
    </div>"""

    summary = f"""<section class="section"><h2>Executive summary</h2>
      <p>Three named pipeline arms were evaluated, but prior exploratory sweeps mean this is not a valid prospective preregistration and total experiment/time-budget compliance is not claimed. A post-run scientific audit also found that CTHG and inherited BHGC features treated Band 6 (tc) as magnetic tilt even though prior repository forensics identify it as radiometric Total Count (IR-CTHG-BAND6-TC-02). Thus the claimed tilt geology is unverified. The candidate has an improved off-catalogue SGMC diagnostic against the 0.2778 reference; however, primary hide-and-recover and detached paired intervals overlap the reference, and literal registry uniqueness fails. This is a negative research result, not evidence of a higher live leaderboard score.</p>
      <div class="metrics">
       <article><label>HOLDOUT-DTI · GEMSDOE32-HIDE-RECOVER-v3.0</label><strong>{hr['pooled_dti']:.6f}</strong><small>n={hr['n_withheld_positives']:,}; 95% CI [{hr['ci95'][0]:.6f}, {hr['ci95'][1]:.6f}]</small></article>
       <article><label>HOLDOUT-DTI · detached ≥600 m v3.0</label><strong>{det['pooled_dti']:.6f}</strong><small>n={det['n_withheld_positives']:,}; 95% CI [{det['ci95'][0]:.6f}, {det['ci95'][1]:.6f}]</small></article>
       <article><label>HOLDOUT-DTI · SGMC-CAL-v3.0</label><strong>{sg['prevalence_calibrated_dti']:.6f}</strong><small>n={sg['n_withheld_positives']:,}; 95% CI [{sg['calibrated_ci95'][0]:.6f}, {sg['calibrated_ci95'][1]:.6f}]</small></article>
       <article><label>Pre-placement surface |Spearman|</label><strong>{reg['max_abs_surface_spearman']:.4f}</strong><small>below 0.90 threshold; surface passes</small></article>
       <article><label>Final dot overlap · literal maximum</label><strong class="bad">{reg['literal_5px_calibration_lattice_probe']['within_3px_fraction']:.2%}</strong><small>exceeds 70% protocol ceiling; uniqueness fails</small></article>
      </div>
      <p><b>Important score distinction:</b> HOLDOUT-DTI is a local diagnostic, not an organizer leaderboard score or reliable projection. All historical live scores below are OWNER-REPORTS based on supplied repository data; this checkout has no organizer submission-page receipts tying each score to an artifact hash. <b>Protocol accounting:</b> the final pipeline has three named arms, but additional exploratory placement/holdout sweeps occurred and exact cumulative experiment/time accounting was not retained. Therefore strict three-experiment/two-hour compliance is not claimed.</p>
    </section>"""

    sources = """<section class="section"><h2>Verified/primary source links and caveats</h2><ul>
      <li><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/">DrivenData competition 306 landing page</a> and <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/">leaderboard</a> (login required for submissions / receipts).</li>
      <li><a href="https://github.com/drivendataorg/gems-prize-reference-solution">DrivenData reference solution</a>.</li>
      <li><a href="https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and">USGS GeoDAWN data release</a>, DOI <a href="https://doi.org/10.5066/P93LGLVQ">10.5066/P93LGLVQ</a>.</li>
      <li><a href="https://gbcge.org/current-projects/ingenious/">Great Basin Center for Geothermal Energy INGENIOUS project</a>; <a href="https://gdr.openei.org/submissions/1391">DOE GDR submission 1391</a>.</li>
      <li><a href="https://www.usgs.gov/3d-elevation-program">USGS 3DEP</a> and <a href="https://epsg.io/32611">EPSG:32611</a>.</li>
      <li>Potential-field fundamentals: <a href="https://doi.org/10.1017/CBO9780511549816">Blakely (1995)</a>; tilt interpretation: <a href="https://doi.org/10.1016/0926-9851(94)90022-1">Miller &amp; Singh (1994)</a>. The exact fluvial-chi citation is not resolved in the current source ledger; do not treat the method name as literature verification.</li>
    </ul><p class="muted">The competition data are mirrored from public project repositories because DrivenData data files are login-walled. Manifest hashes verify those mirrors, not organizer authentication. No score receipt or slot selection was accessed. The supplied prompt gives two incompatible “current high score” values (0.3195 and 0.4413); neither was independently verified, so neither is used as a target or projection.</p></section>"""

    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>ApartGEMSDOE3 · CTHG research &amp; submission audit</title><style>
:root{{--bg:#080d19;--card:#101a2e;--line:#26344f;--text:#e7edf8;--muted:#9baac2;--cyan:#6ed5ff;--green:#43d9a3;--red:#ff737d;--amber:#ffc96b}}*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--text);font:16px/1.55 Inter,system-ui,sans-serif}}a{{color:var(--cyan)}}main{{max-width:1180px;margin:auto;padding:24px}}header{{border-bottom:1px solid var(--line);padding:14px 24px;position:sticky;top:0;background:#080d19ee;backdrop-filter:blur(12px);z-index:2}}.nav{{max-width:1180px;margin:auto;display:flex;flex-wrap:wrap;gap:18px;align-items:center}}.brand{{font-weight:800;margin-right:auto}}.hero,.section{{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:24px;margin:20px 0}}.hero{{border-color:#bc5360;background:linear-gradient(130deg,#27151e,#101a2e 65%)}}h1{{font-size:clamp(1.8rem,4vw,3rem);line-height:1.1;margin:.6rem 0}}h2{{margin-top:0}}.lead{{font-size:1.1rem;max-width:850px}}.status{{display:inline-block;border:1px solid var(--red);color:#ff9aa1;border-radius:30px;padding:5px 12px;font-weight:800;letter-spacing:.04em}}.buttons{{display:flex;flex-wrap:wrap;gap:10px;margin:18px 0}}.button{{background:#1b2943;border:1px solid #425b82;border-radius:9px;padding:11px 16px;text-decoration:none;color:var(--text);font-weight:700}}.primary{{background:#134c43;border-color:#32c89c;color:#d9fff1}}.grid,.metrics{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px;margin-top:18px}}.grid>div,.metrics article{{padding:14px;background:#0a1222;border:1px solid var(--line);border-radius:10px}}label{{display:block;color:var(--muted);font-size:.78rem;text-transform:uppercase;font-weight:700;margin-bottom:6px}}code{{overflow-wrap:anywhere;font: .82rem ui-monospace,monospace;color:#dce9ff}}.metrics strong{{display:block;font:800 1.55rem ui-monospace,monospace;color:var(--green)}}.metrics small,.muted,small{{color:var(--muted)}}.bad{{color:var(--red)!important}}.reason{{background:#30171d;border-left:4px solid var(--red);padding:12px 16px;border-radius:6px;margin-top:18px}}.tablewrap{{overflow:auto;border:1px solid var(--line);border-radius:10px}}table{{border-collapse:collapse;width:100%;min-width:1050px;font-size:.88rem}}th,td{{padding:11px;text-align:left;vertical-align:top;border-bottom:1px solid var(--line)}}th{{background:#17243b;color:#c4d0e3;text-transform:uppercase;font-size:.74rem}}tr:last-child td{{border:0}}.badge{{font-weight:800}}.good{{color:var(--green)}}li{{margin:.55rem 0}}footer{{padding:28px;text-align:center;border-top:1px solid var(--line);color:var(--muted)}}@media(max-width:650px){{main{{padding:12px}}.hero,.section{{padding:17px}}}}
</style></head><body><header><nav class="nav"><span class="brand">ApartGEMSDOE3 · CTHG-DHC</span><a href="index.html">Overview</a><a href="executive-summary.html">Executive summary &amp; site comparison</a><a href="submissions.html">Artifacts &amp; validator receipt</a><a href="research/h-apart3-2-cthg-dhc-preregistration-20261028.md">Preregistration</a><a href="data/feed.json">Current feed</a><a href="data/latest-run-card.json">Run card JSON</a></nav></header><main>{download}{summary}
    <section class="section"><h2>Three preregistered experiment results</h2><p>All entries below are HOLDOUT-DTI diagnostics, not organizer leaderboard scores. Exact evaluator versions, withheld-positive counts, and 95% CIs are shown for each metric. Paired spatial-block CI for HR vs the reference includes zero; it is not a statistically established HR improvement.</p><div class="tablewrap"><table><thead><tr><th>Arm</th><th>Hide-and-recover</th><th>Detached ≥600 m</th><th>Off-catalogue SGMC-cal</th></tr></thead><tbody>{''.join(arm_rows)}</tbody></table></div></section>
    <section class="section"><h2>9-site executive comparison</h2><p>Each link points to the pinned GitHub artifact. The scores are OWNER-REPORTS copied from the supplied project history; this checkout does not contain organizer receipts tying each score to a file hash. Historical score reports are not local score estimates. The pairwise uniqueness rule is literal: duplicate if any pair has &gt;70% of dots within 3 px or |Spearman| &gt;0.90.</p><div class="tablewrap"><table><thead><tr><th>Site</th><th>Best reported historical file</th><th>Reported live score</th><th>Leaderboard estimate</th><th>Unique among listed site files?</th></tr></thead><tbody>{''.join(focus_rows)}</tbody></table></div>
    <p><b>Interpretation:</b> all selected historical files are duplicates under at least one pairwise gate. Retrospective static raster checks are omitted from this table because they are not fold-local model OOF and cannot support a leaderboard estimate. The 0.2778 report is the highest of the nine supplied historical values, but is not backed by an organizer receipt in this checkout. Do not resubmit a historical raster.</p></section>
    <section class="section"><h2>Why the H33-2-B2 artifact is reported at 0.2778</h2><p><b>Evidence status: OWNER-REPORT.</b> The repository’s corrected forensic note records a nested H19-5 family: dense ridge surface → 1.5-pixel thinning → 2.8-pixel thinning → B=1 then B=2 catalogue collar pruning. It does not contain the organizer receipt that binds the reported 0.2778 to the exact file hash, so causality is not established.</p><p>The plausible metric-level explanation is that a 300 m triangular distance kernel credits nearby emitted pixels, while false-positive mass is accumulated across the prediction field. Thinning redundant adjacent ridge pixels can therefore reduce false-positive cost while preserving local coverage of hidden traces. Increasing the catalogue collar can suppress pixels that are near known faults; it can also remove useful detections. The reported score ladder alone cannot identify hidden truth, weighted TP/FP/FN, per-pixel marginal credit, or prove that B=2 caused the score change. See <a href="research/why-02778-reported-score.md">the corrected, evidence-limited forensic note</a>.</p></section>
    <section class="section"><h2>Candidate validation (automatic, no human inspection)</h2><ul>{checks_html}</ul><p>Grid from owner-mirrored competition sample template, SHA-pinned in <code>registry/ci_format_manifest.json</code>; mirror consistency is not organizer authentication. The validator output for the TIFF is included in <a href="data/latest-run-card.json">the run card</a>.</p></section>
    <section class="section"><h2>How to submit (only after separate selector approval)</h2><ol><li>Download the research GeoTIFF above; current verdict is negative for upload.</li><li>Do not upload while <code>ok_to_submit=false</code>. A separate weekly selector must approve a slot; this run used no slot.</li><li>If selected later: open the <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/">official competition 306</a> submission form, upload the single-band <code>.tif</code> (or single-file ZIP), use the submission name and note above, and preserve the resulting organizer receipt.</li><li>Do not use the unrelated /309 URL in older repository pages. Competition identifiers 306 vs 309 have appeared in prior docs; use competition 306 as specified in the official-source link and flag any portal mismatch.</li></ol></section>
    {sources}
    <section class="section"><h2>Run card</h2><p>Full machine-readable values and evidence:</p><ul><li><a href="data/latest-run-card.json">Current CTHG run card</a></li><li><a href="../evidence/apart3_cthg_dhc_experiments.json">Three-experiment ledger</a> (repository file)</li><li><a href="../evidence/apart3_cthg_dhc_registry_uniqueness.json">Registry uniqueness audit</a></li><li><a href="../evidence/nine_site_best_files_audit.json">Nine-site exact hash and pairwise audit</a></li></ul></section>
    </main><footer>H-APART3-2 · Candidate research artifact only · no leaderboard score guaranteed · slot selector not run</footer></body></html>"""
    (DOCS / "index.html").write_text(page, encoding="utf-8")
    (DOCS / "executive-summary.html").write_text(page, encoding="utf-8")
    (DOCS / "executive-summary" / "index.html").parent.mkdir(parents=True, exist_ok=True)
    nested_page = (page
        .replace('href="data/', 'href="../data/')
        .replace('href="downloads/', 'href="../downloads/')
        .replace('href="research/', 'href="../research/')
        .replace('href="executive-summary.html"', 'href="../executive-summary.html"')
        .replace('href="submissions.html"', 'href="../submissions.html"')
        .replace('href="../evidence/', 'href="../../evidence/'))
    (DOCS / "executive-summary" / "index.html").write_text(nested_page, encoding="utf-8")
    (DOCS / "submissions.html").write_text(page, encoding="utf-8")
    # Retire legacy pages whose prior-session authorization/metrics no longer apply.
    legacy_notice = '''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Archived research · ApartGEMSDOE3</title><style>body{font:16px/1.6 system-ui;background:#080d19;color:#e7edf8;max-width:900px;margin:10vh auto;padding:24px}section{background:#101a2e;border:1px solid #26344f;border-radius:14px;padding:24px}a{color:#6ed5ff}.bad{color:#ff737d;font-weight:800}</style></head><body><section><h1>Archived page — do not use for submission status</h1><p class="bad">Legacy claims and links have been superseded. Current candidate is a research artifact only; literal all-registry uniqueness failed and upload is not authorized.</p><p>Read the <a href="index.html">current executive portal</a>, the <a href="data/latest-run-card.json">current run card</a>, and the <a href="../README.md">project README</a>.</p></section></body></html>'''
    for name in ("research.html", "hypotheses.html", "leaderboard.html", "sources.html"):
        (DOCS / name).write_text(legacy_notice, encoding="utf-8")
    release_page = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Release status · ApartGEMSDOE3</title><style>body{{font:16px/1.6 system-ui;background:#080d19;color:#e7edf8;max-width:900px;margin:8vh auto;padding:24px}}article{{background:#26151d;border:2px solid #ff737d;border-radius:16px;padding:24px}}a{{color:#6ed5ff}}code{{overflow-wrap:anywhere}}</style></head><body><article><h1>NO FILE AUTHORIZED · DO NOT SUBMIT</h1><p>Current candidate <code>{esc(Path(f).name)}</code> is a research artifact only. It passes local format checks but fails literal all-registry uniqueness and scientific integrity. The weekly selector has not approved a slot.</p><p>Critical issue <code>IR-CTHG-BAND6-TC-02</code>: the implementation used Band 6 <code>tc</code> as magnetic tilt despite the repository forensic record identifying it as radiometric total count.</p><p><a href="index.html">Current executive portal</a> · <a href="data/latest-run-card.json">Run card</a> · <a href="repo-review-2026-10-28.md">Full review</a></p></article></body></html>'''
    (DOCS / "release-status.html").write_text(release_page, encoding="utf-8")
    site_data = {"run_card": card, "nine_site_best_files_audit": audit,
                 "registry_uniqueness": load("evidence/apart3_cthg_dhc_registry_uniqueness.json")}
    (DOCS / "assets" / "site-data.json").write_text(json.dumps(site_data, indent=2) + "\n", encoding="utf-8")
    feed_path = DOCS / "data" / "feed.json"
    if feed_path.exists():
        feed = json.loads(feed_path.read_text(encoding="utf-8"))
        feed["generated_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
        feed["current_status"] = load("registry/current_status.json")
        feed["current_candidate"] = {"run_card": "run_card.json", "experiments": "evidence/apart3_cthg_dhc_experiments.json", "registry_audit": "evidence/apart3_cthg_dhc_registry_uniqueness.json", "verdict": card["verdict"], "ok_to_submit": card["ok_to_submit"]}
        feed["submission"] = {"candidate_id": card["candidate_id"], "file": card["artifacts"]["primary_zeros_tif"], "sha256": card["raster_sha256"], "submission_name": card["submission_name"], "submission_note": card["submission_note"], "download_ok_for_research": True, "ok_to_submit": card["ok_to_submit"], "slot_used": False, "selector_required": card["selector_required"], "verdict": card["verdict"]}
        feed["holdout"] = {"label": "HOLDOUT-DTI; local diagnostics only, not leaderboard scores/projections", "primary_hide_and_recover": hr, "detached_600m": det, "off_catalogue_sgmc_cal": sg}
        feed["leaderboard_note"] = "Historical official public snapshot in registry/current_status.json only; not refreshed during this site build. No current score for this team is claimed."
        feed_path.write_text(json.dumps(feed, indent=1, allow_nan=False) + "\n", encoding="utf-8")
    root_page = page.replace('href="downloads/', 'href="docs/downloads/').replace('href="data/', 'href="docs/data/').replace('href="executive-summary.html"', 'href="docs/executive-summary.html"').replace('href="submissions.html"', 'href="docs/submissions.html"').replace('href="research/', 'href="docs/research/').replace('href="../evidence/', 'href="evidence/').replace('href="assets/', 'href="docs/assets/')
    (ROOT / "index.html").write_text(root_page, encoding="utf-8")
    print("Built CTHG executive portal at docs/index.html and root index.html")


if __name__ == "__main__":
    main()
