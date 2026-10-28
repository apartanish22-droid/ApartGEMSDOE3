#!/usr/bin/env python3
"""Build a fail-closed research portal from the archived nine-site audit."""
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def esc(s):
    return html.escape(str(s), quote=True)

def main():
    card = json.loads((ROOT / 'run_card.json').read_text())
    if card.get('verdict') != 'negative' or card.get('ok_to_submit') is not False:
        raise SystemExit('Review portal expects a negative, non-authorized run card')
    audit = json.loads((ROOT / 'evidence/nine_site_best_files_audit.json').read_text())
    rows = []
    for s in audit['sites']:
        site = s['site']
        rows.append(f'<tr><td><a href="https://github.com/buffedlizard55-lab/{esc(site)}">{esc(site)}</a></td>'
                    f'<td><code>{esc(s["leaderboard_name"])}</code></td>'
                    f'<td>OWNER-REPORT {s["published_score_OWNER_REPORT"]:.4f}</td>'
                    '<td>Not estimable</td><td>Historical; not authorized</td></tr>')
    primary = Path(card['artifacts']['primary_zeros_tif']).name
    body = f'''<header><div class="wrap"><p class="eyebrow">APARTGEMSDOE3 · RESEARCH REVIEW</p><h1>Executive summary</h1>
    <div class="alert"><strong>DO NOT SUBMIT — no candidate has passed all required gates.</strong><p>No weekly slot has been used in this review. There is no defensible leaderboard-score estimate or verified unique new submission.</p></div></div></header>
    <main class="wrap"><section><h2>Download for audit only</h2><p>Historical CSHD: <a href="https://github.com/apartanish22-droid/ApartGEMSDOE3/blob/main/docs/downloads/{esc(primary)}">{esc(primary)}</a> · <code>{esc(card['raster_sha256'])}</code></p>
    <p>Historical name: <code>{esc(card['submission_name'])}</code>. This file passes local range/grid checks against a hash-pinned owner mirror, not an organizer-authenticated template. It fails the literal registry rule: the archived card reports 99.7583% of its dots within 3 pixels of a registry lattice. It also uses an inherited feature that misidentifies band 6 total count as magnetic tilt. <strong>Format-valid is not submit-ready.</strong></p>
    <p>The former promotion claim is withdrawn; the original card remains in the repository history and <a href="https://github.com/apartanish22-droid/ApartGEMSDOE3/blob/main/evidence/cshd_historical_promotion_card_20261028.json">historical evidence</a>. The current <a href="https://github.com/apartanish22-droid/ApartGEMSDOE3/blob/main/run_card.json">run card</a> is negative.</p></section>
    <section><h2>Nine-site comparison</h2><p>These are owner-reported historical results supplied by the user and recorded in the prior audit, not organizer receipts. They are not current leaderboard estimates. Previous files are for learning only; none is recommended for resubmission. Archived pairwise analysis found duplicate-family overlaps among these references; a new candidate must be compared against the full registry.</p>
    <div class="scroll"><table><thead><tr><th>Site</th><th>Reported best submission</th><th>Reported score</th><th>New submission estimate</th><th>Decision</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div>
    <p>GEMSDOE32 is the highest owner-reported result in this comparison. Pruning lower-value predictions could reduce false-positive mass, but hidden truth and receipt-linked evidence are unavailable; causality and an improvement above it are unproven. <a href="https://github.com/apartanish22-droid/ApartGEMSDOE3/blob/main/knowledge/03_why_02778_and_the_anatomy_of_the_family.md">Read the analysis and limitations</a>.</p></section>
    <section><h2>How to submit when authorized</h2><ol><li>Generate a new raster within the assigned lane and run the shared holdout, feature canaries, literal registry comparisons and strict format validator.</li><li>Require a better comparable holdout than the incumbent and a separate weekly-slot selector decision. Do not submit on format alone.</li><li>Only after authorization, download the exact hash-verified single-band GeoTIFF; on <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/">DrivenData</a> choose the file, add the short recorded note and submit. Confirm the live competition and quota there.</li></ol><p>No upload is authorized today. Exact portal acceptance cannot be guaranteed by a local check.</p></section>
    <section><h2>Review &amp; next work</h2><p>The supplied prompt refers to a method lane but does not provide the method paragraph. The feature stack, full registry rasters and organizer-authenticated data are absent in this checkout. No new experiment was run; no fabricated score or uniqueness result is reported.</p>
    <p><a href="https://github.com/apartanish22-droid/ApartGEMSDOE3/blob/main/docs/repo-review-2026-10-28.md">Prior review</a> · <a href="https://github.com/apartanish22-droid/ApartGEMSDOE3/blob/main/docs/research/next-hypotheses-20261028.md">Proposed research</a> · <a href="https://github.com/drivendataorg/gems-prize-reference-solution">Organizer reference solution</a> · <a href="https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and">USGS GeoDAWN</a></p></section></main>'''
    page = '''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>GEMS research · release review</title><style>body{margin:0;background:#0c1423;color:#e8edf7;font:16px/1.6 system-ui,sans-serif} .wrap{max-width:1100px;margin:auto;padding:24px}header{background:#111f35}h1{font-size:2.3rem;margin:.2em 0}h2{margin-top:0}section{background:#142238;border:1px solid #30415c;border-radius:12px;margin:20px 0;padding:24px}.alert{padding:18px;background:#4c2025;border:1px solid #f88;border-radius:8px}.eyebrow{color:#77d0ed;letter-spacing:.12em}a{color:#82d9fa}code{overflow-wrap:anywhere;color:#fff}.scroll{overflow:auto}table{border-collapse:collapse;width:100%;min-width:750px}th,td{text-align:left;vertical-align:top;padding:12px;border-bottom:1px solid #40516b}</style></head><body>''' + body + '</body></html>\n'
    for rel in ['index.html', 'docs/index.html', 'docs/executive-summary.html', 'docs/executive-summary/index.html', 'docs/release-status.html', 'docs/submissions.html', 'docs/research.html', 'docs/hypotheses.html', 'docs/leaderboard.html', 'docs/review.html', 'docs/sources.html']:
        (ROOT / rel).write_text(page, encoding='utf-8')
    print('Built fail-closed review portal')

if __name__ == '__main__':
    main()
