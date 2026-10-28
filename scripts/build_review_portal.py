"""Render a fail-closed review portal from the current card; no embedded promotion claims."""
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def build():
    card = json.loads((ROOT / 'run_card.json').read_text())
    audit = json.loads((ROOT / 'evidence/nine_site_refreshed_audit_20261028.json').read_text())
    result = json.loads((ROOT / 'evidence/session_literal_review_20261028.json').read_text())['results'][0]
    esc = html.escape
    rows = []
    for site in audit['sites']:
        p = site['published_scored_artifact']
        repo = site['repo']
        ref = audit['refs'][repo]
        url = f"https://github.com/buffedlizard55-lab/{repo}/blob/{ref}/{p['path']}"
        rows.append(f"<tr><td>{repo}</td><td><a href='{esc(url)}'>{esc(Path(p['path']).name)}</a></td>"
                    f"<td>Unverified owner report: {p['user_reported_live_dti']:.4f}; not ORGANIZER-CONFIRMED</td>"
                    f"<td>Unavailable</td><td>{p['within_3px_of_02778_champion']:.2%} vs GEMSDOE32 reference; not cleared for resubmission</td></tr>")
    hr = card['holdout_dti']['primary_hide_and_recover']
    body = f"""<h1>ApartGEMSDOE3 · Executive review</h1>
    <aside><strong>DO NOT SUBMIT — uniqueness gate failed.</strong> Format-valid is not release-valid.
    No new TIF generated, no submission slot used. Separate selector remains required.</aside>
    <h2>Download and decision</h2><p><a download href='{{prefix}}{esc(card['download_files']['primary_download_path'].removeprefix('docs/'))}'>Download existing CSHD TIF — RESEARCH ONLY</a></p>
    <p>Name: {esc(card['submission_name'])}<br>Note: {esc(card['submission_note'])}<br>SHA-256: <code>{card['raster_sha256']}</code></p>
    <p>Automated recheck: single band; finite whole array in [0,1]; CRS, shape and transform match the pinned template.
    Literal directional overlap within 3 pixels of the registry lattice: <strong>{result['directional_within_3px']:.6%}</strong>, above the 70% limit.
    This is a geometric overlap measurement, not a score. Dense-raster exemptions are not authorized by the protocol.</p>
    <h2>Measured performance, not a leaderboard estimate</h2>
    <p>Historical HOLDOUT-DTI: {hr['dti']}, 95% CI {hr['ci95']}; evaluator {esc(hr['evaluator_version'])};
    {hr['n_withheld_positives']} withheld positive pixels. Not rerun this session. These results do not establish a live score or clear uniqueness.
    Live-score estimate: unavailable. No organizer receipt for CSHD is present.</p>
    <h2>Nine-site historical comparison</h2><p>Snapshot from the pinned repository refs in the linked audit, not a current live feed.
    Scores below are user/owner claims only and are deliberately excluded from verified scoring evidence. No verified estimate exists for these downloads.</p>
    <div class='scroll'><table><tr><th>Site</th><th>Historical best file (source)</th><th>Reported result — unverified</th><th>Estimated score</th><th>Uniqueness / decision</th></tr>{''.join(rows)}</table></div>
    <h2>Why GEMSDOE32 may have performed better</h2>
    <p>The archived method thins the H19-5 family and applies a catalogue collar. Under a distance-tolerant metric,
    spacing predictions can avoid redundant nearby positives while retaining coverage. This is a mechanistic explanation,
    not proof of the reported result: hidden labels and an organizer receipt are absent. A higher score cannot be guaranteed.
    The target is missing fault traces relevant to geothermal exploration, not directly measured vent locations.</p>
    <h2>Scientific input irregularity</h2><p>The concurrent repository review flags inherited band-6 total-count data interpreted as magnetic tilt (IR-CTHG-BAND6-TC-02). This is an additional reason not to promote dependent models. Band metadata and dependent caches must be verified before training resumes. <a href="{prefix}repo-review-2026-10-28.md">Prior scientific review</a>.</p>
    <h2>Next research and limitations</h2><p><a href='{{prefix}}research/session-review-20261028.md'>Ranked hypotheses, three-pass review, limitations and next steps</a>.
    Stop-on-duplicate takes precedence over generating another upload. No new lane paragraph was supplied.
    A space-filling calibration lattice makes this gate restrictive; it must not be silently removed to manufacture uniqueness.</p>
    <h2>Submission instructions (only after all gates pass)</h2><ol><li>Require per-feature leakage canaries, matching spatial holdout improvement with paired confidence interval, literal full-registry checks before placement and on final dots, and strict template validation.</li>
    <li>The separate selector checks the current weekly cap on DrivenData. This site does not allocate slots.</li>
    <li>Only for a cleared candidate, download the single-band .tif, choose it on New submission, paste its short note and save the organizer receipt. The current research file is NOT cleared.</li></ol>
    <h2>Audit and official reference links</h2><ul>
    <li><a href='{{prefix}}run_card.json'>Current run card</a> · <a href='{{prefix}}evidence/session_literal_review_20261028.json'>Byte-level recheck</a> · <a href='{{prefix}}evidence/nine_site_refreshed_audit_20261028.json'>Pinned nine-site audit</a></li>
    <li><a href='https://github.com/drivendataorg/gems-prize-reference-solution'>Organizer reference solution</a></li>
    <li><a href='https://www.drivendata.org/competitions/306/competition-doe-gems/'>Competition</a> · <a href='https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/'>Leaderboard (not verified in this session)</a></li></ul>"""
    style = 'body{font:16px/1.6 system-ui;max-width:1150px;margin:40px auto;padding:20px;color:#192d3a;background:#f6f8fa}aside{padding:24px;background:#ffe4e4;border:2px solid #a11}a{color:#005b9f}table{border-collapse:collapse;width:100%}td,th{border:1px solid #bac7d0;padding:12px;text-align:left}code{overflow-wrap:anywhere}.scroll{overflow:auto}'
    for name in ['index.html','executive-summary.html','executive-summary/index.html','research.html','hypotheses.html','leaderboard.html','sources.html','release-status.html','submissions.html']:
        prefix = '../' if '/' in name else ''
        text = f'<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>ApartGEMSDOE3 — DO NOT SUBMIT</title><style>{style}</style><body>{body.replace("{prefix}", prefix)}</body></html>'
        target = ROOT / 'docs' / name
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_text(text)
    # Root entry points use docs-relative links, not missing root downloads.
    root_text = (ROOT / 'docs/index.html').read_text().replace("href='", "href='docs/")
    root_text = root_text.replace("href='docs/https://", "href='https://")
    (ROOT / 'index.html').write_text(root_text)
    (ROOT / 'docs/assets/site-data.json').write_text(json.dumps({'run_card': card, 'nine_site_audit': audit},indent=2)+'\n')
