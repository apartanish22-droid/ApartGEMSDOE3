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


def latest_verified_leaderboard(root: Path = ROOT) -> dict:
    """Return the newest verified public-board snapshot, preferring the last same-date read."""
    history_path = root / "registry/leaderboard_history.jsonl"
    if not history_path.is_file():
        raise FileNotFoundError(f"Leaderboard history is missing: {history_path}")
    records = []
    for index, line in enumerate(history_path.read_text(encoding="utf-8").splitlines()):
        if not line.strip():
            continue
        record = json.loads(line)
        if (
            record.get("verified") is True
            and isinstance(record.get("rows"), list)
            and record["rows"]
        ):
            records.append((str(record.get("observed_utc", "")), index, record))
    if not records:
        raise ValueError("Leaderboard history has no verified public-board snapshot")
    latest = max(records, key=lambda item: (item[0], item[1]))[2]
    if not latest.get("source", "").startswith("https://www.drivendata.org/"):
        raise ValueError("Latest verified leaderboard record does not cite the official public source")
    return latest


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

    current = status["current_candidate"]
    if card.get("candidate_id") != current.get("candidate_id"):
        raise ValueError("Current status candidate and current evidence card disagree")
    artifact_path = card.get("artifact_path") or card.get("artifacts", {}).get("primary_zeros_tif")
    raster_sha256 = card.get("raster_sha256") or card.get("artifacts", {}).get("primary_zeros_sha256")
    if not artifact_path or raster_sha256 != current.get("sha256"):
        raise ValueError("Current candidate artifact/hash is incomplete or inconsistent")

    card["release_status"] = card.get("verdict", "negative")
    card["ok_to_download_as_submission"] = False
    latest_path = root / "docs/data/latest-run-card.json"
    latest_path.write_text(json.dumps(card, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    site_data_path = root / "docs/assets/site-data.json"
    site_data = json.loads(site_data_path.read_text())
    site_data["run_card"] = card
    site_data_path.write_text(json.dumps(site_data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    feed_path = root / "docs/data/feed.json"
    feed = json.loads(feed_path.read_text())
    latest_board = latest_verified_leaderboard(root)
    feed["leaderboard"] = latest_board["rows"]
    feed["leaderboard_observed_utc"] = latest_board["observed_utc"]
    feed["leaderboard_verified"] = True
    history_path = root / "registry/leaderboard_history.jsonl"
    history_records = [
        json.loads(line)
        for line in history_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    feed["leaderboard_snapshots"] = len(
        {
            str(record.get("observed_utc", ""))[:10]
            for record in history_records
            if record.get("verified") is True
        }
    )
    feed["leaderboard_source_url"] = latest_board["source"]
    feed["leaderboard_note"] = (
        f"Static official public-board snapshot observed {latest_board['observed_utc']}; "
        f"{latest_board.get('note', '')} Not a score for any GEMSDOE file or an organizer receipt; "
        "no live refresh is implied."
    )
    review_card_path = root / status["current_review"]
    if not review_card_path.is_file():
        raise FileNotFoundError(f"Current review card is missing: {status['current_review']}")
    review_card = json.loads(review_card_path.read_text(encoding="utf-8"))
    if review_card.get("verdict") != "negative" or review_card.get("ok_to_submit") is not False:
        raise ValueError("Current review card must remain fail-closed")
    review_report = review_card.get("review_report")
    if not review_report or not (root / review_report).is_file():
        raise ValueError("Current review card must point to an existing review report")
    feed["generated_utc"] = status["updated_utc"]
    feed["feed_scope_note"] = status.get(
        "feed_scope_note",
        "Static repository snapshot; no live external-source refresh is implied.",
    )
    feed["current_status"] = status
    feed["current_review"] = {
        "review_card": status["current_review"],
        "review_report": review_report,
        "reviewed_utc_date": review_card.get("reviewed_utc_date"),
        "verdict": review_card.get("verdict", "negative"),
        "new_experiment_run": review_card.get("experiments_used", 0) > 0,
    }
    feed["current_candidate"] = {
        "run_card": status["current_run_card"],
        "experiments": None,
        "registry_audit": None,
        "verdict": card["verdict"],
        "ok_to_submit": card["ok_to_submit"],
    }
    feed["submission"] = {
        "candidate_id": current["candidate_id"],
        "file": artifact_path,
        "sha256": raster_sha256,
        "submission_name": card["submission_name"],
        "submission_note": card["submission_note"],
        "download_ok_for_research": card.get("download_for_research_ok", card.get("download_ok_for_audit_only", False)),
        "ok_to_submit": card["ok_to_submit"],
        "slot_used": card.get("slot_used", False),
        "selector_required": card["selector_required"],
        "verdict": card["verdict"],
    }
    feed_path.write_text(json.dumps(feed, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return card


def build_pages(root: Path = ROOT) -> dict[str, str]:
    status = json.loads((root / "registry/current_status.json").read_text())
    current_card = json.loads((root / status["current_run_card"]).read_text())
    current = status["current_candidate"]
    current_id = current["candidate_id"]
    current_hash = current["sha256"]
    audit = json.loads((root / "evidence/nine_site_best_files_audit.json").read_text())
    latest_board = latest_verified_leaderboard(root)
    review_card_rel = status.get("current_review")
    if not review_card_rel:
        raise ValueError("current_status.json must identify the current review card")
    review_card_path = root / review_card_rel
    if not review_card_path.is_file():
        raise FileNotFoundError(f"Current review card is missing: {review_card_rel}")
    review_card = json.loads(review_card_path.read_text(encoding="utf-8"))
    if review_card.get("verdict") != "negative" or review_card.get("ok_to_submit") is not False:
        raise ValueError("Current review card must remain fail-closed")
    review_report_rel = review_card.get("review_report")
    if not review_report_rel:
        raise ValueError("Current review card must identify its report")
    review_report_path = root / review_report_rel
    research_rel = status.get(
        "current_research_shortlist",
        "docs/research/next-hypotheses-review-20261028.md",
    )
    research = root / research_rel
    if not research.is_file() or not review_report_path.is_file():
        raise FileNotFoundError("Current review report and hypothesis notes must exist before site build")
    try:
        review_href = review_report_path.relative_to(root / "docs").as_posix()
        research_href = research.relative_to(root / "docs").as_posix()
    except ValueError as exc:
        raise ValueError("Review and hypothesis reports must be inside docs/") from exc
    review_card_repo_href = repo_link(Path(review_card_rel).as_posix())

    sites = audit["sites"]
    top = max(sites, key=lambda row: row["published_score_OWNER_REPORT"])
    rows = []
    for item in sites:
        site = esc(item["site"])
        score = float(item["published_score_OWNER_REPORT"])
        site_pairings = []
        for pair in audit.get("pairwise", []):
            if pair["a"] == item["site"]:
                site_pairings.append((pair["b"], float(pair["a_dots_within_3px_of_b"]), abs(float(pair["spearman_footprint"]))))
            elif pair["b"] == item["site"]:
                site_pairings.append((pair["a"], float(pair["b_dots_within_3px_of_a"]), abs(float(pair["spearman_footprint"]))))
        peer, overlap, _ = max(site_pairings, key=lambda row: row[1])
        max_rho = max(row[2] for row in site_pairings)
        duplicate_status = f"NOT UNIQUE vs supplied nine: {overlap:.2%} within 3 px of {esc(peer)}; max |rho| {max_rho:.4f}; >70% gate FAIL"
        rows.append(
            "<tr>"
            f'<td><a href="https://github.com/buffedlizard55-lab/{site}">{site}</a></td>'
            f'<td><code>{esc(item["leaderboard_name"])}</code></td>'
            f"<td>OWNER-REPORT {score:.4f}</td>"
            "<td>Not estimable</td>"
            f"<td>{duplicate_status}</td></tr>"
        )
    table = (
        '<div class="scroll"><table><thead><tr><th>Site</th><th>Reported best artifact</th>'
        '<th>Reported score</th><th>New score estimate</th><th>Uniqueness vs these nine</th></tr></thead><tbody>'
        + "".join(rows)
        + "</tbody></table></div>"
    )
    warning = (
        '<section class="alert"><strong>DO NOT SUBMIT.</strong> No candidate has passed all '
        "required scientific, uniqueness, format, and selector gates. No weekly slot was used. "
        f"Current negative candidate {esc(current_id)}; SHA-256 <code>{esc(current_hash)}</code>; "
        f"submission name <code>{esc(current_card.get('submission_name', 'not recorded'))}</code>. "
        "The historical files are audit/research records only; this site does not authorize downloads.</section>"
    )
    # Additional exploratory artifact, kept separate from the current release record.
    # The byte-level format pass is not a uniqueness or submission authorization.
    wchd_card_path = root / "evidence/wchd_run_card.json"
    if wchd_card_path.is_file():
        wchd = json.loads(wchd_card_path.read_text(encoding="utf-8"))
        if wchd.get("verdict") != "negative" or wchd.get("ok_to_submit") is not False:
            raise ValueError("WCHD research artifact must remain fail-closed")
        warning += (
            '<section class="alert"><h2>WCHD research artifact — DO NOT SUBMIT</h2>'
            '<p>Format checks pass against an owner-mirrored template, but its final dots fail the literal '
            'all-registry overlap rule (99.56% against the registered calibration lattice). '
            'The assigned lane was missing and the run exceeded protocol limits; the result is exploratory, not a score estimate. '
            'It is retained for audit, but no download link is provided because the uniqueness and protocol gates fail.</p>'
            f'<p><a href="{esc(repo_link("evidence/wchd_run_card.json"))}">Negative run card</a> · '
            f'<a href="{esc(repo_link("evidence/wchd_literal_recheck.json"))}">Format and overlap recheck</a></p>'
            f'<p>SHA-256 <code>{esc(wchd["raster_sha256"])}</code></p></section>'
        )
    artifact = current_card.get("artifacts", {}).get("primary_zeros_tif", current.get("artifact", ""))
    artifact_name = current_card.get("submission_name", "not recorded")
    holdout_data = current_card.get("holdout_dti") or {}
    holdout = holdout_data.get("primary_hide_and_recover", holdout_data)
    paired = holdout_data.get("paired_delta_vs_02778_champion")
    if paired:
        paired_note = (
            f"Paired delta vs 0.2778 incumbent: {float(paired['mean_boot_delta']):+.6f} "
            f"(95% CI {paired['ci95']}); this does not establish a positive improvement."
        )
    else:
        paired_note = "No paired same-evaluator comparison to the incumbent is recorded; improvement is not established."
    if current_id == "H-APART3-2-CTHG-DHC":
        current_registry_note = "This CTHG-DHC card reports registered-raster overlap examples of 75.90%, 72.25%, and 99.8035% within 3 px; its literal gate fails."
    else:
        current_registry_note = "For this current candidate, the full-registry surface and final-dot comparison was not run; off-catalogue masking is not a uniqueness pass."
    if current_card.get("scientific_integrity_gate", {}).get("issue"):
        science_note = esc(current_card["scientific_integrity_gate"]["issue"])
    else:
        science_note = "Feature-alone leakage canaries were not computed, and the assigned lane is absent; physical mimics remain unresolved."

    home = warning + f'''<section><h2>Decision at a glance</h2>
<p>The highest result among these nine sites is <b>{esc(top['site'])}: OWNER-REPORT {float(top['published_score_OWNER_REPORT']):.4f}</b> for <code>{esc(top['leaderboard_name'])}</code>. This is an owner-supplied report, not an organizer receipt. It does not establish that the artifact's method caused the score or predict the score of a new raster.</p>
<p><a href="executive-summary.html">Open the executive summary</a> for the site-by-site comparison and exact upload checklist.</p>
<p>Current candidate record: <code>{esc(current_id)}</code>, file <code>{esc(artifact)}</code>, SHA-256 <code>{esc(current_hash)}</code>, submission name <code>{esc(artifact_name)}</code>. It is a negative research record; no download or upload is authorized. The associated literal-registry and scientific-integrity gates fail.</p></section>
<section><h2>What blocks a new result?</h2><ul><li>The assigned method paragraph is missing.</li><li>The large feature raster, cached feature stack, and complete registry are not restored in this checkout.</li><li>Historical candidate audits found uniqueness/scientific-integrity failures; format validation alone is insufficient.</li></ul><p class="muted">Details: <a href="release-status.html">release status</a> · <a href="review.html">current repository review</a> · <a href="research.html">unrun research shortlist</a></p></section>'''

    exec_body = warning + f'''<section><h2>Nine-site comparison</h2>
<p>All submitted-score entries below are <b>OWNER-REPORT</b> from the supplied/repository audit. None is organizer-confirmed here. The score estimate for a new submission is <b>not estimable</b>; a HOLDOUT-DTI result cannot be converted to a live score without a validated calibration study.</p>{table}
<p>{esc(top['site'])} is the largest listed owner report ({float(top['published_score_OWNER_REPORT']):.4f}). Existing analysis says the reported nested pruning sequence is consistent with removing low-credit false-positive mass, but no hidden truth or receipt-linked evidence establishes causation. See <a href="{esc(repo_link('knowledge/03_why_02778_and_the_anatomy_of_the_family.md'))}">the evidence and limitations</a>.</p><p>There is no file currently OK to submit. The nine reported files are <b>NOT UNIQUE in this nine-site cohort</b> according to the repository overlap audit; scores remain OWNER-REPORT, not organizer receipts. {current_registry_note} Earlier `H-APART3-2-CTHG-DHC` (`apartgemsdoe3-h-apart3-2-cthg-dhc-37654-20261028T084500Z-5d4d0085-zeros.tif`) had recorded overlaps of 75.90%, 72.25%, and 99.8035% within 3 px and a Band 6 interpretation issue; its paired comparison with the local mask for the 0.2778 OWNER-REPORT incumbent is HOLDOUT-DTI (evaluator GEMSDOE32-HIDE-RECOVER-v3.0, 22,232 withheld positives, paired 95% CI [-0.006306, +0.007311]): delta +0.000571, spanning zero. For the current candidate, HOLDOUT-DTI diagnostic is <b>{float(holdout.get('pooled_dti', 0.0)):.6f}</b> (evaluator <code>{esc(holdout.get('evaluator_version', 'not recorded'))}</code>, n={int(holdout.get('n_withheld_positives', 0))}, 95% CI {esc(holdout.get('ci95', []))}); it is not a leaderboard score projection. {paired_note} Scientific-integrity review: {science_note}</p><p>Current negative candidate: <code>{esc(current_id)}</code> · <code>{esc(artifact)}</code> · SHA-256 <code>{esc(current_hash)}</code>. Not authorized to download or submit; local format validity does not cure scientific or uniqueness failures.</p></section>
<section><h2>How to submit when a candidate is authorized</h2><ol><li>Only after the separate selector authorizes a slot, download the exact hash-verified GeoTIFF linked by the release page.</li><li>Open the correct <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/">DOE GEMS competition</a> and select <b>New submission</b>.</li><li>Choose the single-band GeoTIFF (or a ZIP containing exactly one GeoTIFF) that passed the release checklist. Confirm its CRS, shape, geotransform, and all predicted values in [0, 1].</li><li>Enter the submission name and a short note (140 characters maximum) recorded in the run card. Do not use an estimated score as the note.</li><li>Submit and retain the organizer's receipt. Record the exact file SHA-256 and the receipt's score as <b>ORGANIZER-CONFIRMED</b>.</li></ol><p><b>Current decision: no file is authorized for submission.</b> Exact portal acceptance cannot be guaranteed by a local validator.</p></section>'''

    release = warning + f'''<section><h2>Current release gates</h2><p>{esc(status.get('headline', 'DO NOT SUBMIT'))}</p>
<ul><li>Method lane explicitly assigned: no.</li><li>New surface/final-dot registry comparisons: not run in this review.</li><li>Historical CSHD literal uniqueness: failed; the local format check is against an owner mirror only.</li><li>Organizer-authenticated template: not available in this checkout.</li><li>Weekly slot selected or used: no.</li></ul><p>Machine-readable status: <a href="{esc(repo_link('registry/current_status.json'))}">current status JSON</a> · <a href="{esc(review_card_repo_href)}">current review card</a> · <a href="{esc(repo_link('run_card.json'))}">historical candidate run card</a>.</p></section>'''

    instructions = warning + '''<section><h2>Submission checklist</h2><ol><li>Do not submit until a candidate beats the current holdout incumbent on the agreed spatially blocked, buffered hide-and-recover evaluator, with a paired 95% CI supporting the improvement.</li><li>Run each feature-alone leakage canary; AUC above 0.90 is presumed leakage until resolved.</li><li>Pass the pre-placement surface correlation and post-placement dot overlap gates against every registry raster; log a duplicate and stop on a threshold breach.</li><li>Pass automated single-band GeoTIFF validation against the competition template: matching CRS, shape, transform, finite values in [0,1] across the full array.</li><li>Obtain explicit separate selector authorization within the current weekly slot cap.</li><li>Download the exact authorized file, submit it on the competition page, and save the organizer receipt.</li></ol><p>These checks are independent; a format pass does not override a holdout, uniqueness, scientific-integrity, or selector failure.</p></section>
<section><h2>Submission fields</h2><p>The submission-form text supplied in this project says a single-band GeoTIFF or a ZIP containing one GeoTIFF is accepted. Confirm the live rules on the official competition page before upload. Use the submission name and a concise comment stored in that candidate's run card. The local validator checks file structure/range, not portal account, slot quota, score, or scientific validity.</p><p><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/data/">Competition data / format page</a> (login may be required).</p></section>'''

    research_body = warning + f'''<section><h2>Research status</h2><p>There was no new experiment in this review. The assigned method paragraph was not identifiable, and the predictor stack and full raster registry are missing. The shortlist is preregisterable research, not validated performance or a submission recommendation.</p><p><a href="{esc(research_href)}">Read the ranked four-hypothesis shortlist</a> · <a href="{esc(repo_link('knowledge/03_why_02778_and_the_anatomy_of_the_family.md'))}">Why the 0.2778 owner report does not imply a score projection</a>.</p><h3>Next gates</h3><ol><li>Resolve the lane and restore hash-checked data.</li><li>Run feature-alone canaries.</li><li>Use visible-only buffered segment holdout and exact masking.</li><li>Run literal all-registry checks before and after placement.</li><li>Keep weekly-slot selection separate.</li></ol></section>'''

    hypotheses_body = warning + f'''<section><h2>Unrun candidates</h2><p>The current shortlist ranks four in-band hypotheses by qualitative expected utility and cost, names non-fault mimics, and documents repository overlaps. These are not numeric DTI estimates.</p><ol><li>Buried sediment-cover thickness ridge with a surface-quiescence gate (top research priority; related to unvalidated H61-1).</li><li>Directional semivariogram anisotropy of potential-field residuals.</li><li>Signed cross-edge magnetic–gravity offset persistence.</li><li>Paired signed cross-front topographic profile residual.</li></ol><p><a href="{esc(research_href)}">Full proposal, layer names, caveats, and cost ranking</a>.</p></section>'''

    latest_top = latest_board["rows"][0]
    leaderboard = warning + f'''<section><h2>Scope and evidence classes</h2><p>This page audits the nine supplied site claims; it is not a live leaderboard feed. Best listed result: {esc(top['site'])}, OWNER-REPORT {float(top['published_score_OWNER_REPORT']):.4f}. No new score estimate is available.</p>{table}<p>Latest stored public-board observation ({esc(latest_board.get('observed_utc', 'date not recorded'))}): {esc(latest_top.get('participant', 'not recorded'))} {float(latest_top.get('score', 0.0)):.4f}. This is a static observation from the companion review, not a score for any GEMSDOE file or a receipt. See <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/">the official public leaderboard</a> and <a href="repo-review-2026-10-30.md">the dated review</a>; the feed is not live.</p></section>'''

    test_record = review_card.get("automated_tests", {})
    test_summary = (
        f"{int(test_record.get('pytest_passed', 0))} passed, "
        f"{int(test_record.get('pytest_skipped', 0))} skipped, "
        f"{int(test_record.get('pytest_failed', 0))} failed"
    )
    latest_board_rows = latest_board["rows"]
    latest_top = latest_board_rows[0]
    companion_review_rel = "docs/repo-review-2026-10-30.md"
    companion_review_link = (
        '<a href="repo-review-2026-10-30.md">companion nine-site and source review</a>'
        if (root / companion_review_rel).is_file()
        else ""
    )
    review_body = warning + f'''<section><h2>Current review</h2><p><a href="{esc(review_href)}">Read this branch's session review ({esc(review_card.get('reviewed_utc_date', 'date not recorded'))})</a>. It records the repository audit, test results, evidence limits, and next steps. {companion_review_link}</p><p>Automated checks: {esc(test_summary)}; release-status check: {esc(test_record.get('release_status_check', 'not recorded'))}; format validation is against an owner mirror only. No holdout or uniqueness experiment was run in this branch review.</p><p>The latest stored official public-board observation is dated {esc(latest_board.get('observed_utc', 'date not recorded'))}: {esc(latest_top.get('participant', 'not recorded'))} at {float(latest_top.get('score', 0.0)):.4f}. This is a public leaderboard result for another participant, not a score for any GEMSDOE file or an organizer receipt. The static feed is not live. See the <a href="{esc(repo_link('evidence/repo_review_20261030.json'))}">companion review card</a> and <a href="{esc(repo_link('evidence/nine_site_best_files_audit.json'))}">nine-site byte/overlap audit</a>.</p><p>Historical reports and claims remain distinct from newly verified results. Review the <a href="{esc(review_card_repo_href)}">current session review card</a> and <a href="{esc(repo_link('evidence/irregularities_ledger.json'))}">irregularities ledger</a>.</p></section>'''


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


def build_page(source: dict, audit: dict, status: dict) -> str:
    """Compatibility API for the executive summary; inputs are repository audit records."""
    del source, audit, status  # build_pages loads the same versioned records from ROOT.
    return build_pages(ROOT)["executive-summary.html"]


def main() -> None:
    sync_status_artifacts()
    pages = build_pages()
    for relative, content in pages.items():
        target = ROOT / "docs" / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    status = json.loads((ROOT / "registry/current_status.json").read_text())
    current = status["current_candidate"]
    current_card = json.loads((ROOT / status["current_run_card"]).read_text())
    current_file = current_card.get("artifacts", {}).get("primary_zeros_tif", "")
    current_name = current_card.get("submission_name", "not recorded")
    gateway = (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta http-equiv="refresh" content="0; url=docs/index.html">'
        '<title>ApartGEMSDOE3 — DO NOT SUBMIT</title></head><body>'
        '<h1>DO NOT SUBMIT</h1><p>Current negative candidate '
        + esc(current["candidate_id"]) + ' · SHA-256 <code>' + esc(current["sha256"])
        + '</code> · file <code>' + esc(current_file) + '</code> · submission name <code>'
        + esc(current_name) + '</code>.</p><p><a href="docs/index.html">Open the fail-closed review portal</a>.'
        '</p></body></html>\n'
    )
    (ROOT / "index.html").write_text(gateway, encoding="utf-8")
    print(f"Built {len(pages)} distinct fail-closed pages and the root gateway")


if __name__ == "__main__":
    main()
