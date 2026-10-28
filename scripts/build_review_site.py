#!/usr/bin/env python3
"""Build distinct fail-closed public pages from the audited repository records."""
from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAV = [
    ("index.html", "Overview"),
    ("executive-summary.html", "Executive summary"),
    ("release-status.html", "Release status"),
    ("submissions.html", "How to submit"),
    ("research.html", "Research"),
    ("hypotheses.html", "Hypotheses"),
    ("leaderboard.html", "Score audit"),
    ("review.html", "Repository review"),
    ("sources.html", "Sources"),
]


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def repo_link(path: str) -> str:
    return "https://github.com/apartanish22-droid/ApartGEMSDOE3/blob/main/" + path.lstrip("/")


def page(title: str, body: str, *, prefix: str = "") -> str:
    links = "".join(
        f'<a href="{prefix}{esc(path)}">{esc(label)}</a>' for path, label in NAV
    )
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} · ApartGEMSDOE3</title>
<style>
:root{{color-scheme:dark;--bg:#0b1220;--panel:#142238;--line:#30415c;--text:#e8edf7;--muted:#a8b7cc;--link:#8bd7fa;--alert:#4b2025}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--text);font:16px/1.6 system-ui,sans-serif}}
header{{background:#111f35;border-bottom:1px solid var(--line)}}.wrap{{max-width:1120px;margin:auto;padding:20px}}
.brand{{color:#8bd7fa;letter-spacing:.12em;font-size:.82rem}}h1{{margin:.15em 0;font-size:2.2rem}}h2{{margin-top:0}}nav{{display:flex;flex-wrap:wrap;gap:8px 18px;margin-top:14px}}a{{color:var(--link)}}nav a{{text-decoration:none}}main section{{background:var(--panel);border:1px solid var(--line);border-radius:12px;margin:18px 0;padding:22px}}
.alert{{padding:16px;background:var(--alert);border:1px solid #e47b82;border-radius:8px}}.muted{{color:var(--muted)}}.scroll{{overflow:auto}}table{{border-collapse:collapse;width:100%;min-width:780px}}th,td{{text-align:left;vertical-align:top;padding:10px;border-bottom:1px solid var(--line)}}code{{overflow-wrap:anywhere;color:#fff}}li{{margin:.45em 0}}
</style></head><body><header><div class="wrap"><div class="brand">APARTGEMSDOE3 · RESEARCH / RELEASE REVIEW</div><h1>{esc(title)}</h1><nav aria-label="Main navigation">{links}</nav></div></header>
<main class="wrap">{body}</main></body></html>\n'''


def sync_status_artifacts(root: Path = ROOT) -> dict:
    """Keep public feed/run-card copies aligned with the single current status record."""
    status = json.loads((root / "registry/current_status.json").read_text())
    card_path = root / status["current_run_card"]
    card = json.loads(card_path.read_text())
    if card.get("verdict") != "negative" or card.get("ok_to_submit") is not False:
        raise ValueError("Public status builder requires a fail-closed negative current card")
    if status.get("any_file_ok_to_submit") is not False:
        raise ValueError("Public status builder refuses a current status that authorizes a file")

    latest_path = root / "docs/data/latest-run-card.json"
    latest_path.write_text(json.dumps(card, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    site_data_path = root / "docs/assets/site-data.json"
    site_data = json.loads(site_data_path.read_text())
    site_data["run_card"] = card
    site_data_path.write_text(json.dumps(site_data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    feed_path = root / "docs/data/feed.json"
    feed = json.loads(feed_path.read_text())
    feed["generated_utc"] = status["updated_utc"]
    feed["current_status"] = status
    feed["current_candidate"] = {
        "run_card": status["current_run_card"],
        "experiments": None,
        "registry_audit": None,
        "verdict": card["verdict"],
        "ok_to_submit": card["ok_to_submit"],
    }
    feed["submission"] = {
        "candidate_id": "NO-CURRENT-CANDIDATE (historical audit artifact only)",
        "file": card["artifact_path"],
        "sha256": card["raster_sha256"],
        "submission_name": card["submission_name"],
        "submission_note": card["submission_note"],
        "download_ok_for_research": card["download_ok_for_audit_only"],
        "ok_to_submit": card["ok_to_submit"],
        "slot_used": card["weekly_slots_used"] > 0,
        "selector_required": card["selector_required"],
        "verdict": card["verdict"],
    }
    feed_path.write_text(json.dumps(feed, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return card


def build_pages(root: Path = ROOT) -> dict[str, str]:
    status = json.loads((root / "registry/current_status.json").read_text())
    audit = json.loads((root / "evidence/nine_site_best_files_audit.json").read_text())
    research = root / "docs/research/next-hypotheses-review-20261028.md"
    review = root / "docs/repo-review-current-session-2026-10-28.md"
    if not research.exists() or not review.exists():
        raise FileNotFoundError("Current review and hypothesis notes must exist before site build")

    sites = audit["sites"]
    top = max(sites, key=lambda row: row["published_score_OWNER_REPORT"])
    rows = []
    for item in sites:
        site = esc(item["site"])
        score = float(item["published_score_OWNER_REPORT"])
        rows.append(
            "<tr>"
            f'<td><a href="https://github.com/buffedlizard55-lab/{site}">{site}</a></td>'
            f'<td><code>{esc(item["leaderboard_name"])}</code></td>'
            f"<td>OWNER-REPORT {score:.4f}</td>"
            "<td>Not estimable</td><td>Historical; not authorized</td></tr>"
        )
    table = (
        '<div class="scroll"><table><thead><tr><th>Site</th><th>Reported best artifact</th>'
        '<th>Reported score</th><th>New score estimate</th><th>Decision</th></tr></thead><tbody>'
        + "".join(rows)
        + "</tbody></table></div>"
    )
    warning = (
        '<section class="alert"><strong>DO NOT SUBMIT.</strong> No candidate has passed all '
        "required scientific, uniqueness, format, and selector gates. No weekly slot was used. "
        "The historical files linked here are for audit and learning only.</section>"
    )
    artifact = "apartgemsdoe3-h2-cshd-dual97-axial362-37654-20261028T063000Z-37b32d5b-zeros.tif"

    home = warning + f'''<section><h2>Decision at a glance</h2>
<p>The highest result among these nine sites is <b>{esc(top['site'])}: OWNER-REPORT {float(top['published_score_OWNER_REPORT']):.4f}</b> for <code>{esc(top['leaderboard_name'])}</code>. This is an owner-supplied report, not an organizer receipt. It does not establish that the artifact's method caused the score or predict the score of a new raster.</p>
<p><a href="executive-summary.html">Open the executive summary</a> for the site-by-site comparison and exact upload checklist.</p>
<p>Historical audit artifact only: <a href="downloads/{esc(artifact)}">download the CSHD GeoTIFF</a> · SHA-256 <code>65f2ac84ff2c762495107487769a49e90919c5c6bf4a7948ca77e4a6971e5b38</code> · submission name <code>APARTGEMSDOE3-CSHD-37B32D5B</code>. It passed local range/grid checks against an owner mirror but failed the literal registry gate; <b>DO NOT SUBMIT</b>.</p></section>
<section><h2>What blocks a new result?</h2><ul><li>The assigned method paragraph is missing.</li><li>The large feature raster, cached feature stack, and complete registry are not restored in this checkout.</li><li>Historical candidate audits found uniqueness/scientific-integrity failures; format validation alone is insufficient.</li></ul><p class="muted">Details: <a href="release-status.html">release status</a> · <a href="review.html">current repository review</a> · <a href="research.html">unrun research shortlist</a></p></section>'''

    exec_body = warning + f'''<section><h2>Nine-site comparison</h2>
<p>All submitted-score entries below are <b>OWNER-REPORT</b> from the supplied/repository audit. None is organizer-confirmed here. The score estimate for a new submission is <b>not estimable</b>; a HOLDOUT-DTI result cannot be converted to a live score without a validated calibration study.</p>{table}
<p>{esc(top['site'])} is the largest listed owner report ({float(top['published_score_OWNER_REPORT']):.4f}). Existing analysis says the reported nested pruning sequence is consistent with removing low-credit false-positive mass, but no hidden truth or receipt-linked evidence establishes causation. See <a href="{esc(repo_link('knowledge/03_why_02778_and_the_anatomy_of_the_family.md'))}">the evidence and limitations</a>.</p><p>Historical audit-only file: <a href="downloads/{esc(artifact)}">download CSHD GeoTIFF</a> (<code>APARTGEMSDOE3-CSHD-37B32D5B</code>, SHA-256 <code>65f2ac84ff2c762495107487769a49e90919c5c6bf4a7948ca77e4a6971e5b38</code>). It is not authorized to submit; local format validity does not cure scientific or uniqueness failures.</p></section>
<section><h2>How to submit when a candidate is authorized</h2><ol><li>Only after the separate selector authorizes a slot, download the exact hash-verified GeoTIFF linked by the release page.</li><li>Open the correct <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/">DOE GEMS competition</a> and select <b>New submission</b>.</li><li>Choose the single-band GeoTIFF (or a ZIP containing exactly one GeoTIFF) that passed the release checklist. Confirm its CRS, shape, geotransform, and all predicted values in [0, 1].</li><li>Enter the submission name and a short note (140 characters maximum) recorded in the run card. Do not use an estimated score as the note.</li><li>Submit and retain the organizer's receipt. Record the exact file SHA-256 and the receipt's score as <b>ORGANIZER-CONFIRMED</b>.</li></ol><p><b>Current decision: no file is authorized for submission.</b> Exact portal acceptance cannot be guaranteed by a local validator.</p></section>'''

    release = warning + f'''<section><h2>Current release gates</h2><p>{esc(status.get('headline', 'DO NOT SUBMIT'))}</p>
<ul><li>Method lane explicitly assigned: no.</li><li>New surface/final-dot registry comparisons: not run this review.</li><li>Historical CSHD literal uniqueness: failed; format pass is against an owner mirror only.</li><li>Organizer-authenticated template: not available in this checkout.</li><li>Weekly slot selected or used: no.</li></ul><p>Machine-readable status: <a href="{esc(repo_link('registry/current_status.json'))}">current status JSON</a> · <a href="{esc(repo_link('evidence/session_review_20261028.json'))}">current review card</a> · <a href="{esc(repo_link('run_card.json'))}">historical candidate run card</a>.</p></section>'''

    instructions = warning + '''<section><h2>Submission checklist</h2><ol><li>Do not submit until a candidate beats the current holdout incumbent on the agreed spatially blocked, buffered hide-and-recover evaluator, with a paired 95% CI supporting the improvement.</li><li>Run each feature-alone leakage canary; AUC above 0.90 is presumed leakage until resolved.</li><li>Pass the pre-placement surface correlation and post-placement dot overlap gates against every registry raster; log a duplicate and stop on a threshold breach.</li><li>Pass automated single-band GeoTIFF validation against the competition template: matching CRS, shape, transform, finite values in [0,1] across the full array.</li><li>Obtain explicit separate selector authorization within the current weekly slot cap.</li><li>Download the exact authorized file, submit it on the competition page, and save the organizer receipt.</li></ol><p>These checks are independent; a format pass does not override a holdout, uniqueness, scientific-integrity, or selector failure.</p></section>
<section><h2>Submission fields</h2><p>The submission-form text supplied in this project says a single-band GeoTIFF or a ZIP containing one GeoTIFF is accepted. Confirm the live rules on the official competition page before upload. Use the submission name and a concise comment stored in that candidate's run card. The local validator checks file structure/range, not portal account, slot quota, score, or scientific validity.</p><p><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/data/">Competition data / format page</a> (login may be required).</p></section>'''

    research_body = warning + f'''<section><h2>Research status</h2><p>There was no new experiment in this review. The assigned method paragraph was not identifiable, and the predictor stack and full raster registry are missing. The shortlist is preregisterable research, not validated performance or a submission recommendation.</p><p><a href="research/next-hypotheses-review-20261028.md">Read the ranked four-hypothesis shortlist</a> · <a href="{esc(repo_link('knowledge/03_why_02778_and_the_anatomy_of_the_family.md'))}">Why the 0.2778 owner report does not imply a score projection</a>.</p><h3>Next gates</h3><ol><li>Resolve the lane and restore hash-checked data.</li><li>Run feature-alone canaries.</li><li>Use visible-only buffered segment holdout and exact masking.</li><li>Run literal all-registry checks before and after placement.</li><li>Keep weekly-slot selection separate.</li></ol></section>'''

    hypotheses_body = warning + '''<section><h2>Unrun candidates</h2><p>The current shortlist ranks four in-band hypotheses by qualitative expected utility and cost, names non-fault mimics, and documents repository overlaps. These are not numeric DTI estimates.</p><ol><li>Buried sediment-cover thickness ridge with a surface-quiescence gate (top research priority; related to unvalidated H61-1).</li><li>Directional semivariogram anisotropy of potential-field residuals.</li><li>Signed cross-edge magnetic–gravity offset persistence.</li><li>Paired signed cross-front topographic profile residual.</li></ol><p><a href="research/next-hypotheses-review-20261028.md">Full proposal, layer names, caveats, and cost ranking</a>.</p></section>'''

    leaderboard = warning + f'''<section><h2>Scope and evidence classes</h2><p>This page audits the nine supplied site claims; it is not a live leaderboard feed. Best listed result: {esc(top['site'])}, OWNER-REPORT {float(top['published_score_OWNER_REPORT']):.4f}. No new score estimate is available.</p>{table}<p>Official public leaderboard: <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/">DrivenData leaderboard</a>. It was not fetched during this review, so no current rank is asserted.</p></section>'''

    review_body = warning + f'''<section><h2>Current review</h2><p><a href="repo-review-current-session-2026-10-28.md">Read the current session review</a>. It records test results, missing inputs, stale metadata, and site-build issues.</p><p>Automated checks on the recorded session: 101 passed, 2 skipped; fail-closed release check passed; historical GeoTIFF structural validation passed against a hash-pinned owner mirror. No holdout or uniqueness experiment was run in the current review.</p><p>Historical reports and claims remain distinct from newly verified results. Review the <a href="{esc(repo_link('evidence/session_review_20261028.json'))}">session run card</a> and <a href="{esc(repo_link('evidence/irregularities_ledger.json'))}">irregularities ledger</a>.</p></section>'''

    sources_body = warning + f'''<section><h2>Official review pointers</h2><ul><li><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/">Competition overview</a>, <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">problem description</a>, <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/data/">data/format page</a>, and <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/">leaderboard</a>.</li><li><a href="https://github.com/drivendataorg/gems-prize-reference-solution">DrivenData reference solution</a>.</li><li><a href="https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and">USGS GeoDAWN</a>, <a href="https://www.usgs.gov/3d-elevation-program">USGS 3DEP</a>, <a href="https://gbcge.org/current-projects/ingenious/">INGENIOUS</a>, and <a href="https://gdr.openei.org/submissions/1391">GDR submission 1391</a>.</li><li><a href="https://epsg.io/32611">EPSG:32611</a>.</li></ul><p>These are source pointers for review. Current source contents/reachability were not revalidated in this session. Provenance and prior access notes are in <a href="{esc(repo_link('registry/sources.json'))}">registry/sources.json</a>.</p></section>'''

    docs = {
        "index.html": page("Overview", home),
        "executive-summary.html": page("Executive summary", exec_body),
        "release-status.html": page("Release status", release),
        "submissions.html": page("How to submit", instructions),
        "research.html": page("Research status", research_body),
        "hypotheses.html": page("Research hypotheses", hypotheses_body),
        "leaderboard.html": page("Score audit", leaderboard),
        "review.html": page("Repository review", review_body),
        "sources.html": page("Sources", sources_body),
        "executive-summary/index.html": page(
            "Executive summary",
            exec_body.replace('href="downloads/', 'href="../downloads/').replace(
                'href="../knowledge/', 'href="../../knowledge/'
            ),
            prefix="../",
        ),
    }
    return docs


def main() -> None:
    sync_status_artifacts()
    pages = build_pages()
    for relative, content in pages.items():
        target = ROOT / "docs" / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    print(f"Built {len(pages)} distinct fail-closed pages")


if __name__ == "__main__":
    main()
