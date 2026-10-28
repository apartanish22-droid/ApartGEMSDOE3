#!/usr/bin/env python3
"""Build a fail-closed review portal from pinned site-audit evidence and the latest negative run card."""
from __future__ import annotations

import html
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CURRENT_CARD = ROOT / "evidence" / "apart3_cthg_dhc_run_card.json"
SITE_AUDIT = ROOT / "evidence" / "nine_site_best_files_audit.json"
CURRENT_STATUS = ROOT / "registry" / "current_status.json"


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def _read_current_card() -> dict:
    card = json.loads(CURRENT_CARD.read_text(encoding="utf-8"))
    if card.get("verdict") != "negative" or card.get("ok_to_submit") is not False:
        raise SystemExit("Portal builder refuses a non-negative or upload-authorized card")
    if card.get("slot_used") is not False:
        raise SystemExit("Portal builder refuses a card that does not explicitly say no slot was used")
    return card


def _site_rows(audit: dict) -> tuple[str, list[dict]]:
    sites = audit["sites"]
    pairs = audit["pairwise"]
    rows: list[str] = []
    summaries: list[dict] = []
    for site in sites:
        name = site["site"]
        peers = [p for p in pairs if p["a"] == name or p["b"] == name]
        if len(peers) != len(sites) - 1:
            raise SystemExit(f"Expected eight pairwise comparisons for {name}, got {len(peers)}")
        max_rho = max(abs(float(p["spearman_footprint"])) for p in peers)
        directional = [
            float(p["a_dots_within_3px_of_b"] if p["a"] == name else p["b_dots_within_3px_of_a"])
            for p in peers
        ]
        max_overlap = max(directional)
        duplicate = max_rho > 0.90 or max_overlap > 0.70
        summaries.append({"site": name, "max_abs_spearman": max_rho, "max_peer_overlap": max_overlap, "duplicate": duplicate})
        score = float(site["published_score_OWNER_REPORT"])
        rows.append(
            "<tr>"
            f'<td><a href="https://github.com/buffedlizard55-lab/{esc(name)}">{esc(name)}</a></td>'
            f'<td><code>{esc(site["leaderboard_name"])}</code></td>'
            f'<td>OWNER-REPORT {score:.4f}<br><small>not an organizer receipt</small></td>'
            '<td>Not estimable<br><small>No validated holdout-to-live-score calibration</small></td>'
            f'<td>{"NOT UNIQUE in this nine-site cohort" if duplicate else "No pairwise threshold breach"}<br>'
            f'<small>max |ρ| {max_rho:.3f}; max directional 3 px overlap {100*max_overlap:.1f}%</small></td>'
            '<td>Do not resubmit prior artifact</td>'
            "</tr>"
        )
    return "\n".join(rows), summaries


def build_page(card: dict, audit: dict, status: dict) -> str:
    rows, summaries = _site_rows(audit)
    candidate = card["candidate_id"]
    artifact = card.get("artifacts", {}).get("primary_zeros_tif", "")
    sha = card.get("raster_sha256", "")
    # Keep the literal gate result from the independent current uniqueness scan, not
    # the legacy "genuine-only" summary which excludes dense/lattice probes.
    uniqueness = json.loads((ROOT / "evidence" / "apart3_cthg_dhc_registry_uniqueness.json").read_text())
    overlap = uniqueness["worst_literal_overlap"]["within_3px_fraction"]
    holdout = card.get("holdout_dti", {}).get("primary_hide_and_recover", {})
    dti = holdout.get("pooled_dti")
    ci = holdout.get("ci95")
    n = holdout.get("n_withheld_positives")
    evaluator = holdout.get("evaluator_version")
    dti_text = "Not available in the current card"
    if dti is not None and ci is not None:
        dti_text = f"HOLDOUT-DTI {float(dti):.6f} (95% CI {float(ci[0]):.6f}–{float(ci[1]):.6f}); {int(n):,} withheld positives; {esc(evaluator)}. This is not a leaderboard score."

    best = max(audit["sites"], key=lambda item: float(item["published_score_OWNER_REPORT"]))
    headline = status.get("headline", "DO NOT SUBMIT")
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>ApartGEMSDOE3 · executive review</title>
<style>
:root{{--bg:#0b1220;--panel:#131e31;--line:#30415c;--text:#e8edf7;--muted:#a9bad1;--cyan:#82d9fa;--red:#ffb3b8;--gold:#f7d77e}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--text);font:16px/1.62 system-ui,sans-serif}}.wrap{{max-width:1180px;margin:auto;padding:24px}}header{{background:#101d32;border-bottom:1px solid var(--line)}}h1{{font-size:clamp(2rem,5vw,3rem);line-height:1.1;margin:.2em 0}}h2{{margin:.1em 0 .45em}}section{{background:var(--panel);border:1px solid var(--line);border-radius:14px;margin:20px 0;padding:24px}}.eyebrow{{color:var(--cyan);letter-spacing:.12em;font-weight:700}}.alert{{padding:18px;background:#46232a;border:1px solid #a55a64;border-radius:10px;color:var(--text)}}.alert strong{{font-size:1.25rem;color:#fff}}a{{color:var(--cyan)}}small,.muted{{color:var(--muted)}}code{{overflow-wrap:anywhere;color:#fff}}.scroll{{overflow:auto}}table{{border-collapse:collapse;width:100%;min-width:1000px}}th,td{{text-align:left;vertical-align:top;padding:12px;border-bottom:1px solid #40516b}}th{{color:var(--cyan)}}.pill{{display:inline-block;border-radius:999px;padding:3px 10px;background:#48252a;color:#ffd7d9;font-weight:700}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:12px}}.metric{{padding:14px;background:#0d1728;border:1px solid var(--line);border-radius:10px}}li{{margin:.45em 0}}.cta{{font-weight:700;color:var(--red)}}
</style></head><body>
<header><div class="wrap"><p class="eyebrow">APARTGEMSDOE3 · REVIEWED {esc(card.get("generated_utc", ""))} UTC</p><h1>Executive summary</h1>
<div class="alert"><strong>DO NOT SUBMIT — no candidate has passed all release gates.</strong>
<p>{esc(headline)}</p><p><span class="pill">No weekly slot used</span> &nbsp; No new unique, authorized submission is available to download. A local format pass is not submission authorization.</p></div></div></header>
<main class="wrap">
<section><h2>Decision at a glance</h2><div class="grid">
<div class="metric"><strong>Best supplied score among the nine sites</strong><br>{esc(best['site'])}: OWNER-REPORT {float(best['published_score_OWNER_REPORT']):.4f}<br><small>Score claim supplied in project records; no organizer receipt is attached.</small></div>
<div class="metric"><strong>Expected live score for this candidate</strong><br>Not estimable<br><small>HOLDOUT-DTI is not a calibrated leaderboard projection.</small></div>
<div class="metric"><strong>Current candidate</strong><br>{esc(candidate)}<br><small>Negative/research-only; scientific mapping and uniqueness gates failed.</small></div>
<div class="metric"><strong>Download decision</strong><br><span class="cta">No submission download recommended</span><br><small>Current TIF is for audit only; do not upload it.</small></div>
</div></section>
<section><h2>Nine-site results and uniqueness audit</h2>
<p>All scores below are <strong>OWNER-REPORT</strong> values from the supplied submission log, not organizer-confirmed receipts. “Not estimable” means we will not invent an expected live score. The prior files have been pairwise compared on the competition footprint using the stated |Spearman| &gt; 0.90 or directional within-3-pixel overlap &gt; 70% rules. This is a cohort comparison only; it does not certify uniqueness against the full registry.</p>
<div class="scroll"><table><thead><tr><th>Site</th><th>Reported highest-scoring file</th><th>Reported score / provenance</th><th>New live-score estimate</th><th>Unique among these nine?</th><th>Recommendation</th></tr></thead><tbody>{rows}</tbody></table></div>
<p>The current winner by reported score is <strong>{esc(best['site'])}</strong> ({float(best['published_score_OWNER_REPORT']):.4f}, OWNER-REPORT). The table's pairwise flags show why a site's historical best is not a novel candidate: the listed winners are nearly identical or exceed the literal duplicate threshold relative to other members of this nine-site set. Do not reuse them as submissions.</p>
<p>Why the GEMSDOE32 file may have scored highest: the supplied record says its file uses a 37,654-pixel binary prediction mask with a denser, multiscale H33-style targeting strategy. A sparse, spatially structured mask can balance matched faults against false positives under a distance-tolerant DTI metric. This is a plausible mechanism, not a verified causal explanation: no submission receipt linked to that exact raster/hash is present here, and comparisons across owner-reported scores do not isolate the cause. The result does not prove a higher score is achievable.</p>
<p><a href="research/why-02778-reported-score.md">Read the evidence-labeled H33 analysis</a> · <a href="research/next-hypotheses-20261028.md">Three research hypotheses, ranking and prerequisites</a> · <a href="data/nine_site_best_files_audit.json">Pairwise audit evidence</a></p></section>
<section><h2>Current candidate: {esc(candidate)}</h2>
<p><strong>Audit artifact (not approved for upload):</strong> {esc(artifact)}<br>SHA-256: <code>{esc(sha)}</code><br>Submission name/note should not be used for a competition upload while status is negative.</p>
<p><strong>HOLDOUT-DTI:</strong> {dti_text}</p>
<p><strong>Uniqueness:</strong> literal final-dot comparison found {100*float(overlap):.2f}% within 3 px of a registered calibration-lattice raster, above the 70% stop rule. The current result therefore fails the user's literal registry test. The research card also records IR-CTHG-BAND6-TC-02: a radiometric Total Count band was misidentified and interpreted as magnetic tilt. This invalidates the claimed physical mechanism pending correction and a complete rerun. <strong>Verdict: negative.</strong></p>
<p>Do not click or publish a submission download from this page. The artifact is retained only for reproducibility/audit. The earlier withdrawn CSHD file <code>apartgemsdoe3-h2-cshd-dual97-axial362-37654-20261028T063000Z-37b32d5b-zeros.tif</code> (SHA-256 <code>65f2ac84ff2c762495107487769a49e90919c5c6bf4a7948ca77e4a6971e5b38</code>; historical name <code>APARTGEMSDOE3-CSHD-37B32D5B</code>) is also audit-only, not a recommendation.</p><p>This decision can be changed only by a fresh, authorized lane run that passes every holdout, leakage, registry, format, science-integrity and separate selector gate.</p></section>
<section id="submission"><h2>How to submit — only after a later explicit approval</h2><ol>
<li>Use a newly generated, non-copied GeoTIFF from an explicitly assigned method lane. Do not spend a weekly slot while a hypothesis has not beaten a same-evaluator holdout baseline.</li>
<li>Run feature-by-feature leakage checks and the shared buffered whole-segment hide-and-recover evaluator. Keep every score labeled HOLDOUT-DTI with evaluator version, withheld count and 95% CI.</li>
<li>Run surface and final-dot registry comparisons; if either literal uniqueness gate fails, stop and mark negative. Validate exact saved bytes for one band, finite values in [0,1], and CRS/shape/transform equality to the sample template.</li>
<li>Only after the automated gates pass and the separate weekly-slot selector authorizes promotion: download the exact TIFF, open the competition-306 submission page, choose the file, enter the recorded unique name/note, submit, and save the organizer receipt. Verify the contest and quota on the official portal.</li>
</ol><p><strong>There is no file currently OK to submit.</strong> Local checks cannot guarantee organizer acceptance or predict the live score.</p></section>
<section><h2>Blockers and next actions</h2><ul>
<li>The parallel-run prompt references a single method paragraph assigning this lane, but no such paragraph was supplied. Do not invent the lane.</li>
<li>The current checkout has no cached full feature stack or full registry raster collection. It includes small manifests/receipts, not the underlying ignored .cache files. The pinned owner mirror supplies a sample template only; it is not organizer-authenticated.</li>
<li>Correct the shared Band 6 feature mapping and verify source metadata; invalidate dependent features/model caches, run leakage canaries and at most three experiments or two hours once a lane is assigned.</li>
<li>Resolve the literal registry failure protocol without silently excluding the calibration lattice; preserve pre-placement and final-dot comparisons.</li>
<li>Reconcile score-source conflicts from receipts. User-provided prompt cites multiple current leaderboard highs; no live access/receipt is asserted here.</li>
<li>Obtain the official competition data through permitted authenticated access, or keep all findings explicitly mirror-based. Do not claim organizer confirmation from third-party mirrors.</li>
</ul><p>Potentially useful official references for manual review: <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/">competition overview</a>, <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">problem statement</a>, <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/data/">data page</a>, <a href="https://github.com/drivendataorg/gems-prize-reference-solution">reference solution</a>, <a href="https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and">USGS GeoDAWN</a>, <a href="https://www.usgs.gov/3d-elevation-program">USGS 3DEP</a>, <a href="https://gbcge.org/current-projects/ingenious/">INGENIOUS</a>.</p></section>
</main></body></html>'''


def main() -> None:
    card = _read_current_card()
    audit = json.loads(SITE_AUDIT.read_text(encoding="utf-8"))
    status = json.loads(CURRENT_STATUS.read_text(encoding="utf-8"))
    page = build_page(card, audit, status)
    for rel in [
        "index.html", "docs/index.html", "docs/executive-summary.html",
        "docs/executive-summary/index.html", "docs/release-status.html",
        "docs/submissions.html", "docs/research.html", "docs/hypotheses.html",
        "docs/leaderboard.html", "docs/review.html", "docs/sources.html",
    ]:
        rendered = page
        if rel == "index.html":
            # The repository-root preview is not the Pages document root.
            rendered = rendered.replace('href="research/', 'href="docs/research/').replace('href="data/', 'href="docs/data/')
        (ROOT / rel).write_text(rendered, encoding="utf-8")
    # Keep the web feed synchronized with the same negative candidate card; never publish a stale promotion.
    feed_card = dict(card)
    feed_card.update({
        "portal_generated_utc": card.get("generated_utc"),
        "release_status": "negative",
        "ok_to_download_as_submission": False,
        "ok_to_submit": False,
        "download_note": "Audit artifact only; do not upload.",
    })
    (ROOT / "docs/data/latest-run-card.json").write_text(json.dumps(feed_card, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    # Keep a static-site-local copy so the published audit link works both in Pages and in tests.
    shutil.copyfile(SITE_AUDIT, ROOT / "docs/data/nine_site_best_files_audit.json")
    print("Built fail-closed portal and synchronized negative CTHG status feed")


if __name__ == "__main__":
    main()
